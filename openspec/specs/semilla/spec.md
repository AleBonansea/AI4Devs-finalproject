# semilla Specification

## Purpose

Deja una base de desarrollo o de demostración lista para usar con una sola orden, `python tasks.py seed`: una temporada completa con usuarios, grupos y tarifario inventados, mientras el ABM que los carga desde la aplicación no existe.

## Requirements

### Requirement: La semilla solo corre sobre una base vacía
La semilla SHALL cargar sus datos solo si la base no tiene ninguna temporada, ningún usuario, ninguna familia ni ninguna persona. Si tiene alguna, MUST terminar con error, con el mensaje `La base no está vacía: la semilla solo corre sobre una base vacía.`, sin escribir nada.

#### Scenario: Base vacía
- **GIVEN** una base migrada sin temporadas ni usuarios
- **WHEN** se corre la semilla
- **THEN** la semilla termina bien y la base tiene la temporada 2026-27

#### Scenario: Base con un usuario
- **GIVEN** una base migrada con un único usuario y ninguna temporada
- **WHEN** se corre la semilla
- **THEN** la semilla termina con error y el mensaje `La base no está vacía: la semilla solo corre sobre una base vacía.`
- **AND** la base sigue con ese único usuario, sin temporadas, grupos ni filas de tarifario

#### Scenario: Base con una temporada
- **GIVEN** una base migrada con una única temporada y ningún usuario
- **WHEN** se corre la semilla
- **THEN** la semilla termina con error y la base sigue con esa única temporada, sin usuarios, grupos ni filas de tarifario

#### Scenario: Base con una persona
- **GIVEN** una base migrada con una única persona, sin temporadas, usuarios ni familias
- **WHEN** se corre la semilla
- **THEN** la semilla termina con error y el mensaje `La base no está vacía: la semilla solo corre sobre una base vacía.`
- **AND** la base sigue con esa única persona y sin temporadas ni usuarios

#### Scenario: Correr la semilla dos veces
- **GIVEN** una base en la que ya se corrió la semilla
- **WHEN** se corre la semilla otra vez
- **THEN** la semilla termina con error y la base tiene una sola temporada y los mismos cuatro usuarios

### Requirement: La semilla solo corre contra una base local
La semilla SHALL negarse a correr si el host de la URL de la base no es `localhost`, `127.0.0.1`, `::1` o `db`, el servicio de `docker-compose.yml`, o si la query de la URL trae un `host` o un `hostaddr` que no sea uno de esos. Los hosts de la query se comparan sin su `:puerto`. Al negarse MUST terminar con error, con el mensaje `La semilla solo corre contra una base local.`, sin conectarse a la base. La excepción es el permiso de `SEMILLA_FUERA_DE_LOCAL`, en su propio requirement.

#### Scenario: Base del docker-compose
- **WHEN** se comprueba la URL `postgresql+psycopg://escuelita:escuelita@db:5432/escuelita`
- **THEN** la semilla puede correr

#### Scenario: Base en localhost
- **WHEN** se comprueba la URL `postgresql+psycopg://escuelita:escuelita@localhost:5432/escuelita`
- **THEN** la semilla puede correr

#### Scenario: Base remota
- **GIVEN** un entorno sin la variable `SEMILLA_FUERA_DE_LOCAL`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@dpg-abc123.oregon-postgres.render.com/escuelita`
- **THEN** la semilla se niega con el mensaje `La semilla solo corre contra una base local.`

#### Scenario: Un host que solo empieza como uno local
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@localhost.ejemplo.com/escuelita`
- **THEN** la semilla se niega con el mensaje `La semilla solo corre contra una base local.`

#### Scenario: Un host remoto escondido en la query
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@localhost/escuelita?host=dpg-abc123.oregon-postgres.render.com`
- **THEN** la semilla se niega con el mensaje `La semilla solo corre contra una base local.`

#### Scenario: Una dirección remota escondida en la query
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@localhost/escuelita?hostaddr=203.0.113.7`
- **THEN** la semilla se niega con el mensaje `La semilla solo corre contra una base local.`

#### Scenario: Un host local con puerto en la query
- **GIVEN** un entorno sin la variable `SEMILLA_FUERA_DE_LOCAL`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@localhost/escuelita?host=localhost:5432`
- **THEN** la semilla puede correr

### Requirement: Permiso explícito para sembrar una base remota
Si el entorno del proceso trae `SEMILLA_FUERA_DE_LOCAL` con el valor exacto `1`, la semilla SHALL aceptar una URL cuyo host no es local y, antes de conectarse, MUST escribir en pantalla `Atención: SEMILLA_FUERA_DE_LOCAL=1. La semilla va a escribir en una base remota: <hosts>.`, con los hosts no locales de la URL (el principal y los de `host` y `hostaddr` de la query) separados por `, `. Cualquier otro valor de la variable no da el permiso.

#### Scenario: Base remota con el permiso
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `1`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@dpg-abc123.oregon-postgres.render.com/escuelita`
- **THEN** la semilla puede correr
- **AND** el aviso es `Atención: SEMILLA_FUERA_DE_LOCAL=1. La semilla va a escribir en una base remota: dpg-abc123.oregon-postgres.render.com.`

#### Scenario: El aviso nombra el host escondido en la query
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `1`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@localhost/escuelita?host=dpg-abc123.oregon-postgres.render.com`
- **THEN** la semilla puede correr
- **AND** el aviso es `Atención: SEMILLA_FUERA_DE_LOCAL=1. La semilla va a escribir en una base remota: dpg-abc123.oregon-postgres.render.com.`

#### Scenario: El aviso nombra cada host remoto una sola vez
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `1`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@dpg-a.oregon-postgres.render.com/escuelita?host=dpg-b.oregon-postgres.render.com,dpg-a.oregon-postgres.render.com`
- **THEN** la semilla puede correr
- **AND** el aviso es `Atención: SEMILLA_FUERA_DE_LOCAL=1. La semilla va a escribir en una base remota: dpg-a.oregon-postgres.render.com, dpg-b.oregon-postgres.render.com.`

#### Scenario: El aviso nombra el host sin su puerto
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `1`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@localhost/escuelita?host=dpg-abc123.oregon-postgres.render.com:5432`
- **THEN** la semilla puede correr
- **AND** el aviso es `Atención: SEMILLA_FUERA_DE_LOCAL=1. La semilla va a escribir en una base remota: dpg-abc123.oregon-postgres.render.com.`

#### Scenario: Base local con el permiso no avisa
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `1`
- **WHEN** se comprueba la URL `postgresql+psycopg://escuelita:escuelita@localhost:5432/escuelita`
- **THEN** la semilla puede correr y no hay aviso

#### Scenario: La variable en cero no da el permiso
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `0`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@dpg-abc123.oregon-postgres.render.com/escuelita`
- **THEN** la semilla se niega con el mensaje `La semilla solo corre contra una base local.`

#### Scenario: La variable en true no da el permiso
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `true`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@dpg-abc123.oregon-postgres.render.com/escuelita`
- **THEN** la semilla se niega con el mensaje `La semilla solo corre contra una base local.`

#### Scenario: El aviso sale antes de conectarse
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `1` y `DATABASE_URL` apuntando a un host remoto que no responde
- **WHEN** se corre `python tasks.py seed`
- **THEN** el aviso con el nombre de ese host aparece en pantalla antes del error de conexión
- **AND** el comando termina con error

#### Scenario: El permiso no ablanda la negativa de base no vacía
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `1`
- **AND** una base migrada con un único usuario y ninguna temporada
- **WHEN** se corre la semilla
- **THEN** la semilla termina con error y el mensaje `La base no está vacía: la semilla solo corre sobre una base vacía.`
- **AND** la base sigue con ese único usuario, sin temporadas, grupos ni filas de tarifario

### Requirement: Con el permiso, un host vacío se rechaza
Con `SEMILLA_FUERA_DE_LOCAL` igual a `1`, si la URL no trae host o si `host` o `hostaddr` de la query tienen un elemento vacío, la semilla MUST negarse sin conectarse, con el mensaje `La semilla no siembra una base remota sin nombrar su host: la URL tiene un host vacío.` En ese caso libpq toma el host de otro lado (el entorno o un socket) y el aviso no podría nombrarlo.

#### Scenario: URL sin host con el permiso
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `1`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@/escuelita`
- **THEN** la semilla se niega con el mensaje `La semilla no siembra una base remota sin nombrar su host: la URL tiene un host vacío.`

#### Scenario: Un elemento vacío en la lista de hosts con el permiso
- **GIVEN** un entorno con `SEMILLA_FUERA_DE_LOCAL` igual a `1`
- **WHEN** se comprueba la URL `postgresql+psycopg://u:p@localhost/escuelita?host=localhost,`
- **THEN** la semilla se niega con el mensaje `La semilla no siembra una base remota sin nombrar su host: la URL tiene un host vacío.`

### Requirement: Temporada vigente 2026-27
La semilla SHALL crear una única temporada, `2026-27`, en estado `vigente`, del 2027-01-04 al 2027-02-26.

#### Scenario: La temporada de la semilla
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** hay exactamente una temporada, `2026-27`, `vigente`, con `fecha_inicio` 2027-01-04 y `fecha_cierre` 2027-02-26

### Requirement: Usuarios de los tres roles que pueden ingresar
La semilla SHALL crear cuatro usuarios activos, todos con la contraseña `Verano2026`, sin intentos fallidos y sin cambio de contraseña pendiente: `mgarcia` (admin), `lrodriguez` (coordinador), `jperez` y `cfernandez` (profesores).

#### Scenario: Cada usuario ingresa con su rol
- **GIVEN** una base en la que se corrió la semilla
- **WHEN** se llama a `POST /api/v1/auth/login` con cada uno de `mgarcia`, `lrodriguez`, `jperez` y `cfernandez`, con la contraseña `Verano2026`
- **THEN** las cuatro respuestas son 200, con `usuario.rol` igual a `admin`, `coordinador`, `profesor` y `profesor` respectivamente
- **AND** en las cuatro `usuario.debe_cambiar_password` es false

#### Scenario: Exactamente cuatro usuarios
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** la base tiene exactamente cuatro usuarios: uno admin, uno coordinador y dos profesores

### Requirement: Grupos con profesores asignados
La semilla SHALL crear cuatro grupos activos en 2026-27, «Delfines» y «Tiburones» en cada turno, y asignarles profesores de modo que todos tengan al menos uno.

#### Scenario: Los grupos de la semilla
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** la temporada 2026-27 tiene exactamente estos grupos, todos activos:
  - «Delfines», `manana`, nacidos del 2020-01-01 al 2021-12-31, con `jperez`
  - «Tiburones», `manana`, nacidos del 2017-01-01 al 2019-12-31, con `cfernandez`
  - «Delfines», `tarde`, nacidos del 2020-01-01 al 2021-12-31, con `jperez`
  - «Tiburones», `tarde`, nacidos del 2017-01-01 al 2019-12-31, con `cfernandez`
- **AND** no hay otras asignaciones de profesores

### Requirement: Tarifa base completa
La semilla SHALL cargar las 8 tarifas base de 2026-27, una por turno y modalidad, con los montos del contexto común de HU-CC-01.

#### Scenario: Las ocho tarifas
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** la temporada 2026-27 tiene exactamente 8 tarifas base:

  | Turno | Mes | Quincena | Semana | Día |
  |---|---|---|---|---|
  | `manana` | 100000.00 | 55000.00 | 30000.00 | 8000.00 |
  | `tarde` | 80000.00 | 45000.00 | 25000.00 | 7000.00 |

### Requirement: Tabla de descuentos con la política 2026-27
La semilla SHALL cargar la tabla de descuentos completa de 2026-27 con la política de Acl. 5: el socio paga la mitad y el empleado tres cuartos de lo que paga el no socio en la misma celda, cargado como porcentaje efectivo. Son 9 filas por modalidad y 12 por tramo de hijos.

#### Scenario: Descuentos de Día, Semana y Quincena
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** la temporada 2026-27 tiene exactamente 9 descuentos por modalidad: para `dia`, `semana` y `quincena`, `socio` 50.00, `empleado` 25.00 y `no_socio` 0.00

#### Scenario: Descuentos del Mes por tramo
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** la temporada 2026-27 tiene exactamente 12 descuentos del Mes:

  | Categoría | Tramo 1 | Tramo 2 | Tramo 3 | Tramo 4 |
  |---|---|---|---|---|
  | `no_socio` | 0.00 | 10.00 | 15.00 | 20.00 |
  | `socio` | 50.00 | 55.00 | 57.50 | 60.00 |
  | `empleado` | 25.00 | 32.50 | 36.25 | 40.00 |

### Requirement: Períodos de cobro de la temporada
La semilla SHALL cargar los períodos de cobro de 2026-27: 2 meses, 4 quincenas y 8 semanas, todos de lunes a viernes y dentro de la temporada.

#### Scenario: Los meses
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** la modalidad `mes` tiene exactamente «Mes 1», del 2027-01-04 al 2027-01-29, y «Mes 2», del 2027-02-01 al 2027-02-26

#### Scenario: Las quincenas
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** la modalidad `quincena` tiene exactamente «Quincena 1» (2027-01-04 al 2027-01-15), «Quincena 2» (2027-01-18 al 2027-01-29), «Quincena 3» (2027-02-01 al 2027-02-12) y «Quincena 4» (2027-02-15 al 2027-02-26)

#### Scenario: Las semanas
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** la modalidad `semana` tiene exactamente ocho períodos, «Semana 1» a «Semana 8», donde la «Semana N» va del lunes 2027-01-04 más 7×(N−1) días al viernes siguiente
- **AND** «Semana 1» va del 2027-01-04 al 2027-01-08 y «Semana 8» del 2027-02-22 al 2027-02-26

### Requirement: Tipos de cargo Preinscripción y Abono
La semilla SHALL cargar exactamente dos tipos de cargo en 2026-27: «Preinscripción», de monto fijo 20000.00, y «Abono», calculado con el tarifario.

#### Scenario: Los tipos de cargo
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** la temporada 2026-27 tiene exactamente dos tipos de cargo: «Preinscripción», cálculo `monto_fijo`, monto 20000.00, y «Abono», cálculo `tarifario`, sin monto

### Requirement: Familias y alumnos de ejemplo
La semilla SHALL crear tres familias con sus personas, sus alumnos y una inscripción por alumno en la temporada 2026-27, con datos inventados, de modo que cada grupo tenga al menos un alumno y una familia tenga dos hijos en el mismo turno.

#### Scenario: Las familias de la semilla
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** hay exactamente estas familias:
  - `Pérez – Ana`, `empleado`: Ana Pérez, nacida el 2018-07-05, en «Tiburones» mañana, y Juan Pérez, nacido el 2020-03-10, en «Delfines» mañana; tutora María Pérez (teléfono `3511234567`, DNI `30111222`) y autorizado a retirar Raúl Pérez (teléfono `3517654321`, sin DNI)
  - `Gómez – Lucía`, `socio`: Lucía Gómez, nacida el 2021-05-20, en «Delfines» tarde; tutor Pablo Gómez (teléfono `3519998877`, DNI `28999888`) y autorizada a retirar María Pérez
  - `Ruiz – Sofía`, `no_socio`: Sofía Ruiz, nacida el 2017-09-01, en «Tiburones» tarde; tutora Laura Ruiz (teléfono `3515556666`, sin DNI)
- **AND** hay exactamente cuatro personas, y María Pérez es una sola fila vinculada a dos familias
- **AND** hay exactamente cuatro inscripciones, todas de la temporada 2026-27
