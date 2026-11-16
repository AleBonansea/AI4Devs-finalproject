"""Formato del nombre de la temporada, comprobado contra Postgres.

Change `menu-lateral-y-edad-de-grupos`, capability `temporadas`, Requirement
«Formato del nombre de la temporada»: el nombre tiene la forma `AAAA-AA` y la
base rechaza cualquier otro. Son restricciones de la base, asi que se insertan
filas con el ORM y se espera el rechazo al hacer `flush`.
"""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import EstadoTemporada, Temporada


def _temporada(nombre: str) -> Temporada:
    return Temporada(
        nombre=nombre,
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=EstadoTemporada.VIGENTE,
    )


class TestFormatoDelNombre:
    def test_un_nombre_con_el_formato_queda_guardado(self, sesion: Session) -> None:
        # Scenario: Nombre con el formato
        sesion.add(_temporada("2026-27"))
        sesion.flush()
        nombres = (
            sesion.execute(select(Temporada.nombre).where(Temporada.nombre == "2026-27"))
            .scalars()
            .all()
        )
        assert nombres == ["2026-27"]

    def test_la_base_rechaza_un_nombre_con_el_anio_corto(self, sesion: Session) -> None:
        # Scenario: Nombre con el año corto
        sesion.add(_temporada("26-27"))
        with pytest.raises(IntegrityError):
            sesion.flush()

    def test_la_base_rechaza_un_nombre_con_texto(self, sesion: Session) -> None:
        # Scenario: Nombre con texto
        sesion.add(_temporada("Verano 2026"))
        with pytest.raises(IntegrityError):
            sesion.flush()

    def test_la_base_rechaza_un_nombre_con_el_segundo_anio_completo(self, sesion: Session) -> None:
        # Scenario: Nombre con el segundo año completo
        sesion.add(_temporada("2026-2027"))
        with pytest.raises(IntegrityError):
            sesion.flush()
