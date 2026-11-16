# Spec Delta

## MODIFIED Requirements

### Requirement: Inicio de la zona protegida
La dirección `/` SHALL mostrar, dentro del encabezado y el menú de la zona protegida (capability `navegacion`), el saludo `Hola, <nombre>` con el nombre del usuario actual. Los accesos a las pantallas son los del menú: el inicio no repite botones de acceso ni tiene otro contenido. Lo que se ve en toda la página respeta el rol: al Coordinador y al Profesor no se les ofrece `Registrar cargo` ni `Cuenta corriente`.

#### Scenario: Inicio de un Profesor
- **GIVEN** la sesión de un usuario `Carlos Gómez` con rol `profesor` y `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** se ve `Hola, Carlos`
- **AND** se ven `Carlos Gómez`, `Profesor` y el botón `Salir`

#### Scenario: El inicio no repite los accesos del menú
- **GIVEN** la sesión de un Admin con `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** cada uno de `Registrar alumno`, `Tomar asistencia`, `Registrar cargo` y `Cuenta corriente` aparece una sola vez en la página, en el menú

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

#### Scenario: Ir a la cuenta corriente
- **GIVEN** la sesión de un Admin con `debe_cambiar_password` en false
- **WHEN** se abre `/` y se pulsa `Cuenta corriente`
- **THEN** la dirección pasa a `/cuenta-corriente`

#### Scenario: El Coordinador no ve el acceso a cobrar
- **GIVEN** la sesión de un Coordinador con `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** se ven `Registrar alumno` y `Tomar asistencia`, y no se ven `Registrar cargo` ni `Cuenta corriente`

#### Scenario: El Profesor no ve el acceso a cobrar
- **GIVEN** la sesión de un Profesor con `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** no se ven `Registrar cargo` ni `Cuenta corriente`
