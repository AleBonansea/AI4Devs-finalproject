# pagos Specification

## Purpose
Asienta cada cobro que recibe la familia sobre un cargo, en uno o varios pagos parciales hasta saldarlo, sin saldos a favor y con su ingreso en la tesorería. Solo el Admin registra pagos.

## Requirements

### Requirement: El pago guarda su monto, su fecha y su autor
Cada pago SHALL guardar el cargo, el monto (positivo, con dos decimales exactos), la fecha del pago, quién lo registró y cuándo. La base MUST rechazar un pago con monto cero o negativo, o sin cargo existente. Los datos de anulación (momento, autor y motivo) MUST estar los tres completos o los tres vacíos.

#### Scenario: Pago válido
- **WHEN** se inserta un pago de un cargo existente con `monto` 30000.00 y `fecha_pago` 2026-11-02, sin datos de anulación
- **THEN** la fila queda guardada

#### Scenario: Monto en cero
- **WHEN** se inserta un pago con `monto` 0.00
- **THEN** la base rechaza la fila

#### Scenario: Monto de un centavo
- **WHEN** se inserta un pago con `monto` 0.01
- **THEN** la fila queda guardada

#### Scenario: Cargo que no existe
- **WHEN** se inserta un pago con un `cargo_id` que no existe
- **THEN** la base rechaza la fila

#### Scenario: Anulación a medias
- **WHEN** se inserta un pago con `anulado_en` y `anulado_por` completos y sin `motivo_anulacion`
- **THEN** la base rechaza la fila

#### Scenario: Anulación completa
- **WHEN** se inserta un pago con `anulado_en`, `anulado_por` y `motivo_anulacion` completos
- **THEN** la fila queda guardada

### Requirement: Registrar un pago
`POST /api/v1/cargos/{cargo_id}/pagos` con `monto` y `fecha_pago` SHALL guardar el pago con quien llama como autor y responder 201 con `id`, `cargo_id`, `monto`, `fecha_pago`, `registrado_por`, `registrado_en`, `saldo_cargo` (lo que falta pagar del cargo) y `saldo_pendiente` (de la familia en la temporada del cargo). Montos como texto con dos decimales.

#### Scenario: Primer pago parcial
- **GIVEN** la familia «Pérez – Ana» con un «Abono» del Mes de Juan por 85000.00, sin pagos, y una «Preinscripción» de Ana por 20000.00 con un pago de 5000.00, todo en la temporada vigente
- **WHEN** un Admin llama a `POST /api/v1/cargos/{id del Abono}/pagos` con `monto` `"30000.00"` y `fecha_pago` `2026-11-02`
- **THEN** la respuesta es 201 con `cargo_id` el del Abono, `monto` `"30000.00"`, `fecha_pago` `2026-11-02`, `registrado_por` el id del Admin, `saldo_cargo` `"55000.00"` y `saldo_pendiente` `"70000.00"`
- **AND** el pago queda en la base con esos datos

#### Scenario: Pagos parciales hasta saldar
- **GIVEN** el «Abono» del Mes de Juan por 85000.00 con un pago de 30000.00
- **WHEN** un Admin registra sobre ese cargo un pago de `"55000.00"`
- **THEN** la respuesta es 201 con `saldo_cargo` `"0.00"`
- **AND** el cargo tiene dos pagos en la base, que suman 85000.00

#### Scenario: Pago con centavos
- **GIVEN** un cargo de 8925.00 sin pagos
- **WHEN** un Admin registra un pago de `"4462.50"`
- **THEN** la respuesta es 201 con `monto` `"4462.50"` y `saldo_cargo` `"4462.50"`

#### Scenario: Monto con un solo decimal
- **GIVEN** un cargo de 85000.00 sin pagos
- **WHEN** un Admin registra un pago de `"4462.5"`
- **THEN** la respuesta es 201 con `monto` `"4462.50"`

#### Scenario: Solo la familia y la temporada del cargo en el saldo
- **GIVEN** la familia «Pérez – Ana» con un cargo de 30000.00 sin pagos en la temporada cerrada 2025-26, y otra familia con un cargo de 50000.00 en la temporada vigente
- **WHEN** un Admin registra un pago de `"10000.00"` sobre un cargo de Juan Pérez de 85000.00 de la temporada vigente
- **THEN** `saldo_pendiente` es `"75000.00"`

#### Scenario: El saldo del cargo coincide con la cuenta corriente
- **GIVEN** la familia «Pérez – Ana» con un cargo de 85000.00 de la temporada vigente con dos pagos, de 30000.00 y de 12345.50
- **WHEN** un Admin registra sobre ese cargo un pago de `"10000.25"` y enseguida pide `GET /api/v1/familias/{id de Pérez – Ana}/cuenta-corriente`
- **THEN** la respuesta del pago trae `saldo_cargo` `"32654.25"`
- **AND** en la cuenta corriente ese mismo cargo tiene `saldo` `"32654.25"`, igual al `saldo_cargo` del pago

### Requirement: Un pago no supera el saldo del cargo
La suma de los pagos no anulados de un cargo MUST NOT superar su total: no hay saldos a favor. Un pago que lo superaría SHALL responder 422 en `monto` con `El monto supera el saldo del cargo.` Un cargo con saldo cero SHALL responder 409 con `El cargo ya está saldado.` En ningún caso se guarda nada.

#### Scenario: Pago exacto del saldo
- **GIVEN** un cargo de 85000.00 con un pago de 30000.00
- **WHEN** un Admin registra un pago de `"55000.00"`
- **THEN** la respuesta es 201

#### Scenario: Un centavo más que el saldo
- **GIVEN** un cargo de 85000.00 con un pago de 30000.00
- **WHEN** un Admin registra un pago de `"55000.01"`
- **THEN** la respuesta es 422 con un error con `loc` `["body", "monto"]`, `msg` `El monto supera el saldo del cargo.` y `type` `regla_de_negocio`
- **AND** el cargo sigue con un solo pago

#### Scenario: Cargo saldado
- **GIVEN** un cargo de 85000.00 con pagos que suman 85000.00
- **WHEN** un Admin registra un pago de `"0.01"`
- **THEN** la respuesta es 409 con `detail` `El cargo ya está saldado.`

#### Scenario: Cargo del cien por ciento
- **GIVEN** un cargo con `monto_total` 0.00
- **WHEN** un Admin registra un pago de `"100.00"`
- **THEN** la respuesta es 409 con `detail` `El cargo ya está saldado.`

#### Scenario: Un pago anulado no ocupa saldo
- **GIVEN** un cargo de 85000.00 con un pago de 30000.00 anulado (insertado con sus tres datos de anulación)
- **WHEN** un Admin registra un pago de `"85000.00"`
- **THEN** la respuesta es 201 con `saldo_cargo` `"0.00"`

#### Scenario: Dos pagos simultáneos del mismo cargo
- **GIVEN** una «Preinscripción» de 20000.00 sin pagos
- **WHEN** dos Admin registran a la vez sobre ese cargo un pago de `"20000.00"` cada uno
- **THEN** uno responde 201 y el otro 409 con `El cargo ya está saldado.`
- **AND** el cargo tiene un solo pago y la tesorería un solo ingreso

### Requirement: El monto y la fecha del pago
`monto` SHALL ser un texto con hasta diez cifras enteras y hasta dos decimales, mayor que cero; si no, 422 en `monto` con `Tiene que ser un monto con hasta dos decimales.` o `Tiene que ser mayor que cero.` `fecha_pago` es obligatoria y MUST NOT ser posterior a hoy: 422 con `La fecha del pago no puede ser posterior a hoy.` Fecha del pago escrita por el Admin: [SUPUESTO] (`aclaraciones-cliente.md`, «Fecha del pago»).

#### Scenario: Monto con tres decimales
- **WHEN** un Admin registra un pago con `monto` `"4462.505"`
- **THEN** la respuesta es 422 con `msg` `Tiene que ser un monto con hasta dos decimales.` en `monto` y no se guarda nada

#### Scenario: Monto como número
- **WHEN** un Admin registra un pago con `monto` 4462.50, como número JSON
- **THEN** la respuesta es 422 con `msg` `Tiene que ser un monto con hasta dos decimales.` en `monto`

#### Scenario: Monto escrito con coma
- **WHEN** un Admin registra un pago con `monto` `"4462,50"`
- **THEN** la respuesta es 422 con `msg` `Tiene que ser un monto con hasta dos decimales.` en `monto`

#### Scenario: Monto en cero
- **WHEN** un Admin registra un pago con `monto` `"0.00"`
- **THEN** la respuesta es 422 con `msg` `Tiene que ser mayor que cero.` en `monto` y no se guarda nada

#### Scenario: Monto con once cifras enteras
- **WHEN** un Admin registra un pago con `monto` `"12345678901.00"`
- **THEN** la respuesta es 422 con `msg` `Tiene que ser un monto con hasta dos decimales.` en `monto`

#### Scenario: Pago con fecha de hoy
- **GIVEN** un cargo de 85000.00 sin pagos
- **WHEN** un Admin registra un pago de `"10000.00"` con `fecha_pago` la fecha de hoy
- **THEN** la respuesta es 201

#### Scenario: Pago con fecha de mañana
- **WHEN** un Admin registra un pago con `fecha_pago` el día siguiente a hoy
- **THEN** la respuesta es 422 con `msg` `La fecha del pago no puede ser posterior a hoy.` en `fecha_pago` y no se guarda nada

#### Scenario: Pago anterior al inicio de la temporada
- **GIVEN** la temporada vigente, que empieza el 2027-01-04, y un cargo suyo de 85000.00 sin pagos
- **WHEN** un Admin registra un pago de `"20000.00"` con `fecha_pago` 2026-11-10
- **THEN** la respuesta es 201

#### Scenario: Sin fecha
- **WHEN** un Admin registra un pago con `monto` `"10000.00"` y sin `fecha_pago`
- **THEN** la respuesta es 422 con `msg` `Este dato es obligatorio.` en `fecha_pago`

#### Scenario: Campo desconocido en el cuerpo
- **WHEN** un Admin registra un pago con `monto`, `fecha_pago` y además `medio` `"efectivo"`
- **THEN** la respuesta es 422 y no se guarda nada

### Requirement: El cargo del pago existe y es de una temporada abierta
Un pago a un cargo que no existe SHALL responder 404 con `El cargo no existe.` Un pago a un cargo de una temporada cerrada SHALL responder 409 con `El cargo es de una temporada cerrada, que queda solo para consulta.` En ningún caso se guarda nada.

#### Scenario: Cargo que no existe
- **WHEN** un Admin registra un pago válido sobre un `cargo_id` que no existe
- **THEN** la respuesta es 404 con `detail` `El cargo no existe.`

#### Scenario: Id de cargo más grande que el máximo
- **WHEN** un Admin registra un pago válido sobre el `cargo_id` 9223372036854775808
- **THEN** la respuesta es 404 con `detail` `El cargo no existe.`

#### Scenario: Cargo de una temporada cerrada
- **GIVEN** un cargo de 30000.00 sin pagos de la temporada cerrada 2025-26
- **WHEN** un Admin registra un pago de `"10000.00"` sobre ese cargo
- **THEN** la respuesta es 409 con `detail` `El cargo es de una temporada cerrada, que queda solo para consulta.` y no se guarda ningún pago

### Requirement: Solo el Admin registra pagos
`POST /api/v1/cargos/{cargo_id}/pagos` SHALL estar disponible solo para el Admin. Coordinador y Profesor reciben 403 con `No tenés permiso para esta operación.`, exista el cargo o no, y no se guarda nada; sin sesión, 401.

#### Scenario: Coordinador registra un pago
- **WHEN** un Coordinador registra un pago válido sobre un cargo existente
- **THEN** la respuesta es 403 con `detail` `No tenés permiso para esta operación.`
- **AND** no se guarda ningún pago ni ningún movimiento de tesorería

#### Scenario: Profesor del grupo del alumno
- **GIVEN** `jperez`, Profesor asignado a «Delfines» mañana, donde está inscripto Juan, y un cargo de Juan
- **WHEN** `jperez` registra un pago válido sobre ese cargo
- **THEN** la respuesta es 403 y no se guarda ningún pago

#### Scenario: Profesor con un cargo que no existe
- **WHEN** un Profesor registra un pago sobre un `cargo_id` que no existe
- **THEN** la respuesta es 403, no 404

#### Scenario: Sin sesión
- **WHEN** se registra un pago sin token
- **THEN** la respuesta es 401 y no se guarda ningún pago

#### Scenario: Admin con el cambio de contraseña pendiente
- **GIVEN** un Admin con `debe_cambiar_password` en true
- **WHEN** registra un pago válido
- **THEN** la respuesta es 403 y no se guarda ningún pago

### Requirement: Registrar un pago desde la pantalla
En la pantalla «Cuenta corriente», cada cargo con saldo SHALL ofrecer `Registrar pago`, que abre un formulario con el cargo, `Saldo del cargo`, `Monto` (propuesto con el saldo del cargo, escrito como `55.000` o `4.462,50`) y `Fecha del pago` (propuesta con la fecha de hoy), y los botones `Registrar pago` y `Cancelar`. Un cargo saldado no lo ofrece.

#### Scenario: Abrir el formulario
- **GIVEN** la sesión de un Admin con la cuenta corriente de «Pérez – Ana» a la vista, con el «Abono · Mes 1» de Juan con saldo `"55000.00"`
- **WHEN** pulsa `Registrar pago` en ese cargo
- **THEN** ve `Abono · Mes 1`, `Saldo del cargo` con `$ 55.000`, `Monto` con `55.000` y `Fecha del pago` con la fecha de hoy

#### Scenario: Saldo con centavos
- **GIVEN** un cargo con saldo `"4462.50"`
- **WHEN** el Admin abre su formulario de pago
- **THEN** `Monto` tiene `4.462,50`

#### Scenario: Fecha propuesta a la noche
- **GIVEN** el reloj del navegador en el 2027-01-05 a las 21:30, hora de Argentina (las 00:30 del 2027-01-06 en UTC)
- **WHEN** el Admin abre el formulario de pago de un cargo con saldo
- **THEN** `Fecha del pago` propone el 05/01/2027, es decir, el campo tiene el valor `2027-01-05`

#### Scenario: Cancelar
- **GIVEN** el formulario de pago abierto
- **WHEN** el Admin pulsa `Cancelar`
- **THEN** el formulario se cierra y no se envía ningún pedido a `/api/v1/cargos`

### Requirement: Enviar el pago desde la pantalla
`Registrar pago` SHALL enviar a `POST /api/v1/cargos/{cargo_id}/pagos` solo `monto` (como `"4462.50"`) y `fecha_pago`, y estar deshabilitado mientras se registra. Un monto vacío o mal escrito se marca junto a `Monto` sin enviar nada. Al 201 cierra el formulario, muestra `Pago registrado por $ M. Saldo pendiente de la familia: $ S.` con lo que devolvió la API, y vuelve a pedir la cuenta corriente.

#### Scenario: Registrar un pago parcial
- **GIVEN** el formulario de pago del «Abono · Mes 1» de Juan abierto, con saldo `"55000.00"`
- **WHEN** el Admin escribe `30.000` en `Monto`, pone `2026-11-02` en `Fecha del pago`, pulsa `Registrar pago` y la API responde 201 con `monto` `"30000.00"` y `saldo_pendiente` `"40000.00"`
- **THEN** el cuerpo enviado tiene exactamente las claves `monto` `"30000.00"` y `fecha_pago` `2026-11-02`
- **AND** ve `Pago registrado por $ 30.000. Saldo pendiente de la familia: $ 40.000.`
- **AND** el formulario se cerró y se volvió a pedir la cuenta corriente de la familia

#### Scenario: Monto con miles y centavos
- **GIVEN** el formulario de pago abierto
- **WHEN** el Admin escribe `4.462,50` en `Monto` y pulsa `Registrar pago`
- **THEN** el cuerpo enviado tiene `monto` `"4462.50"`

#### Scenario: Monto mal escrito
- **GIVEN** el formulario de pago abierto
- **WHEN** el Admin escribe `4,462.50` en `Monto` y pulsa `Registrar pago`
- **THEN** ve `Escribí el monto como 4.462,50.` junto a `Monto` y no se envía ningún pedido

#### Scenario: Monto vacío
- **GIVEN** el formulario de pago abierto
- **WHEN** el Admin borra `Monto` y pulsa `Registrar pago`
- **THEN** ve `Este dato es obligatorio.` junto a `Monto` y no se envía ningún pedido

#### Scenario: La API rechaza el monto
- **GIVEN** el formulario de pago abierto
- **WHEN** el Admin pulsa `Registrar pago` y la API responde 422 con `El monto supera el saldo del cargo.` en `monto`
- **THEN** ve ese mensaje junto a `Monto` y el formulario sigue abierto con lo escrito

#### Scenario: Mientras se registra
- **GIVEN** el Admin pulsó `Registrar pago` y el pedido no respondió
- **WHEN** mira el formulario
- **THEN** `Registrar pago` está deshabilitado y un segundo clic no envía otro pedido
