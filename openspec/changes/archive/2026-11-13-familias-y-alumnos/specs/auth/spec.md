# Spec Delta

## MODIFIED Requirements

### Requirement: Inicio de la zona protegida
La dirección `/` SHALL mostrar el nombre y el apellido del usuario actual, su rol escrito como `Admin`, `Coordinador` o `Profesor`, un botón `Salir` y un acceso `Registrar alumno` que lleva a `/alumnos/nuevo`. Además del nombre de la aplicación, no tiene otro contenido.

#### Scenario: Inicio de un Profesor
- **GIVEN** la sesión de un usuario `Carlos Gómez` con rol `profesor` y `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** se ve `Carlos Gómez`, `Profesor` y el botón `Salir`

#### Scenario: Ir a registrar un alumno
- **GIVEN** la sesión de un Coordinador con `debe_cambiar_password` en false
- **WHEN** se abre `/` y se pulsa `Registrar alumno`
- **THEN** la dirección pasa a `/alumnos/nuevo`

## ADDED Requirements

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
