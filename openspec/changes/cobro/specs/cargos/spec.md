# Spec Delta

## Purpose

Asienta lo que una familia tiene que pagar por cada alumno: calcula el monto con la tarifa base y un único porcentaje de descuento, lo guarda congelado en el cargo y no lo recalcula nunca. Solo el Admin registra cargos.

## ADDED Requirements

### Requirement: El cargo guarda su cálculo
Cada cargo SHALL guardar temporada, familia, alumno, tipo de cargo, categoría aplicada, tarifa base (`monto_base`), porcentaje aplicado y total, con dos decimales exactos. La base MUST rechazar un cargo cuyo total no sea `monto_base × (1 − porcentaje / 100)` redondeado a centavos, o cuyo porcentaje esté fuera de 0 a 100.

#### Scenario: Total coherente con la base y el porcentaje
- **WHEN** se inserta un cargo con `monto_base` 100000.00, `porcentaje_aplicado` 15.00 y `monto_total` 85000.00
- **THEN** la fila queda guardada

#### Scenario: Total que no corresponde
- **WHEN** se inserta un cargo con `monto_base` 100000.00, `porcentaje_aplicado` 15.00 y `monto_total` 85000.01
- **THEN** la base rechaza la fila

#### Scenario: Porcentaje fuera de rango
- **WHEN** se inserta un cargo con `porcentaje_aplicado` 100.01, y aparte otro con -0.01
- **THEN** la base rechaza las dos filas

### Requirement: La forma del cargo según el tipo y la modalidad
Un cargo sin modalidad (monto fijo) MUST NOT tener inscripción, período, fecha ni cantidad de hijos. Un cargo con modalidad SHALL tener inscripción; período si es Mes, Quincena o Semana, y del mismo modo que el cargo; fecha si es Día; y cantidad de hijos (1 o más) si y solo si es Mes. La base MUST rechazar cualquier otra combinación.

#### Scenario: Cargo de monto fijo
- **WHEN** se inserta un cargo sin inscripción, modalidad, período, fecha ni cantidad de hijos, con `monto_base` 20000.00 y `porcentaje_aplicado` 0.00
- **THEN** la fila queda guardada

#### Scenario: Cargo de monto fijo con período
- **WHEN** se inserta un cargo sin modalidad pero con el período «Mes 1»
- **THEN** la base rechaza la fila

#### Scenario: Mes sin cantidad de hijos
- **WHEN** se inserta un cargo con inscripción, modalidad `mes`, el período «Mes 1» y sin cantidad de hijos
- **THEN** la base rechaza la fila

#### Scenario: Semana con cantidad de hijos
- **WHEN** se inserta un cargo con inscripción, modalidad `semana`, el período «Semana 1» y cantidad de hijos 2
- **THEN** la base rechaza la fila

#### Scenario: Cantidad de hijos cero
- **WHEN** se inserta un cargo con inscripción, modalidad `mes`, el período «Mes 1» y cantidad de hijos 0
- **THEN** la base rechaza la fila

#### Scenario: Período de otra modalidad
- **WHEN** se inserta un cargo con modalidad `mes` y el período «Semana 1», que es de modalidad `semana`
- **THEN** la base rechaza la fila

#### Scenario: Día con fecha
- **WHEN** se inserta un cargo con inscripción, modalidad `dia`, fecha 2027-01-05 y sin período
- **THEN** la fila queda guardada

#### Scenario: Día con período
- **WHEN** se inserta un cargo con inscripción, modalidad `dia`, fecha 2027-01-05 y el período «Semana 1»
- **THEN** la base rechaza la fila

### Requirement: Un cargo no se repite
La base MUST rechazar un segundo cargo de la misma inscripción y el mismo período, o de la misma inscripción y la misma fecha, y un segundo cargo sin modalidad del mismo alumno y el mismo tipo de cargo. **[SUPUESTO]**: `aclaraciones-cliente.md`, «Preguntas abiertas», «Cargos repetidos».

#### Scenario: Mismo período en la misma inscripción
- **GIVEN** un cargo de la inscripción de Juan Pérez en «Delfines» mañana por el «Mes 1»
- **WHEN** se inserta otro cargo de la misma inscripción por el «Mes 1»
- **THEN** la base rechaza la fila

#### Scenario: Otro período en la misma inscripción
- **GIVEN** un cargo de la inscripción de Juan Pérez en «Delfines» mañana por el «Mes 1»
- **WHEN** se inserta un cargo de la misma inscripción por el «Mes 2»
- **THEN** la fila queda guardada

#### Scenario: El mismo día en la misma inscripción
- **GIVEN** un cargo Día de la inscripción de Juan Pérez en «Delfines» mañana del 2027-01-05
- **WHEN** se inserta otro cargo Día de la misma inscripción del 2027-01-05
- **THEN** la base rechaza la fila

#### Scenario: Dos cargos de monto fijo del mismo tipo para el mismo alumno
- **GIVEN** un cargo «Preinscripción» de Juan Pérez en 2026-27
- **WHEN** se inserta otro cargo «Preinscripción» de Juan Pérez en 2026-27
- **THEN** la base rechaza la fila

#### Scenario: El mismo cargo de monto fijo para un hermano
- **GIVEN** un cargo «Preinscripción» de Juan Pérez en 2026-27
- **WHEN** se inserta un cargo «Preinscripción» de Ana Pérez, de la misma familia, en 2026-27
- **THEN** la fila queda guardada

### Requirement: Registrar un cargo
`POST /api/v1/cargos` con `alumno_id`, `tipo_cargo_id` y, si corresponde, `inscripcion_id`, `modalidad`, `periodo_cobro_id` o `fecha_dia` SHALL calcular el monto, guardar el cargo con quien llama como autor y responder 201 con el cargo, su desglose (`categoria_aplicada`, `cantidad_hijos_aplicada`, `monto_base`, `porcentaje_aplicado`, `monto_total`) y el `saldo_pendiente` de la familia. Montos y porcentajes viajan como texto con dos decimales.

#### Scenario: Abono del Mes con descuento por cantidad de hijos
- **GIVEN** la familia «Pérez – Ana», categoría `empleado`, con Ana y Juan inscriptos en el turno mañana de 2026-27, sin cargos
- **AND** la tarifa base de la mañana para el Mes es 100000.00 y los descuentos de `empleado` en el Mes son 10.00, 15.00 y 20.00 para 1, 2 y 3 hijos
- **WHEN** un Admin registra un cargo «Abono» para Juan, con su inscripción de la mañana, modalidad `mes` y el período «Mes 1»
- **THEN** la respuesta es 201 con `categoria_aplicada` `empleado`, `cantidad_hijos_aplicada` 2, `monto_base` `"100000.00"`, `porcentaje_aplicado` `"15.00"` y `monto_total` `"85000.00"`
- **AND** trae `familia_id` de la familia «Pérez – Ana», `modalidad` `mes`, el `periodo_cobro_id` del «Mes 1» y `saldo_pendiente` `"85000.00"`
- **AND** la base tiene ese cargo, con el Admin como autor

#### Scenario: Preinscripción con monto fijo y sin descuento
- **GIVEN** el tipo de cargo «Preinscripción» de 2026-27, de monto fijo 20000.00, y Juan inscripto en 2026-27 en una familia `socio`
- **WHEN** un Admin registra un cargo «Preinscripción» para Juan, sin inscripción, modalidad, período ni fecha
- **THEN** la respuesta es 201 con `categoria_aplicada` `socio`, `monto_base` `"20000.00"`, `porcentaje_aplicado` `"0.00"`, `monto_total` `"20000.00"`, y `inscripcion_id`, `modalidad`, `periodo_cobro_id`, `fecha_dia` y `cantidad_hijos_aplicada` null

#### Scenario: La Preinscripción no depende de la categoría
- **GIVEN** el tipo de cargo «Preinscripción» de monto fijo 20000.00, y los descuentos de `no_socio` todos en 0.00 y los de `socio` todos en 50.00
- **WHEN** un Admin registra una «Preinscripción» para un alumno de una familia `no_socio` y otra para un alumno de una familia `socio`
- **THEN** los dos cargos tienen `monto_total` `"20000.00"`

#### Scenario: Abono del Día
- **GIVEN** Juan, de una familia `empleado`, inscripto en el turno mañana; la tarifa base de la mañana para el Día es 8000.00 y el descuento de `empleado` para el Día es 10.00
- **WHEN** un Admin registra un «Abono» para Juan, modalidad `dia`, `fecha_dia` 2027-01-05
- **THEN** la respuesta es 201 con `fecha_dia` `2027-01-05`, `periodo_cobro_id` null, `cantidad_hijos_aplicada` null y `monto_total` `"7200.00"`

#### Scenario: La ficha incompleta no impide el cargo
- **GIVEN** Juan inscripto en el turno mañana sin ningún documento presentado
- **WHEN** un Admin le registra un «Abono» del Mes, período «Mes 1»
- **THEN** la respuesta es 201

#### Scenario: El importe no viene del cliente
- **WHEN** un Admin llama a `POST /api/v1/cargos` con un «Abono» válido de Juan más `monto_total` `"1.00"`
- **THEN** la respuesta es 422 con un error cuyo `loc` termina en `monto_total`
- **AND** no se guarda ningún cargo

### Requirement: Un único porcentaje sobre la tarifa base
El total del Abono SHALL ser la tarifa base del turno de la inscripción y la modalidad, menos un único porcentaje: en el Mes, el de la categoría de la familia y su tramo de hijos; en Día, Semana y Quincena, el de la categoría y la modalidad, sin importar los hijos. Los porcentajes MUST NOT acumularse.

#### Scenario: En la Semana no cuentan los hijos
- **GIVEN** una familia `empleado` con 3 hijos inscriptos en el turno mañana; la tarifa base de la mañana para la Semana es 30000.00, el descuento de `empleado` para la Semana es 10.00 y el de `empleado` en el Mes con 3 hijos es 20.00
- **WHEN** un Admin registra un «Abono» para uno de ellos, turno mañana, modalidad `semana`, período «Semana 1»
- **THEN** la respuesta es 201 con `porcentaje_aplicado` `"10.00"`, `cantidad_hijos_aplicada` null y `monto_total` `"27000.00"`

#### Scenario: Quincena de la tarde
- **GIVEN** una familia `socio` con un hijo inscripto en el turno tarde; la tarifa base de la tarde para la Quincena es 45000.00 y el descuento de `socio` para la Quincena es 50.00
- **WHEN** un Admin registra un «Abono» para él, modalidad `quincena`, período «Quincena 1»
- **THEN** `monto_base` es `"45000.00"` y `monto_total` `"22500.00"`

#### Scenario: Un solo porcentaje, nunca acumulado
- **GIVEN** una familia `socio` con 4 hijos inscriptos en el turno mañana; la tarifa base de la mañana para el Mes es 100000.00 y todos los descuentos de `socio`, en el Mes y en las demás modalidades, son 50.00
- **WHEN** un Admin registra un «Abono» del Mes, turno mañana, para uno de ellos
- **THEN** `porcentaje_aplicado` es `"50.00"` y `monto_total` `"50000.00"`, ni `"25000.00"` ni `"0.00"`

#### Scenario: Porcentaje con decimales
- **GIVEN** una familia `empleado` con 3 hijos inscriptos en el turno mañana; la tarifa base de la mañana para el Mes es 100000.00 y el descuento de `empleado` en el Mes con 3 hijos es 36.25
- **WHEN** un Admin registra un «Abono» del Mes, turno mañana, para uno de ellos
- **THEN** `porcentaje_aplicado` es `"36.25"` y `monto_total` `"63750.00"`

#### Scenario: Medio centavo se redondea hacia arriba
- **GIVEN** una familia `socio` con un hijo inscripto en el turno mañana; la tarifa base de la mañana para el Día es 1000.05 y el descuento de `socio` para el Día es 50.00
- **WHEN** un Admin registra un «Abono» del Día para él
- **THEN** `monto_total` es `"500.03"`, no `"500.02"`

### Requirement: El tramo de hijos del Mes
En el Mes, la cantidad de hijos SHALL ser la de alumnos de la familia inscriptos en el mismo turno y la misma temporada que la inscripción del cargo, incluido el propio. Con 4 o más vale el tramo «4 o más». El porcentaje del tramo SHALL aplicarse a cada hijo, incluido el primero.

#### Scenario: Un solo hijo no toma el tramo de dos
- **GIVEN** una familia `no_socio` con un solo hijo inscripto en el turno mañana; la tarifa base de la mañana para el Mes es 100000.00 y los descuentos de `no_socio` en el Mes son 0.00, 10.00, 15.00 y 20.00 para 1, 2, 3 y 4 o más hijos
- **WHEN** un Admin registra un «Abono» del Mes, turno mañana, «Mes 1»
- **THEN** `cantidad_hijos_aplicada` es 1, `porcentaje_aplicado` `"0.00"` y `monto_total` `"100000.00"`, no `"90000.00"`

#### Scenario: Tres hijos
- **GIVEN** la misma tarifa y los mismos descuentos de `no_socio`, y una familia `no_socio` con 3 hijos inscriptos en el turno mañana
- **WHEN** un Admin registra un «Abono» del Mes, turno mañana, para uno de ellos
- **THEN** `cantidad_hijos_aplicada` es 3 y `monto_total` `"85000.00"`

#### Scenario: El tramo alcanza a todos los hijos
- **GIVEN** la misma tarifa y los mismos descuentos de `no_socio`, y una familia `no_socio` con 4 hijos inscriptos en el turno mañana
- **WHEN** un Admin registra un «Abono» del Mes, turno mañana, «Mes 1», para cada uno de los 4
- **THEN** los 4 cargos tienen `porcentaje_aplicado` `"20.00"` y `monto_total` `"80000.00"`, incluido el del primer hijo

#### Scenario: Cinco hijos usan el tramo de cuatro o más
- **GIVEN** la misma tarifa y los mismos descuentos de `no_socio`, y una familia `no_socio` con 5 hijos inscriptos en el turno mañana
- **WHEN** un Admin registra un «Abono» del Mes, turno mañana, para uno de ellos
- **THEN** la respuesta es 201 con `cantidad_hijos_aplicada` 5, `porcentaje_aplicado` `"20.00"` y `monto_total` `"80000.00"`

#### Scenario: Los hijos se cuentan por turno
- **GIVEN** la familia «Pérez – Ana», `empleado`, con Ana inscripta solo en el turno mañana y Juan en los turnos mañana y tarde
- **AND** las tarifas base del Mes son 100000.00 a la mañana y 80000.00 a la tarde, y los descuentos de `empleado` en el Mes son 10.00 y 15.00 para 1 y 2 hijos
- **WHEN** un Admin registra para Juan un «Abono» del Mes con la inscripción de la mañana y otro con la de la tarde, los dos del «Mes 1»
- **THEN** el de la mañana tiene `cantidad_hijos_aplicada` 2 y `monto_total` `"85000.00"`
- **AND** el de la tarde tiene `cantidad_hijos_aplicada` 1 y `monto_total` `"72000.00"`

#### Scenario: Un hermano de otra temporada no cuenta
- **GIVEN** una familia `empleado` con Juan inscripto en el turno mañana de 2026-27 y Ana inscripta en el turno mañana solo de la temporada cerrada 2025-26
- **WHEN** un Admin registra un «Abono» del Mes de 2026-27 para Juan, turno mañana
- **THEN** `cantidad_hijos_aplicada` es 1

### Requirement: Un cargo registrado no se recalcula
Un cargo ya registrado SHALL conservar su categoría, cantidad de hijos, tarifa base, porcentaje y total aunque después cambien la composición de la familia, su categoría o el tarifario. Solo los cargos nuevos usan los valores nuevos.

#### Scenario: Hijo que se suma a mitad de temporada
- **GIVEN** la familia «Pérez – Ana», `empleado`, con un «Abono» del Mes de Juan, turno mañana, «Mes 1», por 85000.00 con 2 hijos, y el descuento de `empleado` en el Mes con 3 hijos en 20.00
- **AND** después se inscribe a Tomás en el turno mañana
- **WHEN** un Admin registra un «Abono» del Mes para Juan, turno mañana, «Mes 2»
- **THEN** el cargo nuevo tiene `cantidad_hijos_aplicada` 3 y `monto_total` `"80000.00"`
- **AND** el cargo del «Mes 1» sigue en la base con `cantidad_hijos_aplicada` 2 y `monto_total` 85000.00

#### Scenario: Cambia el tarifario después del cargo
- **GIVEN** un «Abono» del Mes de Juan, turno mañana, «Mes 1», registrado con `monto_base` 100000.00
- **WHEN** la tarifa base de la mañana para el Mes pasa a 120000.00 y un Admin registra un «Abono» del Mes de Juan, turno mañana, «Mes 2»
- **THEN** el cargo nuevo tiene `monto_base` `"120000.00"`
- **AND** el del «Mes 1» sigue con `monto_base` 100000.00

### Requirement: Saldo pendiente al registrar
El `saldo_pendiente` que devuelve el registro SHALL ser la suma de los totales de los cargos de la familia en la temporada del cargo, incluido el nuevo. Mientras no existan pagos, no se descuenta nada. No se guarda: se calcula en cada respuesta.

#### Scenario: Segundo cargo de la familia
- **GIVEN** la familia «Pérez – Ana» con una «Preinscripción» de Ana por 20000.00 en 2026-27
- **WHEN** un Admin registra para Juan un «Abono» del Mes de 85000.00
- **THEN** `saldo_pendiente` es `"105000.00"`

#### Scenario: Solo la familia y la temporada del cargo
- **GIVEN** la familia «Pérez – Ana» con un cargo de 30000.00 en la temporada cerrada 2025-26, y otra familia con un cargo de 50000.00 en 2026-27
- **WHEN** un Admin registra para Juan Pérez un «Abono» del Mes de 85000.00 en 2026-27
- **THEN** `saldo_pendiente` es `"85000.00"`

### Requirement: Simular un cargo
`POST /api/v1/cargos/simulacion`, con el mismo cuerpo que el registro, SHALL responder 200 con `familia_id`, `categoria_aplicada`, `cantidad_hijos_aplicada`, `monto_base`, `porcentaje_aplicado` y `monto_total`, calculados como en el registro, y MUST NOT guardar nada. Rechaza con los mismos códigos y mensajes que el registro.

#### Scenario: Simular el Abono del Mes
- **GIVEN** la familia «Pérez – Ana», `empleado`, con Ana y Juan inscriptos en el turno mañana, tarifa base del Mes 100000.00 y descuento de `empleado` en el Mes con 2 hijos 15.00
- **WHEN** un Admin llama a `POST /api/v1/cargos/simulacion` con un «Abono» de Juan, turno mañana, modalidad `mes`, «Mes 1»
- **THEN** la respuesta es 200 con `cantidad_hijos_aplicada` 2, `monto_base` `"100000.00"`, `porcentaje_aplicado` `"15.00"` y `monto_total` `"85000.00"`
- **AND** la cantidad de cargos de la base es la misma que antes

#### Scenario: Simular un cargo que ya existe
- **GIVEN** un «Abono» del Mes de Juan, turno mañana, «Mes 1», ya registrado
- **WHEN** un Admin simula el mismo cargo
- **THEN** la respuesta es 409, igual que al registrarlo

### Requirement: Qué pide cada tipo de cargo
El registro y la simulación SHALL responder 422 con un error `regla_de_negocio` en cada campo que no cumple, todos juntos: alumno y tipo de cargo existentes; sin inscripción, modalidad, período ni fecha en el monto fijo; con inscripción del alumno y de la temporada, y modalidad, en el Abono; con período existente, de la temporada y de esa modalidad, o fecha en el Día. Nada se guarda.

#### Scenario: Alumno y tipo de cargo que no existen
- **WHEN** un Admin registra un cargo con un `alumno_id` y un `tipo_cargo_id` que no existen
- **THEN** la respuesta es 422 con un error en `alumno_id` cuyo `msg` es `El alumno no existe.` y otro en `tipo_cargo_id` con `El tipo de cargo no existe.`

#### Scenario: Monto fijo con datos del Abono
- **WHEN** un Admin registra una «Preinscripción» para Juan con `inscripcion_id`, `modalidad` `mes` y `periodo_cobro_id`
- **THEN** la respuesta es 422 con un error en cada uno de `inscripcion_id`, `modalidad` y `periodo_cobro_id`, con `msg` `Un cargo de monto fijo no lleva este dato.`
- **AND** no se guarda ningún cargo

#### Scenario: Abono sin inscripción ni modalidad
- **WHEN** un Admin registra un «Abono» para Juan sin `inscripcion_id` ni `modalidad`
- **THEN** la respuesta es 422 con un error en `inscripcion_id` y otro en `modalidad`, los dos con `msg` `Este dato es obligatorio.`

#### Scenario: Inscripción de otro alumno
- **GIVEN** Juan y Sofía, de familias distintas, inscriptos en el turno mañana
- **WHEN** un Admin registra un «Abono» para Juan con la inscripción de Sofía
- **THEN** la respuesta es 422 con un error en `inscripcion_id` cuyo `msg` es `La inscripción no es del alumno.`

#### Scenario: Inscripción que no existe
- **WHEN** un Admin registra un «Abono» para Juan con un `inscripcion_id` que no existe
- **THEN** la respuesta es 422 con un error en `inscripcion_id` cuyo `msg` es `La inscripción no existe.`

#### Scenario: Inscripción de otra temporada
- **GIVEN** Juan con una inscripción en la temporada cerrada 2025-26
- **WHEN** un Admin registra un «Abono» de 2026-27 para Juan con esa inscripción
- **THEN** la respuesta es 422 con un error en `inscripcion_id` cuyo `msg` es `La inscripción no es de la temporada del tipo de cargo.`

#### Scenario: Mes sin período
- **WHEN** un Admin registra un «Abono» para Juan, con su inscripción, modalidad `mes` y sin `periodo_cobro_id`
- **THEN** la respuesta es 422 con un error en `periodo_cobro_id` cuyo `msg` es `Este dato es obligatorio.`

#### Scenario: Período de otra modalidad
- **WHEN** un Admin registra un «Abono» para Juan, modalidad `mes`, con el período «Semana 1»
- **THEN** la respuesta es 422 con un error en `periodo_cobro_id` cuyo `msg` es `El período es de otra modalidad.`

#### Scenario: Período que no existe
- **WHEN** un Admin registra un «Abono» para Juan, modalidad `mes`, con un `periodo_cobro_id` que no existe
- **THEN** la respuesta es 422 con un error en `periodo_cobro_id` cuyo `msg` es `El período no existe.`

#### Scenario: Período de otra temporada
- **GIVEN** el período «Mes 1» de la temporada cerrada 2025-26
- **WHEN** un Admin registra un «Abono» de 2026-27 para Juan, modalidad `mes`, con ese período
- **THEN** la respuesta es 422 con un error en `periodo_cobro_id` cuyo `msg` es `El período no es de la temporada del tipo de cargo.`

#### Scenario: Semana con fecha
- **WHEN** un Admin registra un «Abono» para Juan, modalidad `semana`, con el período «Semana 1» y `fecha_dia` 2027-01-05
- **THEN** la respuesta es 422 con un error en `fecha_dia` cuyo `msg` es `Solo la modalidad Día lleva fecha.`

#### Scenario: Día sin fecha y con período
- **WHEN** un Admin registra un «Abono» para Juan, modalidad `dia`, sin `fecha_dia` y con el período «Semana 1»
- **THEN** la respuesta es 422 con un error en `fecha_dia` cuyo `msg` es `Este dato es obligatorio.` y otro en `periodo_cobro_id` con `La modalidad Día no lleva período.`

### Requirement: El alumno está inscripto en la temporada
Todo cargo SHALL ser de un alumno con al menos una inscripción en la temporada del tipo de cargo, aunque el monto fijo no lleve inscripción. Si no, responde 422 en `alumno_id` con `El alumno no está inscripto en la temporada.` **[SUPUESTO]**: `aclaraciones-cliente.md`, «Preguntas abiertas», «Cargo de un alumno sin inscripción».

#### Scenario: Preinscripción de un alumno inscripto solo en la temporada anterior
- **GIVEN** Sofía, inscripta solo en la temporada cerrada 2025-26
- **WHEN** un Admin registra una «Preinscripción» de 2026-27 para Sofía
- **THEN** la respuesta es 422 con un error en `alumno_id` cuyo `msg` es `El alumno no está inscripto en la temporada.`

#### Scenario: Preinscripción de un alumno inscripto solo a la tarde
- **GIVEN** Lucía, inscripta en 2026-27 solo en el turno tarde
- **WHEN** un Admin registra una «Preinscripción» de 2026-27 para Lucía
- **THEN** la respuesta es 201

### Requirement: La fecha del Día está dentro de la temporada
La `fecha_dia` de un Abono del Día SHALL estar entre la fecha de inicio y la de cierre de la temporada, ambas incluidas. Si no, responde 422 en `fecha_dia` con `La fecha está fuera de la temporada, del DD/MM/AAAA al DD/MM/AAAA.` **[SUPUESTO]**: `aclaraciones-cliente.md`, «Preguntas abiertas», «Fecha del cargo del Día».

#### Scenario: Primer día de la temporada
- **GIVEN** la temporada 2026-27, del 2027-01-04 al 2027-02-26
- **WHEN** un Admin registra un «Abono» del Día para Juan con `fecha_dia` 2027-01-04
- **THEN** la respuesta es 201

#### Scenario: Día anterior al inicio
- **GIVEN** la temporada 2026-27, del 2027-01-04 al 2027-02-26
- **WHEN** un Admin registra un «Abono» del Día para Juan con `fecha_dia` 2027-01-03
- **THEN** la respuesta es 422 con un error en `fecha_dia` cuyo `msg` es `La fecha está fuera de la temporada, del 04/01/2027 al 26/02/2027.`

#### Scenario: Último día de la temporada
- **GIVEN** la temporada 2026-27, del 2027-01-04 al 2027-02-26
- **WHEN** un Admin registra un «Abono» del Día para Juan con `fecha_dia` 2027-02-26
- **THEN** la respuesta es 201

#### Scenario: Día posterior al cierre
- **GIVEN** la temporada 2026-27, del 2027-01-04 al 2027-02-26
- **WHEN** un Admin registra un «Abono» del Día para Juan con `fecha_dia` 2027-02-27
- **THEN** la respuesta es 422 con el mismo `msg` en `fecha_dia`

### Requirement: La temporada cerrada queda para consulta
El registro y la simulación MUST rechazar un tipo de cargo de una temporada cerrada con 422 en `tipo_cargo_id` y `msg` `El tipo de cargo es de una temporada cerrada, que queda solo para consulta.`, sin guardar nada.

#### Scenario: Cargo en la temporada anterior
- **GIVEN** la temporada 2025-26 cerrada, con su tipo de cargo «Abono» y Juan inscripto en ella
- **WHEN** un Admin registra un cargo con el «Abono» de 2025-26 para Juan, con esa inscripción
- **THEN** la respuesta es 422 con un error en `tipo_cargo_id` cuyo `msg` es `El tipo de cargo es de una temporada cerrada, que queda solo para consulta.`
- **AND** no se guarda ningún cargo

### Requirement: Falta configuración del tarifario
Si falta la tarifa base del turno y la modalidad, o el porcentaje de la celda que corresponde, el registro y la simulación SHALL responder 409 con un `detail` de texto que dice qué falta, sin calcular ni guardar nada.

#### Scenario: Falta la tarifa base
- **GIVEN** que no hay tarifa base de la tarde para la Quincena, y Lucía está inscripta en el turno tarde
- **WHEN** un Admin registra un «Abono» para Lucía, turno tarde, modalidad `quincena`, «Quincena 1»
- **THEN** la respuesta es 409 con `detail` `Falta la tarifa base del turno tarde para la modalidad Quincena.`
- **AND** no se guarda ningún cargo

#### Scenario: Falta el porcentaje del tramo
- **GIVEN** una familia `empleado` con 3 hijos en el turno mañana, y sin descuento de `empleado` en el Mes para 3 hijos
- **WHEN** un Admin registra un «Abono» del Mes, turno mañana, para uno de ellos
- **THEN** la respuesta es 409 con `detail` `Falta el descuento de la categoría empleado para el Mes con 3 hijos.`

#### Scenario: Falta el porcentaje de la modalidad
- **GIVEN** una familia `socio` y sin descuento de `socio` para la Semana
- **WHEN** un Admin registra un «Abono» de la Semana para un hijo suyo
- **THEN** la respuesta es 409 con `detail` `Falta el descuento de la categoría socio para la modalidad Semana.`

### Requirement: Un cargo repetido se rechaza
El registro y la simulación SHALL responder 409 cuando ya existe el mismo cargo: el mismo Abono para la misma inscripción y período, o la misma inscripción y fecha, o el mismo tipo de monto fijo para el alumno en la temporada. **[SUPUESTO]**: `aclaraciones-cliente.md`, «Preguntas abiertas», «Cargos repetidos».

#### Scenario: El mismo Abono del Mes dos veces
- **GIVEN** un «Abono» del Mes de Juan, turno mañana, «Mes 1», ya registrado
- **WHEN** un Admin registra otra vez un «Abono» del Mes de Juan, turno mañana, «Mes 1»
- **THEN** la respuesta es 409 con `detail` `El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana.`
- **AND** la base sigue teniendo un solo cargo de esa inscripción y período

#### Scenario: El mismo período en el otro turno
- **GIVEN** un «Abono» del Mes de Juan, turno mañana, «Mes 1», ya registrado, y Juan inscripto también a la tarde
- **WHEN** un Admin registra un «Abono» del Mes de Juan, turno tarde, «Mes 1»
- **THEN** la respuesta es 201

#### Scenario: El mismo Día dos veces
- **GIVEN** un «Abono» del Día de Juan, turno mañana, del 2027-01-05, ya registrado
- **WHEN** un Admin registra otra vez un «Abono» del Día de Juan, turno mañana, del 2027-01-05
- **THEN** la respuesta es 409 con `detail` `El alumno ya tiene un cargo «Abono» del día 05/01/2027 en el turno mañana.`

#### Scenario: Dos Preinscripciones del mismo alumno
- **GIVEN** una «Preinscripción» de Juan en 2026-27, ya registrada
- **WHEN** un Admin registra otra «Preinscripción» de 2026-27 para Juan
- **THEN** la respuesta es 409 con `detail` `El alumno ya tiene un cargo «Preinscripción» en esta temporada.`

### Requirement: Opciones para registrar un cargo
`GET /api/v1/cargos/opciones` SHALL responder 200 con `tipos_cargo` (cada uno con `id`, `nombre`, `calculo` y `monto_fijo`), por nombre, y `periodos` (cada uno con `id`, `modalidad`, `nombre`, `fecha_desde` y `fecha_hasta`), por modalidad (Mes, Quincena, Semana) y fecha de inicio, todos de la temporada vigente.

#### Scenario: Tipos y períodos de la temporada vigente
- **GIVEN** la temporada vigente 2026-27 con «Preinscripción» y «Abono», «Mes 2» del 2027-02-01, «Mes 1» del 2027-01-04 y «Semana 1» del 2027-01-04; y la temporada cerrada 2025-26 con su propio «Abono» y su «Mes 1»
- **WHEN** un Admin llama a `GET /api/v1/cargos/opciones`
- **THEN** la respuesta es 200 con `tipos_cargo` «Abono» (`calculo` `tarifario`, `monto_fijo` null) y «Preinscripción» (`calculo` `monto_fijo`, `monto_fijo` `"20000.00"`), en ese orden
- **AND** `periodos` trae «Mes 1», «Mes 2» y «Semana 1», en ese orden, y nada de 2025-26

### Requirement: Solo el Admin registra cargos
`POST /api/v1/cargos`, `POST /api/v1/cargos/simulacion` y `GET /api/v1/cargos/opciones` SHALL estar disponibles solo para el Admin. Coordinador y Profesor reciben 403 con `No tenés permiso para esta operación.` y no se guarda nada; sin sesión, 401.

#### Scenario: Coordinador registra un cargo
- **WHEN** un Coordinador llama a `POST /api/v1/cargos` con un «Abono» válido de Juan
- **THEN** la respuesta es 403 con `detail` `No tenés permiso para esta operación.`
- **AND** no se guarda ningún cargo

#### Scenario: Profesor registra un cargo a un alumno de su grupo
- **GIVEN** `jperez`, Profesor asignado a «Delfines» mañana, donde está inscripto Juan
- **WHEN** `jperez` llama a `POST /api/v1/cargos` con un «Abono» válido de Juan
- **THEN** la respuesta es 403 y no se guarda ningún cargo

#### Scenario: Profesor simula un cargo
- **WHEN** un Profesor llama a `POST /api/v1/cargos/simulacion` con un «Abono» válido
- **THEN** la respuesta es 403 y la respuesta no trae ningún monto

#### Scenario: Coordinador pide las opciones
- **WHEN** un Coordinador llama a `GET /api/v1/cargos/opciones`
- **THEN** la respuesta es 403

#### Scenario: Sin sesión
- **WHEN** se llama a `POST /api/v1/cargos` sin token
- **THEN** la respuesta es 401 y no se guarda ningún cargo

#### Scenario: Admin con el cambio de contraseña pendiente
- **GIVEN** un Admin con `debe_cambiar_password` en true
- **WHEN** llama a `POST /api/v1/cargos` con un «Abono» válido
- **THEN** la respuesta es 403 y no se guarda ningún cargo

### Requirement: Pantalla «Registrar cargo»
La dirección `/cargos/nuevo`, dentro de la zona protegida y solo para el Admin, SHALL mostrar `Familia` (buscador por apellido) y, con una familia elegida, su categoría, `Alumno y turno`, `Tipo de cargo` y el botón `Registrar cargo`. Con un tipo por tarifario, además `Modalidad` y, según ella, `Período` o `Fecha`. Coordinador y Profesor son llevados a `/`.

#### Scenario: Elegir la familia
- **GIVEN** la sesión de un Admin y la familia «Pérez – Ana», `empleado`, con Ana inscripta en «Tiburones» mañana y Juan en «Delfines» mañana y «Pulpos» tarde
- **WHEN** abre `/cargos/nuevo`, escribe `Pér` en `Familia` y elige `Pérez – Ana`
- **THEN** ve `Empleado` y `Alumno y turno` ofrece `Ana Pérez · Mañana`, `Juan Pérez · Mañana` y `Juan Pérez · Tarde`

#### Scenario: Familia sin hijos inscriptos
- **GIVEN** la sesión de un Admin y una familia sin inscripciones en la temporada vigente
- **WHEN** la elige en `Familia`
- **THEN** ve `La familia no tiene hijos inscriptos en la temporada.` y no ve `Alumno y turno`

#### Scenario: Los campos según el tipo y la modalidad
- **GIVEN** la sesión de un Admin con una familia y `Juan Pérez · Mañana` elegidos
- **WHEN** elige `Tipo de cargo` «Abono» y `Modalidad` `Mes`
- **THEN** ve `Período`, que ofrece solo los períodos del Mes, escritos como `Mes 1 · 04/01/2027 al 29/01/2027`, y no ve `Fecha`
- **AND** al cambiar `Modalidad` a `Día` ve `Fecha` y no ve `Período`
- **AND** al cambiar `Tipo de cargo` a «Preinscripción» no ve ni `Modalidad`, ni `Período`, ni `Fecha`

#### Scenario: Coordinador abre la pantalla
- **GIVEN** la sesión de un Coordinador
- **WHEN** abre `/cargos/nuevo`
- **THEN** la dirección pasa a `/` y no se pide nada a `/api/v1/cargos`

### Requirement: El desglose en la pantalla
Con todos los datos del cargo elegidos, la pantalla SHALL pedir la simulación a la API y mostrar la tarifa base, el porcentaje y el total que devuelve, con los montos como `$ 85.000`. Al cambiar cualquier dato, el desglose anterior desaparece y vale solo la respuesta del último pedido. La pantalla no calcula ningún monto.

#### Scenario: Desglose del Abono del Mes
- **GIVEN** la sesión de un Admin, la familia «Pérez – Ana» y `Juan Pérez · Mañana`, «Abono», `Mes` y «Mes 1» elegidos, y la simulación responde `monto_base` `"100000.00"`, `porcentaje_aplicado` `"15.00"`, `cantidad_hijos_aplicada` 2, `categoria_aplicada` `empleado` y `monto_total` `"85000.00"`
- **WHEN** llega la respuesta
- **THEN** ve `Tarifa base · Mañana · Mes` con `$ 100.000`, `Descuento Empleado · 2 hijos en el turno` con `15 %` y `Total del cargo` con `$ 85.000`
- **AND** `Registrar cargo` está habilitado

#### Scenario: Desglose de la Preinscripción
- **GIVEN** la sesión de un Admin con `Juan Pérez · Mañana` y «Preinscripción» elegidos, y la simulación responde `monto_base` `"20000.00"`, `porcentaje_aplicado` `"0.00"` y `monto_total` `"20000.00"`
- **WHEN** llega la respuesta
- **THEN** ve `Monto fijo` con `$ 20.000`, `Sin descuento` y `Total del cargo` con `$ 20.000`

#### Scenario: La simulación rechaza el cargo
- **GIVEN** la sesión de un Admin con un cargo completo elegido, y la simulación responde 409 con `El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana.`
- **WHEN** llega la respuesta
- **THEN** ve ese mensaje, no ve `Total del cargo` y `Registrar cargo` está deshabilitado

#### Scenario: Cambia un dato con la simulación en curso
- **GIVEN** la sesión de un Admin con «Mes 1» elegido y su simulación todavía sin responder
- **WHEN** elige «Mes 2», y la respuesta del «Mes 2» llega antes que la del «Mes 1»
- **THEN** el desglose que queda es el del «Mes 2»

### Requirement: Registrar desde la pantalla
`Registrar cargo` SHALL enviar a `POST /api/v1/cargos` solo qué se cobra, sin ningún monto, y estar deshabilitado mientras no haya un desglose del cargo elegido y mientras se registra. Al registrarse, muestra `Cargo registrado. Saldo pendiente de la familia: $ X.` y deja la familia elegida y el resto de los campos vacíos.

#### Scenario: Registrar el Abono del Mes
- **GIVEN** la sesión de un Admin con el desglose del «Abono» del Mes de Juan, «Mes 1», a la vista
- **WHEN** pulsa `Registrar cargo` y la API responde 201 con `saldo_pendiente` `"105000.00"`
- **THEN** el cuerpo enviado tiene `alumno_id`, `tipo_cargo_id`, `inscripcion_id`, `modalidad` y `periodo_cobro_id`, y ningún campo de monto ni de porcentaje
- **AND** ve `Cargo registrado. Saldo pendiente de la familia: $ 105.000.`
- **AND** `Familia` sigue en `Pérez – Ana` y `Alumno y turno` y `Tipo de cargo` quedan vacíos

#### Scenario: Sin desglose no se registra
- **GIVEN** la sesión de un Admin con familia, alumno y «Abono» elegidos, sin modalidad
- **WHEN** mira el botón
- **THEN** `Registrar cargo` está deshabilitado

#### Scenario: Mientras se registra
- **GIVEN** la sesión de un Admin que pulsó `Registrar cargo`, con el pedido sin responder
- **WHEN** mira la pantalla
- **THEN** `Registrar cargo` está deshabilitado y un segundo clic no envía otro pedido

#### Scenario: El registro falla
- **GIVEN** la sesión de un Admin con un desglose a la vista
- **WHEN** pulsa `Registrar cargo` y la API responde 409 con `El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana.`
- **THEN** ve ese mensaje y los campos conservan lo elegido
