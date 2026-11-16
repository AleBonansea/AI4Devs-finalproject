# Spec Delta

## MODIFIED Requirements

### Requirement: Grupos en la pantalla
El campo `Grupo` SHALL ofrecer los grupos de `GET /api/v1/grupos`, escritos como nombre, turno y edad (`Delfines · Mañana · 5 a 6 años`; `7 años` si `edad_desde` y `edad_hasta` coinciden). Con la fecha de nacimiento los vuelve a pedir y marca los sugeridos con `(sugerido)` al final. Mientras el usuario no haya elegido el grupo a mano, la sugerencia manda: con exactamente un sugerido lo elige, y con dos o ninguno deja el grupo sin elegir. Una elección a mano no la pisa ninguna sugerencia.

#### Scenario: Profesor ve solo sus grupos
- **GIVEN** la sesión de un Profesor y `GET /api/v1/grupos` responde solo «Delfines» mañana, con `edad_desde` 5 y `edad_hasta` 6
- **WHEN** se abre `/alumnos/nuevo` y se despliega `Grupo`
- **THEN** la única opción es `Delfines · Mañana · 5 a 6 años`

#### Scenario: Grupos de la semilla con su edad
- **GIVEN** la sesión de un Coordinador y `GET /api/v1/grupos` responde «Delfines» mañana (`edad_desde` 5, `edad_hasta` 6), «Tiburones» mañana (7 y 9), «Delfines» tarde (5 y 6) y «Tiburones» tarde (7 y 9)
- **WHEN** se abre `/alumnos/nuevo` y se despliega `Grupo`
- **THEN** las opciones son, en este orden, `Delfines · Mañana · 5 a 6 años`, `Tiburones · Mañana · 7 a 9 años`, `Delfines · Tarde · 5 a 6 años` y `Tiburones · Tarde · 7 a 9 años`

#### Scenario: Grupo de una sola edad
- **GIVEN** `GET /api/v1/grupos` responde «Pulpos» mañana con `edad_desde` 7 y `edad_hasta` 7
- **WHEN** se abre `/alumnos/nuevo` y se despliega `Grupo`
- **THEN** la opción es `Pulpos · Mañana · 7 años`

#### Scenario: Sugerencia por fecha de nacimiento
- **GIVEN** `GET /api/v1/grupos?fecha_nacimiento=2020-03-10` marca «Delfines» mañana (`edad_desde` 5, `edad_hasta` 6) como sugerido
- **WHEN** se escribe `2020-03-10` en `Fecha de nacimiento` sin haber elegido grupo
- **THEN** `Grupo` queda en `Delfines · Mañana · 5 a 6 años (sugerido)`

#### Scenario: Dos grupos sugeridos
- **GIVEN** `GET /api/v1/grupos?fecha_nacimiento=2020-03-10` marca como sugeridos «Delfines» mañana y «Delfines» tarde, los dos con `edad_desde` 5 y `edad_hasta` 6
- **WHEN** se escribe `2020-03-10` en `Fecha de nacimiento` sin haber elegido grupo
- **THEN** `Grupo` sigue sin elegir
- **AND** al desplegarlo se ven `Delfines · Mañana · 5 a 6 años (sugerido)` y `Delfines · Tarde · 5 a 6 años (sugerido)`

#### Scenario: Corregir la fecha cambia el grupo elegido por la sugerencia
- **GIVEN** se escribió `2020-03-10` en `Fecha de nacimiento` y `Grupo` quedó en `Delfines · Mañana · 5 a 6 años (sugerido)` sin tocarlo a mano
- **AND** `GET /api/v1/grupos?fecha_nacimiento=2018-05-05` marca «Tiburones» mañana (`edad_desde` 7, `edad_hasta` 9) como único sugerido
- **WHEN** se corrige la fecha a `2018-05-05`
- **THEN** `Grupo` queda en `Tiburones · Mañana · 7 a 9 años (sugerido)`

#### Scenario: La sugerencia no pisa una elección
- **GIVEN** se eligió `Tiburones · Mañana · 7 a 9 años` en `Grupo`
- **WHEN** se escribe `2020-03-10` en `Fecha de nacimiento` y «Delfines» mañana viene sugerido
- **THEN** `Grupo` sigue en `Tiburones · Mañana · 7 a 9 años`
