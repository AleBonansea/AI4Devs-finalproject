# Spec Delta

## Purpose

Muestra en todo momento cuánto debe una familia en la temporada: sus cargos, lo pagado de cada uno y el saldo pendiente, calculados a partir de cargos y pagos y nunca guardados. Solo el Admin la ve.

## ADDED Requirements

### Requirement: El saldo de la familia es cargos menos pagos
El saldo pendiente de una familia en una temporada SHALL ser la suma de los totales de sus cargos de esa temporada menos la suma de los pagos no anulados de esos cargos. El saldo de un cargo es su total menos sus pagos no anulados. Ninguno de los dos se guarda: se calculan en cada respuesta.

#### Scenario: Dos cargos con pagos parciales
- **GIVEN** la familia «Pérez – Ana» con un «Abono» del Mes de Juan por 85000.00 con pagos de 30000.00 y 10000.00, y una «Preinscripción» de Ana por 20000.00 con un pago de 5000.00, en la temporada vigente
- **WHEN** un Admin pide su cuenta corriente
- **THEN** `total_cargos` es `"105000.00"`, `total_pagado` `"45000.00"` y `saldo_pendiente` `"60000.00"`
- **AND** el Abono tiene `pagado` `"40000.00"` y `saldo` `"45000.00"`, y la Preinscripción `pagado` `"5000.00"` y `saldo` `"15000.00"`

#### Scenario: Un pago anulado no cuenta
- **GIVEN** la familia «Pérez – Ana» con un cargo de 85000.00 con un pago de 30000.00 y otro de 20000.00 anulado (insertado con sus tres datos de anulación)
- **WHEN** un Admin pide su cuenta corriente
- **THEN** `total_pagado` es `"30000.00"` y `saldo_pendiente` `"55000.00"`
- **AND** el cargo lista un solo pago, el de 30000.00

#### Scenario: Cargo del cien por ciento
- **GIVEN** la familia «Pérez – Ana» con un único cargo, de `monto_total` 0.00
- **WHEN** un Admin pide su cuenta corriente
- **THEN** el cargo tiene `saldo` `"0.00"` y la familia `saldo_pendiente` `"0.00"`

### Requirement: Ver la cuenta corriente de una familia
`GET /api/v1/familias/{familia_id}/cuenta-corriente` SHALL responder 200 con `familia_id`, `etiqueta`, `categoria`, `total_cargos`, `total_pagado`, `saldo_pendiente` y `cargos`, todos de la temporada vigente, del más antiguo al más nuevo. Cada cargo trae exactamente `id`, `alumno_id`, `nombre`, `apellido`, `tipo_cargo`, `modalidad`, `turno`, `periodo`, `fecha_dia`, `monto_total`, `pagado`, `saldo`, `creado_en` y `pagos`.

#### Scenario: El detalle de cada cargo
- **GIVEN** la familia «Pérez – Ana», `empleado`, con, en este orden, una «Preinscripción» de Ana por 20000.00 sin pagos, un «Abono» del Mes de Juan, turno mañana, «Mes 1» (del 2027-01-04 al 2027-01-29), por 85000.00, con pagos de 10000.00 del 2026-11-05 y 30000.00 del 2026-11-02, y un «Abono» del Día de Juan, turno tarde, del 2027-01-08, por 9000.00
- **WHEN** un Admin llama a `GET /api/v1/familias/{id de Pérez – Ana}/cuenta-corriente`
- **THEN** la respuesta es 200 con `etiqueta` `Pérez – Ana`, `categoria` `empleado` y tres cargos en ese orden
- **AND** la Preinscripción tiene `tipo_cargo` `Preinscripción`, `nombre` `Ana`, y `modalidad`, `turno`, `periodo` y `fecha_dia` null
- **AND** el Abono del Mes tiene `modalidad` `mes`, `turno` `manana`, `periodo` con `nombre` `Mes 1`, `fecha_desde` 2027-01-04 y `fecha_hasta` 2027-01-29, `fecha_dia` null, y `pagos` con el de 30000.00 del 2026-11-02 primero y el de 10000.00 del 2026-11-05 después, cada uno con exactamente `id`, `monto` y `fecha_pago`
- **AND** el Abono del Día tiene `modalidad` `dia`, `turno` `tarde`, `periodo` null y `fecha_dia` 2027-01-08

#### Scenario: Solo la temporada vigente
- **GIVEN** la familia «Pérez – Ana» con un cargo de 30000.00 sin pagos en la temporada cerrada 2025-26 y un cargo de 85000.00 en la vigente
- **WHEN** un Admin pide su cuenta corriente
- **THEN** trae solo el cargo de 85000.00 y `saldo_pendiente` es `"85000.00"`

#### Scenario: Solo los cargos de esa familia
- **GIVEN** Juan Pérez y Lucía Gómez, de familias distintas, cada uno con un «Abono» del Mes en «Delfines» mañana
- **WHEN** un Admin pide la cuenta corriente de la familia de Juan
- **THEN** no trae el cargo de Lucía Gómez y el saldo no lo incluye

#### Scenario: Familia sin cargos en la temporada
- **GIVEN** una familia con un hijo inscripto y sin cargos en la temporada vigente
- **WHEN** un Admin pide su cuenta corriente
- **THEN** la respuesta es 200 con `cargos` vacío y `total_cargos`, `total_pagado` y `saldo_pendiente` en `"0.00"`

#### Scenario: Sin datos médicos ni de personas
- **GIVEN** la familia «Pérez – Ana» con un cargo de Juan
- **WHEN** un Admin pide su cuenta corriente
- **THEN** cada cargo tiene exactamente los catorce campos del requisito y ninguno más

#### Scenario: Familia que no existe
- **WHEN** un Admin pide la cuenta corriente de un `familia_id` que no existe
- **THEN** la respuesta es 404 con `detail` `La familia no existe.`

#### Scenario: Id de familia más grande que el máximo
- **WHEN** un Admin pide la cuenta corriente del `familia_id` 9223372036854775808
- **THEN** la respuesta es 404 con `detail` `La familia no existe.`

### Requirement: Solo el Admin ve la cuenta corriente
`GET /api/v1/familias/{familia_id}/cuenta-corriente` SHALL estar disponible solo para el Admin. Coordinador y Profesor reciben 403 con `No tenés permiso para esta operación.`, exista la familia o no y sean o no sus hijos de los grupos del Profesor, sin ningún monto en la respuesta; sin sesión, 401.

#### Scenario: Profesor de otro grupo
- **GIVEN** `cfernandez`, Profesora asignada solo a grupos donde no hay ningún hijo de la familia «Pérez – Ana», que tiene cargos
- **WHEN** `cfernandez` pide la cuenta corriente de «Pérez – Ana»
- **THEN** la respuesta es 403 con `detail` `No tenés permiso para esta operación.` y no trae ningún cargo ni monto

#### Scenario: Profesor del grupo de un hijo
- **GIVEN** `jperez`, Profesor asignado a «Delfines» mañana, donde está inscripto Juan Pérez
- **WHEN** `jperez` pide la cuenta corriente de «Pérez – Ana»
- **THEN** la respuesta es 403

#### Scenario: Profesor con una familia que no existe
- **WHEN** un Profesor pide la cuenta corriente de un `familia_id` que no existe
- **THEN** la respuesta es 403, no 404

#### Scenario: Coordinador
- **WHEN** un Coordinador pide la cuenta corriente de «Pérez – Ana»
- **THEN** la respuesta es 403

#### Scenario: Sin sesión
- **WHEN** se pide la cuenta corriente de una familia sin token
- **THEN** la respuesta es 401

### Requirement: Pantalla «Cuenta corriente»
La dirección `/cuenta-corriente`, dentro de la zona protegida y solo para el Admin, SHALL mostrar `Familia` (buscador por apellido) y, con una familia elegida, su categoría, `Saldo pendiente` y un renglón por cargo con su descripción, `Total`, `Pagado`, `Saldo` y sus pagos. Todos los montos son los que devolvió la API: la pantalla no suma ni resta. Coordinador y Profesor son llevados a `/`.

#### Scenario: Elegir la familia
- **GIVEN** la sesión de un Admin y la API responde la cuenta corriente de «Pérez – Ana», `empleado`, con `saldo_pendiente` `"60000.00"` y el «Abono» del Mes de Juan, turno mañana, «Mes 1», con `monto_total` `"85000.00"`, `pagado` `"40000.00"`, `saldo` `"45000.00"` y pagos de `"30000.00"` del 2026-11-02 y `"10000.00"` del 2026-11-05
- **WHEN** abre `/cuenta-corriente`, escribe `Pér` en `Familia` y elige `Pérez – Ana`
- **THEN** ve `Empleado` y `Saldo pendiente` con `$ 60.000`
- **AND** ve el renglón `Abono · Mes 1` con `Juan Pérez · Mañana`, `Total` `$ 85.000`, `Pagado` `$ 40.000` y `Saldo` `$ 45.000`
- **AND** ve los pagos `02/11/2026 · $ 30.000` y `05/11/2026 · $ 10.000`

#### Scenario: Descripción de cada tipo de cargo
- **GIVEN** la sesión de un Admin y la cuenta corriente con una «Preinscripción» de Ana y un «Abono» del Día de Juan, turno tarde, del 2027-01-08
- **WHEN** elige la familia
- **THEN** ve el renglón `Preinscripción` con `Ana Pérez` y el renglón `Abono · Día 08/01/2027` con `Juan Pérez · Tarde`

#### Scenario: Los montos son los de la API
- **GIVEN** la sesión de un Admin y una cuenta corriente con un solo cargo de `monto_total` `"85000.00"` y `pagado` `"30000.00"`, y `saldo` `"12345.67"` y `saldo_pendiente` `"99999.99"`
- **WHEN** elige la familia
- **THEN** ve `Saldo` `$ 12.345,67` y `Saldo pendiente` `$ 99.999,99`

#### Scenario: Cargo saldado
- **GIVEN** la sesión de un Admin y una cuenta corriente con un cargo de `saldo` `"0.00"`
- **WHEN** elige la familia
- **THEN** ese renglón dice `Saldado` y no ofrece `Registrar pago`

#### Scenario: Familia sin cargos
- **GIVEN** la sesión de un Admin y una cuenta corriente con `cargos` vacío y `saldo_pendiente` `"0.00"`
- **WHEN** elige la familia
- **THEN** ve `La familia no tiene cargos en la temporada.` y `Saldo pendiente` con `$ 0`

#### Scenario: Cambia de familia con la consulta en curso
- **GIVEN** la sesión de un Admin que eligió «Pérez – Ana» y su cuenta corriente todavía no respondió
- **WHEN** elige «Gómez – Lucía», y la respuesta de «Gómez – Lucía» llega antes que la de «Pérez – Ana»
- **THEN** la cuenta corriente que queda es la de «Gómez – Lucía»

#### Scenario: Coordinador abre la pantalla
- **GIVEN** la sesión de un Coordinador
- **WHEN** abre `/cuenta-corriente`
- **THEN** la dirección pasa a `/` y no se pide nada a `/api/v1/familias`
