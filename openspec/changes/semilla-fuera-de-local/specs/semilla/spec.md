# Spec Delta

## MODIFIED Requirements

### Requirement: La semilla solo corre contra una base local
La semilla SHALL negarse a correr si el host de la URL de la base no es `localhost`, `127.0.0.1`, `::1` o `db`, el servicio de `docker-compose.yml`, o si la query de la URL trae un `host` o un `hostaddr` que no sea uno de esos. Los hosts de la query se comparan sin su `:puerto`. Al negarse MUST terminar con error, con el mensaje `La semilla solo corre contra una base local.`, sin conectarse a la base. La única excepción es el permiso explícito de `SEMILLA_FUERA_DE_LOCAL`, en su propio requirement.

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

## ADDED Requirements

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
