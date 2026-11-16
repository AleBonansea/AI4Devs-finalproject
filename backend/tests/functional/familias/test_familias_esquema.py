"""Capability `familias`: las restricciones de `familia`, `persona`,
`familia_persona` y la vista `v_familia_etiqueta`.

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/familias/spec.md`, Requirements
«Categoria de la familia», «Etiqueta de la familia», «Persona reutilizable
entre familias» y «Vinculo de una persona con una familia».

Esta tarea no expone nada por la API, asi que el contrato que se prueba es el
de la base: cada test inserta con SQL crudo sobre los nombres de
`3-modelo-de-datos.md` y comprueba que Postgres guarde o rechace la fila. El
SQL crudo es a proposito: el ORM rechazaria una categoria inexistente antes de
llegar a la base, y el Scenario dice que la rechaza la base.

Cada sentencia rechazada va dentro de `sesion.begin_nested()`: si no, el
error aborta la transaccion y lo que se comprueba despues no corre.

«Se registro primero» es el id menor: los alumnos se insertan en el orden del
Scenario y el id lo asigna la base.
"""

from collections.abc import Mapping
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

# --- preparacion -----------------------------------------------------------


def _rechaza(
    sesion: Session,
    sql: str,
    parametros: Mapping[str, object],
    errores: type[Exception] | tuple[type[Exception], ...] = IntegrityError,
) -> None:
    """La sentencia tiene que fallar en la base, aislada en un savepoint."""
    with pytest.raises(errores), sesion.begin_nested():
        sesion.execute(text(sql), parametros)


def _contar(sesion: Session, sql: str, parametros: Mapping[str, object]) -> int:
    return int(sesion.execute(text(sql), parametros).scalar_one())


_INSERTAR_FAMILIA = "INSERT INTO familia (categoria) VALUES (:categoria) RETURNING id"


def _crear_familia(sesion: Session, categoria: str = "empleado") -> int:
    return int(sesion.execute(text(_INSERTAR_FAMILIA), {"categoria": categoria}).scalar_one())


def _crear_alumno(
    sesion: Session, familia_id: int, nombre: str, apellido: str, nacimiento: date
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO alumno (familia_id, nombre, apellido, fecha_nacimiento) "
                "VALUES (:f, :n, :a, :fn) RETURNING id"
            ),
            {"f": familia_id, "n": nombre, "a": apellido, "fn": nacimiento},
        ).scalar_one()
    )


_INSERTAR_PERSONA = (
    "INSERT INTO persona (nombre, apellido, telefono, dni) "
    "VALUES (:nombre, :apellido, :telefono, :dni) RETURNING id"
)


def _datos_persona(**extra: object) -> dict[str, object]:
    datos: dict[str, object] = {
        "nombre": "Maria",
        "apellido": "Pérez",
        "telefono": "3511234567",
        "dni": None,
    }
    datos.update(extra)
    return datos


def _crear_persona(sesion: Session, **extra: object) -> int:
    return int(sesion.execute(text(_INSERTAR_PERSONA), _datos_persona(**extra)).scalar_one())


_INSERTAR_VINCULO = (
    "INSERT INTO familia_persona "
    "(familia_id, persona_id, es_tutor, autorizado_retiro, contacto_emergencia) "
    "VALUES (:f, :p, :tutor, :retiro, :emergencia)"
)


def _datos_vinculo(familia_id: int, persona_id: int, **extra: object) -> dict[str, object]:
    datos: dict[str, object] = {
        "f": familia_id,
        "p": persona_id,
        "tutor": True,
        "retiro": True,
        "emergencia": False,
    }
    datos.update(extra)
    return datos


def _vincular(sesion: Session, familia_id: int, persona_id: int, **extra: object) -> None:
    sesion.execute(text(_INSERTAR_VINCULO), _datos_vinculo(familia_id, persona_id, **extra))


def _etiqueta(sesion: Session, familia_id: int) -> str:
    return str(
        sesion.execute(
            text("SELECT etiqueta FROM v_familia_etiqueta WHERE familia_id = :f"),
            {"f": familia_id},
        ).scalar_one()
    )


def _vinculos(sesion: Session, familia_id: int, persona_id: int) -> int:
    return _contar(
        sesion,
        "SELECT count(*) FROM familia_persona WHERE familia_id = :f AND persona_id = :p",
        {"f": familia_id, "p": persona_id},
    )


def _familia_perez_ana(sesion: Session) -> int:
    """La familia `Pérez – Ana`: Ana nacida el 2018-07-05 como unico alumno."""
    familia = _crear_familia(sesion, "empleado")
    _crear_alumno(sesion, familia, "Ana", "Pérez", date(2018, 7, 5))
    return familia


# --- Requirement: Categoria de la familia ----------------------------------


class TestCategoriaDeLaFamilia:
    def test_una_familia_con_categoria_valida_queda_guardada_con_id_de_la_base(
        self, sesion: Session
    ) -> None:
        # Scenario: Familia con categoria valida
        familia_id = sesion.execute(text(_INSERTAR_FAMILIA), {"categoria": "empleado"}).scalar_one()
        assert familia_id is not None
        categoria = sesion.execute(
            text("SELECT categoria::text FROM familia WHERE id = :id"), {"id": familia_id}
        ).scalar_one()
        assert categoria == "empleado"

    def test_la_base_rechaza_una_familia_sin_categoria(self, sesion: Session) -> None:
        # Scenario: Familia sin categoria
        antes = _contar(sesion, "SELECT count(*) FROM familia", {})
        _rechaza(sesion, "INSERT INTO familia DEFAULT VALUES", {})
        _rechaza(sesion, _INSERTAR_FAMILIA, {"categoria": None})
        assert _contar(sesion, "SELECT count(*) FROM familia", {}) == antes

    def test_la_base_rechaza_una_categoria_que_no_existe(self, sesion: Session) -> None:
        # Scenario: Categoria que no existe
        antes = _contar(sesion, "SELECT count(*) FROM familia", {})
        _rechaza(
            sesion,
            _INSERTAR_FAMILIA,
            {"categoria": "vip"},
            errores=(DataError, IntegrityError),
        )
        assert _contar(sesion, "SELECT count(*) FROM familia", {}) == antes


# --- Requirement: Etiqueta de la familia -----------------------------------


class TestEtiquetaDeLaFamilia:
    def test_la_etiqueta_de_una_familia_con_un_solo_hijo_es_apellido_raya_nombre(
        self, sesion: Session
    ) -> None:
        # Scenario: Familia con un solo hijo
        familia = _crear_familia(sesion)
        _crear_alumno(sesion, familia, "Juan", "Pérez", date(2020, 3, 10))
        assert _etiqueta(sesion, familia) == "Pérez – Juan"

    def test_al_sumarse_un_hijo_mayor_la_etiqueta_pasa_a_el_y_el_id_no_cambia(
        self, sesion: Session
    ) -> None:
        # Scenario: Se suma un hijo mayor
        familia = _crear_familia(sesion)
        _crear_alumno(sesion, familia, "Juan", "Pérez", date(2020, 3, 10))
        assert _etiqueta(sesion, familia) == "Pérez – Juan"

        _crear_alumno(sesion, familia, "Ana", "Pérez", date(2018, 7, 5))

        assert _etiqueta(sesion, familia) == "Pérez – Ana"
        # AND el id de la familia es el mismo que antes
        assert _contar(sesion, "SELECT count(*) FROM familia WHERE id = :id", {"id": familia}) == 1
        ids_en_la_vista = [
            f[0]
            for f in sesion.execute(
                text("SELECT familia_id FROM v_familia_etiqueta " "WHERE etiqueta = 'Pérez – Ana'")
            )
        ]
        assert ids_en_la_vista == [familia]

    def test_un_hijo_menor_con_otro_apellido_no_cambia_la_etiqueta(self, sesion: Session) -> None:
        # Scenario: Se suma un hijo menor con otro apellido
        familia = _familia_perez_ana(sesion)
        assert _etiqueta(sesion, familia) == "Pérez – Ana"

        _crear_alumno(sesion, familia, "Tomás", "Gómez", date(2019, 11, 20))

        assert _etiqueta(sesion, familia) == "Pérez – Ana"

    def test_un_medio_hermano_mayor_por_un_dia_pasa_a_ser_la_etiqueta(
        self, sesion: Session
    ) -> None:
        # Scenario: Medio hermano mayor con otro apellido
        familia = _familia_perez_ana(sesion)
        assert _etiqueta(sesion, familia) == "Pérez – Ana"

        _crear_alumno(sesion, familia, "Lucas", "Gómez", date(2018, 7, 4))

        assert _etiqueta(sesion, familia) == "Gómez – Lucas"

    def test_entre_mellizos_la_etiqueta_es_del_que_se_registro_primero(
        self, sesion: Session
    ) -> None:
        # Scenario: Mellizos
        familia = _crear_familia(sesion)
        sofia = _crear_alumno(sesion, familia, "Sofía", "Ruiz", date(2019, 5, 1))
        assert _etiqueta(sesion, familia) == "Ruiz – Sofía"

        mateo = _crear_alumno(sesion, familia, "Mateo", "Ruiz", date(2019, 5, 1))

        assert sofia < mateo  # Sofia se registro primero
        assert _etiqueta(sesion, familia) == "Ruiz – Sofía"


# --- Requirement: Persona reutilizable entre familias ----------------------


class TestPersonaReutilizable:
    def test_la_base_rechaza_dos_personas_con_el_mismo_dni(self, sesion: Session) -> None:
        # Scenario: Dos personas con el mismo DNI
        _crear_persona(sesion, nombre="Maria", dni="30111222")
        _rechaza(sesion, _INSERTAR_PERSONA, _datos_persona(nombre="Raul", dni="30111222"))
        assert (
            _contar(sesion, "SELECT count(*) FROM persona WHERE dni = :d", {"d": "30111222"}) == 1
        )

    def test_dos_personas_sin_dni_quedan_guardadas(self, sesion: Session) -> None:
        # Scenario: Dos personas sin DNI
        primera = _crear_persona(sesion, nombre="Maria", dni=None)
        segunda = _crear_persona(sesion, nombre="Raul", dni=None)
        assert primera != segunda
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM persona WHERE id IN (:a, :b) AND dni IS NULL",
                {"a": primera, "b": segunda},
            )
            == 2
        )

    def test_la_base_rechaza_una_persona_sin_telefono(self, sesion: Session) -> None:
        # Scenario: Persona sin telefono
        antes = _contar(sesion, "SELECT count(*) FROM persona", {})
        _rechaza(sesion, _INSERTAR_PERSONA, _datos_persona(telefono=None))
        _rechaza(
            sesion,
            "INSERT INTO persona (nombre, apellido) VALUES ('Maria', 'Pérez')",
            {},
        )
        assert _contar(sesion, "SELECT count(*) FROM persona", {}) == antes

    def test_la_misma_persona_queda_vinculada_a_dos_familias_con_una_sola_fila(
        self, sesion: Session
    ) -> None:
        # Scenario: La misma persona en dos familias
        perez_ana = _familia_perez_ana(sesion)
        gomez_lucia = _crear_familia(sesion, "socio")
        _crear_alumno(sesion, gomez_lucia, "Lucía", "Gómez", date(2019, 2, 2))
        maria = _crear_persona(sesion, nombre="María", apellido="Pérez", dni="30111222")
        _vincular(sesion, perez_ana, maria, tutor=True, retiro=True)

        _vincular(sesion, gomez_lucia, maria, tutor=False, retiro=True)

        assert _vinculos(sesion, perez_ana, maria) == 1
        assert _vinculos(sesion, gomez_lucia, maria) == 1
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM persona WHERE nombre = 'María' AND apellido = 'Pérez'",
                {},
            )
            == 1
        )


# --- Requirement: Vinculo de una persona con una familia -------------------


class TestVinculoPersonaFamilia:
    def test_la_base_rechaza_un_tutor_sin_autorizacion_a_retirar(self, sesion: Session) -> None:
        # Scenario: Tutor sin autorizacion a retirar
        familia = _familia_perez_ana(sesion)
        maria = _crear_persona(sesion)
        _rechaza(
            sesion,
            _INSERTAR_VINCULO,
            _datos_vinculo(familia, maria, tutor=True, retiro=False, emergencia=False),
        )
        assert _vinculos(sesion, familia, maria) == 0

    def test_un_autorizado_a_retirar_que_no_es_tutor_queda_guardado(self, sesion: Session) -> None:
        # Scenario: Autorizado a retirar que no es tutor
        familia = _familia_perez_ana(sesion)
        raul = _crear_persona(sesion, nombre="Raúl")
        _vincular(sesion, familia, raul, tutor=False, retiro=True, emergencia=False)
        fila = sesion.execute(
            text(
                "SELECT es_tutor, autorizado_retiro FROM familia_persona "
                "WHERE familia_id = :f AND persona_id = :p"
            ),
            {"f": familia, "p": raul},
        ).one()
        assert fila[0] is False
        assert fila[1] is True

    def test_la_base_rechaza_un_vinculo_sin_ninguna_marca(self, sesion: Session) -> None:
        # Scenario: Vinculo sin ninguna marca
        familia = _familia_perez_ana(sesion)
        maria = _crear_persona(sesion)
        _rechaza(
            sesion,
            _INSERTAR_VINCULO,
            _datos_vinculo(familia, maria, tutor=False, retiro=False, emergencia=False),
        )
        assert _vinculos(sesion, familia, maria) == 0

    def test_la_base_rechaza_el_mismo_vinculo_dos_veces(self, sesion: Session) -> None:
        # Scenario: El mismo vinculo dos veces
        familia = _familia_perez_ana(sesion)
        maria = _crear_persona(sesion, nombre="María")
        _vincular(sesion, familia, maria, tutor=True, retiro=True)
        _rechaza(
            sesion,
            _INSERTAR_VINCULO,
            _datos_vinculo(familia, maria, tutor=False, retiro=True),
        )
        assert _vinculos(sesion, familia, maria) == 1

    def test_la_base_rechaza_borrar_una_persona_vinculada_y_el_vinculo_sigue(
        self, sesion: Session
    ) -> None:
        # Scenario: Borrar una persona vinculada
        familia = _familia_perez_ana(sesion)
        maria = _crear_persona(sesion, nombre="María")
        _vincular(sesion, familia, maria, tutor=True, retiro=True)

        _rechaza(sesion, "DELETE FROM persona WHERE id = :id", {"id": maria})

        # AND el vinculo sigue en la base
        assert _contar(sesion, "SELECT count(*) FROM persona WHERE id = :id", {"id": maria}) == 1
        assert _vinculos(sesion, familia, maria) == 1
