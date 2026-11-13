"""El alta de un alumno: familia, personas, vinculos, alumno e inscripcion en
una sola transaccion.

Las reglas se comprueban en un orden fijo (design, «El alta, en un servicio,
con las reglas en un orden fijo»): permiso del Profesor, grupo, familia y
personas, y recien entonces se escribe.
"""

from dataclasses import dataclass

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import ReglaIncumplida, Ubicacion
from app.models.alumno import Alumno, Inscripcion
from app.models.enums import CategoriaFamilia
from app.models.familia import Familia, FamiliaPersona, Persona, v_familia_etiqueta
from app.models.grupo import Grupo, GrupoProfesor
from app.models.temporada import EstadoTemporada, Temporada
from app.models.usuario import RolUsuario, Usuario
from app.schemas.alumnos import AltaAlumnoEntrada, PersonaNueva, PersonaReutilizada

MENSAJE_GRUPO_INEXISTENTE = "El grupo no existe."
MENSAJE_GRUPO_INACTIVO = "El grupo no está activo."
MENSAJE_GRUPO_NO_VIGENTE = "El grupo no es de la temporada vigente."
MENSAJE_OBLIGATORIO = "Este dato es obligatorio."
MENSAJE_CATEGORIA_EXISTENTE = "La categoría de una familia existente no se cambia en el alta."
MENSAJE_FAMILIA_INEXISTENTE = "La familia no existe."
MENSAJE_PERSONA_INEXISTENTE = "La persona no existe."
MENSAJE_PERSONA_REPETIDA = "Esa persona ya está en el alta."
MENSAJE_PERSONA_YA_VINCULADA = "Esa persona ya está vinculada a la familia."
MENSAJE_DNI_CARGADO = "Ya hay una persona con ese DNI. Buscala por DNI para reutilizarla."
MENSAJE_SIN_TUTOR = "La familia nueva necesita al menos un tutor."

# Tope de las columnas BIGINT. Un id mas grande hacia fallar a Postgres y
# respondia 500; se trata como inexistente.
_ID_MAXIMO = 2**63 - 1

# Nombre de la restriccion de persona.dni (ver app/models/familia.py).
_RESTRICCION_DNI = "uq_persona_dni"


class GrupoAjeno(Exception):
    """El Profesor eligio un grupo que no tiene asignado."""


class _ChoqueDeDni(Exception):
    """El INSERT de una persona nueva choco con uq_persona_dni: otra alta
    cargo el mismo DNI despues de la comprobacion previa."""

    def __init__(self, indice: int) -> None:
        super().__init__(indice)
        self.indice = indice


@dataclass(frozen=True)
class AltaRegistrada:
    alumno: Alumno
    familia: Familia
    etiqueta: str
    grupo: Grupo


def _id_posible(valor: int) -> bool:
    return 1 <= valor <= _ID_MAXIMO


def _comprobar_grupo(sesion: Session, grupo_id: int) -> Grupo:
    """Paso 3: el grupo existe, esta activo y es de la temporada vigente."""
    fila = (
        sesion.execute(
            select(Grupo, Temporada.estado)
            .join(Temporada, Temporada.id == Grupo.temporada_id)
            .where(Grupo.id == grupo_id)
        ).one_or_none()
        if _id_posible(grupo_id)
        else None
    )
    if fila is None:
        raise ReglaIncumplida([(("grupo_id",), MENSAJE_GRUPO_INEXISTENTE)])
    grupo: Grupo = fila[0]
    estado: EstadoTemporada = fila[1]
    if not grupo.activo:
        raise ReglaIncumplida([(("grupo_id",), MENSAJE_GRUPO_INACTIVO)])
    if estado != EstadoTemporada.VIGENTE:
        raise ReglaIncumplida([(("grupo_id",), MENSAJE_GRUPO_NO_VIGENTE)])
    return grupo


def _comprobar_profesor(sesion: Session, usuario: Usuario, grupo_id: int) -> None:
    """Paso 2: el Profesor solo inscribe en sus grupos.

    Va antes de mirar el grupo: un grupo ajeno da 403 exista o no, este
    activo o no, asi el alta no le cuenta nada de grupos que no son suyos.
    Y antes del paso 4, para que no sirva de oraculo de familias y personas
    ajenas.
    """
    if usuario.rol != RolUsuario.PROFESOR:
        return
    # Un id fuera de rango no puede estar asignado; ademas haria fallar a
    # Postgres.
    asignado = (
        _id_posible(grupo_id)
        and sesion.execute(
            select(
                exists().where(
                    GrupoProfesor.grupo_id == grupo_id, GrupoProfesor.usuario_id == usuario.id
                )
            )
        ).scalar_one()
    )
    if not asignado:
        raise GrupoAjeno


def _comprobar_familia_y_personas(
    sesion: Session, entrada: AltaAlumnoEntrada
) -> Familia | CategoriaFamilia:
    """Paso 4: junta todos los errores de familia y personas en un solo 422.

    Devuelve la familia existente, o la categoria de la familia nueva.
    """
    errores: list[tuple[Ubicacion, str]] = []

    familia: Familia | None = None
    if entrada.familia_id is not None:
        if entrada.categoria is not None:
            errores.append((("categoria",), MENSAJE_CATEGORIA_EXISTENTE))
        if _id_posible(entrada.familia_id):
            familia = sesion.get(Familia, entrada.familia_id)
        if familia is None:
            errores.append((("familia_id",), MENSAJE_FAMILIA_INEXISTENTE))
    elif entrada.categoria is None:
        errores.append((("categoria",), MENSAJE_OBLIGATORIO))

    # Lo que hay en la base, en tres consultas para todas las personas.
    ids_pedidos = {
        p.persona_id
        for p in entrada.personas
        if isinstance(p, PersonaReutilizada) and _id_posible(p.persona_id)
    }
    dnis_pedidos = {p.dni for p in entrada.personas if isinstance(p, PersonaNueva) and p.dni}
    ids_existentes = (
        set(sesion.execute(select(Persona.id).where(Persona.id.in_(ids_pedidos))).scalars())
        if ids_pedidos
        else set()
    )
    ids_vinculados = (
        set(
            sesion.execute(
                select(FamiliaPersona.persona_id).where(
                    FamiliaPersona.familia_id == familia.id,
                    FamiliaPersona.persona_id.in_(ids_pedidos),
                )
            ).scalars()
        )
        if familia is not None and ids_pedidos
        else set()
    )
    dnis_cargados = (
        set(sesion.execute(select(Persona.dni).where(Persona.dni.in_(dnis_pedidos))).scalars())
        if dnis_pedidos
        else set()
    )

    vistos_ids: set[int] = set()
    vistos_dnis: set[str] = set()
    for i, persona in enumerate(entrada.personas):
        if isinstance(persona, PersonaReutilizada):
            lugar: Ubicacion = ("personas", i, "persona_id")
            if persona.persona_id in vistos_ids:
                errores.append((lugar, MENSAJE_PERSONA_REPETIDA))
                continue
            vistos_ids.add(persona.persona_id)
            if persona.persona_id not in ids_existentes:
                errores.append((lugar, MENSAJE_PERSONA_INEXISTENTE))
            elif persona.persona_id in ids_vinculados:
                errores.append((lugar, MENSAJE_PERSONA_YA_VINCULADA))
        elif persona.dni is not None:
            lugar = ("personas", i, "dni")
            if persona.dni in dnis_cargados:
                errores.append((lugar, MENSAJE_DNI_CARGADO))
            elif persona.dni in vistos_dnis:
                # Dos personas nuevas con el mismo DNI son la misma persona.
                errores.append((lugar, MENSAJE_PERSONA_REPETIDA))
            vistos_dnis.add(persona.dni)

    if entrada.familia_id is None and not any(p.es_tutor for p in entrada.personas):
        errores.append((("personas",), MENSAJE_SIN_TUTOR))

    if errores:
        raise ReglaIncumplida(errores)
    if familia is not None:
        return familia
    # Sin errores y sin familia_id, la categoria vino (si no, habria error).
    # La comprobacion repetida es para el tipo, no para el negocio.
    categoria = entrada.categoria
    if categoria is None:
        raise ReglaIncumplida([(("categoria",), MENSAJE_OBLIGATORIO)])
    return categoria


def _escribir(
    sesion: Session,
    usuario: Usuario,
    entrada: AltaAlumnoEntrada,
    grupo: Grupo,
    familia_o_categoria: Familia | CategoriaFamilia,
) -> tuple[Alumno, Familia]:
    """Paso 5: familia (si es nueva), personas nuevas, vinculos, alumno e
    inscripcion, en la transaccion de la peticion.

    Los modelos no declaran relationship(), asi que se hace flush cuando
    hace falta el id generado de una fila para la FK de la siguiente.
    """
    if isinstance(familia_o_categoria, Familia):
        familia = familia_o_categoria
    else:
        familia = Familia(categoria=familia_o_categoria)
        sesion.add(familia)
        sesion.flush()

    for i, persona in enumerate(entrada.personas):
        if isinstance(persona, PersonaReutilizada):
            persona_id = persona.persona_id
        else:
            # El DNI ya llega normalizado del esquema.
            nueva = Persona(
                nombre=persona.nombre,
                apellido=persona.apellido,
                telefono=persona.telefono,
                dni=persona.dni,
            )
            sesion.add(nueva)
            # Este flush es el unico que inserta en persona: aca se sabe de
            # que fila del alta es el DNI si otra alta se adelanto.
            try:
                sesion.flush()
            except IntegrityError as exc:
                if _es_choque_de_dni(exc):
                    raise _ChoqueDeDni(i) from exc
                raise
            persona_id = nueva.id
        # Todas autorizadas a retirar: la seccion es «Personas autorizadas a
        # retirar» y este alta no carga contactos de emergencia.
        sesion.add(
            FamiliaPersona(
                familia_id=familia.id,
                persona_id=persona_id,
                es_tutor=persona.es_tutor,
                autorizado_retiro=True,
                contacto_emergencia=False,
            )
        )

    alumno = Alumno(
        familia_id=familia.id,
        nombre=entrada.nombre,
        apellido=entrada.apellido,
        fecha_nacimiento=entrada.fecha_nacimiento,
    )
    sesion.add(alumno)
    sesion.flush()
    # Temporada y turno se copian del grupo; la FK compuesta lo garantiza.
    sesion.add(
        Inscripcion(
            alumno_id=alumno.id,
            grupo_id=grupo.id,
            temporada_id=grupo.temporada_id,
            turno=grupo.turno,
            creado_por=usuario.id,
        )
    )
    sesion.flush()
    return alumno, familia


def _es_choque_de_dni(exc: IntegrityError) -> bool:
    diagnostico = getattr(exc.orig, "diag", None)
    return getattr(diagnostico, "constraint_name", None) == _RESTRICCION_DNI


def registrar_alumno(
    sesion: Session, usuario: Usuario, entrada: AltaAlumnoEntrada
) -> AltaRegistrada:
    """Da de alta al alumno. Levanta ReglaIncumplida (422 por campo) o
    GrupoAjeno (403); en los dos casos no escribe nada."""
    _comprobar_profesor(sesion, usuario, entrada.grupo_id)
    grupo = _comprobar_grupo(sesion, entrada.grupo_id)
    familia_o_categoria = _comprobar_familia_y_personas(sesion, entrada)

    try:
        alumno, familia = _escribir(sesion, usuario, entrada, grupo, familia_o_categoria)
        sesion.commit()
    except _ChoqueDeDni as choque:
        # Carrera: otra alta cargo el mismo DNI despues del paso 4. Se revierte
        # todo lo escrito y se responde lo mismo que si el paso 4 lo hubiera
        # visto. No se vuelve a consultar la base para ubicar el DNI: despues
        # de revertir, la fila de la otra alta puede no verse (sin commit
        # todavia, o revertida con esta transaccion).
        sesion.rollback()
        raise ReglaIncumplida([(("personas", choque.indice, "dni"), MENSAJE_DNI_CARGADO)]) from None
    except IntegrityError:
        sesion.rollback()
        raise

    # La etiqueta sale de la vista, ya con el alumno nuevo contado.
    etiqueta = sesion.execute(
        select(v_familia_etiqueta.c.etiqueta).where(v_familia_etiqueta.c.familia_id == familia.id)
    ).scalar_one()
    return AltaRegistrada(alumno=alumno, familia=familia, etiqueta=etiqueta, grupo=grupo)
