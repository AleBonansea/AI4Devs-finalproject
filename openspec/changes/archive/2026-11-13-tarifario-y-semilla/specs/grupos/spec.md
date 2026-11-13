# Spec Delta

## Purpose

Organiza a los chicos de cada temporada en grupos por turno y rango de fechas de nacimiento, y registra qué profesores tiene cada grupo, que es la base del permiso por grupo del Profesor.

## ADDED Requirements

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
