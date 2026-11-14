# Spec Delta

## MODIFIED Requirements

### Requirement: Inicio de la zona protegida
La dirección `/` SHALL mostrar el nombre y el apellido del usuario actual, su rol escrito como `Admin`, `Coordinador` o `Profesor`, un botón `Salir`, un acceso `Registrar alumno` que lleva a `/alumnos/nuevo` y un acceso `Tomar asistencia` que lleva a `/asistencia`. Solo para el Admin, además, un acceso `Registrar cargo` que lleva a `/cargos/nuevo`. Además del nombre de la aplicación, no tiene otro contenido.

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

#### Scenario: Ir a registrar un cargo
- **GIVEN** la sesión de un Admin con `debe_cambiar_password` en false
- **WHEN** se abre `/` y se pulsa `Registrar cargo`
- **THEN** la dirección pasa a `/cargos/nuevo`

#### Scenario: El Coordinador no ve el acceso a cobrar
- **GIVEN** la sesión de un Coordinador con `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** se ven `Registrar alumno` y `Tomar asistencia`, y no se ve `Registrar cargo`

#### Scenario: El Profesor no ve el acceso a cobrar
- **GIVEN** la sesión de un Profesor con `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** no se ve `Registrar cargo`
