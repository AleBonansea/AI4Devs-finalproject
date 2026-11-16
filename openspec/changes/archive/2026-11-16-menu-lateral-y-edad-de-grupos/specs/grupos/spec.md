# Spec Delta

## MODIFIED Requirements

### Requirement: Grupos donde se puede inscribir
`GET /api/v1/grupos` SHALL devolver los grupos activos de la temporada vigente, ordenados por turno (mañana primero) y por nombre, cada uno con `id`, `nombre`, `turno`, `nacimiento_desde`, `nacimiento_hasta`, `edad_desde`, `edad_hasta` y `sugerido`. Admin y Coordinador reciben todos; el Profesor recibe solo los que tiene asignados, filtrados en la consulta.

#### Scenario: Coordinador ve todos los grupos activos
- **GIVEN** en la temporada vigente los grupos activos «Delfines» y «Tiburones» de cada turno, y un grupo inactivo «Pulpos» mañana
- **WHEN** un Coordinador llama a `GET /api/v1/grupos`
- **THEN** la respuesta es 200 con «Delfines» mañana, «Tiburones» mañana, «Delfines» tarde y «Tiburones» tarde, en ese orden
- **AND** no incluye «Pulpos»

#### Scenario: Grupos de otra temporada
- **GIVEN** un grupo activo «Delfines» mañana en la temporada cerrada 2025-26
- **WHEN** un Admin llama a `GET /api/v1/grupos`
- **THEN** la respuesta no incluye ese grupo

#### Scenario: Profesor ve solo sus grupos
- **GIVEN** un Profesor asignado solo a «Delfines» mañana, y los grupos activos «Delfines» y «Tiburones» de cada turno en la temporada vigente
- **WHEN** el Profesor llama a `GET /api/v1/grupos`
- **THEN** la respuesta es 200 con un solo grupo: «Delfines» mañana

#### Scenario: Profesor sin grupos
- **GIVEN** un Profesor sin grupos asignados
- **WHEN** llama a `GET /api/v1/grupos`
- **THEN** la respuesta es 200 con una lista vacía

#### Scenario: Sin sesión
- **WHEN** se llama a `GET /api/v1/grupos` sin token
- **THEN** la respuesta es 401

## ADDED Requirements

### Requirement: Edad que cubre el grupo
Cada grupo de `GET /api/v1/grupos` SHALL traer `edad_desde` y `edad_hasta`, enteros, en años enteros contra el año de referencia: el primer año del nombre de la temporada vigente. `edad_desde` = año de referencia − año de `nacimiento_hasta`; `edad_hasta` = año de referencia − año de `nacimiento_desde`. No depende del día ni del mes de las fechas, ni de la fecha de hoy. La edad no se guarda.

#### Scenario: Grupos de la semilla
- **GIVEN** la temporada vigente «2026-27», con «Delfines» mañana para nacidos del 2020-01-01 al 2021-12-31 y «Tiburones» mañana para nacidos del 2017-01-01 al 2019-12-31
- **WHEN** un Coordinador llama a `GET /api/v1/grupos`
- **THEN** «Delfines» mañana trae `edad_desde` 5 y `edad_hasta` 6
- **AND** «Tiburones» mañana trae `edad_desde` 7 y `edad_hasta` 9

#### Scenario: Un día de más en el año siguiente suma una edad
- **GIVEN** la temporada vigente «2026-27» y un grupo «Pulpos» mañana para nacidos del 2020-01-01 al 2022-01-01
- **WHEN** un Coordinador llama a `GET /api/v1/grupos`
- **THEN** «Pulpos» mañana trae `edad_desde` 4 y `edad_hasta` 6

#### Scenario: Un día de menos en el año anterior suma una edad
- **GIVEN** la temporada vigente «2026-27» y un grupo «Pulpos» mañana para nacidos del 2019-12-31 al 2021-12-31
- **WHEN** un Coordinador llama a `GET /api/v1/grupos`
- **THEN** «Pulpos» mañana trae `edad_desde` 5 y `edad_hasta` 7

#### Scenario: Grupo de un solo año
- **GIVEN** la temporada vigente «2026-27» y un grupo «Pulpos» mañana para nacidos del 2019-01-01 al 2019-12-31
- **WHEN** un Coordinador llama a `GET /api/v1/grupos`
- **THEN** «Pulpos» mañana trae `edad_desde` 7 y `edad_hasta` 7

#### Scenario: La referencia es el nombre de la temporada, no su fecha de inicio
- **GIVEN** la temporada vigente «2027-28», que empieza el 2028-01-03, con «Delfines» mañana para nacidos del 2020-01-01 al 2021-12-31
- **WHEN** un Coordinador llama a `GET /api/v1/grupos`
- **THEN** «Delfines» mañana trae `edad_desde` 6 y `edad_hasta` 7

#### Scenario: El Profesor recibe la edad solo de sus grupos
- **GIVEN** la temporada vigente «2026-27» y un Profesor asignado solo a «Delfines» mañana, para nacidos del 2020-01-01 al 2021-12-31
- **WHEN** el Profesor llama a `GET /api/v1/grupos`
- **THEN** la respuesta es 200 con un solo grupo, «Delfines» mañana, con `edad_desde` 5 y `edad_hasta` 6
