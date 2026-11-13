"""Capability `semilla`: lo que suma el change `familias-y-alumnos`.

Un test por Scenario nuevo de
`openspec/changes/familias-y-alumnos/specs/semilla/spec.md`:

- «Base con una persona» (Requirement MODIFIED «La semilla solo corre sobre
  una base vacía»). Los otros cuatro Scenarios de ese Requirement ya estan
  en `test_semilla.py`.
- «Las familias de la semilla» (Requirement ADDED «Familias y alumnos de
  ejemplo»).

Misma forma que `test_semilla.py`: `cargar(sesion)` corre dentro de la
transaccion revertida del fixture `sesion`, y lo sembrado se lee con SQL
crudo. Los «exactamente» se comparan como listas ordenadas completas, asi
que falla tanto si sobra como si falta una fila.
"""

from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.semilla import SemillaRechazada, cargar

MENSAJE_BASE_NO_VACIA = "La base no está vacía: la semilla solo corre sobre una base vacía."


def _contar(sesion: Session, tabla: str) -> int:
    sesion.flush()
    return int(sesion.execute(text(f"SELECT count(*) FROM {tabla}")).scalar_one())


# --- Requirement: La semilla solo corre sobre una base vacía ----------------


def test_con_una_persona_la_semilla_se_niega_y_la_base_sigue_con_esa_unica_persona(
    sesion: Session,
) -> None:
    # Scenario: Base con una persona
    # Nombre y DNI distintos de los de la semilla: si la semilla no se negara,
    # no chocaria con la UNIQUE del DNI y el test veria las filas de mas.
    sesion.execute(
        text(
            "INSERT INTO persona (nombre, apellido, telefono, dni) "
            "VALUES ('Hector', 'Ibarra', '3510000001', '40123456')"
        )
    )
    assert _contar(sesion, "temporada") == 0
    assert _contar(sesion, "usuario") == 0
    assert _contar(sesion, "familia") == 0

    with pytest.raises(SemillaRechazada) as error:
        cargar(sesion)

    assert str(error.value) == MENSAJE_BASE_NO_VACIA
    assert _contar(sesion, "temporada") == 0
    assert _contar(sesion, "usuario") == 0
    personas = sesion.execute(text("SELECT nombre, apellido, telefono, dni FROM persona")).all()
    assert [tuple(p) for p in personas] == [("Hector", "Ibarra", "3510000001", "40123456")]


# --- Requirement: Familias y alumnos de ejemplo -----------------------------


def test_la_semilla_crea_exactamente_las_tres_familias_con_sus_alumnos_personas_e_inscripciones(
    sesion: Session,
) -> None:
    # Scenario: Las familias de la semilla
    cargar(sesion)
    sesion.flush()

    # Exactamente tres familias, con su etiqueta y su categoria.
    familias = sesion.execute(
        text(
            "SELECT v.etiqueta, f.categoria::text "
            "FROM familia f JOIN v_familia_etiqueta v ON v.familia_id = f.id "
            "ORDER BY v.etiqueta"
        )
    ).all()
    assert [tuple(f) for f in familias] == [
        ("Gómez – Lucía", "socio"),
        ("Pérez – Ana", "empleado"),
        ("Ruiz – Sofía", "no_socio"),
    ]
    assert _contar(sesion, "familia") == 3

    # Cada alumno con su familia, su fecha y su grupo (nombre y turno) en 2026-27.
    alumnos = sesion.execute(
        text(
            "SELECT v.etiqueta, a.nombre, a.apellido, a.fecha_nacimiento, "
            "       g.nombre, g.turno::text, t.nombre "
            "FROM alumno a "
            "JOIN v_familia_etiqueta v ON v.familia_id = a.familia_id "
            "JOIN inscripcion i ON i.alumno_id = a.id "
            "JOIN grupo g ON g.id = i.grupo_id "
            "JOIN temporada t ON t.id = i.temporada_id "
            "ORDER BY v.etiqueta, a.fecha_nacimiento"
        )
    ).all()
    assert [tuple(a) for a in alumnos] == [
        ("Gómez – Lucía", "Lucía", "Gómez", date(2021, 5, 20), "Delfines", "tarde", "2026-27"),
        ("Pérez – Ana", "Ana", "Pérez", date(2018, 7, 5), "Tiburones", "manana", "2026-27"),
        ("Pérez – Ana", "Juan", "Pérez", date(2020, 3, 10), "Delfines", "manana", "2026-27"),
        ("Ruiz – Sofía", "Sofía", "Ruiz", date(2017, 9, 1), "Tiburones", "tarde", "2026-27"),
    ]
    assert _contar(sesion, "alumno") == 4

    # Exactamente cuatro personas, con telefono y DNI (o sin DNI).
    personas = sesion.execute(
        text("SELECT nombre, apellido, telefono, dni FROM persona ORDER BY apellido, nombre")
    ).all()
    assert [tuple(p) for p in personas] == [
        ("Pablo", "Gómez", "3519998877", "28999888"),
        ("María", "Pérez", "3511234567", "30111222"),
        ("Raúl", "Pérez", "3517654321", None),
        ("Laura", "Ruiz", "3515556666", None),
    ]

    # Los vinculos: tutores con las dos marcas, autorizados solo a retirar.
    vinculos = sesion.execute(
        text(
            "SELECT v.etiqueta, p.nombre, p.apellido, fp.es_tutor, fp.autorizado_retiro "
            "FROM familia_persona fp "
            "JOIN v_familia_etiqueta v ON v.familia_id = fp.familia_id "
            "JOIN persona p ON p.id = fp.persona_id "
            "ORDER BY v.etiqueta, p.apellido, p.nombre"
        )
    ).all()
    assert [tuple(f) for f in vinculos] == [
        ("Gómez – Lucía", "Pablo", "Gómez", True, True),
        ("Gómez – Lucía", "María", "Pérez", False, True),
        ("Pérez – Ana", "María", "Pérez", True, True),
        ("Pérez – Ana", "Raúl", "Pérez", False, True),
        ("Ruiz – Sofía", "Laura", "Ruiz", True, True),
    ]

    # María Pérez es una sola fila vinculada a dos familias.
    maria = (
        sesion.execute(text("SELECT id FROM persona WHERE nombre = 'María' AND apellido = 'Pérez'"))
        .scalars()
        .all()
    )
    assert len(maria) == 1
    familias_de_maria = sesion.execute(
        text("SELECT count(DISTINCT familia_id) FROM familia_persona WHERE persona_id = :p"),
        {"p": maria[0]},
    ).scalar_one()
    assert familias_de_maria == 2

    # Exactamente cuatro inscripciones, todas de 2026-27.
    temporadas_de_inscripciones = (
        sesion.execute(
            text(
                "SELECT t.nombre FROM inscripcion i "
                "JOIN temporada t ON t.id = i.temporada_id ORDER BY t.nombre"
            )
        )
        .scalars()
        .all()
    )
    assert temporadas_de_inscripciones == ["2026-27"] * 4
