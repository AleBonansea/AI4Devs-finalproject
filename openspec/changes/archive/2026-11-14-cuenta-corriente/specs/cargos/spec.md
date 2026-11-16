# Spec Delta

## MODIFIED Requirements

### Requirement: Saldo pendiente al registrar
El `saldo_pendiente` que devuelve el registro SHALL ser el saldo de la familia en la temporada del cargo, incluido el nuevo: la suma de los totales de sus cargos menos la suma de los pagos no anulados de esos cargos (spec `cuenta-corriente`, «El saldo de la familia es cargos menos pagos»). No se guarda: se calcula en cada respuesta.

#### Scenario: Segundo cargo de la familia
- **GIVEN** la familia «Pérez – Ana» con una «Preinscripción» de Ana por 20000.00 en 2026-27
- **WHEN** un Admin registra para Juan un «Abono» del Mes de 85000.00
- **THEN** `saldo_pendiente` es `"105000.00"`

#### Scenario: Solo la familia y la temporada del cargo
- **GIVEN** la familia «Pérez – Ana» con un cargo de 30000.00 en la temporada cerrada 2025-26, y otra familia con un cargo de 50000.00 en 2026-27
- **WHEN** un Admin registra para Juan Pérez un «Abono» del Mes de 85000.00 en 2026-27
- **THEN** `saldo_pendiente` es `"85000.00"`

#### Scenario: La familia ya pagó una parte
- **GIVEN** la familia «Pérez – Ana» con una «Preinscripción» de Ana por 20000.00 en 2026-27, con un pago de 5000.00 y otro de 3000.00 anulado
- **WHEN** un Admin registra para Juan un «Abono» del Mes de 85000.00
- **THEN** `saldo_pendiente` es `"100000.00"`
