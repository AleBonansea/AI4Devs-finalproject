# Spec Delta

## ADDED Requirements

### Requirement: Grupos donde se puede inscribir
`GET /api/v1/grupos` SHALL devolver los grupos activos de la temporada vigente, ordenados por turno (mañana primero) y por nombre, cada uno con `id`, `nombre`, `turno`, `nacimiento_desde`, `nacimiento_hasta` y `sugerido`. Admin y Coordinador reciben todos; el Profesor recibe solo los que tiene asignados, filtrados en la consulta.

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

### Requirement: Grupo sugerido por fecha de nacimiento
Con `?fecha_nacimiento=`, cada grupo SHALL traer `sugerido` en true si esa fecha está dentro de su rango, con los dos extremos incluidos, y en false si no. Sin el parámetro, todos traen `sugerido` en false. La sugerencia no filtra: la respuesta trae los mismos grupos con o sin fecha.

#### Scenario: Primer día del rango
- **GIVEN** el grupo «Delfines» mañana, para nacidos del 2020-01-01 al 2021-12-31
- **WHEN** un Coordinador llama a `GET /api/v1/grupos?fecha_nacimiento=2020-01-01`
- **THEN** «Delfines» mañana trae `sugerido` en true

#### Scenario: Día anterior al rango
- **GIVEN** el grupo «Delfines» mañana, para nacidos del 2020-01-01 al 2021-12-31
- **WHEN** un Coordinador llama a `GET /api/v1/grupos?fecha_nacimiento=2019-12-31`
- **THEN** «Delfines» mañana trae `sugerido` en false
- **AND** la respuesta sigue incluyendo a «Delfines» mañana

#### Scenario: Último día del rango
- **GIVEN** el grupo «Delfines» mañana, para nacidos del 2020-01-01 al 2021-12-31
- **WHEN** un Coordinador llama a `GET /api/v1/grupos?fecha_nacimiento=2021-12-31`
- **THEN** «Delfines» mañana trae `sugerido` en true

#### Scenario: Día posterior al rango
- **GIVEN** el grupo «Delfines» mañana, para nacidos del 2020-01-01 al 2021-12-31
- **WHEN** un Coordinador llama a `GET /api/v1/grupos?fecha_nacimiento=2022-01-01`
- **THEN** «Delfines» mañana trae `sugerido` en false

#### Scenario: Sugerido en los dos turnos
- **GIVEN** «Delfines» mañana y «Delfines» tarde, los dos para nacidos del 2020-01-01 al 2021-12-31
- **WHEN** un Coordinador llama a `GET /api/v1/grupos?fecha_nacimiento=2020-03-10`
- **THEN** los dos traen `sugerido` en true

#### Scenario: Sin fecha
- **WHEN** un Coordinador llama a `GET /api/v1/grupos`
- **THEN** todos los grupos traen `sugerido` en false
