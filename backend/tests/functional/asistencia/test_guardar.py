"""Capability `asistencia`: guardar la asistencia de un grupo en una fecha.

Un test por Scenario de `openspec/changes/asistencia/specs/asistencia/spec.md`,
Requirement «Guardar la asistencia de un grupo en una fecha»
(`PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}`).

El autor y la hora de cada registro (`registrado_por`, `registrado_en`) no
salen en la respuesta: se leen de la base. La asistencia «ya tomada» se
inserta con un `registrado_en` explicito (2027-01-05 09:00 -03) para que el
`now()` de una correccion se distinga de el.

Los alumnos se insertan en un orden distinto del de la respuesta, y el cuerpo
del pedido va en otro orden mas, para que el orden por apellido y nombre no
salga gratis de ninguno de los dos.
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    asignar,
    contar_asistencias,
    crear_alumno,
    crear_usuario,
    crear_vigente,
    cuerpo_guardado,
    filas_por_tabla,
    ingresar,
    inscribir,
    insertar_grupo,
    nombres_y_presente,
    registrar_asistencia_con_hora,
    registros_de,
    url_asistencia,
)

DIA = date(2027, 1, 5)
HORA_VIEJA = datetime(2027, 1, 5, 9, 0, tzinfo=timezone(timedelta(hours=-3)))

# --- fixtures --------------------------------------------------------------


@pytest.fixture
def vigente(sesion: Session) -> int:
    return crear_vigente(sesion)


@pytest.fixture
def coordinador_id(sesion: Session) -> int:
    return crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)


@pytest.fixture
def coordinador(cliente: TestClient, coordinador_id: int) -> dict[str, str]:
    return ingresar(cliente, "coordi")


@pytest.fixture
def delfines_manana(sesion: Session, vigente: int) -> int:
    return insertar_grupo(sesion, vigente, "Delfines", "manana")


@pytest.fixture
def jperez_id(sesion: Session, delfines_manana: int) -> int:
    """Profesor asignado a «Delfines» manana."""
    profesor = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
    asignar(sesion, delfines_manana, profesor)
    return profesor


@pytest.fixture
def tres_en_delfines(
    sesion: Session, vigente: int, delfines_manana: int, coordinador_id: int
) -> dict[str, int]:
    """Juan Perez, Sofia Ruiz y Martin Gomez inscriptos en «Delfines» manana.

    Se insertan Ruiz, Perez, Gomez: al reves del orden esperado.
    Devuelve la inscripcion de cada uno, por apellido.
    """
    inscripciones: dict[str, int] = {}
    for nombre, apellido in (("Sofía", "Ruiz"), ("Juan", "Pérez"), ("Martín", "Gómez")):
        alumno = crear_alumno(sesion, nombre, apellido)
        inscripciones[apellido] = inscribir(
            sesion, alumno, delfines_manana, vigente, "manana", coordinador_id
        )
    return inscripciones


@pytest.fixture
def ya_tomada_por_jperez(
    sesion: Session, tres_en_delfines: dict[str, int], jperez_id: int
) -> dict[str, int]:
    """La asistencia del 2027-01-05 registrada por `jperez` a las 09:00 -03:
    Juan y Sofia presentes, Martin ausente."""
    registrar_asistencia_con_hora(
        sesion, tres_en_delfines["Pérez"], DIA, True, jperez_id, HORA_VIEJA
    )
    registrar_asistencia_con_hora(
        sesion, tres_en_delfines["Ruiz"], DIA, True, jperez_id, HORA_VIEJA
    )
    registrar_asistencia_con_hora(
        sesion, tres_en_delfines["Gómez"], DIA, False, jperez_id, HORA_VIEJA
    )
    return tres_en_delfines


# --- Requirement: Guardar la asistencia de un grupo en una fecha -----------


class TestGuardarLaAsistencia:
    def test_tomar_la_asistencia_responde_por_apellido_y_deja_tres_registros_de_jperez(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        delfines_manana: int,
        tres_en_delfines: dict[str, int],
        jperez_id: int,
        coordinador_id: int,
    ) -> None:
        # Scenario: Tomar la asistencia del día
        # Ruido: otro grupo con un inscripto, y un registro de otro dia. Ni
        # uno ni otro cuentan entre los registros del 2027-01-05 de Delfines.
        tiburones = insertar_grupo(sesion, vigente, "Tiburones", "manana")
        ana = crear_alumno(sesion, "Ana", "Pérez")
        inscribir(sesion, ana, tiburones, vigente, "manana", coordinador_id)
        registrar_asistencia_con_hora(
            sesion, tres_en_delfines["Gómez"], date(2027, 1, 6), True, coordinador_id, HORA_VIEJA
        )
        jperez = ingresar(cliente, "jperez")

        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado(
                (tres_en_delfines["Pérez"], True),
                (tres_en_delfines["Ruiz"], True),
                (tres_en_delfines["Gómez"], False),
            ),
            headers=jperez,
        )

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["grupo_id"] == delfines_manana
        assert cuerpo["grupo"] == "Delfines"
        assert cuerpo["turno"] == "manana"
        assert cuerpo["fecha"] == "2027-01-05"
        assert nombres_y_presente(cuerpo) == [
            ("Martín", "Gómez", False),
            ("Juan", "Pérez", True),
            ("Sofía", "Ruiz", True),
        ]
        assert [a["inscripcion_id"] for a in cuerpo["alumnos"]] == [
            tres_en_delfines["Gómez"],
            tres_en_delfines["Pérez"],
            tres_en_delfines["Ruiz"],
        ]

        assert contar_asistencias(sesion, DIA) == 3
        esperado = {"Pérez": True, "Ruiz": True, "Gómez": False}
        for apellido, presente in esperado.items():
            registros = registros_de(sesion, tres_en_delfines[apellido], DIA)
            assert len(registros) == 1, (apellido, registros)
            assert registros[0].presente is presente, apellido
            assert registros[0].registrado_por == jperez_id, apellido
        # El registro del otro dia sigue como estaba.
        otro = registros_de(sesion, tres_en_delfines["Gómez"], date(2027, 1, 6))
        assert [(r.presente, r.registrado_por) for r in otro] == [(True, coordinador_id)]

    def test_corregir_deja_un_solo_registro_de_martin_con_el_coordinador_como_autor(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        ya_tomada_por_jperez: dict[str, int],
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Corregir una asistencia ya tomada
        martin = ya_tomada_por_jperez["Gómez"]

        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((martin, True)),
            headers=coordinador,
        )

        assert respuesta.status_code == 200, respuesta.text
        assert nombres_y_presente(respuesta.json()) == [
            ("Martín", "Gómez", True),
            ("Juan", "Pérez", True),
            ("Sofía", "Ruiz", True),
        ]
        registros = registros_de(sesion, martin, DIA)
        assert len(registros) == 1, registros
        assert registros[0].presente is True
        assert registros[0].registrado_por == coordinador_id
        assert registros[0].registrado_en != HORA_VIEJA
        assert contar_asistencias(sesion, DIA) == 3

    def test_los_que_no_vienen_en_el_pedido_quedan_como_estaban(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        ya_tomada_por_jperez: dict[str, int],
        jperez_id: int,
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Los que no vienen en el pedido no se tocan
        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((ya_tomada_por_jperez["Gómez"], True)),
            headers=coordinador,
        )

        assert respuesta.status_code == 200, respuesta.text
        juan = registros_de(sesion, ya_tomada_por_jperez["Pérez"], DIA)
        assert len(juan) == 1, juan
        assert juan[0].presente is True
        assert juan[0].registrado_por == jperez_id
        assert juan[0].registrado_en == HORA_VIEJA
        # Contraste: el que si vino en el pedido cambio de autor, asi que el
        # pedido se aplico y lo de Juan no quedo igual por no guardar nada.
        martin = registros_de(sesion, ya_tomada_por_jperez["Gómez"], DIA)
        assert [(r.presente, r.registrado_por) for r in martin] == [(True, coordinador_id)]

    def test_guardar_parte_de_la_lista_deja_a_los_demas_en_null_y_un_solo_registro(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        tres_en_delfines: dict[str, int],
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Guardar parte de la lista
        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((tres_en_delfines["Pérez"], True)),
            headers=coordinador,
        )

        assert respuesta.status_code == 200, respuesta.text
        assert nombres_y_presente(respuesta.json()) == [
            ("Martín", "Gómez", None),
            ("Juan", "Pérez", True),
            ("Sofía", "Ruiz", None),
        ]
        assert contar_asistencias(sesion, DIA) == 1
        juan = registros_de(sesion, tres_en_delfines["Pérez"], DIA)
        assert [(r.presente, r.registrado_por) for r in juan] == [(True, coordinador_id)]

    def test_marcar_presente_a_la_manana_no_cambia_el_ausente_de_la_tarde(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        delfines_manana: int,
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Alumno inscripto en los dos turnos
        pulpos_tarde = insertar_grupo(sesion, vigente, "Pulpos", "tarde")
        otro_profesor = crear_usuario(sesion, "cfernandez", RolUsuario.PROFESOR)
        juan = crear_alumno(sesion, "Juan", "Pérez")
        # La de la tarde se crea primero: si el guardado tomara la primera
        # inscripcion del alumno en vez de la del pedido, pisaria esta.
        juan_tarde = inscribir(sesion, juan, pulpos_tarde, vigente, "tarde", coordinador_id)
        juan_manana = inscribir(sesion, juan, delfines_manana, vigente, "manana", coordinador_id)
        registrar_asistencia_con_hora(sesion, juan_tarde, DIA, False, otro_profesor, HORA_VIEJA)

        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((juan_manana, True)),
            headers=coordinador,
        )

        assert respuesta.status_code == 200, respuesta.text
        assert nombres_y_presente(respuesta.json()) == [("Juan", "Pérez", True)]
        tarde = registros_de(sesion, juan_tarde, DIA)
        assert len(tarde) == 1, tarde
        assert tarde[0].presente is False
        assert tarde[0].registrado_por == otro_profesor
        assert tarde[0].registrado_en == HORA_VIEJA
        manana = registros_de(sesion, juan_manana, DIA)
        assert [(r.presente, r.registrado_por) for r in manana] == [(True, coordinador_id)]

        abrir_tarde = cliente.get(url_asistencia(pulpos_tarde, "2027-01-05"), headers=coordinador)
        assert abrir_tarde.status_code == 200, abrir_tarde.text
        assert nombres_y_presente(abrir_tarde.json()) == [("Juan", "Pérez", False)]
        assert abrir_tarde.json()["alumnos"][0]["inscripcion_id"] == juan_tarde

    def test_guardar_solo_suma_una_fila_en_asistencia_y_ninguna_en_otra_tabla(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        delfines_manana: int,
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Guardar la asistencia no toca nada más
        martin = crear_alumno(sesion, "Martín", "Gómez")
        inscripcion = inscribir(sesion, martin, delfines_manana, vigente, "manana", coordinador_id)
        # El login va antes de contar: lo que haga el ingreso no es del PUT.
        antes = filas_por_tabla(sesion)
        assert "asistencia" in antes, antes

        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((inscripcion, False)),
            headers=coordinador,
        )

        assert respuesta.status_code == 200, respuesta.text
        despues = filas_por_tabla(sesion)
        assert set(despues) == set(antes)
        esperado = {**antes, "asistencia": antes["asistencia"] + 1}
        assert despues == esperado


# --- Requirement: Guardar la asistencia (tarea 7.3) --------------------------
# Clase aparte para no tocar los tests que ya estaban. El estado previo lleva
# `registrado_en` fijado a mano (HORA_VIEJA): `now()` de Postgres es la hora
# de inicio de la transaccion y el test corre dentro de una sola, asi que sin
# fijarlo un registro reescrito tendria la misma hora que el original.


class TestGuardarSoloLoQueCambia:
    def test_corregir_a_martin_no_cambia_autor_ni_hora_de_juan_y_sofia(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        ya_tomada_por_jperez: dict[str, int],
        jperez_id: int,
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Corregir a uno no cambia el autor de los demás
        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado(
                (ya_tomada_por_jperez["Pérez"], True),
                (ya_tomada_por_jperez["Ruiz"], True),
                (ya_tomada_por_jperez["Gómez"], True),
            ),
            headers=coordinador,
        )

        assert respuesta.status_code == 200, respuesta.text
        assert nombres_y_presente(respuesta.json()) == [
            ("Martín", "Gómez", True),
            ("Juan", "Pérez", True),
            ("Sofía", "Ruiz", True),
        ]

        for apellido in ("Pérez", "Ruiz"):
            registros = registros_de(sesion, ya_tomada_por_jperez[apellido], DIA)
            assert len(registros) == 1, (apellido, registros)
            assert registros[0].presente is True, apellido
            assert registros[0].registrado_por == jperez_id, apellido
            assert registros[0].registrado_en == HORA_VIEJA, (apellido, registros[0])

        martin = registros_de(sesion, ya_tomada_por_jperez["Gómez"], DIA)
        assert len(martin) == 1, martin
        assert martin[0].presente is True
        assert martin[0].registrado_por == coordinador_id
        assert martin[0].registrado_en != HORA_VIEJA
        assert contar_asistencias(sesion, DIA) == 3

    def test_guardar_lo_mismo_deja_autor_y_hora_de_jperez(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        tres_en_delfines: dict[str, int],
        jperez_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Guardar lo mismo no cambia nada
        # Given del Scenario: solo Juan presente y Martin ausente (Sofia sin tomar).
        juan = tres_en_delfines["Pérez"]
        martin = tres_en_delfines["Gómez"]
        registrar_asistencia_con_hora(sesion, juan, DIA, True, jperez_id, HORA_VIEJA)
        registrar_asistencia_con_hora(sesion, martin, DIA, False, jperez_id, HORA_VIEJA)

        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((juan, True), (martin, False)),
            headers=coordinador,
        )

        assert respuesta.status_code == 200, respuesta.text
        assert nombres_y_presente(respuesta.json()) == [
            ("Martín", "Gómez", False),
            ("Juan", "Pérez", True),
            ("Sofía", "Ruiz", None),
        ]
        for inscripcion, presente in ((juan, True), (martin, False)):
            registros = registros_de(sesion, inscripcion, DIA)
            assert len(registros) == 1, registros
            assert registros[0].presente is presente
            assert registros[0].registrado_por == jperez_id
            assert registros[0].registrado_en == HORA_VIEJA, registros[0]
        assert contar_asistencias(sesion, DIA) == 2
