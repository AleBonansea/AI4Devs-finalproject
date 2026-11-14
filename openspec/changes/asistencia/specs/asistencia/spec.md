# Spec Delta

## Purpose

Registra la presencia de cada alumno inscripto por día y turno, para que el staff controle quién vino. Es solo control: no interviene en el cobro ni dispara avisos.

## ADDED Requirements

### Requirement: Un registro de asistencia por inscripción y fecha
Cada registro de asistencia SHALL pertenecer a una inscripción y a una fecha, y decir si el alumno estuvo presente, quién lo registró por última vez y cuándo. La base MUST rechazar un segundo registro para la misma inscripción y fecha. Como cada turno es una inscripción, un alumno anotado en los dos turnos tiene un registro por turno.

#### Scenario: Dos registros para la misma inscripción y fecha
- **GIVEN** un registro de asistencia de la inscripción de Juan Pérez en «Delfines» mañana para el 2027-01-05
- **WHEN** se inserta otro registro para la misma inscripción y el 2027-01-05
- **THEN** la base rechaza la fila

#### Scenario: La misma inscripción en otra fecha
- **GIVEN** un registro de asistencia de la inscripción de Juan Pérez en «Delfines» mañana para el 2027-01-05
- **WHEN** se inserta un registro para la misma inscripción y el 2027-01-06
- **THEN** la fila queda guardada

#### Scenario: El mismo alumno y fecha en el otro turno
- **GIVEN** Juan Pérez inscripto en «Delfines» mañana y en «Pulpos» tarde, con un registro de la inscripción de la mañana para el 2027-01-05
- **WHEN** se inserta un registro de la inscripción de la tarde para el 2027-01-05
- **THEN** la fila queda guardada

#### Scenario: Registro sin presente
- **WHEN** se inserta un registro de asistencia sin valor para `presente`
- **THEN** la base rechaza la fila

### Requirement: Abrir la asistencia de un grupo en una fecha
`GET /api/v1/grupos/{grupo_id}/asistencias/{fecha}` SHALL responder 200 con `grupo_id`, `grupo` (nombre), `turno`, `fecha` y `alumnos`: los inscriptos en ese grupo, por apellido y nombre, cada uno con exactamente `inscripcion_id`, `nombre`, `apellido` y `presente` (true, false, o null si no se tomó esa fecha).

#### Scenario: Asistencia todavía no tomada
- **GIVEN** Juan Pérez, Sofía Ruiz y Martín Gómez inscriptos en «Delfines» mañana, sin asistencia registrada
- **WHEN** un Coordinador llama a `GET /api/v1/grupos/{id de Delfines mañana}/asistencias/2027-01-05`
- **THEN** la respuesta es 200 con `grupo` `Delfines`, `turno` `manana`, `fecha` `2027-01-05`
- **AND** `alumnos` trae, en este orden, a Martín Gómez, Juan Pérez y Sofía Ruiz, los tres con `presente` null

#### Scenario: Asistencia ya tomada
- **GIVEN** la asistencia del 2027-01-05 de «Delfines» mañana registrada con Juan Pérez y Sofía Ruiz presentes y Martín Gómez ausente
- **WHEN** un Coordinador abre la asistencia de «Delfines» mañana del 2027-01-05
- **THEN** Juan Pérez y Sofía Ruiz traen `presente` true y Martín Gómez `presente` false

#### Scenario: Lo registrado otro día no aparece
- **GIVEN** Martín Gómez marcado ausente en «Delfines» mañana el 2027-01-05
- **WHEN** un Coordinador abre la asistencia de «Delfines» mañana del 2027-01-06
- **THEN** Martín Gómez trae `presente` null

#### Scenario: Solo los inscriptos en ese grupo
- **GIVEN** Juan Pérez inscripto en «Delfines» mañana y en «Pulpos» tarde, y Ana Pérez inscripta solo en «Tiburones» mañana
- **WHEN** un Coordinador abre la asistencia de «Pulpos» tarde del 2027-01-05
- **THEN** `alumnos` trae solo a Juan Pérez
- **AND** su `inscripcion_id` es la de «Pulpos» tarde, no la de «Delfines» mañana

#### Scenario: Grupo sin alumnos inscriptos
- **GIVEN** el grupo «Caballitos» tarde de la temporada vigente, sin inscriptos
- **WHEN** un Coordinador abre su asistencia del 2027-01-05
- **THEN** la respuesta es 200 con `alumnos` como lista vacía

#### Scenario: Sin datos médicos ni de familia
- **GIVEN** Juan Pérez inscripto en «Delfines» mañana
- **WHEN** un Coordinador abre la asistencia de «Delfines» mañana del 2027-01-05
- **THEN** cada elemento de `alumnos` tiene exactamente los campos `inscripcion_id`, `nombre`, `apellido` y `presente`

#### Scenario: Grupo de una temporada cerrada se puede consultar
- **GIVEN** el grupo «Delfines» mañana de la temporada cerrada 2025-26, del 2026-01-05 al 2026-02-27, con Juan Pérez marcado presente el 2026-01-06
- **WHEN** un Admin abre la asistencia de ese grupo del 2026-01-06
- **THEN** la respuesta es 200 y Juan Pérez trae `presente` true

### Requirement: Guardar la asistencia de un grupo en una fecha
`PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}` con `asistencias` (cada una con `inscripcion_id` y `presente`) SHALL crear o actualizar un registro por inscripción y fecha, con quien llama como autor, y responder 200 con lo mismo que devuelve abrir esa asistencia después de guardar. Las inscripciones que no vienen no se modifican.

#### Scenario: Tomar la asistencia del día
- **GIVEN** Juan Pérez, Sofía Ruiz y Martín Gómez inscriptos en «Delfines» mañana, sin asistencia registrada, y `jperez` asignado a ese grupo
- **WHEN** `jperez` llama a `PUT /api/v1/grupos/{id de Delfines mañana}/asistencias/2027-01-05` con Juan Pérez y Sofía Ruiz `presente` true y Martín Gómez `presente` false
- **THEN** la respuesta es 200 con Martín Gómez `presente` false, Juan Pérez `presente` true y Sofía Ruiz `presente` true, en ese orden
- **AND** la base tiene exactamente tres registros de asistencia del 2027-01-05, los tres con `jperez` como autor

#### Scenario: Corregir una asistencia ya tomada
- **GIVEN** la asistencia del 2027-01-05 de «Delfines» mañana registrada por `jperez`, con Martín Gómez ausente
- **WHEN** un Coordinador llama al `PUT` de esa fecha con solo Martín Gómez `presente` true
- **THEN** la respuesta es 200 con Martín Gómez `presente` true
- **AND** hay un solo registro de Martín Gómez para el 2027-01-05, con el Coordinador como autor

#### Scenario: Los que no vienen en el pedido no se tocan
- **GIVEN** la asistencia del 2027-01-05 de «Delfines» mañana registrada por `jperez`, con Juan Pérez presente y Martín Gómez ausente
- **WHEN** un Coordinador llama al `PUT` de esa fecha con solo Martín Gómez `presente` true
- **THEN** el registro de Juan Pérez sigue con `presente` true y `jperez` como autor

#### Scenario: Guardar parte de la lista
- **GIVEN** Juan Pérez, Sofía Ruiz y Martín Gómez inscriptos en «Delfines» mañana, sin asistencia registrada
- **WHEN** un Coordinador llama al `PUT` del 2027-01-05 con solo Juan Pérez `presente` true
- **THEN** la respuesta trae a Juan Pérez con `presente` true y a Martín Gómez y Sofía Ruiz con `presente` null
- **AND** la base tiene un solo registro de asistencia del 2027-01-05

#### Scenario: Alumno inscripto en los dos turnos
- **GIVEN** Juan Pérez inscripto en «Delfines» mañana y en «Pulpos» tarde, marcado ausente en «Pulpos» tarde el 2027-01-05
- **WHEN** un Coordinador lo marca presente en «Delfines» mañana el 2027-01-05
- **THEN** su registro de «Pulpos» tarde del 2027-01-05 sigue con `presente` false
- **AND** al abrir la asistencia de «Pulpos» tarde del 2027-01-05, Juan Pérez trae `presente` false

#### Scenario: Guardar la asistencia no toca nada más
- **GIVEN** Martín Gómez inscripto en «Delfines» mañana
- **WHEN** un Coordinador guarda la asistencia de «Delfines» mañana del 2027-01-05 con Martín Gómez `presente` false
- **THEN** la cantidad de filas de todas las tablas, salvo `asistencia`, es la misma que antes del pedido

### Requirement: El cuerpo del guardado
El `PUT` SHALL rechazar con 422, sin guardar nada, una lista vacía, un elemento sin `presente`, una inscripción que no es de ese grupo y una inscripción repetida. Cada rechazo de un elemento lleva su `loc` terminado en `asistencias`, índice y campo.

#### Scenario: Lista vacía
- **WHEN** un Coordinador llama al `PUT` de «Delfines» mañana del 2027-01-05 con `asistencias` vacía
- **THEN** la respuesta es 422 con un error con `loc` terminado en `asistencias` y `msg` `Tiene que haber al menos un alumno.`

#### Scenario: Falta presente
- **WHEN** un Coordinador llama al `PUT` de «Delfines» mañana del 2027-01-05 con un elemento con `inscripcion_id` y sin `presente`
- **THEN** la respuesta es 422 con un error con `loc` terminado en `asistencias`, `0`, `presente` y `msg` `Este dato es obligatorio.`

#### Scenario: Inscripción de otro grupo
- **GIVEN** Juan Pérez inscripto en «Delfines» mañana y Ana Pérez en «Tiburones» mañana, sin asistencia registrada
- **WHEN** un Coordinador llama al `PUT` de «Delfines» mañana del 2027-01-05 con Juan Pérez `presente` true y, segunda, la inscripción de Ana Pérez `presente` true
- **THEN** la respuesta es 422 con un error con `loc` terminado en `asistencias`, `1`, `inscripcion_id` y `msg` `Esa inscripción no es de este grupo.`
- **AND** no hay ningún registro de asistencia del 2027-01-05, tampoco el de Juan Pérez

#### Scenario: Inscripción que no existe
- **WHEN** un Coordinador llama al `PUT` de «Delfines» mañana del 2027-01-05 con `inscripcion_id` 999999
- **THEN** la respuesta es 422 con un error con `loc` terminado en `asistencias`, `0`, `inscripcion_id` y `msg` `Esa inscripción no es de este grupo.`

#### Scenario: Inscripción repetida
- **WHEN** un Coordinador llama al `PUT` de «Delfines» mañana del 2027-01-05 con la inscripción de Juan Pérez dos veces, primero `presente` true y después `presente` false
- **THEN** la respuesta es 422 con un error con `loc` terminado en `asistencias`, `1`, `inscripcion_id` y `msg` `Esa inscripción ya está en la lista.`
- **AND** no hay ningún registro de asistencia del 2027-01-05

### Requirement: La fecha está dentro de la temporada del grupo
Abrir o guardar la asistencia SHALL aceptar solo fechas entre el inicio y el cierre de la temporada del grupo, los dos incluidos. Fuera de ese rango responde 422 con `detail` `La fecha está fuera de la temporada del grupo, del DD/MM/AAAA al DD/MM/AAAA.` y no guarda nada.

#### Scenario: Primer día de la temporada
- **GIVEN** la temporada vigente 2026-27, del 2027-01-04 al 2027-02-26, y Juan Pérez inscripto en «Delfines» mañana
- **WHEN** un Coordinador guarda la asistencia de «Delfines» mañana del 2027-01-04 con Juan Pérez `presente` true
- **THEN** la respuesta es 200

#### Scenario: Día anterior al inicio
- **GIVEN** la temporada vigente 2026-27, del 2027-01-04 al 2027-02-26, y Juan Pérez inscripto en «Delfines» mañana
- **WHEN** un Coordinador guarda la asistencia de «Delfines» mañana del 2027-01-03 con Juan Pérez `presente` true
- **THEN** la respuesta es 422 con `detail` `La fecha está fuera de la temporada del grupo, del 04/01/2027 al 26/02/2027.`
- **AND** no hay ningún registro de asistencia del 2027-01-03

#### Scenario: Último día de la temporada
- **GIVEN** la temporada vigente 2026-27, del 2027-01-04 al 2027-02-26, y Juan Pérez inscripto en «Delfines» mañana
- **WHEN** un Coordinador guarda la asistencia de «Delfines» mañana del 2027-02-26 con Juan Pérez `presente` true
- **THEN** la respuesta es 200

#### Scenario: Día posterior al cierre
- **GIVEN** la temporada vigente 2026-27, del 2027-01-04 al 2027-02-26, y Juan Pérez inscripto en «Delfines» mañana
- **WHEN** un Coordinador guarda la asistencia de «Delfines» mañana del 2027-02-27 con Juan Pérez `presente` true
- **THEN** la respuesta es 422 con `detail` `La fecha está fuera de la temporada del grupo, del 04/01/2027 al 26/02/2027.`

#### Scenario: Abrir una fecha fuera de la temporada
- **GIVEN** la temporada vigente 2026-27, del 2027-01-04 al 2027-02-26
- **WHEN** un Coordinador abre la asistencia de «Delfines» mañana del 2027-03-01
- **THEN** la respuesta es 422 con `detail` `La fecha está fuera de la temporada del grupo, del 04/01/2027 al 26/02/2027.`

#### Scenario: Fecha mal escrita
- **WHEN** un Coordinador abre la asistencia de «Delfines» mañana de `05-01-2027`
- **THEN** la respuesta es 422 con un error con `loc` terminado en `fecha` y `msg` `La fecha no es válida.`

### Requirement: Grupos donde no se guarda asistencia
El `PUT` SHALL responder 404 con `El grupo no existe.` si el grupo no existe, y 409 sin guardar nada si el grupo es de una temporada cerrada o está inactivo. El `GET` responde 404 para un grupo que no existe, y 200 para uno cerrado o inactivo, que se puede consultar. Lo del grupo inactivo es **[SUPUESTO]** (pregunta abierta en `aclaraciones-cliente.md`).

#### Scenario: Guardar en un grupo que no existe
- **WHEN** un Coordinador llama al `PUT` de `/api/v1/grupos/999999/asistencias/2027-01-05`
- **THEN** la respuesta es 404 con `detail` `El grupo no existe.`

#### Scenario: Abrir un grupo que no existe
- **WHEN** un Coordinador llama a `GET /api/v1/grupos/999999/asistencias/2027-01-05`
- **THEN** la respuesta es 404 con `detail` `El grupo no existe.`

#### Scenario: Id de grupo más grande que el máximo
- **WHEN** un Coordinador llama a `GET /api/v1/grupos/9223372036854775808/asistencias/2027-01-05`
- **THEN** la respuesta es 404 con `detail` `El grupo no existe.`

#### Scenario: Guardar en un grupo de una temporada cerrada
- **GIVEN** el grupo «Delfines» mañana de la temporada cerrada 2025-26, del 2026-01-05 al 2026-02-27, con Juan Pérez inscripto
- **WHEN** un Admin guarda su asistencia del 2026-01-06 con Juan Pérez `presente` true
- **THEN** la respuesta es 409 con `detail` `El grupo es de una temporada cerrada, que queda solo para consulta.`
- **AND** no hay ningún registro de asistencia del 2026-01-06

#### Scenario: Guardar en un grupo inactivo
- **GIVEN** un grupo inactivo «Pulpos» mañana de la temporada vigente, con Juan Pérez inscripto
- **WHEN** un Coordinador guarda su asistencia del 2027-01-05 con Juan Pérez `presente` true
- **THEN** la respuesta es 409 con `detail` `El grupo no está activo.`
- **AND** no hay ningún registro de asistencia del 2027-01-05

#### Scenario: Abrir un grupo inactivo
- **GIVEN** un grupo inactivo «Pulpos» mañana de la temporada vigente, con Juan Pérez inscripto
- **WHEN** un Coordinador abre su asistencia del 2027-01-05
- **THEN** la respuesta es 200 con Juan Pérez en `alumnos`

### Requirement: Quién puede abrir y guardar la asistencia
Los dos endpoints SHALL estar disponibles para Admin y Coordinador en cualquier grupo, aunque no tengan grupos asignados, y para el Profesor solo en los grupos que tiene asignados. Sobre otro grupo, exista o no, esté activo o no y sea de la temporada que sea, el Profesor recibe 403 con `Solo podés tomar asistencia de tus grupos.`, sin datos de alumnos y sin que se guarde nada.

#### Scenario: Profesor en su grupo
- **GIVEN** `jperez` asignado a «Delfines» mañana, con Juan Pérez inscripto
- **WHEN** `jperez` abre la asistencia de «Delfines» mañana del 2027-01-05
- **THEN** la respuesta es 200 con Juan Pérez en `alumnos`

#### Scenario: Profesor guarda en un grupo ajeno
- **GIVEN** `jperez` asignado solo a «Delfines» mañana, y Lucía Gómez inscripta en «Pulpos» tarde
- **WHEN** `jperez` guarda la asistencia de «Pulpos» tarde del 2027-01-05 con Lucía Gómez `presente` true
- **THEN** la respuesta es 403 con `detail` `Solo podés tomar asistencia de tus grupos.`
- **AND** no hay ningún registro de asistencia del 2027-01-05

#### Scenario: Profesor abre un grupo ajeno
- **GIVEN** `jperez` asignado solo a «Delfines» mañana, y Lucía Gómez inscripta en «Pulpos» tarde
- **WHEN** `jperez` abre la asistencia de «Pulpos» tarde del 2027-01-05
- **THEN** la respuesta es 403 con `detail` `Solo podés tomar asistencia de tus grupos.`
- **AND** la respuesta no contiene `Lucía` ni `Gómez`

#### Scenario: Profesor con un grupo que no existe
- **GIVEN** `jperez` asignado solo a «Delfines» mañana
- **WHEN** `jperez` abre la asistencia de `/api/v1/grupos/999999/asistencias/2027-01-05`
- **THEN** la respuesta es 403 con `detail` `Solo podés tomar asistencia de tus grupos.`

#### Scenario: Profesor con un grupo ajeno de una temporada cerrada y fecha fuera de ella
- **GIVEN** `jperez` asignado solo a «Delfines» mañana de 2026-27, y un grupo de la temporada cerrada 2025-26
- **WHEN** `jperez` guarda la asistencia de ese grupo del 2027-01-05
- **THEN** la respuesta es 403 con `detail` `Solo podés tomar asistencia de tus grupos.`

#### Scenario: Coordinador sin grupos asignados
- **GIVEN** un Coordinador sin grupos asignados, y Lucía Gómez inscripta en «Pulpos» tarde
- **WHEN** el Coordinador guarda la asistencia de «Pulpos» tarde del 2027-01-05 con Lucía Gómez `presente` true
- **THEN** la respuesta es 200 y queda registrada con el Coordinador como autor

#### Scenario: Admin en cualquier grupo
- **GIVEN** un Admin sin grupos asignados, y Lucía Gómez inscripta en «Pulpos» tarde
- **WHEN** el Admin abre la asistencia de «Pulpos» tarde del 2027-01-05
- **THEN** la respuesta es 200 con Lucía Gómez en `alumnos`

#### Scenario: Sin sesión
- **WHEN** se llama al `PUT` de «Delfines» mañana del 2027-01-05 sin token
- **THEN** la respuesta es 401
- **AND** no hay ningún registro de asistencia del 2027-01-05

### Requirement: Pantalla «Tomar asistencia»
La dirección `/asistencia`, dentro de la zona protegida, SHALL mostrar el campo `Grupo`, con los grupos de `GET /api/v1/grupos` escritos como nombre y turno (`Delfines · Mañana`), y el campo `Fecha`, con la fecha de hoy del dispositivo. Si hay un solo grupo, queda elegido. Con grupo y fecha, abre esa asistencia y muestra la lista.

#### Scenario: Profesor ve solo sus grupos
- **GIVEN** la sesión de un Profesor y `GET /api/v1/grupos` responde «Delfines» mañana y «Delfines» tarde
- **WHEN** se abre `/asistencia` y se despliega `Grupo`
- **THEN** las únicas opciones son `Delfines · Mañana` y `Delfines · Tarde`
- **AND** `Grupo` está sin elegir

#### Scenario: Un solo grupo queda elegido y abre la asistencia de hoy
- **GIVEN** la fecha del dispositivo es 2027-01-05, `GET /api/v1/grupos` responde solo «Delfines» mañana, y su asistencia del 2027-01-05 trae a Martín Gómez, Juan Pérez y Sofía Ruiz sin tomar
- **WHEN** se abre `/asistencia`
- **THEN** `Grupo` está en `Delfines · Mañana` y `Fecha` tiene `2027-01-05`
- **AND** se ven `Martín Gómez`, `Juan Pérez` y `Sofía Ruiz`, en ese orden, cada uno con las opciones `Presente` y `Ausente` sin elegir

#### Scenario: Cambiar la fecha vuelve a abrir la asistencia
- **GIVEN** `/asistencia` abierta en «Delfines» mañana del 2027-01-05, y la asistencia del 2027-01-04 trae a Martín Gómez ausente
- **WHEN** se escribe `2027-01-04` en `Fecha`
- **THEN** se pide la asistencia de «Delfines» mañana del 2027-01-04
- **AND** Martín Gómez tiene elegida la opción `Ausente`

#### Scenario: Grupo sin alumnos inscriptos
- **GIVEN** la asistencia de «Caballitos» tarde del 2027-01-05 responde con `alumnos` vacía
- **WHEN** se elige `Caballitos · Tarde`
- **THEN** se ve `No hay alumnos inscriptos en este grupo.`
- **AND** no se ve el botón `Guardar`

### Requirement: Guardar desde la pantalla
El botón `Guardar` SHALL estar deshabilitado mientras ningún alumno tenga elegido `Presente` o `Ausente`. Al pulsarlo manda en el `PUT` solo los alumnos con una opción elegida; con 200 muestra `Asistencia guardada.` y la lista de la respuesta. Si la API rechaza, muestra su `detail` y conserva lo marcado.

#### Scenario: Marcar y guardar
- **GIVEN** `/asistencia` abierta en «Delfines» mañana del 2027-01-05 con Martín Gómez, Juan Pérez y Sofía Ruiz sin tomar
- **WHEN** se elige `Presente` para Juan Pérez y Sofía Ruiz y `Ausente` para Martín Gómez, y se pulsa `Guardar`
- **THEN** el `PUT` a la asistencia de «Delfines» mañana del 2027-01-05 lleva exactamente esas tres inscripciones, Juan Pérez y Sofía Ruiz con `presente` true y Martín Gómez con false
- **AND** se ve `Asistencia guardada.`

#### Scenario: Guardar sin marcar a todos
- **GIVEN** `/asistencia` abierta en «Delfines» mañana del 2027-01-05 con Martín Gómez, Juan Pérez y Sofía Ruiz sin tomar
- **WHEN** se elige `Presente` solo para Juan Pérez y se pulsa `Guardar`
- **THEN** el `PUT` lleva solo la inscripción de Juan Pérez, con `presente` true

#### Scenario: Nada marcado
- **GIVEN** `/asistencia` abierta en «Delfines» mañana del 2027-01-05 con los tres alumnos sin tomar
- **WHEN** no se elige ninguna opción
- **THEN** el botón `Guardar` está deshabilitado

#### Scenario: Corregir lo ya tomado
- **GIVEN** `/asistencia` abierta en «Delfines» mañana del 2027-01-05 con Martín Gómez ausente, Juan Pérez presente y Sofía Ruiz presente
- **WHEN** se elige `Presente` para Martín Gómez y se pulsa `Guardar`
- **THEN** el `PUT` lleva las tres inscripciones, con Martín Gómez `presente` true

#### Scenario: La API rechaza el guardado
- **GIVEN** `/asistencia` abierta en «Delfines» mañana del 2027-01-05, y el `PUT` responde 409 con `El grupo no está activo.`
- **WHEN** se elige `Presente` para Juan Pérez y se pulsa `Guardar`
- **THEN** se ve `El grupo no está activo.`
- **AND** Juan Pérez sigue con `Presente` elegido
- **AND** no se ve `Asistencia guardada.`
