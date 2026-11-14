"""Simular y registrar un cargo.

`preparar_cargo` hace las comprobaciones y el cálculo, y la usan tanto
`simular_cargo` como `registrar_cargo`: así los dos no pueden divergir. El
cálculo en sí vive en `app/services/calculo_cargo.py`; acá solo se juntan los
datos que esa función pura necesita (categoría, cantidad de hijos, tarifa,
tabla de descuentos).

Orden fijo de las reglas (design, «El servicio»); el rol y el cuerpo ya los
resolvió FastAPI:
  3. alumno y tipo de cargo existen
  4. (tarea 3.2) temporada del tipo cerrada
  5. (tarea 3.2) forma y referencias, todos los errores juntos
  6. cargo repetido -> 409
  7. cálculo; falta de configuración -> 409
  8. solo al registrar: INSERT y saldo
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import ReglaIncumplida, Ubicacion
from app.models.alumno import Alumno, Inscripcion
from app.models.cargo import Cargo
from app.models.enums import CalculoCargo, CategoriaFamilia, Modalidad, Turno
from app.models.familia import Familia
from app.models.tarifario import (
    DescuentoMes,
    DescuentoModalidad,
    PeriodoCobro,
    TarifaBase,
    TipoCargo,
)
from app.models.usuario import Usuario
from app.schemas.cargos import CargoEntrada, CargoRegistrado, CargoSimulado
from app.services.calculo_cargo import (
    Desglose,
    FaltaDescuento,
    TablaDescuentos,
    calcular_abono,
    calcular_monto_fijo,
)
from app.services.comunes import id_posible

MENSAJE_ALUMNO_INEXISTENTE = "El alumno no existe."
MENSAJE_TIPO_INEXISTENTE = "El tipo de cargo no existe."
MENSAJE_OBLIGATORIO = "Este dato es obligatorio."
MENSAJE_INSCRIPCION_INEXISTENTE = "La inscripción no existe."

_CENTAVO = Decimal("0.01")
# Los tres índices únicos de `cargo` empiezan así (ver app/models/cargo.py).
_PREFIJO_INDICES_UNICOS = "uq_cargo_"

_TURNO = {Turno.MANANA: "mañana", Turno.TARDE: "tarde"}
_MODALIDAD = {
    Modalidad.MES: "Mes",
    Modalidad.QUINCENA: "Quincena",
    Modalidad.SEMANA: "Semana",
    Modalidad.DIA: "Día",
}
_CATEGORIA = {
    CategoriaFamilia.SOCIO: "socio",
    CategoriaFamilia.EMPLEADO: "empleado",
    CategoriaFamilia.NO_SOCIO: "no socio",
}


class ConflictoDeCargo(Exception):
    """Un 409: cargo repetido o falta configuración del tarifario. El mensaje
    ya es el texto para la persona."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


@dataclass(frozen=True)
class CargoPreparado:
    """Lo que dejan los pasos 3 a 7: el desglose y lo necesario para guardar."""

    entrada: CargoEntrada
    temporada_id: int
    familia_id: int
    desglose: Desglose
    # El texto del 409 de repetido, por si lo dispara el índice único.
    mensaje_repetido: str


def _fecha(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


def _mensaje_falta_descuento(falta: FaltaDescuento) -> str:
    categoria = _CATEGORIA[falta.categoria]
    modalidad = _MODALIDAD[falta.modalidad]
    if falta.tramo is None:
        return f"Falta el descuento de la categoría {categoria} para la modalidad {modalidad}."
    # El tramo 4 es «4 o más»; el tramo 1 va en singular.
    cantidad = "4 o más hijos" if falta.tramo >= 4 else f"{falta.tramo} hijo"
    if 1 < falta.tramo < 4:
        cantidad += "s"
    return f"Falta el descuento de la categoría {categoria} para el {modalidad} con {cantidad}."


def _comprobar_existencia(sesion: Session, entrada: CargoEntrada) -> tuple[Alumno, TipoCargo]:
    """Paso 3: el alumno y el tipo existen; se juntan los dos errores.

    Sin tipo no se sabe qué forma pedir, así que acá se responde. `id_posible`
    evita que un id fuera de `bigint` haga fallar a Postgres.
    """
    alumno = sesion.get(Alumno, entrada.alumno_id) if id_posible(entrada.alumno_id) else None
    tipo = (
        sesion.get(TipoCargo, entrada.tipo_cargo_id) if id_posible(entrada.tipo_cargo_id) else None
    )
    errores: list[tuple[Ubicacion, str]] = []
    if alumno is None:
        errores.append((("alumno_id",), MENSAJE_ALUMNO_INEXISTENTE))
    if tipo is None:
        errores.append((("tipo_cargo_id",), MENSAJE_TIPO_INEXISTENTE))
    if alumno is None or tipo is None:
        raise ReglaIncumplida(errores)
    return alumno, tipo


def _comprobar_inscripcion(sesion: Session, entrada: CargoEntrada) -> Inscripcion:
    """Lo mínimo del paso 5 que el cálculo necesita: de la inscripción sale el
    turno. Las demás reglas de forma (tarea 3.2) se suman acá, juntando sus
    errores en el mismo `ReglaIncumplida`."""
    errores: list[tuple[Ubicacion, str]] = []
    if entrada.inscripcion_id is None:
        errores.append((("inscripcion_id",), MENSAJE_OBLIGATORIO))
    if entrada.modalidad is None:
        errores.append((("modalidad",), MENSAJE_OBLIGATORIO))
    inscripcion = (
        sesion.get(Inscripcion, entrada.inscripcion_id)
        if entrada.inscripcion_id is not None and id_posible(entrada.inscripcion_id)
        else None
    )
    if entrada.inscripcion_id is not None and inscripcion is None:
        errores.append((("inscripcion_id",), MENSAJE_INSCRIPCION_INEXISTENTE))
    if errores or inscripcion is None:
        raise ReglaIncumplida(errores)
    return inscripcion


def _existe_repetido(
    sesion: Session, entrada: CargoEntrada, tipo: TipoCargo, inscripcion: Inscripcion | None
) -> bool:
    """Paso 6: la misma condición que el índice único que corresponde."""
    if inscripcion is None:
        condicion = and_(
            Cargo.alumno_id == entrada.alumno_id,
            Cargo.tipo_cargo_id == tipo.id,
            Cargo.modalidad.is_(None),
        )
    elif entrada.modalidad is Modalidad.DIA:
        condicion = and_(
            Cargo.inscripcion_id == inscripcion.id, Cargo.fecha_dia == entrada.fecha_dia
        )
    else:
        condicion = and_(
            Cargo.inscripcion_id == inscripcion.id,
            Cargo.periodo_cobro_id == entrada.periodo_cobro_id,
        )
    return bool(sesion.execute(select(exists().where(condicion))).scalar_one())


def _mensaje_repetido(
    sesion: Session, entrada: CargoEntrada, tipo: TipoCargo, inscripcion: Inscripcion | None
) -> str:
    """El texto del 409, el mismo en la simulación, el registro y el índice."""
    if inscripcion is None:
        return f"El alumno ya tiene un cargo «{tipo.nombre}» en esta temporada."
    turno = _TURNO[inscripcion.turno]
    if entrada.modalidad is Modalidad.DIA and entrada.fecha_dia is not None:
        return (
            f"El alumno ya tiene un cargo «{tipo.nombre}» del día "
            f"{_fecha(entrada.fecha_dia)} en el turno {turno}."
        )
    nombre_periodo = (
        sesion.execute(
            select(PeriodoCobro.nombre).where(PeriodoCobro.id == entrada.periodo_cobro_id)
        ).scalar_one_or_none()
        if entrada.periodo_cobro_id is not None and id_posible(entrada.periodo_cobro_id)
        else None
    )
    return f"El alumno ya tiene un cargo «{tipo.nombre}» de «{nombre_periodo}» en el turno {turno}."


def _tabla_de_descuentos(sesion: Session, temporada_id: int) -> TablaDescuentos:
    """Los descuentos de la temporada (21 filas a lo sumo), en dos consultas."""
    por_modalidad = {
        (fila.categoria, fila.modalidad): fila.porcentaje
        for fila in sesion.execute(
            select(DescuentoModalidad).where(DescuentoModalidad.temporada_id == temporada_id)
        ).scalars()
    }
    mes = {
        (fila.categoria, fila.tramo_hijos): fila.porcentaje
        for fila in sesion.execute(
            select(DescuentoMes).where(DescuentoMes.temporada_id == temporada_id)
        ).scalars()
    }
    return TablaDescuentos(por_modalidad=por_modalidad, mes=mes)


def _calcular(
    sesion: Session,
    tipo: TipoCargo,
    categoria: CategoriaFamilia,
    familia_id: int,
    inscripcion: Inscripcion | None,
    modalidad: Modalidad | None,
) -> Desglose:
    """Paso 7: junta lo que la función pura necesita y la llama. Es el único
    lugar que la invoca; ningún otro calcula un precio."""
    if tipo.calculo is CalculoCargo.MONTO_FIJO:
        # La base exige monto fijo en los tipos de monto fijo; el `or` es para el tipo.
        return calcular_monto_fijo(monto_fijo=tipo.monto_fijo or Decimal(0), categoria=categoria)
    if inscripcion is None or modalidad is None:  # lo garantiza el paso 5
        raise ValueError("Un cargo de tarifario necesita inscripción y modalidad.")

    cantidad_hijos: int | None = None
    if modalidad is Modalidad.MES:
        # Alumnos distintos de la familia inscriptos en el mismo turno y
        # temporada que la inscripción del cargo, el propio incluido.
        cantidad_hijos = sesion.execute(
            select(func.count(func.distinct(Alumno.id)))
            .select_from(Inscripcion)
            .join(Alumno, Alumno.id == Inscripcion.alumno_id)
            .where(
                Alumno.familia_id == familia_id,
                Inscripcion.temporada_id == inscripcion.temporada_id,
                Inscripcion.turno == inscripcion.turno,
            )
        ).scalar_one()

    tarifa = sesion.execute(
        select(TarifaBase.monto).where(
            TarifaBase.temporada_id == tipo.temporada_id,
            TarifaBase.turno == inscripcion.turno,
            TarifaBase.modalidad == modalidad,
        )
    ).scalar_one_or_none()
    if tarifa is None:
        raise ConflictoDeCargo(
            f"Falta la tarifa base del turno {_TURNO[inscripcion.turno]} para la "
            f"modalidad {_MODALIDAD[modalidad]}."
        )
    try:
        return calcular_abono(
            tarifa_base=tarifa,
            categoria=categoria,
            modalidad=modalidad,
            cantidad_hijos=cantidad_hijos,
            descuentos=_tabla_de_descuentos(sesion, tipo.temporada_id),
        )
    except FaltaDescuento as falta:
        raise ConflictoDeCargo(_mensaje_falta_descuento(falta)) from None


def preparar_cargo(sesion: Session, entrada: CargoEntrada) -> CargoPreparado:
    """Pasos 3 a 7. Levanta ReglaIncumplida (422 por campo) o ConflictoDeCargo
    (409); no escribe nada."""
    alumno, tipo = _comprobar_existencia(sesion, entrada)
    inscripcion = (
        _comprobar_inscripcion(sesion, entrada) if tipo.calculo is CalculoCargo.TARIFARIO else None
    )

    # El 409 de repetido va antes que el de configuración: si el cargo ya
    # existe, avisar que falta una tarifa empujaría a cargarla para nada.
    mensaje_repetido = _mensaje_repetido(sesion, entrada, tipo, inscripcion)
    if _existe_repetido(sesion, entrada, tipo, inscripcion):
        raise ConflictoDeCargo(mensaje_repetido)

    # Categoría actual de la familia del alumno: el cargo guarda la que se usó.
    categoria = sesion.execute(
        select(Familia.categoria).where(Familia.id == alumno.familia_id)
    ).scalar_one()
    desglose = _calcular(
        sesion,
        tipo,
        categoria,
        alumno.familia_id,
        inscripcion,
        entrada.modalidad if inscripcion is not None else None,
    )
    return CargoPreparado(
        entrada=entrada,
        temporada_id=tipo.temporada_id,
        familia_id=alumno.familia_id,
        desglose=desglose,
        mensaje_repetido=mensaje_repetido,
    )


def simular_cargo(sesion: Session, entrada: CargoEntrada) -> CargoSimulado:
    """Lo mismo que registrar, sin escribir nada."""
    preparado = preparar_cargo(sesion, entrada)
    d = preparado.desglose
    return CargoSimulado(
        familia_id=preparado.familia_id,
        categoria_aplicada=d.categoria_aplicada,
        cantidad_hijos_aplicada=d.cantidad_hijos_aplicada,
        monto_base=d.monto_base,
        porcentaje_aplicado=d.porcentaje_aplicado,
        monto_total=d.monto_total,
    )


def _es_choque_de_repetido(exc: IntegrityError) -> bool:
    diagnostico = getattr(exc.orig, "diag", None)
    nombre = getattr(diagnostico, "constraint_name", None) or ""
    return bool(nombre.startswith(_PREFIJO_INDICES_UNICOS))


def registrar_cargo(sesion: Session, usuario: Usuario, entrada: CargoEntrada) -> CargoRegistrado:
    """Paso 8 sobre `preparar_cargo`: guarda y suma el saldo. El monto es el
    del cálculo, nunca uno del cliente."""
    preparado = preparar_cargo(sesion, entrada)
    d = preparado.desglose
    cargo = Cargo(
        temporada_id=preparado.temporada_id,
        familia_id=preparado.familia_id,
        alumno_id=entrada.alumno_id,
        tipo_cargo_id=entrada.tipo_cargo_id,
        inscripcion_id=entrada.inscripcion_id,
        modalidad=entrada.modalidad,
        periodo_cobro_id=entrada.periodo_cobro_id,
        fecha_dia=entrada.fecha_dia,
        categoria_aplicada=d.categoria_aplicada,
        cantidad_hijos_aplicada=d.cantidad_hijos_aplicada,
        monto_base=d.monto_base,
        porcentaje_aplicado=d.porcentaje_aplicado,
        monto_total=d.monto_total,
        creado_por=usuario.id,
    )
    sesion.add(cargo)
    try:
        # El flush dispara los índices únicos: un doble clic que pasó la
        # comprobación previa choca acá y se responde igual.
        sesion.flush()
    except IntegrityError as exc:
        sesion.rollback()
        if _es_choque_de_repetido(exc):
            raise ConflictoDeCargo(preparado.mensaje_repetido) from None
        raise

    # El saldo no se guarda: es la suma de los cargos de la familia en la
    # temporada del cargo. Se cuantiza porque la suma vacía daría `0` sin decimales.
    suma = sesion.execute(
        select(func.coalesce(func.sum(Cargo.monto_total), Decimal(0))).where(
            Cargo.familia_id == preparado.familia_id,
            Cargo.temporada_id == preparado.temporada_id,
        )
    ).scalar_one()
    sesion.commit()
    return CargoRegistrado(
        familia_id=cargo.familia_id,
        categoria_aplicada=cargo.categoria_aplicada,
        cantidad_hijos_aplicada=cargo.cantidad_hijos_aplicada,
        monto_base=cargo.monto_base,
        porcentaje_aplicado=cargo.porcentaje_aplicado,
        monto_total=cargo.monto_total,
        id=cargo.id,
        temporada_id=cargo.temporada_id,
        alumno_id=cargo.alumno_id,
        tipo_cargo_id=cargo.tipo_cargo_id,
        inscripcion_id=cargo.inscripcion_id,
        modalidad=cargo.modalidad,
        periodo_cobro_id=cargo.periodo_cobro_id,
        fecha_dia=cargo.fecha_dia,
        creado_por=cargo.creado_por,
        creado_en=cargo.creado_en,
        saldo_pendiente=Decimal(suma).quantize(_CENTAVO),
    )
