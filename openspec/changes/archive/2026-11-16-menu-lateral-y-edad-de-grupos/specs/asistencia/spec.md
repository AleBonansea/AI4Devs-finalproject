# Spec Delta

## MODIFIED Requirements

### Requirement: Pantalla «Tomar asistencia»
La dirección `/asistencia`, dentro de la zona protegida, SHALL mostrar el campo `Grupo`, con los grupos de `GET /api/v1/grupos` escritos como nombre, turno y edad (`Delfines · Mañana · 5 a 6 años`, con la misma regla que el alta: una sola edad si `edad_desde` y `edad_hasta` son iguales), y el campo `Fecha`, con la fecha de hoy del dispositivo. Si hay un solo grupo, queda elegido. Con grupo y fecha, abre esa asistencia y muestra la lista.

#### Scenario: Profesor ve solo sus grupos
- **GIVEN** la sesión de un Profesor y `GET /api/v1/grupos` responde «Delfines» mañana y «Delfines» tarde, los dos con `edad_desde` 5 y `edad_hasta` 6
- **WHEN** se abre `/asistencia` y se despliega `Grupo`
- **THEN** las únicas opciones son `Delfines · Mañana · 5 a 6 años` y `Delfines · Tarde · 5 a 6 años`
- **AND** `Grupo` está sin elegir

#### Scenario: Un solo grupo queda elegido y abre la asistencia de hoy
- **GIVEN** el dispositivo está en el huso de Argentina y son las 21:30 del 2027-01-05 (en UTC ya es el 2027-01-06), `GET /api/v1/grupos` responde solo «Delfines» mañana (`edad_desde` 5, `edad_hasta` 6), y su asistencia del 2027-01-05 trae a Martín Gómez, Juan Pérez y Sofía Ruiz sin tomar
- **WHEN** se abre `/asistencia`
- **THEN** `Grupo` está en `Delfines · Mañana · 5 a 6 años` y `Fecha` tiene `2027-01-05`
- **AND** se ven `Martín Gómez`, `Juan Pérez` y `Sofía Ruiz`, en ese orden, cada uno con las opciones `Presente` y `Ausente` sin elegir

#### Scenario: Cambiar la fecha vuelve a abrir la asistencia
- **GIVEN** `/asistencia` abierta en «Delfines» mañana del 2027-01-05, y la asistencia del 2027-01-04 trae a Martín Gómez ausente
- **WHEN** se escribe `2027-01-04` en `Fecha`
- **THEN** se pide la asistencia de «Delfines» mañana del 2027-01-04
- **AND** Martín Gómez tiene elegida la opción `Ausente`

#### Scenario: Grupo sin alumnos inscriptos
- **GIVEN** `GET /api/v1/grupos` incluye «Caballitos» tarde con `edad_desde` 3 y `edad_hasta` 4, y su asistencia del 2027-01-05 responde con `alumnos` vacía
- **WHEN** se elige `Caballitos · Tarde · 3 a 4 años`
- **THEN** se ve `No hay alumnos inscriptos en este grupo.`
- **AND** no se ve el botón `Guardar`
