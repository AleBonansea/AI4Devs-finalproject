# grupos Specification

## Purpose

Organiza a los chicos de cada temporada en grupos por turno y rango de fechas de nacimiento, y registra qué profesores tiene cada grupo, que es la base del permiso por grupo del Profesor.

## Requirements

### Requirement: Un grupo pertenece a una temporada y a un turno
Cada grupo SHALL pertenecer a una temporada y tener un único turno, `manana` o `tarde`. La base MUST rechazar dos grupos con el mismo nombre y el mismo turno en la misma temporada, y MUST aceptar el mismo nombre en otro turno o en otra temporada.

#### Scenario: Mismo nombre y turno en la misma temporada
- **GIVEN** un grupo «Delfines», turno `manana`, en la temporada 2026-27
- **WHEN** se inserta otro grupo «Delfines», turno `manana`, en la temporada 2026-27
- **THEN** la base rechaza la fila

#### Scenario: Mismo nombre en el otro turno
- **GIVEN** un grupo «Delfines», turno `manana`, en la temporada 2026-27
- **WHEN** se inserta un grupo «Delfines», turno `tarde`, en la temporada 2026-27
- **THEN** la fila queda guardada

#### Scenario: Mismo nombre y turno en otra temporada
- **GIVEN** un grupo «Delfines», turno `manana`, en la temporada 2025-26
- **WHEN** se inserta un grupo «Delfines», turno `manana`, en la temporada 2026-27
- **THEN** la fila queda guardada

#### Scenario: Un turno que no existe
- **WHEN** se inserta un grupo con turno `noche`
- **THEN** la base rechaza la fila

### Requirement: Rango de fechas de nacimiento del grupo
Cada grupo SHALL tener `nacimiento_desde` y `nacimiento_hasta`, obligatorios, con `nacimiento_desde` menor o igual que `nacimiento_hasta`.

#### Scenario: Rango de un solo día
- **WHEN** se inserta un grupo con `nacimiento_desde` y `nacimiento_hasta` iguales a 2019-01-01
- **THEN** la fila queda guardada

#### Scenario: Rango invertido por un día
- **WHEN** se inserta un grupo con `nacimiento_desde` 2019-01-02 y `nacimiento_hasta` 2019-01-01
- **THEN** la base rechaza la fila

### Requirement: Un grupo nuevo está activo
Un grupo SHALL quedar activo si al crearlo no se indica lo contrario. Un grupo inactivo se conserva: la baja es desactivar, nunca borrar.

#### Scenario: Grupo creado sin indicar si está activo
- **WHEN** se inserta un grupo sin valor para `activo`
- **THEN** el grupo queda guardado con `activo` en true

### Requirement: Profesores asignados a un grupo
La asignación de profesores a grupos SHALL ser de muchos a muchos: un grupo puede tener varios profesores y un profesor varios grupos, incluso de turnos distintos. La base MUST rechazar la misma asignación dos veces.

#### Scenario: Un profesor en dos grupos de distinto turno
- **GIVEN** un profesor `jperez` y los grupos «Delfines» mañana y «Delfines» tarde
- **WHEN** se asigna `jperez` a los dos grupos
- **THEN** las dos asignaciones quedan guardadas

#### Scenario: Dos profesores en el mismo grupo
- **GIVEN** los profesores `jperez` y `cfernandez` y el grupo «Delfines» mañana
- **WHEN** se asignan los dos al grupo
- **THEN** las dos asignaciones quedan guardadas

#### Scenario: La misma asignación dos veces
- **GIVEN** `jperez` asignado al grupo «Delfines» mañana
- **WHEN** se lo asigna otra vez al mismo grupo
- **THEN** la base rechaza la fila

### Requirement: Un grupo con profesores no se borra en cascada
Borrar físicamente un grupo que tiene profesores asignados MUST fallar: la base no borra en cascada las asignaciones.

#### Scenario: Borrar un grupo con un profesor asignado
- **GIVEN** el grupo «Delfines» mañana con `jperez` asignado
- **WHEN** se ejecuta un `DELETE` sobre ese grupo
- **THEN** la base rechaza el borrado
- **AND** el grupo y la asignación siguen en la base

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
