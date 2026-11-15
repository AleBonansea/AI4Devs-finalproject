# Spec Delta

## Purpose

Lleva la tesorería general de cada temporada como una lista de movimientos que no se modifican ni se borran: ingresos (cada cobro) y egresos. Por ahora la escribe solo el registro de pagos; las pantallas, los egresos manuales, la anulación y el canon llegan después.

## ADDED Requirements

### Requirement: La forma de un movimiento de tesorería
Cada movimiento SHALL guardar temporada, tipo (`ingreso` o `egreso`), origen, monto positivo, fecha y autor. La base MUST exigir según el origen: `pago` es un ingreso con pago; `anulacion_pago` es un egreso con pago; `manual` es un egreso con descripción. Un movimiento de origen `canon` MUST rechazarse mientras no exista el cierre de canon al que referenciar.

#### Scenario: Ingreso por un pago
- **WHEN** se inserta un movimiento `ingreso`, origen `pago`, con un `pago_id` existente y `monto` 30000.00
- **THEN** la fila queda guardada

#### Scenario: Pago registrado como egreso
- **WHEN** se inserta un movimiento `egreso`, origen `pago`, con un `pago_id` existente
- **THEN** la base rechaza la fila

#### Scenario: Origen pago sin pago
- **WHEN** se inserta un movimiento `ingreso`, origen `pago`, sin `pago_id`
- **THEN** la base rechaza la fila

#### Scenario: Egreso manual con descripción
- **WHEN** se inserta un movimiento `egreso`, origen `manual`, con `descripcion` `Insumos de librería` y sin `pago_id`
- **THEN** la fila queda guardada

#### Scenario: Egreso manual sin descripción
- **WHEN** se inserta un movimiento `egreso`, origen `manual`, sin `descripcion`
- **THEN** la base rechaza la fila

#### Scenario: Movimiento del canon
- **WHEN** se inserta un movimiento `egreso`, origen `canon`, con `descripcion`
- **THEN** la base rechaza la fila

#### Scenario: Monto en cero
- **WHEN** se inserta un movimiento `ingreso`, origen `pago`, con `monto` 0.00
- **THEN** la base rechaza la fila

### Requirement: Un pago tiene un solo movimiento de cada origen
La base MUST rechazar un segundo movimiento con el mismo pago y el mismo origen: un pago genera un solo ingreso y, cuando se anule, un solo egreso de anulación.

#### Scenario: Segundo ingreso del mismo pago
- **GIVEN** un pago con su movimiento `ingreso`, origen `pago`
- **WHEN** se inserta otro movimiento `ingreso`, origen `pago`, con el mismo `pago_id`
- **THEN** la base rechaza la fila

#### Scenario: Egreso de anulación del mismo pago
- **GIVEN** un pago con su movimiento `ingreso`, origen `pago`
- **WHEN** se inserta un movimiento `egreso`, origen `anulacion_pago`, con el mismo `pago_id`
- **THEN** la fila queda guardada

### Requirement: Cada pago escribe su ingreso
Registrar un pago SHALL guardar, en la misma operación, un movimiento `ingreso` de origen `pago` que referencia a ese pago, con el mismo monto, la fecha del pago, la temporada del cargo y el mismo autor, sin descripción. Si el pago no se guarda, el movimiento tampoco.

#### Scenario: El ingreso del pago
- **GIVEN** un «Abono» del Mes de Juan por 85000.00 de la temporada vigente, sin pagos
- **WHEN** el Admin `mgarcia` registra un pago de `"30000.00"` con `fecha_pago` 2026-11-02
- **THEN** la tesorería tiene un solo movimiento nuevo: `ingreso`, origen `pago`, `pago_id` el del pago registrado, `monto` 30000.00, `fecha` 2026-11-02, `temporada_id` la vigente, `registrado_por` `mgarcia` y `descripcion` vacía

#### Scenario: Un ingreso por cada pago parcial
- **GIVEN** un cargo de 85000.00 sin pagos
- **WHEN** el Admin registra un pago de `"30000.00"` y después otro de `"55000.00"`
- **THEN** la tesorería tiene dos ingresos de origen `pago`, uno de 30000.00 y otro de 55000.00, cada uno con su `pago_id`

#### Scenario: Pago rechazado, sin ingreso
- **GIVEN** un cargo de 85000.00 con un pago de 30000.00
- **WHEN** el Admin registra un pago de `"55000.01"` y la respuesta es 422
- **THEN** la tesorería tiene la misma cantidad de movimientos que antes

#### Scenario: Pago sin permiso, sin ingreso
- **WHEN** un Coordinador registra un pago y la respuesta es 403
- **THEN** la tesorería tiene la misma cantidad de movimientos que antes
