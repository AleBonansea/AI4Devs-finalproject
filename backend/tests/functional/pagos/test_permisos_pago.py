"""Capability `pagos`: solo el Admin registra pagos (change cuenta-corriente,
tarea 2.1).

Un test por Scenario de `openspec/changes/cuenta-corriente/specs/pagos/spec.md`,
Requirement «Solo el Admin registra pagos».

Cada pedido es un pago valido sobre un cargo existente con saldo («Abono» del
Mes de Juan, 85000.00 sin pagos): si el cuerpo estuviera mal, un 422 podria
tapar la falta del 403. «No se guarda nada» se comprueba contando pagos y
movimientos de tesoreria antes y despues.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import RolUsuario, Usuario
from tests.functional.asistencia.preparacion import (
    CONTRASENA,
    asignar,
    crear_usuario,
    ingresar,
)
from tests.functional.pagos.preparacion_api import (
    ID_INEXISTENTE,
    MENSAJE_SIN_PERMISO,
    contar_movimientos,
    contar_pagos,
    cuerpo_pago,
    insertar_abono_mes,
    pagar,
    preparar_perez,
)


class TestSoloElAdminRegistraPagos:
    def test_el_coordinador_recibe_403_y_no_se_guarda_ni_pago_ni_movimiento(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Coordinador registra un pago
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        crear_usuario(sesion, "lrodriguez", RolUsuario.COORDINADOR)
        encabezados = ingresar(cliente, "lrodriguez")
        pagos_antes = contar_pagos(sesion)
        movimientos_antes = contar_movimientos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("10000.00"))

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO
        assert contar_pagos(sesion) == pagos_antes
        assert contar_movimientos(sesion) == movimientos_antes

    def test_el_profesor_del_grupo_del_alumno_recibe_403_y_no_se_guarda_ningun_pago(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Profesor del grupo del alumno
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)  # de Juan, inscripto en «Delfines» manana
        jperez = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        asignar(sesion, p.delfines, jperez)
        encabezados = ingresar(cliente, "jperez")
        pagos_antes = contar_pagos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("10000.00"))

        assert respuesta.status_code == 403, respuesta.text
        assert contar_pagos(sesion) == pagos_antes

    def test_el_profesor_con_un_cargo_que_no_existe_recibe_403_y_no_404(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Profesor con un cargo que no existe
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        assert abono != ID_INEXISTENTE
        jperez = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        asignar(sesion, p.delfines, jperez)

        respuesta = pagar(
            cliente, ingresar(cliente, "jperez"), ID_INEXISTENTE, cuerpo_pago("10000.00")
        )

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO

    def test_sin_token_responde_401_y_no_se_guarda_ningun_pago(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Sin sesión
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        pagos_antes = contar_pagos(sesion)

        respuesta = pagar(cliente, None, abono, cuerpo_pago("10000.00"))

        assert respuesta.status_code == 401, respuesta.text
        assert contar_pagos(sesion) == pagos_antes

    def test_el_admin_con_el_cambio_de_contrasena_pendiente_recibe_403_y_no_se_guarda_nada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Admin con el cambio de contraseña pendiente
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        sesion.add(
            Usuario(
                username="admin2",
                password_hash=hashear(CONTRASENA),
                debe_cambiar_password=True,
                intentos_fallidos=0,
                nombre="Usuario",
                apellido="Admin2",
                rol=RolUsuario.ADMIN,
                activo=True,
            )
        )
        sesion.flush()
        encabezados = ingresar(cliente, "admin2")
        pagos_antes = contar_pagos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("10000.00"))

        assert respuesta.status_code == 403, respuesta.text
        assert contar_pagos(sesion) == pagos_antes
