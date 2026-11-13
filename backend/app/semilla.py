"""La semilla: una temporada de demostracion completa con una sola orden.

Carga usuarios, grupos y tarifario inventados mientras el ABM que los carga
desde la aplicacion no existe. Nunca datos reales.

Dos negativas la protegen (ver `design.md` del change tarifario-y-semilla):
- solo corre contra una base local, comprobado antes de conectarse;
- solo corre sobre una base vacia: no borra, no actualiza, no mezcla.

`cargar` hace flush y nunca commit. El commit lo hace `scripts/seed.py`, y
asi los tests la corren dentro de su transaccion revertida.
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import (
    CalculoCargo,
    CategoriaFamilia,
    DescuentoMes,
    DescuentoModalidad,
    EstadoTemporada,
    Grupo,
    GrupoProfesor,
    Modalidad,
    PeriodoCobro,
    RolUsuario,
    TarifaBase,
    Temporada,
    TipoCargo,
    Turno,
    Usuario,
)

MENSAJE_BASE_NO_LOCAL = "La semilla solo corre contra una base local."
MENSAJE_BASE_NO_VACIA = "La base no está vacía: la semilla solo corre sobre una base vacía."

# `db` es el servicio de Postgres del docker-compose.yml. Se compara el host
# exacto: `localhost.ejemplo.com` no es local.
HOSTS_LOCALES = frozenset({"localhost", "127.0.0.1", "::1", "db"})

# --- Datos ------------------------------------------------------------------

# Cumple la regla del documento tecnico: 8 o mas caracteres, letra y numero.
CONTRASENA_DEMO = "Verano2026"

TEMPORADA_NOMBRE = "2026-27"
TEMPORADA_INICIO = date(2027, 1, 4)
TEMPORADA_CIERRE = date(2027, 2, 26)

# username, nombre, apellido, rol
USUARIOS: tuple[tuple[str, str, str, RolUsuario], ...] = (
    ("mgarcia", "María", "García", RolUsuario.ADMIN),
    ("lrodriguez", "Lucía", "Rodríguez", RolUsuario.COORDINADOR),
    ("jperez", "Juan", "Pérez", RolUsuario.PROFESOR),
    ("cfernandez", "Carla", "Fernández", RolUsuario.PROFESOR),
)

# nombre, turno, nacimiento desde, nacimiento hasta, username del profesor
GRUPOS: tuple[tuple[str, Turno, date, date, str], ...] = (
    ("Delfines", Turno.MANANA, date(2020, 1, 1), date(2021, 12, 31), "jperez"),
    ("Tiburones", Turno.MANANA, date(2017, 1, 1), date(2019, 12, 31), "cfernandez"),
    ("Delfines", Turno.TARDE, date(2020, 1, 1), date(2021, 12, 31), "jperez"),
    ("Tiburones", Turno.TARDE, date(2017, 1, 1), date(2019, 12, 31), "cfernandez"),
)

# Contexto comun de HU-CC-01.
TARIFAS_BASE: dict[Turno, dict[Modalidad, Decimal]] = {
    Turno.MANANA: {
        Modalidad.MES: Decimal("100000.00"),
        Modalidad.QUINCENA: Decimal("55000.00"),
        Modalidad.SEMANA: Decimal("30000.00"),
        Modalidad.DIA: Decimal("8000.00"),
    },
    Turno.TARDE: {
        Modalidad.MES: Decimal("80000.00"),
        Modalidad.QUINCENA: Decimal("45000.00"),
        Modalidad.SEMANA: Decimal("25000.00"),
        Modalidad.DIA: Decimal("7000.00"),
    },
}

# Politica 2026-27 de Acl. 5, cargada como porcentaje efectivo: el socio paga
# la mitad y el empleado tres cuartos de lo que paga el no socio en la misma
# celda. Prevalece sobre la tabla de HU-CC-01, que es anterior.
DESCUENTOS_MODALIDAD: dict[CategoriaFamilia, Decimal] = {
    CategoriaFamilia.NO_SOCIO: Decimal("0.00"),
    CategoriaFamilia.SOCIO: Decimal("50.00"),
    CategoriaFamilia.EMPLEADO: Decimal("25.00"),
}
MODALIDADES_CON_DESCUENTO_PROPIO = (Modalidad.DIA, Modalidad.SEMANA, Modalidad.QUINCENA)

# Por tramo de hijos 1, 2, 3 y 4 (el 4 es "4 o mas").
DESCUENTOS_MES: dict[CategoriaFamilia, tuple[Decimal, Decimal, Decimal, Decimal]] = {
    CategoriaFamilia.NO_SOCIO: (
        Decimal("0.00"),
        Decimal("10.00"),
        Decimal("15.00"),
        Decimal("20.00"),
    ),
    CategoriaFamilia.SOCIO: (
        Decimal("50.00"),
        Decimal("55.00"),
        Decimal("57.50"),
        Decimal("60.00"),
    ),
    CategoriaFamilia.EMPLEADO: (
        Decimal("25.00"),
        Decimal("32.50"),
        Decimal("36.25"),
        Decimal("40.00"),
    ),
}

# Meses y quincenas explicitos: son pocos y se leen mejor asi.
MESES: tuple[tuple[str, date, date], ...] = (
    ("Mes 1", date(2027, 1, 4), date(2027, 1, 29)),
    ("Mes 2", date(2027, 2, 1), date(2027, 2, 26)),
)
QUINCENAS: tuple[tuple[str, date, date], ...] = (
    ("Quincena 1", date(2027, 1, 4), date(2027, 1, 15)),
    ("Quincena 2", date(2027, 1, 18), date(2027, 1, 29)),
    ("Quincena 3", date(2027, 2, 1), date(2027, 2, 12)),
    ("Quincena 4", date(2027, 2, 15), date(2027, 2, 26)),
)
# Las semanas se generan: de lunes a viernes, desde el primer lunes.
PRIMER_LUNES = date(2027, 1, 4)
CANTIDAD_DE_SEMANAS = 8
SEMANAS: tuple[tuple[str, date, date], ...] = tuple(
    (
        f"Semana {n}",
        PRIMER_LUNES + timedelta(days=7 * (n - 1)),
        PRIMER_LUNES + timedelta(days=7 * (n - 1) + 4),
    )
    for n in range(1, CANTIDAD_DE_SEMANAS + 1)
)
PERIODOS: dict[Modalidad, tuple[tuple[str, date, date], ...]] = {
    Modalidad.MES: MESES,
    Modalidad.QUINCENA: QUINCENAS,
    Modalidad.SEMANA: SEMANAS,
}

# nombre, calculo, monto fijo (solo si el calculo es de monto fijo)
TIPOS_DE_CARGO: tuple[tuple[str, CalculoCargo, Decimal | None], ...] = (
    ("Preinscripción", CalculoCargo.MONTO_FIJO, Decimal("20000.00")),
    ("Abono", CalculoCargo.TARIFARIO, None),
)


# --- Logica -----------------------------------------------------------------


class SemillaRechazada(Exception):
    """La semilla se nego a correr. El mensaje es para quien la lanzo."""


def verificar_base_local(url: str) -> None:
    """Se niega si el host de la URL no es local. No se conecta a la base.

    libpq tambien toma `host` y `hostaddr` de la query, y esos le ganan al
    host de la URL: cada valor (string o tupla, cada uno una lista separada
    por comas) tiene que ser local.
    """
    url_parseada = make_url(url)
    if url_parseada.host not in HOSTS_LOCALES:
        raise SemillaRechazada(MENSAJE_BASE_NO_LOCAL)
    for clave in ("host", "hostaddr"):
        valor = url_parseada.query.get(clave)
        if valor is None:
            continue
        valores = (valor,) if isinstance(valor, str) else valor
        for elemento in (e.strip() for v in valores for e in v.split(",")):
            if elemento not in HOSTS_LOCALES:
                raise SemillaRechazada(MENSAJE_BASE_NO_LOCAL)


def cargar(sesion: Session) -> None:
    """Agrega la temporada de demostracion y hace flush. Nunca commit.

    Se niega, sin agregar nada, si ya hay alguna temporada o algun usuario.
    """
    hay_temporada = sesion.execute(select(Temporada.id).limit(1)).first() is not None
    hay_usuario = sesion.execute(select(Usuario.id).limit(1)).first() is not None
    if hay_temporada or hay_usuario:
        raise SemillaRechazada(MENSAJE_BASE_NO_VACIA)

    temporada = Temporada(
        nombre=TEMPORADA_NOMBRE,
        fecha_inicio=TEMPORADA_INICIO,
        fecha_cierre=TEMPORADA_CIERRE,
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)

    # Un solo hash para los cuatro: argon2 es caro a proposito y la
    # contrasena es la misma. Cada hash lleva su sal, pero aca no importa.
    hash_demo = hashear(CONTRASENA_DEMO)
    usuarios = {
        username: Usuario(
            username=username,
            password_hash=hash_demo,
            # Sin cambio pendiente: ver design.md, «Usuarios de la semilla
            # sin cambio de contraseña pendiente».
            debe_cambiar_password=False,
            intentos_fallidos=0,
            nombre=nombre,
            apellido=apellido,
            rol=rol,
            activo=True,
        )
        for username, nombre, apellido, rol in USUARIOS
    }
    sesion.add_all(usuarios.values())
    # Los ids hacen falta para las FK de lo que sigue.
    sesion.flush()

    for nombre, turno, desde, hasta, profesor in GRUPOS:
        grupo = Grupo(
            temporada_id=temporada.id,
            nombre=nombre,
            turno=turno,
            nacimiento_desde=desde,
            nacimiento_hasta=hasta,
            activo=True,
        )
        sesion.add(grupo)
        sesion.flush()
        sesion.add(GrupoProfesor(grupo_id=grupo.id, usuario_id=usuarios[profesor].id))

    sesion.add_all(
        TarifaBase(temporada_id=temporada.id, turno=turno, modalidad=modalidad, monto=monto)
        for turno, montos in TARIFAS_BASE.items()
        for modalidad, monto in montos.items()
    )

    sesion.add_all(
        DescuentoModalidad(
            temporada_id=temporada.id,
            categoria=categoria,
            modalidad=modalidad,
            porcentaje=porcentaje,
        )
        for modalidad in MODALIDADES_CON_DESCUENTO_PROPIO
        for categoria, porcentaje in DESCUENTOS_MODALIDAD.items()
    )

    sesion.add_all(
        DescuentoMes(
            temporada_id=temporada.id,
            categoria=categoria,
            tramo_hijos=tramo,
            porcentaje=porcentaje,
        )
        for categoria, porcentajes in DESCUENTOS_MES.items()
        for tramo, porcentaje in enumerate(porcentajes, start=1)
    )

    sesion.add_all(
        PeriodoCobro(
            temporada_id=temporada.id,
            modalidad=modalidad,
            nombre=nombre,
            fecha_desde=desde,
            fecha_hasta=hasta,
        )
        for modalidad, periodos in PERIODOS.items()
        for nombre, desde, hasta in periodos
    )

    sesion.add_all(
        TipoCargo(temporada_id=temporada.id, nombre=nombre, calculo=calculo, monto_fijo=monto)
        for nombre, calculo, monto in TIPOS_DE_CARGO
    )

    sesion.flush()
