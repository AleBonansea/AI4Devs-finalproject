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

### Requirement: Un solo botón de ingreso
La pantalla de ingreso SHALL tener un único botón, `Ingresar`: el rol con el que se entra sale del usuario que ingresa. MUST NOT ofrecer botones ni opciones para entrar eligiendo un rol.

#### Scenario: El único botón es Ingresar
- **WHEN** se abre `/ingresar`
- **THEN** hay exactamente un botón en la pantalla, con el nombre `Ingresar`

#### Scenario: No se puede elegir el rol al entrar
- **WHEN** se abre `/ingresar`
- **THEN** no se ve ningún texto que empiece con `Entrar como`
- **AND** no se ve el texto `Prototipo`
