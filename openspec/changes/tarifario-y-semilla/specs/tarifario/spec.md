# Spec Delta

## Purpose

Guarda, por temporada, todo lo que hace falta para calcular un cargo: la tarifa base por turno y modalidad, la tabla de descuentos por categoría y tramo de hijos, las fechas de cada período de cobro y los tipos de cargo.

## ADDED Requirements

### Requirement: Tarifa base por turno y modalidad
Cada temporada SHALL tener a lo sumo una tarifa base por combinación de turno (`manana`, `tarde`) y modalidad (`mes`, `quincena`, `semana`, `dia`), con un monto mayor que cero y guardado con dos decimales exactos.

#### Scenario: El monto mínimo positivo
- **WHEN** se inserta una tarifa base de 2026-27, turno `manana`, modalidad `dia`, con monto 0.01
- **THEN** la fila queda guardada con monto exactamente 0.01

#### Scenario: Monto cero
- **WHEN** se inserta una tarifa base de 2026-27, turno `manana`, modalidad `dia`, con monto 0
- **THEN** la base rechaza la fila

#### Scenario: Un monto con tres decimales se guarda con dos
- **WHEN** se inserta una tarifa base de 2026-27, turno `manana`, modalidad `mes`, con monto 100000.005
- **THEN** al releerla el monto es exactamente 100000.01, con dos decimales

#### Scenario: Dos tarifas para la misma combinación
- **GIVEN** una tarifa base de 2026-27, turno `manana`, modalidad `mes`, de 100000.00
- **WHEN** se inserta otra tarifa base de 2026-27, turno `manana`, modalidad `mes`, de 90000.00
- **THEN** la base rechaza la fila

### Requirement: Descuento por categoría para Día, Semana y Quincena
Cada temporada SHALL tener a lo sumo un porcentaje por categoría (`socio`, `empleado`, `no_socio`) y modalidad para Día, Semana y Quincena. La base MUST rechazar un porcentaje de esta tabla para la modalidad Mes: el Mes se descuenta solo por tramo de hijos.

#### Scenario: Descuento para la Quincena
- **WHEN** se inserta un descuento por modalidad de 2026-27, categoría `socio`, modalidad `quincena`, de 50.00
- **THEN** la fila queda guardada

#### Scenario: Descuento por modalidad para el Mes
- **WHEN** se inserta un descuento por modalidad de 2026-27, categoría `socio`, modalidad `mes`, de 50.00
- **THEN** la base rechaza la fila

#### Scenario: Dos descuentos para la misma categoría y modalidad
- **GIVEN** un descuento por modalidad de 2026-27, categoría `empleado`, modalidad `semana`, de 25.00
- **WHEN** se inserta otro de 2026-27, categoría `empleado`, modalidad `semana`, de 30.00
- **THEN** la base rechaza la fila

### Requirement: Descuento del Mes por tramo de hijos
Cada temporada SHALL tener a lo sumo un porcentaje por categoría y tramo de hijos para el Mes. El tramo SHALL ir de 1 a 4, donde 4 significa «4 o más».

#### Scenario: Los tramos de los extremos
- **WHEN** se insertan descuentos del Mes de 2026-27, categoría `no_socio`, con tramo 1 y con tramo 4
- **THEN** las dos filas quedan guardadas

#### Scenario: Tramos fuera de rango
- **WHEN** se inserta un descuento del Mes de 2026-27, categoría `no_socio`, con tramo 0, y aparte otro con tramo 5
- **THEN** la base rechaza las dos filas

#### Scenario: Dos descuentos para la misma categoría y tramo
- **GIVEN** un descuento del Mes de 2026-27, categoría `socio`, tramo 2, de 55.00
- **WHEN** se inserta otro de 2026-27, categoría `socio`, tramo 2, de 60.00
- **THEN** la base rechaza la fila

### Requirement: Los porcentajes van de 0 a 100 con dos decimales exactos
Todo porcentaje de las dos tablas de descuento SHALL estar entre 0 y 100, ambos incluidos, y guardarse con dos decimales exactos.

#### Scenario: Porcentajes en los extremos
- **WHEN** se insertan, en cada una de las dos tablas de descuento, una fila con porcentaje 0.00 y otra con 100.00
- **THEN** las cuatro filas quedan guardadas

#### Scenario: Porcentajes fuera de rango
- **WHEN** se intenta insertar, en cada una de las dos tablas de descuento, una fila con porcentaje -0.01 y otra con 100.01
- **THEN** la base rechaza las cuatro filas

#### Scenario: Un porcentaje con dos decimales
- **WHEN** se inserta un descuento del Mes de 2026-27, categoría `empleado`, tramo 3, de 36.25
- **THEN** al releerlo el porcentaje es exactamente 36.25

#### Scenario: Un porcentaje con tres decimales se guarda con dos
- **WHEN** se inserta un descuento del Mes de 2026-27, categoría `empleado`, tramo 3, de 36.255
- **THEN** al releerlo el porcentaje es exactamente 36.26, con dos decimales

### Requirement: Períodos de cobro con fechas fijas
Un período de cobro SHALL tener temporada, modalidad, nombre y fechas desde y hasta, con desde menor o igual que hasta. La modalidad Día MUST NOT tener períodos. El nombre no se repite dentro de la misma temporada y modalidad.

#### Scenario: Período de un solo día
- **WHEN** se inserta un período de 2026-27, modalidad `semana`, «Semana 1», del 2027-01-04 al 2027-01-04
- **THEN** la fila queda guardada

#### Scenario: Período con las fechas invertidas
- **WHEN** se inserta un período de 2026-27, modalidad `semana`, «Semana 1», del 2027-01-05 al 2027-01-04
- **THEN** la base rechaza la fila

#### Scenario: Período para la modalidad Día
- **WHEN** se inserta un período de 2026-27, modalidad `dia`, «Día 1», del 2027-01-04 al 2027-01-04
- **THEN** la base rechaza la fila

#### Scenario: Nombre repetido en la misma modalidad
- **GIVEN** un período de 2026-27, modalidad `mes`, «Mes 1»
- **WHEN** se inserta otro período de 2026-27, modalidad `mes`, «Mes 1», con otras fechas
- **THEN** la base rechaza la fila

#### Scenario: El mismo nombre en otra modalidad
- **GIVEN** un período de 2026-27, modalidad `mes`, «Período 1»
- **WHEN** se inserta un período de 2026-27, modalidad `quincena`, «Período 1»
- **THEN** la fila queda guardada

### Requirement: Tipos de cargo de monto fijo o por tarifario
Un tipo de cargo SHALL ser de cálculo `monto_fijo`, con un monto obligatorio y mayor que cero, o de cálculo `tarifario`, sin monto. Su nombre no se repite dentro de la temporada.

#### Scenario: El monto fijo mínimo positivo
- **WHEN** se inserta un tipo de cargo de 2026-27, cálculo `monto_fijo`, monto 0.01
- **THEN** la fila queda guardada

#### Scenario: Monto fijo cero
- **WHEN** se inserta un tipo de cargo de 2026-27, cálculo `monto_fijo`, monto 0
- **THEN** la base rechaza la fila

#### Scenario: Tipo de monto fijo con su monto
- **WHEN** se inserta el tipo de cargo «Preinscripción» de 2026-27, cálculo `monto_fijo`, monto 20000.00
- **THEN** la fila queda guardada

#### Scenario: Tipo de monto fijo sin monto
- **WHEN** se inserta un tipo de cargo de 2026-27, cálculo `monto_fijo`, sin monto
- **THEN** la base rechaza la fila

#### Scenario: Tipo por tarifario con monto
- **WHEN** se inserta el tipo de cargo «Abono» de 2026-27, cálculo `tarifario`, con monto 20000.00
- **THEN** la base rechaza la fila

#### Scenario: Tipo por tarifario sin monto
- **WHEN** se inserta el tipo de cargo «Abono» de 2026-27, cálculo `tarifario`, sin monto
- **THEN** la fila queda guardada

#### Scenario: Nombre repetido en la misma temporada
- **GIVEN** el tipo de cargo «Abono» en 2026-27
- **WHEN** se inserta otro tipo de cargo «Abono» en 2026-27
- **THEN** la base rechaza la fila
