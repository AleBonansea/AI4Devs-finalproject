# Spec Delta

## Purpose

El marco común de la zona protegida: un encabezado con el usuario y un menú lateral permanente con las pantallas que permite el rol, para moverse entre pantallas sin volver al inicio.

## ADDED Requirements

### Requirement: Encabezado de la zona protegida
Toda pantalla de la zona protegida SHALL mostrar un encabezado con el nombre de la aplicación `Escuela de Verano`, el nombre y el apellido del usuario actual, su rol escrito como `Admin`, `Coordinador` o `Profesor`, y el botón `Salir`.

#### Scenario: Encabezado en una pantalla que no es el inicio
- **GIVEN** la sesión de un usuario `Carlos Gómez` con rol `profesor` y `debe_cambiar_password` en false
- **WHEN** se abre `/asistencia`
- **THEN** se ven `Escuela de Verano`, `Carlos Gómez`, `Profesor` y el botón `Salir`

#### Scenario: Salir desde otra pantalla
- **GIVEN** la sesión de un Coordinador en `/alumnos/nuevo`
- **WHEN** se pulsa `Salir`
- **THEN** la dirección pasa a `/ingresar` y no queda token guardado

### Requirement: Opciones del menú según el rol
Toda pantalla de la zona protegida SHALL mostrar un menú con la sección `Escuela` y sus opciones `Inicio` (lleva a `/`), `Registrar alumno` (lleva a `/alumnos/nuevo`) y `Tomar asistencia` (lleva a `/asistencia`). Solo para el Admin, además, la sección `Administración` con `Registrar cargo` (lleva a `/cargos/nuevo`) y `Cuenta corriente` (lleva a `/cuenta-corriente`). El menú MUST NOT ofrecer opciones de pantallas que no existen.

#### Scenario: Menú del Admin
- **GIVEN** la sesión de un Admin con `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** el menú muestra, en este orden, `Escuela`, `Inicio`, `Registrar alumno`, `Tomar asistencia`, `Administración`, `Registrar cargo` y `Cuenta corriente`, y nada más

#### Scenario: Menú del Coordinador
- **GIVEN** la sesión de un Coordinador con `debe_cambiar_password` en false
- **WHEN** se abre `/`
- **THEN** el menú muestra `Inicio`, `Registrar alumno` y `Tomar asistencia`
- **AND** no se ven `Administración`, `Registrar cargo` ni `Cuenta corriente`

#### Scenario: Menú del Profesor
- **GIVEN** la sesión de un Profesor con `debe_cambiar_password` en false
- **WHEN** se abre `/asistencia`
- **THEN** el menú muestra `Inicio`, `Registrar alumno` y `Tomar asistencia`
- **AND** no se ven `Administración`, `Registrar cargo` ni `Cuenta corriente`

### Requirement: Moverse desde el menú
Pulsar una opción del menú SHALL llevar a su dirección desde cualquier pantalla de la zona protegida, sin pasar por el inicio.

#### Scenario: De registrar alumno a tomar asistencia
- **GIVEN** la sesión de un Coordinador en `/alumnos/nuevo`
- **WHEN** se pulsa `Tomar asistencia` en el menú
- **THEN** la dirección pasa a `/asistencia`

#### Scenario: De la cuenta corriente a registrar un cargo
- **GIVEN** la sesión de un Admin en `/cuenta-corriente`
- **WHEN** se pulsa `Registrar cargo` en el menú
- **THEN** la dirección pasa a `/cargos/nuevo`

#### Scenario: Volver al inicio
- **GIVEN** la sesión de un Profesor en `/asistencia`
- **WHEN** se pulsa `Inicio` en el menú
- **THEN** la dirección pasa a `/`

### Requirement: La pantalla abierta queda marcada en el menú
La opción del menú que corresponde a la dirección abierta SHALL quedar marcada como la página actual (`aria-current="page"`), y ninguna otra.

#### Scenario: Marcada en tomar asistencia
- **GIVEN** la sesión de un Profesor
- **WHEN** se abre `/asistencia`
- **THEN** `Tomar asistencia` está marcada como página actual
- **AND** `Inicio` y `Registrar alumno` no lo están

#### Scenario: Marcada en el inicio
- **GIVEN** la sesión de un Coordinador
- **WHEN** se abre `/`
- **THEN** `Inicio` está marcada como página actual
- **AND** `Registrar alumno` y `Tomar asistencia` no lo están

### Requirement: Sin menú fuera de la zona habilitada
El encabezado de la zona protegida y el menú MUST NOT mostrarse en la pantalla de ingreso, mientras se comprueba la sesión, ni en el aviso de cambio de contraseña pendiente.

#### Scenario: El ingreso no tiene menú
- **GIVEN** no hay token guardado
- **WHEN** se abre `/ingresar`
- **THEN** no se ven `Inicio`, `Registrar alumno` ni `Tomar asistencia`

#### Scenario: Mientras se comprueba la sesión no hay menú
- **GIVEN** hay un token guardado y `GET /api/v1/auth/yo` todavía no respondió
- **WHEN** se abre `/asistencia`
- **THEN** se ve el indicador de carga `Comprobando la sesión`
- **AND** no se ven `Inicio`, `Registrar alumno` ni `Tomar asistencia`

#### Scenario: El cambio de contraseña pendiente no tiene menú
- **GIVEN** hay un token guardado y `GET /api/v1/auth/yo` responde 200 con `debe_cambiar_password` en true
- **WHEN** se abre `/asistencia`
- **THEN** se ve `Tenés que cambiar tu contraseña antes de continuar.`
- **AND** no se ven `Inicio`, `Registrar alumno` ni `Tomar asistencia`
