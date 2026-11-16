# alumnos Specification

## Purpose

Registra a cada chico con sus datos mínimos, lo vincula a su familia y lo inscribe en un grupo y turno de la temporada vigente, desde la API y desde la pantalla «Registrar alumno», con el permiso por grupo del Profesor.

## Requirements

### Requirement: Ficha mínima del alumno
Cada alumno SHALL pertenecer a una familia y tener nombre, apellido y fecha de nacimiento obligatorios. El alumno no pertenece a una temporada: se conserva de un año al otro.

#### Scenario: Alumno sin familia
- **WHEN** se inserta un alumno sin familia
- **THEN** la base rechaza la fila

#### Scenario: Alumno sin fecha de nacimiento
- **GIVEN** una familia
- **WHEN** se inserta un alumno de esa familia sin fecha de nacimiento
- **THEN** la base rechaza la fila

### Requirement: Inscripción en un grupo y turno
Cada inscripción SHALL unir un alumno con un grupo, y su temporada y su turno MUST ser los del grupo. Un alumno MUST tener a lo sumo una inscripción por turno y temporada, y puede tener una en cada turno.

#### Scenario: Segunda inscripción en el mismo turno y temporada
- **GIVEN** Juan inscripto en «Delfines» mañana de la temporada 2026-27
- **WHEN** se inserta una inscripción de Juan en «Tiburones» mañana de la temporada 2026-27
- **THEN** la base rechaza la fila

#### Scenario: Inscripción en el otro turno
- **GIVEN** Juan inscripto en «Delfines» mañana de la temporada 2026-27
- **WHEN** se inserta una inscripción de Juan en «Delfines» tarde de la temporada 2026-27
- **THEN** la fila queda guardada

#### Scenario: Turno distinto del de su grupo
- **GIVEN** el grupo «Delfines» mañana
- **WHEN** se inserta una inscripción en ese grupo con turno `tarde`
- **THEN** la base rechaza la fila

#### Scenario: Borrar un alumno inscripto
- **GIVEN** Juan inscripto en «Delfines» mañana
- **WHEN** se ejecuta un `DELETE` sobre Juan
- **THEN** la base rechaza el borrado y la inscripción sigue en la base

### Requirement: Alta de un alumno con familia nueva
`POST /api/v1/alumnos` con `categoria` y sin `familia_id` SHALL crear, en una sola operación, la familia con esa categoría, el alumno, la inscripción en el grupo elegido y los vínculos de las personas enviadas, todas autorizadas a retirar. Responde 201 con el alumno, su familia (`id`, `etiqueta`, `categoria`) y su inscripción (`grupo_id`, `grupo_nombre`, `turno`, `temporada_id`).

#### Scenario: Primer hijo con su tutora
- **GIVEN** el grupo «Delfines» mañana de la temporada vigente, para nacidos del 2020-01-01 al 2021-12-31
- **WHEN** un Coordinador llama a `POST /api/v1/alumnos` con nombre `Juan`, apellido `Pérez`, `fecha_nacimiento` `2020-03-10`, el `grupo_id` de «Delfines» mañana, `categoria` `empleado` y una persona nueva María Pérez, teléfono `3511234567`, DNI `30111222`, con `es_tutor` en true
- **THEN** la respuesta es 201 con la familia `etiqueta` `Pérez – Juan` y `categoria` `empleado`, y la inscripción en «Delfines», turno `manana`, de la temporada vigente
- **AND** María Pérez queda vinculada a la familia con `es_tutor` y `autorizado_retiro` en true
- **AND** no se pidió ningún documento

#### Scenario: Tutora y otra persona autorizada
- **WHEN** un Coordinador da de alta a Juan Pérez con familia nueva, María Pérez como tutora y Raúl Pérez, teléfono `3517654321`, sin DNI, con `es_tutor` en false
- **THEN** la respuesta es 201
- **AND** Raúl Pérez queda vinculado con `es_tutor` en false y `autorizado_retiro` en true

#### Scenario: Familia nueva sin ningún tutor
- **WHEN** un Coordinador da de alta a Juan Pérez con familia nueva y solo Raúl Pérez, con `es_tutor` en false
- **THEN** la respuesta es 422 con un error en `personas` cuyo `msg` es `La familia nueva necesita al menos un tutor.`
- **AND** no se crean ni la familia, ni el alumno, ni la persona, ni la inscripción

#### Scenario: Familia nueva sin categoría
- **WHEN** un Coordinador da de alta a Juan Pérez sin `familia_id` ni `categoria`
- **THEN** la respuesta es 422 con un error en `categoria`
- **AND** no se crea nada

### Requirement: Alta de un alumno en una familia existente
`POST /api/v1/alumnos` con `familia_id` SHALL registrar al alumno en esa familia, que conserva su categoría y sus tutores. El pedido MUST NOT traer `categoria`: la categoría de una familia existente no se cambia en el alta, para ningún rol. Puede traer personas para sumar a la familia como autorizadas a retirar, o ninguna.

#### Scenario: Segundo hijo, en otro grupo
- **GIVEN** la familia `Pérez – Juan`, categoría `empleado`, con Juan nacido el 2020-03-10 y María Pérez como tutora
- **AND** el grupo «Tiburones» mañana, para nacidos del 2017-01-01 al 2019-12-31
- **WHEN** un Admin da de alta a Ana Pérez, nacida el 2018-07-05, con el `familia_id` de esa familia, sin personas, en «Tiburones» mañana
- **THEN** la respuesta es 201 con la familia del mismo `id`, `etiqueta` `Pérez – Ana` y `categoria` `empleado`
- **AND** la familia sigue teniendo a María Pérez como tutora y ningún otro vínculo

#### Scenario: Intento de cambiar la categoría en el alta
- **GIVEN** la familia `Pérez – Ana`, categoría `empleado`
- **WHEN** un Profesor da de alta a un hijo de esa familia en uno de sus grupos, con el `familia_id` y `categoria` `socio`
- **THEN** la respuesta es 422 con un error en `categoria` cuyo `msg` es `La categoría de una familia existente no se cambia en el alta.`
- **AND** no se crea el alumno y la familia sigue siendo `empleado`

#### Scenario: Familia que no existe
- **WHEN** un Coordinador da de alta a un alumno con un `familia_id` que no existe
- **THEN** la respuesta es 422 con un error en `familia_id` cuyo `msg` es `La familia no existe.`

#### Scenario: Persona ya vinculada a la familia
- **GIVEN** la familia `Pérez – Ana` con María Pérez como tutora
- **WHEN** un Coordinador da de alta a un hijo de esa familia reutilizando a María Pérez por su `persona_id`
- **THEN** la respuesta es 422 con un error en `personas.0.persona_id` cuyo `msg` es `Esa persona ya está vinculada a la familia.`
- **AND** no se crea el alumno

### Requirement: Personas en el alta
Cada persona del alta SHALL ser o bien una persona ya cargada, indicada por `persona_id`, o bien una nueva con `nombre`, `apellido` y `telefono` obligatorios y `dni` optativo, más `es_tutor`. El DNI se guarda sin espacios, puntos ni guiones. La misma persona MUST NOT aparecer dos veces en un alta. Un DNI ya cargado no crea otra persona: se rechaza.

#### Scenario: Reutilizar una persona de otra familia
- **GIVEN** María Pérez, tutora de la familia `Pérez – Ana`
- **WHEN** un Coordinador da de alta a Lucía Gómez con familia nueva, categoría `socio`, y María Pérez por su `persona_id` con `es_tutor` en true
- **THEN** la respuesta es 201
- **AND** María Pérez queda vinculada a las dos familias y sigue habiendo una sola persona con su DNI

#### Scenario: Persona nueva con un DNI ya cargado
- **GIVEN** María Pérez con DNI `30111222`
- **WHEN** un Coordinador da de alta a un alumno con una persona nueva con DNI `30.111.222`
- **THEN** la respuesta es 422 con un error en `personas.0.dni` cuyo `msg` es `Ya hay una persona con ese DNI. Buscala por DNI para reutilizarla.`
- **AND** no se crea nada

#### Scenario: Persona nueva con un DNI ya cargado escrito con guiones
- **GIVEN** María Pérez con DNI `30111222`
- **WHEN** un Coordinador da de alta a un alumno con una persona nueva con DNI `30-111-222`
- **THEN** la respuesta es 422 con un error en `personas.0.dni` cuyo `msg` es `Ya hay una persona con ese DNI. Buscala por DNI para reutilizarla.`

#### Scenario: Dos altas a la vez con el mismo DNI nuevo
- **GIVEN** que entre la comprobación del DNI y la escritura otra alta guardó una persona con DNI `40222333`
- **WHEN** termina un alta de un Coordinador con una persona nueva con DNI `40222333`
- **THEN** la respuesta es 422 con un error en `personas.0.dni` cuyo `msg` es `Ya hay una persona con ese DNI. Buscala por DNI para reutilizarla.`, no 500
- **AND** no se crea nada de esa alta

#### Scenario: La misma persona dos veces
- **WHEN** un Coordinador da de alta a un alumno con familia nueva y dos veces el mismo `persona_id`
- **THEN** la respuesta es 422 con un error en `personas.1.persona_id` cuyo `msg` es `Esa persona ya está en el alta.`

#### Scenario: Persona que no existe
- **WHEN** un Coordinador da de alta a un alumno con un `persona_id` que no existe
- **THEN** la respuesta es 422 con un error en `personas.0.persona_id` cuyo `msg` es `La persona no existe.`

#### Scenario: Persona nueva sin teléfono
- **WHEN** un Coordinador da de alta a un alumno con una persona nueva sin `telefono`
- **THEN** la respuesta es 422 con un error en `personas.0.telefono`

#### Scenario: DNI de 15 caracteres
- **WHEN** un Coordinador da de alta a un alumno con familia nueva y una tutora nueva con DNI `123456789012345`
- **THEN** la respuesta es 201

#### Scenario: DNI de 16 caracteres
- **WHEN** un Coordinador da de alta a un alumno con una persona nueva con DNI `1234567890123456`
- **THEN** la respuesta es 422 con un error en `personas.0.dni`

### Requirement: Datos del alumno en el alta
El alta SHALL exigir `nombre` y `apellido` de 1 a 80 caracteres, sin contar los espacios alrededor, y una `fecha_nacimiento` que no sea posterior al día de hoy. Si falta algún dato mínimo, responde 422 indicando cada campo que falta y no crea nada.

#### Scenario: Nombre de 80 caracteres
- **WHEN** un Coordinador da de alta a un alumno con un `nombre` de 80 caracteres
- **THEN** la respuesta es 201

#### Scenario: Nombre de 81 caracteres
- **WHEN** un Coordinador da de alta a un alumno con un `nombre` de 81 caracteres
- **THEN** la respuesta es 422 con un error en `nombre`

#### Scenario: Nacido hoy
- **WHEN** un Coordinador da de alta a un alumno con `fecha_nacimiento` igual a la fecha de hoy
- **THEN** la respuesta es 201

#### Scenario: Nacido mañana
- **WHEN** un Coordinador da de alta a un alumno con `fecha_nacimiento` igual a la fecha de mañana
- **THEN** la respuesta es 422 con un error en `fecha_nacimiento` cuyo `msg` es `La fecha de nacimiento no puede ser posterior a hoy.`

#### Scenario: Faltan varios datos mínimos
- **WHEN** un Coordinador llama a `POST /api/v1/alumnos` con solo `nombre` `Juan` y `apellido` `Pérez`
- **THEN** la respuesta es 422 con un error en `fecha_nacimiento` y otro en `grupo_id`, cada uno con `msg` `Este dato es obligatorio.`
- **AND** no se crea nada

### Requirement: El grupo del alta
El grupo del alta SHALL existir, estar activo y ser de la temporada vigente; la inscripción toma de él la temporada y el turno. El rango de nacimiento del grupo no restringe: se puede inscribir a un alumno fuera de él.

#### Scenario: Grupo fuera del rango de nacimiento
- **GIVEN** el grupo «Tiburones» mañana, para nacidos del 2017-01-01 al 2019-12-31
- **WHEN** un Coordinador da de alta a Lucía, nacida el 2020-02-02, en «Tiburones» mañana
- **THEN** la respuesta es 201 con la inscripción en «Tiburones»

#### Scenario: Grupo inactivo
- **GIVEN** un grupo inactivo de la temporada vigente
- **WHEN** un Coordinador da de alta a un alumno en ese grupo
- **THEN** la respuesta es 422 con un error en `grupo_id` cuyo `msg` es `El grupo no está activo.`

#### Scenario: Grupo de una temporada cerrada
- **GIVEN** un grupo activo de la temporada cerrada 2025-26
- **WHEN** un Coordinador da de alta a un alumno en ese grupo
- **THEN** la respuesta es 422 con un error en `grupo_id` cuyo `msg` es `El grupo no es de la temporada vigente.`

#### Scenario: Grupo que no existe
- **WHEN** un Coordinador da de alta a un alumno con un `grupo_id` que no existe
- **THEN** la respuesta es 422 con un error en `grupo_id` cuyo `msg` es `El grupo no existe.`

### Requirement: Quién puede dar de alta un alumno
`POST /api/v1/alumnos` SHALL estar disponible para Admin y Coordinador en cualquier grupo, y para el Profesor solo en los grupos que tiene asignados. Si el Profesor elige otro grupo, exista o no, esté activo o no y sea de la temporada que sea, responde 403 con `Solo podés inscribir alumnos en tus grupos.` y no crea nada: el Profesor no se entera de nada de un grupo ajeno.

#### Scenario: Profesor en su grupo
- **GIVEN** un Profesor asignado a «Delfines» mañana
- **WHEN** da de alta a Juan Pérez con familia nueva y su tutora en «Delfines» mañana
- **THEN** la respuesta es 201

#### Scenario: Profesor en un grupo ajeno
- **GIVEN** un Profesor asignado solo a «Delfines» mañana
- **WHEN** llama a `POST /api/v1/alumnos` con familia nueva, su tutora y el `grupo_id` de «Tiburones» mañana
- **THEN** la respuesta es 403 con `detail` `Solo podés inscribir alumnos en tus grupos.`
- **AND** no se crean ni la familia, ni el alumno, ni la persona, ni la inscripción

#### Scenario: Profesor con un grupo ajeno inactivo
- **GIVEN** un Profesor asignado solo a «Delfines» mañana, y un grupo inactivo «Pulpos» mañana de la temporada vigente
- **WHEN** da de alta a un alumno en «Pulpos» mañana
- **THEN** la respuesta es 403 con `detail` `Solo podés inscribir alumnos en tus grupos.`

#### Scenario: Profesor con un grupo que no existe
- **GIVEN** un Profesor asignado solo a «Delfines» mañana
- **WHEN** da de alta a un alumno con un `grupo_id` que no existe
- **THEN** la respuesta es 403 con `detail` `Solo podés inscribir alumnos en tus grupos.`

#### Scenario: Profesor en el mismo grupo del otro turno
- **GIVEN** un Profesor asignado solo a «Delfines» mañana
- **WHEN** da de alta a un alumno en «Delfines» tarde
- **THEN** la respuesta es 403

#### Scenario: Sin sesión
- **WHEN** se llama a `POST /api/v1/alumnos` sin token
- **THEN** la respuesta es 401 y no se crea nada

#### Scenario: Con el cambio de contraseña pendiente
- **GIVEN** un Coordinador con `debe_cambiar_password` en true
- **WHEN** llama a `POST /api/v1/alumnos` con un alta válida
- **THEN** la respuesta es 403 y no se crea nada

### Requirement: Pantalla «Registrar alumno»
La dirección `/alumnos/nuevo`, dentro de la zona protegida, SHALL mostrar un formulario con `Nombre`, `Apellido`, `Fecha de nacimiento`, `Grupo`, la elección de familia (`Familia nueva` o `Familia existente`), la sección `Personas autorizadas a retirar` y el botón `Registrar`.

#### Scenario: Formulario vacío
- **GIVEN** la sesión de un Coordinador
- **WHEN** se abre `/alumnos/nuevo`
- **THEN** se ven los campos `Nombre`, `Apellido`, `Fecha de nacimiento` y `Grupo`, las opciones `Familia nueva` y `Familia existente` con `Familia nueva` elegida, el campo `Categoría` y el botón `Registrar`

### Requirement: Grupos en la pantalla
El campo `Grupo` SHALL ofrecer los grupos que devuelve `GET /api/v1/grupos`, escritos como nombre y turno (`Delfines · Mañana`). Al cargar la fecha de nacimiento, los vuelve a pedir con esa fecha y marca cada sugerido con `(sugerido)`. Mientras el usuario no haya elegido el grupo a mano, la sugerencia manda: con exactamente un sugerido lo elige, y con dos o ninguno deja el grupo sin elegir. Una elección a mano no la pisa ninguna sugerencia.

#### Scenario: Profesor ve solo sus grupos
- **GIVEN** la sesión de un Profesor y `GET /api/v1/grupos` responde solo «Delfines» mañana
- **WHEN** se abre `/alumnos/nuevo` y se despliega `Grupo`
- **THEN** la única opción es `Delfines · Mañana`

#### Scenario: Sugerencia por fecha de nacimiento
- **GIVEN** `GET /api/v1/grupos?fecha_nacimiento=2020-03-10` marca «Delfines» mañana como sugerido
- **WHEN** se escribe `2020-03-10` en `Fecha de nacimiento` sin haber elegido grupo
- **THEN** `Grupo` queda en `Delfines · Mañana (sugerido)`

#### Scenario: Dos grupos sugeridos
- **GIVEN** `GET /api/v1/grupos?fecha_nacimiento=2020-03-10` marca como sugeridos «Delfines» mañana y «Delfines» tarde
- **WHEN** se escribe `2020-03-10` en `Fecha de nacimiento` sin haber elegido grupo
- **THEN** `Grupo` sigue sin elegir
- **AND** al desplegarlo se ven `Delfines · Mañana (sugerido)` y `Delfines · Tarde (sugerido)`

#### Scenario: Corregir la fecha cambia el grupo elegido por la sugerencia
- **GIVEN** se escribió `2020-03-10` en `Fecha de nacimiento` y `Grupo` quedó en `Delfines · Mañana (sugerido)` sin tocarlo a mano
- **AND** `GET /api/v1/grupos?fecha_nacimiento=2018-05-05` marca «Tiburones» mañana como único sugerido
- **WHEN** se corrige la fecha a `2018-05-05`
- **THEN** `Grupo` queda en `Tiburones · Mañana (sugerido)`

#### Scenario: La sugerencia no pisa una elección
- **GIVEN** se eligió `Tiburones · Mañana` en `Grupo`
- **WHEN** se escribe `2020-03-10` en `Fecha de nacimiento` y «Delfines» mañana viene sugerido
- **THEN** `Grupo` sigue en `Tiburones · Mañana`

### Requirement: Familia en la pantalla
Con `Familia nueva`, la pantalla SHALL pedir `Categoría` (`Socio`, `Empleado`, `No socio`). Con `Familia existente`, SHALL ofrecer un buscador por apellido que, desde 2 caracteres, consulta `GET /api/v1/familias` y lista cada familia como etiqueta y categoría; al elegir una muestra su categoría sin dejar cambiarla.

#### Scenario: Elegir una familia existente
- **GIVEN** `GET /api/v1/familias?apellido=Pé` responde la familia `Pérez – Juan`, categoría `empleado`
- **WHEN** se elige `Familia existente`, se escribe `Pé` en el buscador y se elige `Pérez – Juan`
- **THEN** se ve `Categoría: Empleado` como texto, sin campo para cambiarla

#### Scenario: Un carácter no busca
- **WHEN** se elige `Familia existente` y se escribe `P` en el buscador
- **THEN** no se llama a `GET /api/v1/familias`

### Requirement: Personas en la pantalla
La sección `Personas autorizadas a retirar` SHALL permitir agregar una persona nueva (`Nombre`, `Apellido`, `Teléfono`, `DNI` y la casilla `Tutor`) o reutilizar una por DNI: con `Buscar por DNI` consulta `GET /api/v1/personas` y, si la encuentra, la agrega con su nombre y apellido y la casilla `Tutor`. Cada persona agregada se puede quitar antes de registrar.

#### Scenario: Reutilizar una persona por DNI
- **GIVEN** `GET /api/v1/personas?dni=30111222` responde María Pérez
- **WHEN** se escribe `30111222` en el DNI a buscar y se pulsa `Buscar por DNI`
- **THEN** se ve `María Pérez` en la lista de personas con la casilla `Tutor`

#### Scenario: DNI que no está cargado
- **GIVEN** `GET /api/v1/personas?dni=30111222` responde 404 con `No hay ninguna persona con ese DNI.`
- **WHEN** se busca ese DNI
- **THEN** se ve `No hay ninguna persona con ese DNI.` y la lista de personas no cambia

### Requirement: Validación antes de enviar el alta
Al pulsar `Registrar`, la pantalla SHALL marcar en su campo cada dato mínimo vacío con `Este dato es obligatorio.` y, con familia nueva sin ninguna persona marcada como tutor, mostrar `La familia nueva necesita al menos un tutor.` En esos casos no llama a la API.

#### Scenario: Registrar con el formulario vacío
- **WHEN** se pulsa `Registrar` sin completar nada
- **THEN** `Nombre`, `Apellido`, `Fecha de nacimiento`, `Grupo` y `Categoría` muestran `Este dato es obligatorio.`
- **AND** no se llama a `POST /api/v1/alumnos`

#### Scenario: Familia nueva sin tutor
- **GIVEN** los datos del alumno, el grupo y la categoría completos, y una persona nueva sin la casilla `Tutor`
- **WHEN** se pulsa `Registrar`
- **THEN** se ve `La familia nueva necesita al menos un tutor.`
- **AND** no se llama a `POST /api/v1/alumnos`

#### Scenario: Familia existente sin personas
- **GIVEN** los datos del alumno y el grupo completos, y la familia existente `Pérez – Juan` elegida, sin personas agregadas
- **WHEN** se pulsa `Registrar`
- **THEN** se llama a `POST /api/v1/alumnos` con el `familia_id` de esa familia, sin `categoria` y con `personas` vacía

### Requirement: Envío del alta desde la pantalla
Al registrar, la pantalla SHALL mandar qué se registra (datos del alumno, `grupo_id`, `familia_id` o `categoria`, y las personas), con `Registrar` deshabilitado mientras espera. Con 201, muestra `<Nombre> <Apellido> quedó inscripto en <Grupo> (<Turno>). Familia: <etiqueta>.` y deja el formulario vacío. Con un error, conserva lo cargado: un error por campo va junto a su campo, y cualquier otro, en un aviso general.

#### Scenario: Alta correcta
- **GIVEN** el formulario completo para Juan Pérez en «Delfines» mañana, con familia nueva `Empleado` y María Pérez como tutora
- **AND** `POST /api/v1/alumnos` responde 201 con la familia `Pérez – Juan`
- **WHEN** se pulsa `Registrar`
- **THEN** se ve `Juan Pérez quedó inscripto en Delfines (Mañana). Familia: Pérez – Juan.`
- **AND** `Nombre` y `Apellido` quedan vacíos

#### Scenario: Esperando la respuesta
- **GIVEN** el formulario completo y `POST /api/v1/alumnos` todavía sin responder
- **WHEN** se pulsa `Registrar`
- **THEN** el botón `Registrar` está deshabilitado

#### Scenario: Error en el DNI de una persona
- **GIVEN** el formulario completo con una persona nueva con DNI `30111222`
- **AND** `POST /api/v1/alumnos` responde 422 con un error en `personas.0.dni` y `msg` `Ya hay una persona con ese DNI. Buscala por DNI para reutilizarla.`
- **WHEN** se pulsa `Registrar`
- **THEN** el mensaje se ve junto al `DNI` de esa persona y no en un aviso general
- **AND** `Nombre` conserva lo escrito

#### Scenario: Profesor rechazado por el grupo
- **GIVEN** `POST /api/v1/alumnos` responde 403 con `Solo podés inscribir alumnos en tus grupos.`
- **WHEN** se pulsa `Registrar` con el formulario completo
- **THEN** se ve ese mensaje en un aviso general y el formulario conserva lo cargado
