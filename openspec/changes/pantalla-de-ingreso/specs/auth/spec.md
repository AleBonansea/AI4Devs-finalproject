# Spec Delta

## ADDED Requirements

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
La dirección `/` SHALL mostrar el nombre y el apellido del usuario actual, su rol escrito como `Admin`, `Coordinador` o `Profesor`, y un botón `Salir`. No tiene otro contenido.

#### Scenario: Inicio de un Profesor
- **GIVEN** la sesión de un usuario `Carlos Gómez` con rol `profesor` y `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** se ve `Carlos Gómez`, `Profesor` y el botón `Salir`

### Requirement: Aviso de cambio de contraseña pendiente
Si el usuario actual tiene `debe_cambiar_password` en true, venga del ingreso o de `GET /api/v1/auth/yo`, toda la zona protegida SHALL mostrar solo un aviso con el título `Tenés que cambiar tu contraseña antes de continuar.` y el texto `El cambio de contraseña todavía no está disponible. Pedile ayuda a un Admin.`, más el botón `Salir`. MUST NOT mostrar el inicio.

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
