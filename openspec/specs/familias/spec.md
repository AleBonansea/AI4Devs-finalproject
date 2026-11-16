# familias Specification

## Purpose

Agrupa a los hijos en familias, que son la unidad de facturación con una sola categoría y una sola cuenta corriente, y registra a los adultos vinculados a cada familia (tutores y personas autorizadas a retirar), reutilizables entre familias.

## Requirements

### Requirement: Categoría de la familia
Cada familia SHALL tener una categoría obligatoria, `socio`, `empleado` o `no_socio`. La familia no pertenece a una temporada: se conserva de un año al otro.

#### Scenario: Familia con categoría válida
- **WHEN** se inserta una familia con categoría `empleado`
- **THEN** la fila queda guardada con un id asignado por la base

#### Scenario: Familia sin categoría
- **WHEN** se inserta una familia sin categoría
- **THEN** la base rechaza la fila

#### Scenario: Categoría que no existe
- **WHEN** se inserta una familia con categoría `vip`
- **THEN** la base rechaza la fila

### Requirement: Etiqueta de la familia
La etiqueta de una familia SHALL ser `«Apellido – Nombre»` del alumno de la familia con la fecha de nacimiento más antigua, separados por una raya (`–`) entre espacios. Si dos alumnos nacieron el mismo día, vale el que se registró primero. La etiqueta no se guarda ni se edita: se recalcula cada vez que se lee, y el id de la familia no cambia.

#### Scenario: Familia con un solo hijo
- **GIVEN** una familia cuyo único alumno es Juan Pérez, nacido el 2020-03-10
- **WHEN** se lee la etiqueta de la familia
- **THEN** es `Pérez – Juan`

#### Scenario: Se suma un hijo mayor
- **GIVEN** la familia `Pérez – Juan`, con Juan nacido el 2020-03-10
- **WHEN** se registra en esa familia a Ana Pérez, nacida el 2018-07-05
- **THEN** la etiqueta pasa a `Pérez – Ana`
- **AND** el id de la familia es el mismo que antes

#### Scenario: Se suma un hijo menor con otro apellido
- **GIVEN** la familia `Pérez – Ana`, con Ana nacida el 2018-07-05
- **WHEN** se registra en esa familia a Tomás Gómez, nacido el 2019-11-20
- **THEN** la etiqueta sigue siendo `Pérez – Ana`

#### Scenario: Medio hermano mayor con otro apellido
- **GIVEN** la familia `Pérez – Ana`, con Ana nacida el 2018-07-05
- **WHEN** se registra en esa familia a Lucas Gómez, nacido el 2018-07-04
- **THEN** la etiqueta pasa a `Gómez – Lucas`

#### Scenario: Mellizos
- **GIVEN** una familia con Sofía Ruiz, nacida el 2019-05-01, registrada primero
- **WHEN** se registra en esa familia a Mateo Ruiz, nacido el 2019-05-01
- **THEN** la etiqueta sigue siendo `Ruiz – Sofía`

### Requirement: Persona reutilizable entre familias
Una persona SHALL guardarse una sola vez, con nombre, apellido y teléfono obligatorios y DNI optativo, y poder vincularse a más de una familia. La base MUST rechazar dos personas con el mismo DNI y MUST aceptar varias personas sin DNI.

#### Scenario: Dos personas con el mismo DNI
- **GIVEN** una persona con DNI `30111222`
- **WHEN** se inserta otra persona con DNI `30111222`
- **THEN** la base rechaza la fila

#### Scenario: Dos personas sin DNI
- **GIVEN** una persona sin DNI
- **WHEN** se inserta otra persona sin DNI
- **THEN** la fila queda guardada

#### Scenario: Persona sin teléfono
- **WHEN** se inserta una persona sin teléfono
- **THEN** la base rechaza la fila

#### Scenario: La misma persona en dos familias
- **GIVEN** la persona María Pérez, tutora de la familia `Pérez – Ana`
- **WHEN** se la vincula como autorizada a retirar en la familia `Gómez – Lucía`
- **THEN** los dos vínculos quedan guardados y hay una sola fila de María Pérez

### Requirement: Vínculo de una persona con una familia
Cada vínculo entre una persona y una familia SHALL indicar si la persona es tutor y si está autorizada a retirar. Un tutor MUST estar siempre autorizado a retirar. La base MUST rechazar un vínculo sin ninguna marca y el mismo vínculo dos veces.

#### Scenario: Tutor sin autorización a retirar
- **WHEN** se inserta un vínculo con `es_tutor` en true y `autorizado_retiro` en false
- **THEN** la base rechaza la fila

#### Scenario: Autorizado a retirar que no es tutor
- **WHEN** se inserta un vínculo con `es_tutor` en false y `autorizado_retiro` en true
- **THEN** la fila queda guardada

#### Scenario: Vínculo sin ninguna marca
- **WHEN** se inserta un vínculo con `es_tutor`, `autorizado_retiro` y `contacto_emergencia` en false
- **THEN** la base rechaza la fila

#### Scenario: El mismo vínculo dos veces
- **GIVEN** María Pérez vinculada a la familia `Pérez – Ana`
- **WHEN** se inserta otro vínculo de María Pérez con la misma familia
- **THEN** la base rechaza la fila

#### Scenario: Borrar una persona vinculada
- **GIVEN** María Pérez vinculada a la familia `Pérez – Ana`
- **WHEN** se ejecuta un `DELETE` sobre esa persona
- **THEN** la base rechaza el borrado y el vínculo sigue en la base

### Requirement: Buscar familias por apellido
`GET /api/v1/familias?apellido=` SHALL devolver las familias que tienen al menos un alumno cuyo apellido empieza con el texto pedido, sin distinguir mayúsculas y sin tener en cuenta los espacios alrededor. Cada resultado trae solo `id`, `etiqueta` y `categoria`. Busca en todas las familias para los tres roles. El texto MUST tener al menos 2 caracteres; la respuesta trae a lo sumo 20 familias, ordenadas por etiqueta.

#### Scenario: Búsqueda por el apellido del hijo mayor
- **GIVEN** la familia `Pérez – Ana`, categoría `empleado`
- **WHEN** un Coordinador llama a `GET /api/v1/familias?apellido=pér`
- **THEN** la respuesta es 200 y trae un elemento con el `id` de esa familia, `etiqueta` `Pérez – Ana` y `categoria` `empleado`

#### Scenario: Búsqueda por el apellido de un medio hermano
- **GIVEN** la familia `Pérez – Ana`, con Tomás Gómez como hijo menor
- **WHEN** un Admin llama a `GET /api/v1/familias?apellido=Gómez`
- **THEN** la respuesta incluye la familia `Pérez – Ana`

#### Scenario: Un Profesor encuentra una familia sin hijos en sus grupos
- **GIVEN** un Profesor asignado solo a «Delfines» mañana
- **AND** la familia `Pérez – Ana`, cuyos alumnos están inscriptos solo en «Tiburones» mañana
- **WHEN** el Profesor llama a `GET /api/v1/familias?apellido=Pérez`
- **THEN** la respuesta es 200 e incluye la familia `Pérez – Ana`
- **AND** cada elemento tiene exactamente los campos `id`, `etiqueta` y `categoria`: ni alumnos, ni fechas de nacimiento, ni grupos, ni personas

#### Scenario: Texto de dos caracteres
- **WHEN** un Coordinador llama a `GET /api/v1/familias?apellido=Pé`
- **THEN** la respuesta es 200

#### Scenario: Texto de un carácter
- **WHEN** un Coordinador llama a `GET /api/v1/familias?apellido=%20P%20`
- **THEN** la respuesta es 422

#### Scenario: Más de 20 coincidencias
- **GIVEN** 21 familias con un alumno de apellido `Martínez`
- **WHEN** un Coordinador llama a `GET /api/v1/familias?apellido=Mar`
- **THEN** la respuesta trae exactamente 20 familias, ordenadas por etiqueta

#### Scenario: Los comodines se buscan como texto
- **GIVEN** la familia `Pérez – Ana` y ninguna familia con un alumno cuyo apellido tenga `%` o `_`
- **WHEN** un Coordinador llama a `GET /api/v1/familias?apellido=P%25` y a `GET /api/v1/familias?apellido=P_rez`
- **THEN** las dos respuestas son 200 con una lista vacía

#### Scenario: Sin coincidencias
- **WHEN** un Coordinador llama a `GET /api/v1/familias?apellido=Zzz`
- **THEN** la respuesta es 200 con una lista vacía

#### Scenario: Sin sesión
- **WHEN** se llama a `GET /api/v1/familias?apellido=Pérez` sin token
- **THEN** la respuesta es 401

#### Scenario: Con el cambio de contraseña pendiente
- **GIVEN** un Profesor con `debe_cambiar_password` en true
- **WHEN** llama a `GET /api/v1/familias?apellido=Pérez`
- **THEN** la respuesta es 403

### Requirement: Buscar una persona por DNI
`GET /api/v1/personas?dni=` SHALL devolver la persona cuyo DNI coincide exactamente con el pedido, después de quitarle espacios, puntos y guiones, con solo `id`, `nombre` y `apellido`. Si no hay ninguna, responde 404 con `No hay ninguna persona con ese DNI.` Lo usan los tres roles. [SUPUESTO: la reutilización es solo por DNI exacto; ver la pregunta abierta «Reutilizar una persona ya cargada» en `aclaraciones-cliente.md`].

#### Scenario: DNI que existe
- **GIVEN** la persona María Pérez, teléfono `3511234567`, DNI `30111222`, tutora de la familia `Pérez – Ana`
- **WHEN** un Profesor llama a `GET /api/v1/personas?dni=30111222`
- **THEN** la respuesta es 200 con `id` de María Pérez, `nombre` `María` y `apellido` `Pérez`
- **AND** el cuerpo tiene exactamente esos tres campos: ni teléfono, ni DNI, ni familias

#### Scenario: DNI escrito con puntos
- **GIVEN** la persona María Pérez con DNI `30111222`
- **WHEN** un Coordinador llama a `GET /api/v1/personas?dni=30.111.222`
- **THEN** la respuesta es 200 con el `id` de María Pérez

#### Scenario: DNI escrito con guiones
- **GIVEN** la persona María Pérez con DNI `30111222`
- **WHEN** un Coordinador llama a `GET /api/v1/personas?dni=30-111-222`
- **THEN** la respuesta es 200 con el `id` de María Pérez

#### Scenario: DNI incompleto
- **GIVEN** la persona María Pérez con DNI `30111222`
- **WHEN** un Coordinador llama a `GET /api/v1/personas?dni=3011122`
- **THEN** la respuesta es 404 con `detail` `No hay ninguna persona con ese DNI.`

#### Scenario: DNI vacío
- **WHEN** un Coordinador llama a `GET /api/v1/personas?dni=%20`
- **THEN** la respuesta es 422

#### Scenario: Sin sesión
- **WHEN** se llama a `GET /api/v1/personas?dni=30111222` sin token
- **THEN** la respuesta es 401

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
