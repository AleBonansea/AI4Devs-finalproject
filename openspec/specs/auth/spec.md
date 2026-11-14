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

### Requirement: Pantalla de ingreso
El navegador SHALL ofrecer en `/ingresar` un formulario con un campo `Usuario`, un campo `Contraseña` que no muestra lo escrito, y un botón `Ingresar`, cada campo con su etiqueta asociada. Al enviarlo SHALL llamar a `POST /api/v1/auth/login` con `username` y `password` tal como se escribieron: la normalización del usuario la hace la API.

#### Scenario: El formulario tiene sus campos
- **WHEN** se abre `/ingresar`
- **THEN** hay un campo con la etiqueta `Usuario`, un campo con la etiqueta `Contraseña` de tipo contraseña y un botón `Ingresar`

#### Scenario: Se envía lo escrito, sin tocarlo
- **GIVEN** la pantalla de ingreso abierta
- **WHEN** se escribe ` JPerez ` en `Usuario`, `Verano2026` en `Contraseña` y se pulsa `Ingresar`
- **THEN** se hace una sola llamada a `POST /api/v1/auth/login` con el cuerpo `{"username": " JPerez ", "password": "Verano2026"}`

#### Scenario: Se envía con Enter
- **GIVEN** `jperez` en `Usuario` y `Verano2026` en `Contraseña`
- **WHEN** se pulsa Enter con el foco en `Contraseña`
- **THEN** se hace una llamada a `POST /api/v1/auth/login`

### Requirement: Encabezado de las pantallas sin sesión
La pantalla de ingreso y el aviso de cambio de contraseña pendiente SHALL mostrar, arriba de su contenido y en este orden: el logo de la escuela, con texto alternativo `Logo de la Escuela de Verano`; un título de nivel 1 `Escuela de Verano`; y el subtítulo `Centro Médico · Administración de la temporada`. El subtítulo MUST NOT incluir la temporada, porque esas pantallas se ven sin una sesión que permita consultarla.

#### Scenario: El ingreso muestra el encabezado
- **WHEN** se abre `/ingresar`
- **THEN** se ve una imagen con texto alternativo `Logo de la Escuela de Verano`
- **AND** hay un título de nivel 1 con el texto `Escuela de Verano`
- **AND** se ve el texto `Centro Médico · Administración de la temporada`, exacto y sin nada después

#### Scenario: El encabezado va antes de los campos
- **WHEN** se abre `/ingresar`
- **THEN** en el orden del documento, la imagen del logo va antes del título `Escuela de Verano`, el título va antes del subtítulo y el subtítulo va antes del campo `Usuario`

#### Scenario: El aviso de cambio pendiente muestra el mismo encabezado
- **GIVEN** la API responde 200 a `POST /api/v1/auth/login` con `usuario.debe_cambiar_password` en true
- **WHEN** se ingresa con `jperez` y `Verano2026`
- **THEN** se ve la imagen con texto alternativo `Logo de la Escuela de Verano`, el título de nivel 1 `Escuela de Verano` y el texto `Centro Médico · Administración de la temporada`
- **AND** se ve `Tenés que cambiar tu contraseña antes de continuar.`

#### Scenario: En el aviso, el encabezado va antes del aviso
- **GIVEN** hay un token guardado y `GET /api/v1/auth/yo` responde 200 con `debe_cambiar_password` en true
- **WHEN** se abre `/`
- **THEN** en el orden del documento, la imagen del logo va antes del título `Escuela de Verano`, el título va antes del texto `Centro Médico · Administración de la temporada`, ese texto va antes del título del aviso `Tenés que cambiar tu contraseña antes de continuar.`, y el título del aviso va antes del botón `Salir`

### Requirement: Un solo botón de ingreso
La pantalla de ingreso SHALL tener un único botón, `Ingresar`: el rol con el que se entra sale del usuario que ingresa. MUST NOT ofrecer botones ni opciones para entrar eligiendo un rol.

#### Scenario: El único botón es Ingresar
- **WHEN** se abre `/ingresar`
- **THEN** hay exactamente un botón en la pantalla, con el nombre `Ingresar`

#### Scenario: No se puede elegir el rol al entrar
- **WHEN** se abre `/ingresar`
- **THEN** no se ve ningún texto que empiece con `Entrar como`
- **AND** no se ve el texto `Prototipo`

### Requirement: Campos vacíos no se envían
Si `Usuario` está vacío o tiene solo espacios, o `Contraseña` está vacía, el navegador SHALL mostrar al lado de cada campo vacío `Ingresá tu usuario.` o `Ingresá tu contraseña.`, y MUST NOT llamar a la API. Una contraseña de solo espacios no está vacía y se envía.

#### Scenario: Los dos campos vacíos
- **WHEN** se pulsa `Ingresar` sin escribir nada
- **THEN** al lado de `Usuario` aparece `Ingresá tu usuario.` y al lado de `Contraseña` aparece `Ingresá tu contraseña.`
- **AND** no se hace ninguna llamada a la API

#### Scenario: Usuario de solo espacios
- **WHEN** se escribe `   ` en `Usuario`, `Verano2026` en `Contraseña` y se pulsa `Ingresar`
- **THEN** al lado de `Usuario` aparece `Ingresá tu usuario.`
- **AND** no se hace ninguna llamada a la API

#### Scenario: Usuario de un carácter se envía
- **WHEN** se escribe `j` en `Usuario`, `Verano2026` en `Contraseña` y se pulsa `Ingresar`
- **THEN** se hace una llamada a `POST /api/v1/auth/login`
- **AND** no aparece `Ingresá tu usuario.`

#### Scenario: Contraseña de solo espacios se envía
- **WHEN** se escribe `jperez` en `Usuario`, `   ` en `Contraseña` y se pulsa `Ingresar`
- **THEN** se hace una llamada a `POST /api/v1/auth/login` con `password` igual a `   `

### Requirement: Ingreso correcto guarda la sesión
Si la API responde 200, el navegador SHALL guardar el `access_token` para las peticiones siguientes y SHALL mostrar la zona protegida con el usuario que vino en la respuesta, sin volver a pedirlo.

#### Scenario: Ingresa y ve el inicio
- **GIVEN** la API responde 200 a `POST /api/v1/auth/login` con `access_token` igual a `tok-123` y `usuario` con `nombre` `Juana`, `apellido` `Pérez`, `rol` `coordinador` y `debe_cambiar_password` en false
- **WHEN** se ingresa con `jperez` y `Verano2026`
- **THEN** la dirección pasa a `/`
- **AND** se ve `Juana Pérez` y `Coordinador`
- **AND** la petición siguiente a la API lleva el encabezado `Authorization: Bearer tok-123`

#### Scenario: El token sobrevive a recargar la página
- **GIVEN** se ingresó y la API devolvió `access_token` igual a `tok-123`
- **WHEN** se recarga la página en `/`
- **THEN** se llama a `GET /api/v1/auth/yo` con el encabezado `Authorization: Bearer tok-123`

### Requirement: Estado de carga del ingreso
Mientras la llamada de ingreso está en curso, el botón `Ingresar` SHALL quedar deshabilitado y mostrar que está trabajando, y MUST NOT dispararse una segunda llamada. Al terminar, con éxito o error, el botón SHALL volver a habilitarse si la pantalla sigue a la vista.

#### Scenario: El botón se deshabilita mientras espera
- **GIVEN** la API todavía no respondió a `POST /api/v1/auth/login`
- **WHEN** se mira el botón `Ingresar`
- **THEN** está deshabilitado y hay un indicador de progreso visible

#### Scenario: Un doble clic no manda dos ingresos
- **GIVEN** `jperez` y `Verano2026` escritos
- **WHEN** se pulsa `Ingresar` dos veces seguidas antes de que la API responda
- **THEN** se hace una sola llamada a `POST /api/v1/auth/login`

#### Scenario: Tras un error el botón vuelve a habilitarse
- **GIVEN** la API responde 401 a `POST /api/v1/auth/login`
- **WHEN** termina la llamada
- **THEN** el botón `Ingresar` está habilitado

### Requirement: Error general del ingreso
Si la API rechaza el ingreso con un mensaje general (401, 403 o un error del servidor) o no se puede conectar, el navegador SHALL mostrar ese mensaje en un aviso arriba del formulario, SHALL conservar lo escrito en `Usuario`, SHALL vaciar `Contraseña`, MUST NOT guardar ningún token y SHALL quedarse en `/ingresar`.

#### Scenario: Credenciales incorrectas
- **GIVEN** la API responde 401 con `detail` igual a `Usuario o contraseña incorrectos.`
- **WHEN** se ingresa con `jperez` y `Otra1234`
- **THEN** se ve el aviso `Usuario o contraseña incorrectos.`
- **AND** `Usuario` sigue diciendo `jperez` y `Contraseña` está vacía
- **AND** no hay token guardado y la dirección sigue en `/ingresar`

#### Scenario: Usuario bloqueado
- **GIVEN** la API responde 403 con `detail` igual a `Usuario bloqueado. Pedile a un Admin que blanquee tu contraseña.`
- **WHEN** se ingresa con `jperez` y `Verano2026`
- **THEN** se ve el aviso `Usuario bloqueado. Pedile a un Admin que blanquee tu contraseña.`
- **AND** no hay token guardado

#### Scenario: Sin conexión con el servidor
- **GIVEN** la llamada a `POST /api/v1/auth/login` falla sin respuesta, por red o porque el servidor no está
- **WHEN** se ingresa con `jperez` y `Verano2026`
- **THEN** se ve el aviso `No se pudo conectar con el servidor. Revisá tu conexión.`

#### Scenario: Error del servidor
- **GIVEN** la API responde 500 sin cuerpo JSON
- **WHEN** se ingresa con `jperez` y `Verano2026`
- **THEN** se ve el aviso `El servidor tuvo un problema. Intentá de nuevo.`

#### Scenario: El aviso se va al volver a intentar
- **GIVEN** se ve el aviso `Usuario o contraseña incorrectos.`
- **WHEN** se escribe la contraseña de nuevo, se pulsa `Ingresar` y la API responde 200
- **THEN** el aviso ya no está y se ve la zona protegida

### Requirement: Error por campo del ingreso
Si la API responde 422 con errores por campo, el navegador SHALL mostrar cada mensaje al lado del campo al que corresponde (`username` en `Usuario`, `password` en `Contraseña`), tal como lo manda la API, y MUST NOT guardar ningún token.

#### Scenario: La API rechaza el usuario
- **GIVEN** la API responde 422 con `detail` igual a `[{"loc": ["body", "username"], "msg": "Value error, El usuario no puede tener caracteres de control.", "type": "value_error"}]`
- **WHEN** se ingresa con `jperez` y `Verano2026`
- **THEN** al lado de `Usuario` aparece `Value error, El usuario no puede tener caracteres de control.`
- **AND** al lado de `Contraseña` no aparece ningún mensaje
- **AND** no hay token guardado

#### Scenario: La API rechaza la contraseña
- **GIVEN** la API responde 422 con un error cuyo `loc` es `["body", "password"]` y cuyo `msg` es `String should have at most 128 characters`
- **WHEN** se ingresa con `jperez` y una contraseña
- **THEN** al lado de `Contraseña` aparece `String should have at most 128 characters`

### Requirement: La zona protegida exige sesión
Toda dirección distinta de `/ingresar` SHALL exigir sesión. Sin token guardado, el navegador SHALL mostrar el ingreso sin llamar a la API. Con token, SHALL comprobarlo con `GET /api/v1/auth/yo` antes de mostrar nada de la zona protegida, y mientras tanto SHALL mostrar un indicador de carga.

#### Scenario: Sin token
- **GIVEN** no hay token guardado
- **WHEN** se abre `/`
- **THEN** la dirección pasa a `/ingresar` y se ve el formulario de ingreso
- **AND** no se hace ninguna llamada a la API

#### Scenario: Una dirección cualquiera sin token
- **GIVEN** no hay token guardado
- **WHEN** se abre `/familias`
- **THEN** la dirección pasa a `/ingresar`

#### Scenario: Con token vigente
- **GIVEN** hay un token guardado y `GET /api/v1/auth/yo` responde 200 con `nombre` `Juana`, `apellido` `Pérez`, `rol` `admin` y `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** se ve `Juana Pérez` y `Admin`

#### Scenario: Mientras se comprueba el token
- **GIVEN** hay un token guardado y `GET /api/v1/auth/yo` todavía no respondió
- **WHEN** se abre `/`
- **THEN** se ve un indicador de carga y no se ve ni el inicio ni el formulario de ingreso

### Requirement: Sesión rechazada por la API
Si `GET /api/v1/auth/yo` responde 401, el navegador SHALL borrar el token guardado y mandar al ingreso. Si falla por otra causa (sin conexión, error del servidor), SHALL conservar el token y mostrar el mensaje del error con un botón `Reintentar` que vuelve a comprobar la sesión.

#### Scenario: Token vencido o inválido
- **GIVEN** hay un token guardado y `GET /api/v1/auth/yo` responde 401
- **WHEN** se abre `/`
- **THEN** la dirección pasa a `/ingresar`
- **AND** no queda token guardado

#### Scenario: Sin conexión al comprobar la sesión
- **GIVEN** hay un token guardado y la llamada a `GET /api/v1/auth/yo` falla sin respuesta
- **WHEN** se abre `/`
- **THEN** se ve `No se pudo conectar con el servidor. Revisá tu conexión.` y un botón `Reintentar`
- **AND** el token sigue guardado y la dirección sigue en `/`

#### Scenario: Reintentar con la conexión de vuelta
- **GIVEN** se ve el error de conexión con el botón `Reintentar`
- **AND** `GET /api/v1/auth/yo` ahora responde 200 con `debe_cambiar_password` en false
- **WHEN** se pulsa `Reintentar`
- **THEN** se ve el inicio con el nombre del usuario

### Requirement: Inicio de la zona protegida
La dirección `/` SHALL mostrar el nombre y el apellido del usuario actual, su rol escrito como `Admin`, `Coordinador` o `Profesor`, un botón `Salir`, un acceso `Registrar alumno` que lleva a `/alumnos/nuevo` y un acceso `Tomar asistencia` que lleva a `/asistencia`. Además del nombre de la aplicación, no tiene otro contenido.

#### Scenario: Inicio de un Profesor
- **GIVEN** la sesión de un usuario `Carlos Gómez` con rol `profesor` y `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** se ve `Carlos Gómez`, `Profesor` y el botón `Salir`

#### Scenario: Ir a registrar un alumno
- **GIVEN** la sesión de un Coordinador con `debe_cambiar_password` en false
- **WHEN** se abre `/` y se pulsa `Registrar alumno`
- **THEN** la dirección pasa a `/alumnos/nuevo`

#### Scenario: Ir a tomar asistencia
- **GIVEN** la sesión de un Profesor con `debe_cambiar_password` en false
- **WHEN** se abre `/` y se pulsa `Tomar asistencia`
- **THEN** la dirección pasa a `/asistencia`

### Requirement: Aviso de cambio de contraseña pendiente
Si el usuario actual tiene `debe_cambiar_password` en true, venga del ingreso o de `GET /api/v1/auth/yo`, toda la zona protegida SHALL mostrar, debajo del encabezado de las pantallas sin sesión, solo un aviso con el título `Tenés que cambiar tu contraseña antes de continuar.` y el texto `El cambio de contraseña todavía no está disponible. Pedile ayuda a un Admin.`, más el botón `Salir`. MUST NOT mostrar el inicio.

#### Scenario: Ingresa con el cambio pendiente
- **GIVEN** la API responde 200 a `POST /api/v1/auth/login` con `usuario.debe_cambiar_password` en true
- **WHEN** se ingresa con `jperez` y `Verano2026`
- **THEN** se ve `Tenés que cambiar tu contraseña antes de continuar.` y `El cambio de contraseña todavía no está disponible. Pedile ayuda a un Admin.`
- **AND** se ve el botón `Salir`
- **AND** no se ve el nombre ni el rol del inicio

#### Scenario: Recarga con el cambio pendiente
- **GIVEN** hay un token guardado y `GET /api/v1/auth/yo` responde 200 con `debe_cambiar_password` en true
- **WHEN** se abre `/`
- **THEN** se ve `Tenés que cambiar tu contraseña antes de continuar.` y no se ve el inicio

#### Scenario: Sin el cambio pendiente no hay aviso
- **GIVEN** hay un token guardado y `GET /api/v1/auth/yo` responde 200 con `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** no aparece `Tenés que cambiar tu contraseña antes de continuar.`

### Requirement: Salir
El botón `Salir` SHALL borrar el token guardado en el navegador y llevar a `/ingresar`, sin llamar a la API. Después de salir, abrir una dirección de la zona protegida SHALL mandar al ingreso como si nunca se hubiera ingresado.

#### Scenario: Sale desde el inicio
- **GIVEN** la sesión de `Juana Pérez` en `/`
- **WHEN** se pulsa `Salir`
- **THEN** la dirección pasa a `/ingresar` y no queda token guardado
- **AND** no se hace ninguna llamada a la API

#### Scenario: Sale desde el aviso de cambio pendiente
- **GIVEN** se ve el aviso `Tenés que cambiar tu contraseña antes de continuar.`
- **WHEN** se pulsa `Salir`
- **THEN** la dirección pasa a `/ingresar` y no queda token guardado

#### Scenario: Después de salir no se vuelve atrás
- **GIVEN** se pulsó `Salir`
- **WHEN** se abre `/`
- **THEN** la dirección pasa a `/ingresar`
- **AND** no se hace ninguna llamada a `GET /api/v1/auth/yo`

### Requirement: Un 401 en cualquier llamada cierra la sesión
Si cualquier llamada a la API con sesión, no solo `GET /api/v1/auth/yo`, responde 401, el navegador SHALL borrar el token guardado, olvidar el usuario actual y mandar al ingreso.

#### Scenario: Token vencido al buscar una familia
- **GIVEN** la sesión de un Coordinador en `/alumnos/nuevo`
- **AND** `GET /api/v1/familias` responde 401
- **WHEN** se busca una familia por apellido
- **THEN** la dirección pasa a `/ingresar`
- **AND** no queda token guardado

#### Scenario: Un 403 no cierra la sesión
- **GIVEN** la sesión de un Profesor en `/alumnos/nuevo`
- **AND** `POST /api/v1/alumnos` responde 403
- **WHEN** se pulsa `Registrar` con el formulario completo
- **THEN** la dirección sigue en `/alumnos/nuevo` y el token sigue guardado
