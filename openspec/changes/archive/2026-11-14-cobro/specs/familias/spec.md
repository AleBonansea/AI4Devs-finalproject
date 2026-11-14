# Spec Delta

## ADDED Requirements

### Requirement: Inscripciones de una familia
`GET /api/v1/familias/{familia_id}/inscripciones` SHALL responder 200 con las inscripciones de los alumnos de la familia en la temporada vigente, ordenadas por apellido, nombre y turno (mañana antes que tarde), cada una con exactamente `inscripcion_id`, `alumno_id`, `nombre`, `apellido`, `turno` y `grupo` (nombre). Una familia que no existe da 404 con `La familia no existe.`

#### Scenario: Hijos en uno y en los dos turnos
- **GIVEN** la familia «Pérez – Ana» con Ana inscripta en «Tiburones» mañana y Juan en «Delfines» mañana y «Pulpos» tarde, todos de la temporada vigente
- **WHEN** un Admin llama a `GET /api/v1/familias/{id de Pérez – Ana}/inscripciones`
- **THEN** la respuesta es 200 con tres elementos, en este orden: Ana Pérez `manana` «Tiburones», Juan Pérez `manana` «Delfines» y Juan Pérez `tarde` «Pulpos»

#### Scenario: Solo la temporada vigente
- **GIVEN** la familia «Pérez – Ana» con Juan inscripto en «Delfines» mañana de la temporada vigente y Ana inscripta solo en la temporada cerrada 2025-26
- **WHEN** un Admin pide las inscripciones de la familia
- **THEN** la respuesta trae solo la inscripción de Juan

#### Scenario: Solo los hijos de esa familia
- **GIVEN** Juan Pérez y Lucía Gómez, de familias distintas, inscriptos en «Delfines» mañana
- **WHEN** un Admin pide las inscripciones de la familia de Juan
- **THEN** la respuesta no trae a Lucía Gómez

#### Scenario: Familia sin inscripciones en la temporada
- **GIVEN** una familia cuyos hijos no tienen inscripciones en la temporada vigente
- **WHEN** un Admin pide sus inscripciones
- **THEN** la respuesta es 200 con una lista vacía

#### Scenario: Sin datos médicos ni de personas
- **GIVEN** la familia «Pérez – Ana» con Juan inscripto en «Delfines» mañana
- **WHEN** un Admin pide sus inscripciones
- **THEN** cada elemento tiene exactamente los campos `inscripcion_id`, `alumno_id`, `nombre`, `apellido`, `turno` y `grupo`

#### Scenario: Familia que no existe
- **WHEN** un Admin pide las inscripciones de un `familia_id` que no existe
- **THEN** la respuesta es 404 con `detail` `La familia no existe.`

#### Scenario: Id de familia más grande que el máximo
- **WHEN** un Admin pide las inscripciones del `familia_id` 9223372036854775808
- **THEN** la respuesta es 404 con `detail` `La familia no existe.`

### Requirement: Quién puede ver las inscripciones de una familia
`GET /api/v1/familias/{familia_id}/inscripciones` SHALL estar disponible solo para el Admin, que es quien cobra. Coordinador y Profesor reciben 403 con `No tenés permiso para esta operación.`, exista la familia o no y sean o no sus hijos de los grupos del Profesor; sin sesión, 401.

#### Scenario: Profesor de otro grupo
- **GIVEN** `cfernandez`, Profesora asignada solo a grupos donde no hay ningún hijo de la familia «Pérez – Ana»
- **WHEN** `cfernandez` pide las inscripciones de la familia «Pérez – Ana»
- **THEN** la respuesta es 403 con `detail` `No tenés permiso para esta operación.` y no trae ningún alumno

#### Scenario: Profesor del grupo de un hijo
- **GIVEN** `jperez`, Profesor asignado a «Delfines» mañana, donde está inscripto Juan Pérez
- **WHEN** `jperez` pide las inscripciones de la familia «Pérez – Ana»
- **THEN** la respuesta es 403

#### Scenario: Profesor con una familia que no existe
- **WHEN** un Profesor pide las inscripciones de un `familia_id` que no existe
- **THEN** la respuesta es 403, no 404

#### Scenario: Coordinador
- **WHEN** un Coordinador pide las inscripciones de la familia «Pérez – Ana»
- **THEN** la respuesta es 403

#### Scenario: Sin sesión
- **WHEN** se piden las inscripciones de una familia sin token
- **THEN** la respuesta es 401
