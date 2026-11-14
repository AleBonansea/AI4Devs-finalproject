# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
