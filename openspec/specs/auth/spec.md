# auth Specification

## Purpose

Permite que cada persona del staff ingrese con su usuario y contraseña personales y que la API sepa, en cada petición, quién llama y con qué rol, para dejarle hacer solo lo que ese rol permite.

## Requirements

### Requirement: Ingreso con usuario y contraseña
El sistema SHALL ofrecer `POST /api/v1/auth/login`, que recibe `username` y `password`. Si el usuario existe, está activo, no está bloqueado y la contraseña coincide, responde 200 con `access_token`, `token_type` igual a `bearer` y `usuario`, con los mismos campos que `GET /api/v1/auth/yo` (id, username, nombre, apellido, rol, debe_cambiar_password). `debe_cambiar_password` va solo dentro de `usuario`. La respuesta MUST NOT incluir el hash de la contraseña ni el contador de intentos.

#### Scenario: Ingreso correcto
- **GIVEN** un usuario activo `jperez`, rol `coordinador`, con contraseña `Verano2026`, `intentos_fallidos` en 0 y `debe_cambiar_password` en false
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": "jperez", "password": "Verano2026"}`
- **THEN** la respuesta es 200
- **AND** el cuerpo trae `access_token` no vacío, `token_type` igual a `bearer`, `usuario.rol` igual a `coordinador` y `usuario.debe_cambiar_password` en false
- **AND** el primer nivel del cuerpo tiene exactamente las claves `access_token`, `token_type` y `usuario`
- **AND** el cuerpo no tiene ningún campo `password_hash`, `password_hash_anterior` ni `intentos_fallidos`, en ningún nivel

#### Scenario: El usuario se escribe con mayúsculas o espacios
- **GIVEN** un usuario activo `jperez` con contraseña `Verano2026`
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": " JPerez ", "password": "Verano2026"}`
- **THEN** la respuesta es 200 y `usuario.username` es `jperez`

#### Scenario: La contraseña distingue mayúsculas
- **GIVEN** un usuario activo `jperez` con contraseña `Verano2026`
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": "jperez", "password": "verano2026"}`
- **THEN** la respuesta es 401

### Requirement: Pedido de ingreso malformado
`username` se normaliza (sin espacios alrededor y en minúsculas) antes de validarse, y su largo se mide sobre el valor normalizado. El sistema SHALL responder 422, sin token, si `username` queda vacío después de normalizar, supera 60 caracteres, contiene un carácter de control o un surrogate suelto (un carácter que no se puede codificar en UTF-8), o si `password` está vacía, supera 128 caracteres o contiene un surrogate suelto.

#### Scenario: Faltan datos en el pedido
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": "jperez", "password": ""}`
- **THEN** la respuesta es 422 y no se emite ningún token

#### Scenario: El usuario trae un carácter de control
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": "jp\u0000erez", "password": "Verano2026"}` (un carácter NUL en el medio)
- **THEN** la respuesta es 422 y no se emite ningún token

#### Scenario: El usuario es solo espacios
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": "   ", "password": "Verano2026"}`
- **THEN** la respuesta es 422 y no se emite ningún token

#### Scenario: El usuario trae un surrogate suelto
- **WHEN** se llama a `POST /api/v1/auth/login` con el cuerpo JSON `{"username": "jp\ud800erez", "password": "Verano2026"}`, con el surrogate escrito como el escape `\ud800` en el texto del JSON
- **THEN** la respuesta es 422, no 500, y no se emite ningún token

#### Scenario: El usuario de 60 caracteres ingresa
- **GIVEN** un usuario activo cuyo `username` tiene 60 caracteres, con contraseña `Verano2026`
- **WHEN** se llama a `POST /api/v1/auth/login` con ese `username` y `Verano2026`
- **THEN** la respuesta es 200

#### Scenario: El usuario de 61 caracteres es rechazado
- **WHEN** se llama a `POST /api/v1/auth/login` con un `username` de 61 caracteres y `Verano2026`
- **THEN** la respuesta es 422 y no se emite ningún token

#### Scenario: La contraseña de 128 caracteres ingresa
- **GIVEN** un usuario activo `jperez` cuya contraseña tiene 128 caracteres
- **WHEN** se llama a `POST /api/v1/auth/login` con `jperez` y esa contraseña
- **THEN** la respuesta es 200

#### Scenario: La contraseña de 129 caracteres es rechazada
- **GIVEN** un usuario activo `jperez`
- **WHEN** se llama a `POST /api/v1/auth/login` con `jperez` y una contraseña de 129 caracteres
- **THEN** la respuesta es 422 y no se emite ningún token

### Requirement: El rechazo por pedido malformado no repite lo recibido
El 422 de validación SHALL conservar la forma de FastAPI (`detail` como lista de errores con `loc`, `msg` y `type`), pero MUST NOT incluir el campo `input` ni repetir en ningún lugar del cuerpo el valor recibido. Una contraseña rechazada no vuelve en la respuesta.

#### Scenario: El 422 del login no repite la contraseña
- **GIVEN** una contraseña de 129 caracteres que empieza con `Secreta`
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": "jperez", "password": <esa contraseña>}`
- **THEN** la respuesta es 422 y `detail` es una lista de errores, cada uno con `loc`, `msg` y `type`
- **AND** el cuerpo no tiene ningún campo `input`, en ningún nivel
- **AND** el texto del cuerpo no contiene la contraseña enviada

### Requirement: Credenciales rechazadas sin revelar la causa
Cuando el usuario no existe, la contraseña no coincide o el usuario está desactivado, el sistema SHALL responder 401 con el mismo mensaje en los tres casos, `Usuario o contraseña incorrectos.`, sin token. La respuesta MUST NOT permitir distinguir cuál de los tres casos ocurrió.

#### Scenario: Contraseña incorrecta
- **GIVEN** un usuario activo `jperez` con contraseña `Verano2026`
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": "jperez", "password": "Otra1234"}`
- **THEN** la respuesta es 401 con `detail` igual a `Usuario o contraseña incorrectos.`
- **AND** el cuerpo no trae `access_token`

#### Scenario: Usuario inexistente
- **GIVEN** que no existe ningún usuario `nadie`
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": "nadie", "password": "Verano2026"}`
- **THEN** la respuesta es 401 con `detail` igual a `Usuario o contraseña incorrectos.`

#### Scenario: Usuario desactivado con la contraseña correcta
- **GIVEN** un usuario `mgomez` con contraseña `Verano2026` y `activo` en false
- **WHEN** se llama a `POST /api/v1/auth/login` con `{"username": "mgomez", "password": "Verano2026"}`
- **THEN** la respuesta es 401 con `detail` igual a `Usuario o contraseña incorrectos.`
- **AND** el cuerpo no trae `access_token`

### Requirement: Contador de intentos fallidos
Un ingreso con contraseña incorrecta de un usuario activo y no bloqueado SHALL incrementar `intentos_fallidos` en 1. Un ingreso correcto SHALL ponerlo en 0. Los ingresos de usuarios desactivados o ya bloqueados MUST NOT modificar el contador.

#### Scenario: Un ingreso incorrecto incrementa el contador
- **GIVEN** un usuario activo `jperez` con `intentos_fallidos` en 2
- **WHEN** se llama a `POST /api/v1/auth/login` con una contraseña incorrecta
- **THEN** la respuesta es 401
- **AND** `intentos_fallidos` de `jperez` en la base es 3

#### Scenario: Un ingreso correcto pone el contador en cero
- **GIVEN** un usuario activo `jperez` con `intentos_fallidos` en 4 y contraseña `Verano2026`
- **WHEN** se llama a `POST /api/v1/auth/login` con la contraseña `Verano2026`
- **THEN** la respuesta es 200
- **AND** `intentos_fallidos` de `jperez` en la base es 0

#### Scenario: El quinto ingreso incorrecto deja el contador en cinco
- **GIVEN** un usuario activo `jperez` con `intentos_fallidos` en 4
- **WHEN** se llama a `POST /api/v1/auth/login` con una contraseña incorrecta
- **THEN** la respuesta es 401 con `detail` igual a `Usuario o contraseña incorrectos.`
- **AND** `intentos_fallidos` de `jperez` en la base es 5

#### Scenario: El ingreso de un usuario desactivado no toca el contador
- **GIVEN** un usuario `mgomez` con `activo` en false e `intentos_fallidos` en 1
- **WHEN** se llama a `POST /api/v1/auth/login` con una contraseña incorrecta
- **THEN** la respuesta es 401
- **AND** `intentos_fallidos` de `mgomez` en la base sigue en 1

### Requirement: Usuario bloqueado no ingresa
Un usuario activo con `intentos_fallidos` en 5 o más SHALL recibir 403 con `detail` igual a `Usuario bloqueado. Pedile a un Admin que blanquee tu contraseña.`, sin token, sea la contraseña correcta o no. El contador MUST NOT cambiar.

#### Scenario: Bloqueado con la contraseña correcta
- **GIVEN** un usuario activo `jperez` con `intentos_fallidos` en 5 y contraseña `Verano2026`
- **WHEN** se llama a `POST /api/v1/auth/login` con la contraseña `Verano2026`
- **THEN** la respuesta es 403 con `detail` igual a `Usuario bloqueado. Pedile a un Admin que blanquee tu contraseña.`
- **AND** el cuerpo no trae `access_token`
- **AND** `intentos_fallidos` de `jperez` en la base sigue en 5

#### Scenario: Bloqueado con la contraseña incorrecta
- **GIVEN** un usuario activo `jperez` con `intentos_fallidos` en 7
- **WHEN** se llama a `POST /api/v1/auth/login` con una contraseña incorrecta
- **THEN** la respuesta es 403 con el mismo `detail` de usuario bloqueado
- **AND** `intentos_fallidos` de `jperez` en la base sigue en 7

#### Scenario: Con cuatro intentos todavía entra
- **GIVEN** un usuario activo `jperez` con `intentos_fallidos` en 4 y contraseña `Verano2026`
- **WHEN** se llama a `POST /api/v1/auth/login` con la contraseña `Verano2026`
- **THEN** la respuesta es 200 con un `access_token`

### Requirement: Identificación del usuario actual por token
Todo endpoint protegido SHALL identificar a quien llama por el encabezado `Authorization: Bearer <token>` y releer el usuario de la base en cada petición. SHALL responder 401 si falta el token, si no es válido, si venció, si el `sub` del token no es un entero dentro del rango de los ids, si no corresponde a ningún usuario, si el usuario está desactivado o si está bloqueado. `GET /api/v1/auth/yo` devuelve los datos públicos del usuario actual y su `debe_cambiar_password`.

#### Scenario: El token del ingreso sirve para identificarse
- **GIVEN** un usuario activo `jperez` que acaba de ingresar y recibió un `access_token`
- **WHEN** se llama a `GET /api/v1/auth/yo` con el encabezado `Authorization: Bearer <access_token>`
- **THEN** la respuesta es 200 y `username` es `jperez`

#### Scenario: Sin token
- **WHEN** se llama a `GET /api/v1/auth/yo` sin encabezado `Authorization`
- **THEN** la respuesta es 401

#### Scenario: Token adulterado
- **GIVEN** un `access_token` válido de `jperez` al que se le cambió un carácter de la firma
- **WHEN** se llama a `GET /api/v1/auth/yo` con ese token
- **THEN** la respuesta es 401

#### Scenario: Token firmado con otra clave
- **GIVEN** un token con `sub` igual al id de `jperez` y vencimiento futuro, firmado con una clave distinta de la del sistema
- **WHEN** se llama a `GET /api/v1/auth/yo` con ese token
- **THEN** la respuesta es 401

#### Scenario: Token vencido
- **GIVEN** un token de `jperez` firmado con la clave del sistema y vencido hace un minuto
- **WHEN** se llama a `GET /api/v1/auth/yo` con ese token
- **THEN** la respuesta es 401

#### Scenario: Token cuyo sub no corresponde a ningún usuario
- **GIVEN** un token firmado con la clave del sistema, con vencimiento futuro y `sub` igual a un id que no existe en la tabla `usuario`
- **WHEN** se llama a `GET /api/v1/auth/yo` con ese token
- **THEN** la respuesta es 401

#### Scenario: Token cuyo sub está fuera del rango de los ids
- **GIVEN** un token firmado con la clave del sistema, con vencimiento futuro y `sub` igual a `9223372036854775808` (2^63, uno más que el máximo de BIGINT)
- **WHEN** se llama a `GET /api/v1/auth/yo` con ese token
- **THEN** la respuesta es 401

#### Scenario: Token vigente de un usuario desactivado después del ingreso
- **GIVEN** `jperez` ingresó y recibió un `access_token`
- **AND** después se puso `activo` en false
- **WHEN** se llama a `GET /api/v1/auth/yo` con ese token
- **THEN** la respuesta es 401

#### Scenario: Token vigente de un usuario bloqueado después del ingreso
- **GIVEN** `jperez` ingresó y recibió un `access_token`
- **AND** después su `intentos_fallidos` llegó a 5
- **WHEN** se llama a `GET /api/v1/auth/yo` con ese token
- **THEN** la respuesta es 401

#### Scenario: Los datos del usuario actual no exponen secretos
- **GIVEN** un `access_token` vigente de `jperez`, rol `profesor`, con `debe_cambiar_password` en false
- **WHEN** se llama a `GET /api/v1/auth/yo`
- **THEN** la respuesta es 200 con `id`, `username`, `nombre`, `apellido`, `rol` igual a `profesor` y `debe_cambiar_password` en false
- **AND** el cuerpo no tiene `password_hash`, `password_hash_anterior` ni `intentos_fallidos`

### Requirement: Cambio obligatorio de contraseña pendiente
Un usuario con `debe_cambiar_password` en true SHALL poder ingresar y recibir su token, con `usuario.debe_cambiar_password` en true en la respuesta. Con ese token, todo endpoint protegido SHALL responder 403 con `detail` igual a `Tenés que cambiar tu contraseña antes de continuar.`, salvo dos exentos: `GET /api/v1/auth/yo` y el cambio de contraseña.

#### Scenario: Ingresa con el cambio pendiente
- **GIVEN** un usuario activo `jperez` con contraseña `Verano2026`, `debe_cambiar_password` en true e `intentos_fallidos` en 2
- **WHEN** se llama a `POST /api/v1/auth/login` con la contraseña `Verano2026`
- **THEN** la respuesta es 200 con un `access_token` y `usuario.debe_cambiar_password` en true
- **AND** `intentos_fallidos` de `jperez` en la base es 0

#### Scenario: Con el cambio pendiente no puede hacer nada más
- **GIVEN** un endpoint protegido declarado para los roles `admin`, `coordinador` y `profesor`
- **AND** un `access_token` vigente de `jperez`, rol `profesor`, que tiene `debe_cambiar_password` en true
- **WHEN** `jperez` llama a ese endpoint
- **THEN** la respuesta es 403 con `detail` igual a `Tenés que cambiar tu contraseña antes de continuar.`

#### Scenario: Con el cambio pendiente igual puede saber quién es
- **GIVEN** un `access_token` vigente de `jperez`, que tiene `debe_cambiar_password` en true
- **WHEN** se llama a `GET /api/v1/auth/yo` con ese token
- **THEN** la respuesta es 200 con `username` igual a `jperez` y `debe_cambiar_password` en true

#### Scenario: Con el cambio pendiente tampoco pasa un endpoint de su rol
- **GIVEN** un endpoint protegido declarado para el rol `admin`
- **AND** un `access_token` vigente de un Admin con `debe_cambiar_password` en true
- **WHEN** el Admin llama a ese endpoint
- **THEN** la respuesta es 403 con `detail` igual a `Tenés que cambiar tu contraseña antes de continuar.`

#### Scenario: Con el cambio pendiente, el 403 de cambio gana al de rol
- **GIVEN** un endpoint protegido declarado solo para el rol `admin`
- **AND** un `access_token` vigente de un Profesor con `debe_cambiar_password` en true
- **WHEN** el Profesor llama a ese endpoint
- **THEN** la respuesta es 403 con `detail` igual a `Tenés que cambiar tu contraseña antes de continuar.`, no el de falta de permiso

### Requirement: Declaración de roles por endpoint
Cada endpoint protegido SHALL declarar qué roles pueden usarlo. Un usuario autenticado cuyo rol no esté entre los declarados SHALL recibir 403 con `detail` igual a `No tenés permiso para esta operación.`; uno cuyo rol sí esté declarado SHALL pasar. Sin token válido, la respuesta SHALL ser 401 antes de evaluar el rol.

#### Scenario: Rol declarado
- **GIVEN** un endpoint protegido declarado para los roles `admin` y `coordinador`
- **AND** un `access_token` vigente de un Coordinador sin cambio pendiente
- **WHEN** el Coordinador llama a ese endpoint
- **THEN** la respuesta es 200

#### Scenario: Rol no declarado
- **GIVEN** un endpoint protegido declarado para los roles `admin` y `coordinador`
- **AND** un `access_token` vigente de un Profesor sin cambio pendiente
- **WHEN** el Profesor llama a ese endpoint
- **THEN** la respuesta es 403 con `detail` igual a `No tenés permiso para esta operación.`

#### Scenario: Endpoint solo para Admin y un Coordinador
- **GIVEN** un endpoint protegido declarado solo para el rol `admin`
- **AND** un `access_token` vigente de un Coordinador sin cambio pendiente
- **WHEN** el Coordinador llama a ese endpoint
- **THEN** la respuesta es 403 con `detail` igual a `No tenés permiso para esta operación.`

#### Scenario: Sin token en un endpoint con roles
- **GIVEN** un endpoint protegido declarado solo para el rol `admin`
- **WHEN** se lo llama sin encabezado `Authorization`
- **THEN** la respuesta es 401
