"""Regla del ingreso: buscar al usuario, verificar la contrasena y llevar el
contador de intentos fallidos.

El orden de las comprobaciones importa (ver design de auth-ingreso): el
bloqueo se decide sin verificar la contrasena, y el inexistente y el
desactivado verifican igual contra un hash ficticio para no revelar por el
tiempo de respuesta que usuarios existen.
"""

from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import crear_token, hashear, verificar
from app.models.usuario import Usuario

# Calculado una vez al importar, con los mismos parametros de argon2 que un
# hash real, para que verificar contra el tarde lo mismo.
_HASH_FICTICIO = hashear("contrasena-ficticia-para-igualar-tiempos")


class CredencialesInvalidas(Exception):
    """Usuario inexistente, desactivado o contrasena incorrecta. Los tres
    casos se informan igual."""


class UsuarioBloqueado(Exception):
    """El usuario llego al limite de intentos fallidos."""


@dataclass(frozen=True)
class Ingreso:
    token: str
    usuario: Usuario


def ingresar(sesion: Session, username: str, contrasena: str) -> Ingreso:
    # Los usernames se guardan en minusculas; se busca por igualdad exacta
    # para usar el indice unico tal cual. LoginEntrada ya normaliza; se repite
    # aca (es idempotente) para que el servicio no dependa de quien lo llame.
    normalizado = username.strip().lower()
    # FOR UPDATE serializa los logins simultaneos de la misma cuenta hasta el
    # commit (design de auth-ingreso, «Concurrencia»). Sin esto el limite de 5
    # intentos no vale con pedidos simultaneos. Sin test, a proposito.
    usuario = sesion.execute(
        select(Usuario).where(Usuario.username == normalizado).with_for_update()
    ).scalar_one_or_none()

    if usuario is None or not usuario.activo:
        verificar(contrasena, _HASH_FICTICIO)
        raise CredencialesInvalidas

    # Sin verificar la contrasena: si el 403 dependiera de acertarla, la
    # cuenta bloqueada serviria para adivinarla.
    if usuario.bloqueado:
        raise UsuarioBloqueado

    if not verificar(contrasena, usuario.password_hash):
        # Atomico en la base: leer-sumar-escribir en Python pierde intentos
        # simultaneos. Se commitea antes de rechazar para que el intento
        # quede aunque la peticion termine en error.
        sesion.execute(
            update(Usuario)
            .where(Usuario.id == usuario.id)
            .values(intentos_fallidos=Usuario.intentos_fallidos + 1)
        )
        sesion.commit()
        raise CredencialesInvalidas

    usuario.intentos_fallidos = 0
    sesion.commit()
    # Solo el id: rol y estado se releen de la base en cada peticion.
    return Ingreso(token=crear_token(str(usuario.id)), usuario=usuario)
