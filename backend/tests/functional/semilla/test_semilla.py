"""Capability `semilla`: la base de demostracion con una sola orden.

Un test por Scenario de
`openspec/changes/tarifario-y-semilla/specs/semilla/spec.md`.

La interfaz que se prueba la fija `design.md` («La semilla vive en
`app/semilla.py`»): `verificar_base_local(url)`, `cargar(sesion)` y la
excepcion `SemillaRechazada`. `cargar` hace flush y nunca commit, asi que
corre dentro de la transaccion revertida del fixture `sesion`: la base de
pruebas arranca vacia en cada test y queda limpia al terminar.

Lo sembrado se lee con SQL crudo sobre los nombres de `3-modelo-de-datos.md`,
no con los modelos: lo que se comprueba es lo que quedo en la base. Los
Scenarios de «exactamente N» comparan listas ordenadas completas, asi que
fallan si sobra o falta una fila, y los de valores fijan cada celda.
Montos y porcentajes se comparan como `Decimal` exacto.

`scripts/seed.py` no se prueba aca: lo corre a mano la tarea 2.2.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario
from app.semilla import SemillaRechazada, cargar, verificar_base_local

MENSAJE_BASE_NO_VACIA = "La base no está vacía: la semilla solo corre sobre una base vacía."
MENSAJE_BASE_NO_LOCAL = "La semilla solo corre contra una base local."
CONTRASENA_SEMILLA = "Verano2026"

# Todas las tablas que la semilla llena.
TABLAS_DE_LA_SEMILLA = (
    "temporada",
    "usuario",
    "grupo",
    "grupo_profesor",
    "tarifa_base",
    "descuento_modalidad",
    "descuento_mes",
    "periodo_cobro",
    "tipo_cargo",
)


# --- utilidades --------------------------------------------------------------


def _conteos(sesion: Session) -> dict[str, int]:
    # Flush antes de contar: el fixture `sesion` no tiene autoflush, y una
    # semilla que agregara filas sin flush antes de negarse no apareceria en
    # un SELECT. Asi lo pendiente tambien cuenta como escrito.
    sesion.flush()
    return {
        tabla: sesion.execute(text(f"SELECT count(*) FROM {tabla}")).scalar_one()
        for tabla in TABLAS_DE_LA_SEMILLA
    }


def _id_temporada_2026_27(sesion: Session) -> int:
    return sesion.execute(text("SELECT id FROM temporada WHERE nombre = '2026-27'")).scalar_one()


def _usuario_previo(sesion: Session) -> None:
    # Username distinto de los de la semilla: si la semilla no se negara, el
    # alta no chocaria con la UNIQUE y el test veria las filas de mas.
    sesion.add(
        Usuario(
            username="aperez",
            password_hash="$argon2id$no-es-un-hash-real",
            nombre="Ana",
            apellido="Perez",
            rol=RolUsuario.ADMIN,
        )
    )
    sesion.flush()


def _temporada_previa(sesion: Session) -> None:
    # Nombre distinto de 2026-27, por la misma razon que el username.
    sesion.add(
        Temporada(
            nombre="2025-26",
            fecha_inicio=date(2026, 1, 5),
            fecha_cierre=date(2026, 2, 27),
            estado=EstadoTemporada.VIGENTE,
        )
    )
    sesion.flush()


# --- Requirement: La semilla solo corre sobre una base vacía ----------------


def test_sobre_base_vacia_la_semilla_termina_bien_y_crea_la_temporada_2026_27(
    sesion: Session,
) -> None:
    assert _conteos(sesion)["temporada"] == 0
    assert _conteos(sesion)["usuario"] == 0

    cargar(sesion)  # no lanza

    assert (
        sesion.execute(text("SELECT count(*) FROM temporada WHERE nombre = '2026-27'")).scalar_one()
        == 1
    )


def test_con_un_usuario_la_semilla_se_niega_y_no_escribe_nada(sesion: Session) -> None:
    _usuario_previo(sesion)

    with pytest.raises(SemillaRechazada) as error:
        cargar(sesion)

    assert str(error.value) == MENSAJE_BASE_NO_VACIA
    assert _conteos(sesion) == {
        "temporada": 0,
        "usuario": 1,
        "grupo": 0,
        "grupo_profesor": 0,
        "tarifa_base": 0,
        "descuento_modalidad": 0,
        "descuento_mes": 0,
        "periodo_cobro": 0,
        "tipo_cargo": 0,
    }
    assert sesion.execute(text("SELECT username FROM usuario")).scalars().all() == ["aperez"]


def test_con_una_temporada_la_semilla_se_niega_y_no_escribe_nada(sesion: Session) -> None:
    _temporada_previa(sesion)

    with pytest.raises(SemillaRechazada) as error:
        cargar(sesion)

    assert str(error.value) == MENSAJE_BASE_NO_VACIA
    assert _conteos(sesion) == {
        "temporada": 1,
        "usuario": 0,
        "grupo": 0,
        "grupo_profesor": 0,
        "tarifa_base": 0,
        "descuento_modalidad": 0,
        "descuento_mes": 0,
        "periodo_cobro": 0,
        "tipo_cargo": 0,
    }
    assert sesion.execute(text("SELECT nombre FROM temporada")).scalars().all() == ["2025-26"]


def test_la_segunda_corrida_se_niega_y_deja_una_temporada_y_los_mismos_cuatro_usuarios(
    sesion: Session,
) -> None:
    cargar(sesion)
    conteos_antes = _conteos(sesion)
    usuarios_antes = sesion.execute(text("SELECT id, username FROM usuario ORDER BY id")).all()

    with pytest.raises(SemillaRechazada) as error:
        cargar(sesion)

    assert str(error.value) == MENSAJE_BASE_NO_VACIA
    conteos_despues = _conteos(sesion)
    assert conteos_despues["temporada"] == 1
    assert conteos_despues["usuario"] == 4
    assert conteos_despues == conteos_antes
    assert (
        sesion.execute(text("SELECT id, username FROM usuario ORDER BY id")).all() == usuarios_antes
    )


# --- Requirement: La semilla solo corre contra una base local ---------------


def test_la_base_del_docker_compose_se_acepta() -> None:
    assert (
        verificar_base_local("postgresql+psycopg://escuelita:escuelita@db:5432/escuelita") is None
    )


def test_la_base_en_localhost_se_acepta() -> None:
    assert (
        verificar_base_local("postgresql+psycopg://escuelita:escuelita@localhost:5432/escuelita")
        is None
    )


def test_una_base_remota_se_rechaza_por_no_ser_local() -> None:
    with pytest.raises(SemillaRechazada) as error:
        verificar_base_local(
            "postgresql+psycopg://u:p@dpg-abc123.oregon-postgres.render.com/escuelita"
        )
    assert str(error.value) == MENSAJE_BASE_NO_LOCAL


def test_un_host_que_solo_empieza_como_localhost_se_rechaza() -> None:
    with pytest.raises(SemillaRechazada) as error:
        verificar_base_local("postgresql+psycopg://u:p@localhost.ejemplo.com/escuelita")
    assert str(error.value) == MENSAJE_BASE_NO_LOCAL


def test_un_host_remoto_escondido_en_la_query_se_rechaza() -> None:
    with pytest.raises(SemillaRechazada) as error:
        verificar_base_local(
            "postgresql+psycopg://u:p@localhost/escuelita"
            "?host=dpg-abc123.oregon-postgres.render.com"
        )
    assert str(error.value) == MENSAJE_BASE_NO_LOCAL


def test_una_direccion_remota_escondida_en_la_query_se_rechaza() -> None:
    with pytest.raises(SemillaRechazada) as error:
        verificar_base_local("postgresql+psycopg://u:p@localhost/escuelita?hostaddr=203.0.113.7")
    assert str(error.value) == MENSAJE_BASE_NO_LOCAL


# --- Requirement: Temporada vigente 2026-27 ----------------------------------


def test_hay_exactamente_una_temporada_2026_27_vigente_del_4_de_enero_al_26_de_febrero(
    sesion: Session,
) -> None:
    cargar(sesion)

    filas = sesion.execute(
        text("SELECT nombre, estado::text, fecha_inicio, fecha_cierre FROM temporada")
    ).all()
    assert [tuple(f) for f in filas] == [
        ("2026-27", "vigente", date(2027, 1, 4), date(2027, 2, 26))
    ]


# --- Requirement: Usuarios de los tres roles que pueden ingresar -------------


def test_cada_usuario_de_la_semilla_ingresa_con_su_rol_y_sin_cambio_pendiente(
    cliente: TestClient, sesion: Session
) -> None:
    cargar(sesion)

    esperados = {
        "mgarcia": "admin",
        "lrodriguez": "coordinador",
        "jperez": "profesor",
        "cfernandez": "profesor",
    }
    for username, rol in esperados.items():
        respuesta = cliente.post(
            "/api/v1/auth/login",
            json={"username": username, "password": CONTRASENA_SEMILLA},
        )
        assert respuesta.status_code == 200, (username, respuesta.text)
        usuario = respuesta.json()["usuario"]
        assert usuario["rol"] == rol, username
        assert usuario["debe_cambiar_password"] is False, username


def test_la_semilla_crea_exactamente_cuatro_usuarios_un_admin_un_coordinador_y_dos_profesores(
    sesion: Session,
) -> None:
    cargar(sesion)

    roles = sesion.execute(text("SELECT rol::text FROM usuario ORDER BY rol::text")).scalars().all()
    assert roles == ["admin", "coordinador", "profesor", "profesor"]


# --- Requirement: Grupos con profesores asignados ----------------------------


def test_la_temporada_tiene_exactamente_los_cuatro_grupos_con_sus_profesores_y_nada_mas(
    sesion: Session,
) -> None:
    cargar(sesion)
    temporada_id = _id_temporada_2026_27(sesion)

    grupos = sesion.execute(
        text(
            "SELECT nombre, turno::text, nacimiento_desde, nacimiento_hasta, activo "
            "FROM grupo WHERE temporada_id = :t ORDER BY turno::text, nombre"
        ),
        {"t": temporada_id},
    ).all()
    assert [tuple(g) for g in grupos] == [
        ("Delfines", "manana", date(2020, 1, 1), date(2021, 12, 31), True),
        ("Tiburones", "manana", date(2017, 1, 1), date(2019, 12, 31), True),
        ("Delfines", "tarde", date(2020, 1, 1), date(2021, 12, 31), True),
        ("Tiburones", "tarde", date(2017, 1, 1), date(2019, 12, 31), True),
    ]
    # Ningun grupo fuera de 2026-27.
    assert sesion.execute(text("SELECT count(*) FROM grupo")).scalar_one() == 4

    # Todas las asignaciones de la tabla, no solo las de estos grupos.
    asignaciones = sesion.execute(
        text(
            "SELECT g.nombre, g.turno::text, u.username "
            "FROM grupo_profesor gp "
            "JOIN grupo g ON g.id = gp.grupo_id "
            "JOIN usuario u ON u.id = gp.usuario_id "
            "ORDER BY g.turno::text, g.nombre, u.username"
        )
    ).all()
    assert [tuple(a) for a in asignaciones] == [
        ("Delfines", "manana", "jperez"),
        ("Tiburones", "manana", "cfernandez"),
        ("Delfines", "tarde", "jperez"),
        ("Tiburones", "tarde", "cfernandez"),
    ]


# --- Requirement: Tarifa base completa ---------------------------------------


def test_la_temporada_tiene_exactamente_las_ocho_tarifas_base_con_sus_montos(
    sesion: Session,
) -> None:
    cargar(sesion)
    temporada_id = _id_temporada_2026_27(sesion)

    filas = sesion.execute(
        text(
            "SELECT turno::text, modalidad::text, monto FROM tarifa_base "
            "WHERE temporada_id = :t ORDER BY turno::text, modalidad::text"
        ),
        {"t": temporada_id},
    ).all()
    assert [tuple(f) for f in filas] == [
        ("manana", "dia", Decimal("8000.00")),
        ("manana", "mes", Decimal("100000.00")),
        ("manana", "quincena", Decimal("55000.00")),
        ("manana", "semana", Decimal("30000.00")),
        ("tarde", "dia", Decimal("7000.00")),
        ("tarde", "mes", Decimal("80000.00")),
        ("tarde", "quincena", Decimal("45000.00")),
        ("tarde", "semana", Decimal("25000.00")),
    ]
    assert all(isinstance(f[2], Decimal) for f in filas)


# --- Requirement: Tabla de descuentos con la política 2026-27 ----------------


def test_hay_exactamente_nueve_descuentos_por_modalidad_socio_50_empleado_25_no_socio_0(
    sesion: Session,
) -> None:
    cargar(sesion)
    temporada_id = _id_temporada_2026_27(sesion)

    filas = sesion.execute(
        text(
            "SELECT modalidad::text, categoria::text, porcentaje FROM descuento_modalidad "
            "WHERE temporada_id = :t ORDER BY modalidad::text, categoria::text"
        ),
        {"t": temporada_id},
    ).all()
    esperado = []
    for modalidad in ("dia", "quincena", "semana"):
        esperado += [
            (modalidad, "empleado", Decimal("25.00")),
            (modalidad, "no_socio", Decimal("0.00")),
            (modalidad, "socio", Decimal("50.00")),
        ]
    assert [tuple(f) for f in filas] == esperado
    assert all(isinstance(f[2], Decimal) for f in filas)


def test_hay_exactamente_doce_descuentos_del_mes_con_cada_celda_de_la_politica(
    sesion: Session,
) -> None:
    cargar(sesion)
    temporada_id = _id_temporada_2026_27(sesion)

    filas = sesion.execute(
        text(
            "SELECT categoria::text, tramo_hijos, porcentaje FROM descuento_mes "
            "WHERE temporada_id = :t ORDER BY categoria::text, tramo_hijos"
        ),
        {"t": temporada_id},
    ).all()
    assert [tuple(f) for f in filas] == [
        ("empleado", 1, Decimal("25.00")),
        ("empleado", 2, Decimal("32.50")),
        ("empleado", 3, Decimal("36.25")),
        ("empleado", 4, Decimal("40.00")),
        ("no_socio", 1, Decimal("0.00")),
        ("no_socio", 2, Decimal("10.00")),
        ("no_socio", 3, Decimal("15.00")),
        ("no_socio", 4, Decimal("20.00")),
        ("socio", 1, Decimal("50.00")),
        ("socio", 2, Decimal("55.00")),
        ("socio", 3, Decimal("57.50")),
        ("socio", 4, Decimal("60.00")),
    ]
    assert all(isinstance(f[2], Decimal) for f in filas)


# --- Requirement: Períodos de cobro de la temporada --------------------------


def _periodos(sesion: Session, modalidad: str) -> list[tuple[str, date, date]]:
    temporada_id = _id_temporada_2026_27(sesion)
    filas = sesion.execute(
        text(
            "SELECT nombre, fecha_desde, fecha_hasta FROM periodo_cobro "
            "WHERE temporada_id = :t AND modalidad::text = :m ORDER BY fecha_desde, nombre"
        ),
        {"t": temporada_id, "m": modalidad},
    ).all()
    return [tuple(f) for f in filas]  # type: ignore[misc]


def test_la_modalidad_mes_tiene_exactamente_el_mes_1_y_el_mes_2(sesion: Session) -> None:
    cargar(sesion)

    assert _periodos(sesion, "mes") == [
        ("Mes 1", date(2027, 1, 4), date(2027, 1, 29)),
        ("Mes 2", date(2027, 2, 1), date(2027, 2, 26)),
    ]


def test_la_modalidad_quincena_tiene_exactamente_las_cuatro_quincenas(sesion: Session) -> None:
    cargar(sesion)

    assert _periodos(sesion, "quincena") == [
        ("Quincena 1", date(2027, 1, 4), date(2027, 1, 15)),
        ("Quincena 2", date(2027, 1, 18), date(2027, 1, 29)),
        ("Quincena 3", date(2027, 2, 1), date(2027, 2, 12)),
        ("Quincena 4", date(2027, 2, 15), date(2027, 2, 26)),
    ]


def test_la_modalidad_semana_tiene_exactamente_ocho_semanas_de_lunes_a_viernes(
    sesion: Session,
) -> None:
    cargar(sesion)

    primer_lunes = date(2027, 1, 4)
    esperado = [
        (
            f"Semana {n}",
            primer_lunes + timedelta(days=7 * (n - 1)),
            primer_lunes + timedelta(days=7 * (n - 1) + 4),
        )
        for n in range(1, 9)
    ]
    semanas = _periodos(sesion, "semana")
    assert semanas == esperado
    # Los dos extremos que fija el Scenario, escritos a mano.
    assert semanas[0] == ("Semana 1", date(2027, 1, 4), date(2027, 1, 8))
    assert semanas[-1] == ("Semana 8", date(2027, 2, 22), date(2027, 2, 26))


# --- Requirement: Tipos de cargo Preinscripción y Abono ----------------------


def test_hay_exactamente_dos_tipos_de_cargo_preinscripcion_fija_y_abono_por_tarifario(
    sesion: Session,
) -> None:
    cargar(sesion)
    temporada_id = _id_temporada_2026_27(sesion)

    filas = sesion.execute(
        text(
            "SELECT nombre, calculo::text, monto_fijo FROM tipo_cargo "
            "WHERE temporada_id = :t ORDER BY nombre"
        ),
        {"t": temporada_id},
    ).all()
    assert [tuple(f) for f in filas] == [
        ("Abono", "tarifario", None),
        ("Preinscripción", "monto_fijo", Decimal("20000.00")),
    ]
    assert isinstance(filas[1][2], Decimal)
