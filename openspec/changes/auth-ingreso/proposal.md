# Proposal

## Why

Cubre **HU-UT-01 — ingresar con usuario y contraseña**, la primera historia del **Lote 1** (`docs/product/historias-backlog.md`, «Entrar»). Ninguna otra historia del lote se puede construir sin ella: cada endpoint que viene después declara qué roles lo usan, y para eso hace falta saber quién llama. El modelo `usuario` ya está en la base; falta la puerta.

Fuentes: Acl. 9 («Acceso al sistema y usuarios»), Acl. 11 («Autenticación») y documento técnico, «Contraseñas y sesión» y «Permisos».

## What Changes

- **Nuevo endpoint `POST /api/v1/auth/login`**: recibe usuario y contraseña y, si son correctos, devuelve un token de acceso JWT con vencimiento y los datos del usuario, con su rol y si tiene pendiente el cambio obligatorio de contraseña, en la misma forma que `GET /api/v1/auth/yo`.
- **Contador de intentos fallidos**: un ingreso correcto lo pone en 0; uno incorrecto lo incrementa. Con el contador en 5 o más el usuario no entra, aunque la contraseña sea correcta.
- **Usuarios desactivados** no entran.
- **Dependencia de usuario actual**: resuelve, desde el token, el usuario que llama, releyéndolo de la base en cada petición. Rechaza token ausente, inválido o vencido, y usuario desactivado o bloqueado.
- **Cambio obligatorio pendiente**: un usuario con `debe_cambiar_password` entra (recibe su token), pero cualquier otro endpoint protegido lo rechaza hasta que la cambie, salvo `GET /api/v1/auth/yo`.
- **`exigir_rol`**: dependencia con la que cada endpoint declara qué roles (Admin, Coordinador, Profesor) pueden usarlo. Un rol no declarado recibe 403.
- **Nuevo endpoint `GET /api/v1/auth/yo`**: devuelve los datos del usuario actual, incluido si tiene el cambio de contraseña pendiente. Es el primer consumidor de la dependencia y lo que el frontend usa para saber quién está logueado.

## Fuera de alcance

- **El cambio de contraseña (HU-UT-06, Lote 2)**: su endpoint, su pantalla y sus reglas de validación. Este change solo hace cumplir el indicador: entra y no puede hacer nada más.
- **El bloqueo como historia (HU-UT-08, Lote 2)**: mensajes y pantalla de usuario bloqueado, y cualquier gestión del bloqueo. Este change solo hace cumplir que con 5 o más intentos no se entra.
- **La mitigación del bloqueo disparado desde afuera** (límite por IP, desbloqueo automático): cualquiera puede bloquear una cuenta con 5 intentos. El riesgo está en el design y la decisión, como pregunta abierta en `aclaraciones-cliente.md`; la mitigación va con HU-UT-08.
- **El blanqueo (HU-UT-07)**, que es lo único que desbloquea y activa el cambio obligatorio.
- **Alta, modificación y baja de usuarios (HU-UT-02, HU-UT-03)**: en el Lote 1 los usuarios vienen de la semilla.
- **Token de renovación en cookie httpOnly y vencimiento por inactividad** (documento técnico): depende del dominio propio, que está pendiente. Mientras tanto la sesión es solo el token de acceso, con el vencimiento configurado.
- **Cierre de sesión del lado del servidor** (lista de tokens revocados): no está en las fuentes. Cerrar sesión es descartar el token en el cliente.
- **La segunda dependencia del Profesor** (que el grupo o el alumno sean de los suyos): llega con la primera historia que expone grupos o alumnos.
- **La pantalla de ingreso**: este change es solo backend.
- **El esquema**: no hay migración; el modelo y la tabla ya existen.

## Capabilities

### New Capabilities

- `auth`: ingreso con usuario y contraseña, sesión por token, resolución del usuario actual y declaración de los roles que usan cada endpoint. Incluye hacer cumplir el bloqueo por intentos y el cambio obligatorio de contraseña, no gestionarlos.

### Modified Capabilities

Ninguna: no hay specs previas.

## Impact

- **Código nuevo**: router `app/api/v1/auth.py`, esquemas `app/schemas/auth.py`, servicio `app/services/auth.py`, dependencias en `app/core/deps.py`. Se reutilizan `hashear`, `verificar`, `crear_token` y `leer_token` de `app/core/security.py`.
- **API**: dos rutas nuevas; `docs/api/openapi.json` se regenera.
- **Dependencias de paquetes**: ninguna nueva (`pyjwt` y `pwdlib[argon2]` ya están).
- **Esquema**: sin cambios.
- **Historias que vienen después**: todas usan `exigir_rol` y la dependencia de usuario actual.
