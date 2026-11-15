# Tasks

> Antes de la primera tarea: rama `feat/cuenta-corriente` salida de la rama de entrega actualizada (regla 1 de CLAUDE.md); ya creada el 14/11/2026 desde `feature/entrega-2-AlexisBonansea` con `cobro` mergeado. Cada tarea que toca rutas, esquemas o modelos cierra su commit con `python tasks.py openapi-generate` (regla 5). La tarea 4.1 lo comprueba al final.

## 1. Esquema de pagos y tesorería, y supuestos

- [x] 1.1 Con la skill `backend-feature`, crear los modelos `Pago` y `TesoreriaMovimiento`, los enumerados `TipoMovimiento` y `OrigenMovimiento`, la vista `v_cuenta_corriente` y la migración `crear_pago_y_tesoreria`, según los Requirements de `pagos` «El pago guarda su monto, su fecha y su autor» (6 Scenarios) y de `tesoreria` «La forma de un movimiento de tesorería» (7) y «Un pago tiene un solo movimiento de cada origen» (2): 15 Scenarios.
  - Columnas según `3-modelo-de-datos.md`; restricciones, nombres e índices según design, «Esquema». `ck_movimiento_origen` sin la rama de `canon`.
  - `metadata_vistas` se mueve de `app/models/familia.py` a `app/models/base.py`; `v_cuenta_corriente` va en `app/models/cuenta_corriente.py`, con el SQL de design, «La vista `v_cuenta_corriente`». Sus Scenarios se prueban por la API en 2.1 y 3.1.
  - Los tests insertan directo en la base: los endpoints todavía no existen. Tests en `backend/tests/functional/pagos/` y `backend/tests/functional/tesoreria/`.
  - Sumar a la regla de `tesoreria_movimiento` en `3-modelo-de-datos.md` que el `CHECK` de `origen` no admite `canon` hasta la migración que cree `cierre_canon`, que agrega la columna y reemplaza el `CHECK`.
  - **Se verifica con** los 15 tests en rojo por el motivo correcto (no existen las tablas) y después en verde; la skill `revisar-migracion` sobre la migración (los dos `CREATE TYPE` una sola vez, la vista con SQL a mano, `DROP TYPE` y `DROP VIEW` en el downgrade), con `upgrade head` → `downgrade -1` → `upgrade head` contra la base de pruebas; `python tasks.py test`, `lint` y `typecheck` en verde.
- [x] 1.2 Registrar en `docs/prd/aclaraciones-cliente.md`, «Preguntas abiertas», la entrada «Fecha del pago» de design, «Supuestos registrados», con su **[SUPUESTO]** vigente y la referencia al change `cuenta-corriente`. Aclarar en CLAUDE.md, «El precio nunca viene del cliente», que la regla es sobre el precio de un cargo y que el monto de un pago lo informa el Admin y lo acota la API (design, «Rutas y roles»). **Se verifica con** la entrada escrita con el título «Fecha del pago», que es el que cita el Requirement de `pagos`, y el párrafo de CLAUDE.md reescrito.

## 2. Registrar un pago

- [x] 2.1 Con la skill `backend-feature`, construir `POST /api/v1/cargos/{cargo_id}/pagos` en `cargos.py`, con el servicio `app/services/pagos.py` y los esquemas de `app/schemas/pagos.py`, según estos Requirements: de `pagos`, «Registrar un pago» (5 Scenarios; todos menos «El saldo del cargo coincide con la cuenta corriente», que va en la 3.1 porque necesita el GET), «Un pago no supera el saldo del cargo» (5), «El monto y la fecha del pago» (10), «El cargo del pago existe y es de una temporada abierta» (3) y «Solo el Admin registra pagos» (5); de `tesoreria`, «Cada pago escribe su ingreso» (4): 32 Scenarios.
  - Orden de los pasos, `FOR UPDATE` sobre el cargo y un solo `commit` según design, «El servicio de pagos». El saldo del cargo sale de `pagado_por_cargo()` y `saldo_de_cargos()`, que se crean acá en `app/services/cuenta_corriente.py` y que la 3.1 reusa (design, «Un solo cálculo del saldo de un cargo»); `saldo_cargo` se vuelve a consultar después del `flush`, no se resta en Python.
  - El 409 de la temporada cerrada cita Acl. 10 y `3-modelo-de-datos.md`, «`temporada`», en el comentario del servicio (design, paso 4). Validación del monto y la fecha en el esquema, con `PydanticCustomError("regla_de_negocio", …)` (design, «Esquemas»).
  - Los tests de las fechas usan la fecha de hoy del sistema, no una fija. Los de «no se guarda nada» cuentan pagos y movimientos antes y después. Los de pagos anulados insertan la fila con sus tres datos de anulación.
  - **Se verifica con** los 32 tests en rojo por el motivo correcto y después en verde, `docs/api/openapi.json` regenerado, y `python tasks.py test`, `lint` y `typecheck` en verde.
- [x] 2.2 Con la skill `backend-feature`, cambiar el saldo de `POST /api/v1/cargos` según el Requirement de `cargos` «Saldo pendiente al registrar», modificado: el Scenario nuevo «La familia ya pagó una parte» (1). Los tests de los otros dos Scenarios ya existen y no se tocan.
  - El paso 8 de `registrar_cargo` lee `v_cuenta_corriente` en lugar de sumar (design, «El cambio en `cargos`»).
  - **Se verifica con** el test nuevo en rojo por el motivo correcto (el saldo da 105000.00) y después en verde; los tests de `cargos` existentes en verde sin tocarlos; `python tasks.py test`, `lint`, `typecheck` y `openapi-check` en verde.

## 3. Ver la cuenta corriente

- [x] 3.1 Con la skill `backend-feature`, construir `GET /api/v1/familias/{familia_id}/cuenta-corriente` en `familias.py`, con el servicio `app/services/cuenta_corriente.py` y los esquemas de `app/schemas/cuenta_corriente.py`, según los Requirements de `cuenta-corriente` «El saldo de la familia es cargos menos pagos» (3 Scenarios), «Ver la cuenta corriente de una familia» (7) y «Solo el Admin ve la cuenta corriente» (5), más el Scenario de `pagos` «El saldo del cargo coincide con la cuenta corriente» (1): 16 Scenarios.
  - Dos consultas y los totales desde la vista, sin sumar en Python (design, «El servicio de la cuenta corriente»). `pagado` y `saldo` de cada cargo con el mismo `pagado_por_cargo()` de la 2.1, no con un subselect propio. `CargoEnCuenta` con exactamente sus catorce campos y `PagoEnCuenta` con tres.
  - El test de «Dos cargos con pagos parciales» tiene un cargo con dos pagos: es el que atrapa un `JOIN` que multiplica el total del cargo.
  - **Se verifica con** los 16 tests en rojo por el motivo correcto y después en verde, incluidos los que comprueban la lista exacta de campos; los tests de `familias` existentes en verde sin tocarlos; `docs/api/openapi.json` regenerado; `python tasks.py test`, `lint` y `typecheck` en verde.

## 4. Contrato

- [x] 4.1 Comprobar que `docs/api/openapi.json` tiene los dos endpoints nuevos con sus esquemas, que `PagoEntrada` tiene solo `monto` (texto) y `fecha_pago` y no admite campos extra, que `CargoEnCuenta` tiene solo sus catorce campos, y que ningún endpoint existente cambió de forma. **Se verifica con** `python tasks.py openapi-check` en verde y el diff de `openapi.json` limitado a lo nuevo (más la descripción de `saldo_pendiente`, si cambió).

## 5. Pantalla «Cuenta corriente»

- [x] 5.1 Con la skill `frontend-feature`, sumar `leerMonto` y `montoParaEditar` a `src/lib/montos.ts`, según design, «Frontend».
  - Casos en `frontend/tests/lib/montos.test.ts`, con los de la lista del design; los casos existentes de `formatearMonto` y `formatearPorcentaje` no se tocan.
  - **Se verifica con** los casos nuevos en rojo por el motivo correcto (no existen las funciones) y después en verde, la huella de `frontend/tests/` intacta, y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.
- [x] 5.2 Con la skill `frontend-feature`, el acceso solo para el Admin: la ruta `/cuenta-corriente` en `App.tsx` dentro de `RutaSoloAdmin` (con una página mínima que la 5.3 completa) y el botón en `Inicio.tsx`, según los Scenarios de `auth` «Ir a la cuenta corriente», «El Coordinador no ve el acceso a cobrar» y «El Profesor no ve el acceso a cobrar» (los dos modificados), y el de `cuenta-corriente` «Coordinador abre la pantalla»: 4 Scenarios.
  - Los dos tests modificados de `frontend/tests/auth/` los corrige el test-writer, que es quien los escribió; el resto de `auth` no se toca.
  - **Se verifica con** los 4 tests en rojo por el motivo correcto y después en verde, la huella de `frontend/tests/` intacta después de implementar, y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.
  - **Hecho (14/11/2026):** «Ir a la cuenta corriente» en rojo por el motivo correcto y después en verde. Los otros tres ya pasaban antes de implementar, porque el comportamiento existía (nadie veía el acceso; una ruta comodín ya llevaba a `/`); se comprobaron con mutaciones: con el botón visible para todos fallan los dos de `auth`, y con la ruta fuera de `RutaSoloAdmin` falla «Coordinador abre la pantalla». Huella intacta; frontend 132 tests y `front-lint` en verde.
- [x] 5.3 Con la skill `frontend-feature`, construir la pantalla `/cuenta-corriente`, según el Requirement de `cuenta-corriente` «Pantalla «Cuenta corriente»», los 6 Scenarios que no son del Coordinador.
  - Las llamadas y sus tipos en `src/lib/api.ts`; `RenglonDeCargo` en `src/components/`; la página en `src/pages/CuentaCorriente.tsx` (design, «Frontend»). Ningún color nuevo. `Registrar pago` puede quedar sin acción: lo completa la 5.4.
  - Tests en `frontend/tests/cuenta-corriente/` con `fetch` fingido. El de «Los montos son los de la API» manda un saldo que no es la resta.
  - **Se verifica con** los 6 tests en rojo por el motivo correcto y después en verde, la huella de `frontend/tests/` intacta después de implementar, los tests de `cargos` y `alumnos` en verde (los dos usan `BuscadorFamilia`), y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.
- [x] 5.4 Con la skill `frontend-feature`, el formulario de pago, según los Requirements de `pagos` «Registrar un pago desde la pantalla» (4 Scenarios) y «Enviar el pago desde la pantalla» (6): 10 Scenarios.
  - Primero, mover `hoyLocal()` de `src/pages/TomarAsistencia.tsx` a `src/lib/fechas.ts`, exportada y sin cambios, y que `TomarAsistencia` la importe de ahí (design, «Frontend»). Los tests de `frontend/tests/asistencia/` no se tocan: son el control de la mudanza.
  - `FormularioPago` en `src/components/`, abierto desde `RenglonDeCargo`, con `Fecha del pago` propuesta con `hoyLocal()`, nunca con `toISOString()`. Después del 201 la página vuelve a pedir la cuenta corriente y no recalcula nada (design, «Frontend»).
  - El test del cuerpo enviado comprueba la lista exacta de claves. El de «Abrir el formulario» compara la fecha con la de hoy del entorno de test, no con una fija. El de «Fecha propuesta a la noche» finge el reloj en el 2027-01-05 a las 21:30 (los tests corren con `TZ=America/Argentina/Buenos_Aires`) y espera `2027-01-05`.
  - **Se verifica con** los 10 tests en rojo por el motivo correcto y después en verde; el de «Fecha propuesta a la noche» en rojo a propósito si la fecha se propone con `toISOString().slice(0, 10)`, y revertido; los tests de asistencia en verde sin tocarlos; la huella de `frontend/tests/` intacta después de implementar; y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.
  - **Hecho (14/11/2026):** los 10 en rojo por el motivo correcto (no se abría ningún diálogo) y después en verde. Con la fecha propuesta con `toISOString().slice(0, 10)` fallan «Fecha propuesta a la noche» y también «Abrir el formulario» (la corrida fue de noche, cuando UTC ya es mañana); revertido. `hoyLocal()` vive en `src/lib/fechas.ts` y la usan asistencia y el formulario; los tests de asistencia, sin tocar, en verde. Fuera del plan: la descripción del cargo se extrajo a `src/lib/descripcionDeCargo.ts` para no duplicarla entre `RenglonDeCargo` y `FormularioPago`. Huella intacta; frontend 148 tests y `front-lint` en verde.

## 6. Comprobación de punta a punta

- [ ] 6.1 Con la base de desarrollo migrada y la semilla cargada, la API y el frontend levantados, comprobar a mano en el navegador:
  - como `lrodriguez` (coordinador) y como `jperez` (profesor), el inicio no muestra `Cuenta corriente` y `/cuenta-corriente` vuelve a `/`;
  - como `mgarcia` (admin), registrar en `/cargos/nuevo` un «Abono» del Mes de Juan, «Mes 1» (con la semilla, $ 67.500) y una «Preinscripción» de Ana ($ 20.000);
  - en `/cuenta-corriente`, «Pérez – Ana» muestra los dos cargos y `Saldo pendiente` `$ 87.500`;
  - pagar `30.000` del Abono con la fecha de hoy: el mensaje dice saldo `$ 57.500` y el renglón `Pagado` `$ 30.000`, `Saldo` `$ 37.500`, con el pago listado;
  - intentar pagar `37.500,01`: el rechazo aparece junto a `Monto` y no se guarda nada;
  - pagar `37.500`: el Abono queda `Saldado` y sin `Registrar pago`;
  - registrar otro cargo para la familia en `/cargos/nuevo` y ver que el saldo del mensaje ya descuenta los pagos;
  - en la base, los dos pagos con su `fecha_pago` y `mgarcia` como autor, y dos ingresos en `tesoreria_movimiento` con los mismos montos y fechas;
  - **la carrera**: con un script de Python en el scratchpad (no en el repo), dos `POST` simultáneos de `"20000.00"` sobre la Preinscripción de Ana (saldo $ 20.000) contra la API de desarrollo: uno 201 y otro 409 o 422, y un solo pago y un solo ingreso en la base;
  - la pantalla y el formulario a 360 px de ancho, sin scroll horizontal, y recorribles con el teclado.
  - **Se verifica con** cada punto anotado como hecho en el informe de la tarea, con lo que haya fallado.
- [ ] 6.2 `python tasks.py test`, `lint`, `typecheck`, `openapi-check`, `front-test` y `front-lint` en verde. **Se verifica con** la salida de cada uno anotada en el informe.

## 7. Revisión adversarial

- [ ] 7.1 Un pase del subagente `adversarial-reviewer` sobre el change terminado, antes del pull request. Rige `REVIEW.md`, «Cuándo se deja de revisar». **Se verifica con** sus hallazgos resueltos o justificados por escrito en esta tarea.

## Workflow follow-up

- Comprobar el change con `/openspec-verify-change` y archivarlo con `/openspec-archive-change`, que crea `openspec/specs/pagos`, `openspec/specs/cuenta-corriente` y `openspec/specs/tesoreria`, y funde los deltas de `cargos` y `auth`.
- HU-CC-02, HU-CC-03 y HU-TES-01 no tienen criterios en `5-historias-de-usuario.md`, así que no hay nada que reemplazar ahí.
- Pull request de `feat/cuenta-corriente` hacia la rama de entrega. Con este change se cierra el lote 1.
