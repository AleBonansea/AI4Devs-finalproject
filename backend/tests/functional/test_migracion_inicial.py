"""Las restricciones de la migracion inicial, comprobadas contra Postgres.

Estos tests no vienen de una historia: vienen del ticket TK-01, que pide
comprobar cada restriccion insertando una fila invalida. Van contra Postgres
de verdad porque SQLite no evalua igual los CHECK ni los indices parciales:
con otro motor todos pasarian sin comprobar nada.
"""

from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario


def _temporada(nombre: str, estado: EstadoTemporada) -> Temporada:
    return Temporada(
        nombre=nombre,
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=estado,
    )


def _usuario(username: str, **extra: object) -> Usuario:
    datos: dict[str, object] = {
        "username": username,
        "password_hash": "$argon2id$no-es-un-hash-real",
        "nombre": "Ana",
        "apellido": "Perez",
        "rol": RolUsuario.ADMIN,
    }
    datos.update(extra)
    return Usuario(**datos)  # type: ignore[arg-type]


class TestTemporada:
    def test_hay_una_sola_temporada_vigente(self, sesion: Session) -> None:
        sesion.add(_temporada("2026-27", EstadoTemporada.VIGENTE))
        sesion.flush()
        sesion.add(_temporada("2027-28", EstadoTemporada.VIGENTE))
        with pytest.raises(IntegrityError):
            sesion.flush()

    def test_puede_haber_varias_temporadas_cerradas(self, sesion: Session) -> None:
        sesion.add(_temporada("2024-25", EstadoTemporada.CERRADA))
        sesion.add(_temporada("2025-26", EstadoTemporada.CERRADA))
        sesion.flush()  # el indice es parcial: solo restringe las vigentes

    def test_una_vigente_conviven_con_las_cerradas(self, sesion: Session) -> None:
        sesion.add(_temporada("2025-26", EstadoTemporada.CERRADA))
        sesion.add(_temporada("2026-27", EstadoTemporada.VIGENTE))
        sesion.flush()

    def test_el_cierre_no_puede_ser_anterior_al_inicio(self, sesion: Session) -> None:
        sesion.add(
            Temporada(
                nombre="2026-27",
                fecha_inicio=date(2027, 2, 28),
                fecha_cierre=date(2026, 12, 14),
                estado=EstadoTemporada.VIGENTE,
            )
        )
        with pytest.raises(IntegrityError):
            sesion.flush()

    def test_el_nombre_no_se_repite(self, sesion: Session) -> None:
        sesion.add(_temporada("2026-27", EstadoTemporada.VIGENTE))
        sesion.flush()
        sesion.add(_temporada("2026-27", EstadoTemporada.CERRADA))
        with pytest.raises(IntegrityError):
            sesion.flush()


class TestUsuario:
    def test_el_username_no_se_repite(self, sesion: Session) -> None:
        sesion.add(_usuario("aperez"))
        sesion.flush()
        sesion.add(_usuario("aperez"))
        with pytest.raises(IntegrityError):
            sesion.flush()

    def test_los_intentos_fallidos_no_pueden_ser_negativos(self, sesion: Session) -> None:
        sesion.add(_usuario("aperez", intentos_fallidos=-1))
        with pytest.raises(IntegrityError):
            sesion.flush()

    def test_un_usuario_nuevo_debe_cambiar_la_contrasena(self, sesion: Session) -> None:
        u = _usuario("aperez")
        sesion.add(u)
        sesion.flush()
        assert (
            u.debe_cambiar_password is True
        ), "El alta tiene que dejar el cambio obligatorio pendiente (HU-UT-06)."
        assert u.activo is True
        assert u.intentos_fallidos == 0

    def test_el_bloqueo_se_deduce_del_contador(self, sesion: Session) -> None:
        u = _usuario("aperez", intentos_fallidos=4)
        sesion.add(u)
        sesion.flush()
        assert u.bloqueado is False
        u.intentos_fallidos = 5
        sesion.flush()
        assert u.bloqueado is True


class TestFormaDelEsquema:
    """Lo que autogenerate hace mal y hubo que corregir a mano."""

    def test_los_enum_estan_en_minusculas(self, sesion: Session) -> None:
        # SQLAlchemy manda los NOMBRES de los miembros ('VIGENTE') salvo que se
        # le pase values_callable. Si esto se rompe, el indice parcial de
        # temporada deja de agarrar y entran dos temporadas vigentes.
        filas = sesion.execute(
            text(
                "SELECT t.typname, e.enumlabel FROM pg_type t "
                "JOIN pg_enum e ON e.enumtypid = t.oid "
                "WHERE t.typname IN ('estado_temporada', 'rol_usuario')"
            )
        ).all()
        etiquetas = {(f[0], f[1]) for f in filas}
        assert etiquetas == {
            ("estado_temporada", "vigente"),
            ("estado_temporada", "cerrada"),
            ("rol_usuario", "admin"),
            ("rol_usuario", "coordinador"),
            ("rol_usuario", "profesor"),
        }

    def test_un_valor_fuera_del_enum_se_rechaza(self, sesion: Session) -> None:
        with pytest.raises((DataError, IntegrityError)):
            sesion.execute(
                text(
                    "INSERT INTO temporada (nombre, fecha_inicio, fecha_cierre, estado) "
                    "VALUES ('x', '2026-12-14', '2027-02-28', 'VIGENTE')"
                )
            )

    def test_creado_en_lleva_zona_horaria(self, sesion: Session) -> None:
        # timestamp sin zona en un servidor UTC y un club en Argentina da horas
        # que no se pueden comparar, y no se nota hasta auditar un cobro.
        tipo = sesion.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'usuario' AND column_name = 'creado_en'"
            )
        ).scalar_one()
        assert tipo == "timestamp with time zone"

    def test_las_claves_primarias_son_bigint(self, sesion: Session) -> None:
        for tabla in ("temporada", "usuario"):
            tipo = sesion.execute(
                text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_name = :t AND column_name = 'id'"
                ),
                {"t": tabla},
            ).scalar_one()
            assert tipo == "bigint", f"{tabla}.id quedo en {tipo}"
