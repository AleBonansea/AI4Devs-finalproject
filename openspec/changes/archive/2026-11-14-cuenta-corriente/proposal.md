# Proposal

## Why

Es el change 7 y último del «Plan de changes del lote 1». Cubre tres historias del Lote 1: **HU-CC-02** (registrar uno o varios pagos parciales sobre un cargo hasta saldarlo), **HU-CC-03** (ver la cuenta corriente de una familia con sus cargos, pagos y saldo pendiente) y **HU-TES-01** (que cada pago registrado escriba su ingreso en la tesorería, como dato y sin pantalla). El change 6 dejó registrar lo que una familia tiene que pagar, pero todavía no hay forma de asentar lo que paga ni de saber cuánto debe: hoy el «saldo pendiente» que devuelve un cargo es solo la suma de los cargos.

Con este change la espina del dinero queda completa de punta a punta (alumno inscripto → cargo calculado → pagos en cuotas → saldo → ingreso en tesorería), que es el «flujo principal operativo» que pide la Entrega 2. HU-TES-01 entra ahora y no después porque escribir el ingreso al registrar el pago cuesta dos líneas, y generarlo más tarde con una migración sería más riesgoso (backlog, «El dato no es lo mismo que la pantalla»).

## What Changes

- **Esquema de pagos y tesorería.** Las tablas `pago` y `tesoreria_movimiento` de `3-modelo-de-datos.md`, con sus `CHECK`, y los tipos enumerados `tipo_movimiento` y `origen_movimiento`. `pago` nace con las columnas de anulación (`anulado_en`, `anulado_por`, `motivo_anulacion`) vacías y sin uso, como pide la convención del modelo para las columnas «de después»: así HU-CC-06 no tiene que migrar. La vista `v_cuenta_corriente` del modelo, que es la única definición del saldo de una familia. Una migración reversible.
- **Registrar un pago** (`POST /api/v1/cargos/{cargo_id}/pagos`): el Admin dice cuánto recibió (`monto`) y cuándo (`fecha_pago`). La API comprueba que no supere lo que falta pagar del cargo (no hay saldos a favor, Acl. 6), guarda el pago y, **en la misma transacción**, su ingreso en la tesorería (Acl. 7). Responde el pago, el saldo del cargo y el saldo de la familia. Pagos parciales, todos los que hagan falta hasta llegar a cero.
- **Ver la cuenta corriente** (`GET /api/v1/familias/{familia_id}/cuenta-corriente`): los cargos de la familia en la temporada vigente, cada uno con lo pagado, su saldo y sus pagos, más los totales y el saldo pendiente de la familia.
- **El saldo al registrar un cargo descuenta los pagos.** El `saldo_pendiente` que devuelve `POST /api/v1/cargos` pasa a ser cargos menos pagos no anulados; hasta ahora no había pagos y el requisito decía «no se descuenta nada».
- **Permisos:** los dos endpoints nuevos son solo del Admin (Acl. 9: solo los Admin registran cobros; el Coordinador y el Profesor no ven nada contable). Coordinador y Profesor reciben 403.
- **La fecha del pago la escribe el Admin** **[SUPUESTO]**, decidido con el usuario el 14/11/2026 y registrado como pregunta abierta: la pantalla la propone con la fecha de hoy y la API rechaza una fecha posterior a hoy. No tiene límite hacia atrás ni se ata a las fechas de la temporada, porque se paga por adelantado (Acl. 6).
- **El monto del pago sí viene del cliente**, y no contradice la regla «el precio nunca viene del cliente»: lo que la regla protege es el precio de un cargo, que calcula la API. Un pago es un hecho que el Admin informa (cuánto recibió), y la API lo acota por el saldo del cargo. Se aclara la redacción de la regla en CLAUDE.md.
- **Pantalla «Cuenta corriente»** en `/cuenta-corriente`, solo para el Admin: buscar la familia, ver sus cargos con lo pagado, el saldo y los pagos de cada uno, el saldo de la familia, y registrar un pago sobre cualquier cargo con saldo, con el monto propuesto en lo que falta. Una sola pantalla, decidido con el usuario. El acceso desde el inicio aparece solo para el Admin.
- **Leer un monto escrito por una persona** en `src/lib/montos.ts` (`4.462,50` → `"4462.50"`), sin pasar por `Number`, como ya se formatean.

## Capabilities

### New Capabilities

- `pagos`: el pago de un cargo, sus reglas (no supera el saldo, fecha no futura, temporada cerrada), su registro con el ingreso en tesorería, sus permisos y el registro desde la pantalla.
- `cuenta-corriente`: el saldo de una familia por temporada como estado derivado, la consulta de su cuenta corriente con cargos y pagos, sus permisos y la pantalla «Cuenta corriente».
- `tesoreria`: los movimientos de la tesorería de la temporada, sus reglas de forma, y el ingreso que escribe cada pago. Crece después con los egresos (HU-TES-02), la pantalla (HU-TES-03), la anulación (HU-CC-06) y el canon.

### Modified Capabilities

- `cargos`: el «Saldo pendiente al registrar» descuenta los pagos no anulados de la familia en la temporada.
- `auth`: el inicio de la zona protegida suma el acceso `Cuenta corriente`, visible solo para el Admin.

## Fuera de alcance

- **Imputar un pago a varios cargos.** El prototipo reparte un pago entre los cargos más antiguos; el modelo y HU-CC-02 dicen que cada pago es de un cargo. Si la familia paga dos cargos juntos, el Admin registra dos pagos.
- **Anular un pago** (HU-CC-06, Should-have) y su egreso de contraasiento. Las columnas existen, nadie las escribe; un pago anulado (que solo puede aparecer insertado a mano) no cuenta en ningún saldo ni se lista.
- **Anular o modificar un cargo**: sigue sin existir (ver change `cobro`).
- **Reporte de deudas** de todas las familias (HU-CC-04, Should-have): la consulta es de a una familia. La vista `v_cuenta_corriente` queda lista para ese reporte.
- **Pantallas de tesorería**: ver movimientos y saldo (HU-TES-03) y cargar egresos (HU-TES-02). La vista `v_tesoreria_saldo` llega con HU-TES-03.
- **Cierre de canon** (HU-CAN-*): `cierre_canon_id` y su `CHECK` se agregan con la migración que cree `cierre_canon`.
- **Medio de pago, recibos y avisos a las familias** (Acl. 6). El prototipo muestra un campo «Medio» que las aclaraciones eliminaron.
- **Saldos a favor y devoluciones** (Acl. 6): un pago que supera el saldo del cargo se rechaza.
- **Cuenta corriente de temporadas anteriores** (HU-UT-05, Backlog): la consulta es de la temporada vigente.
- **Pagos de ejemplo en la semilla.** La semilla no cambia.

## Impact

- **Backend:** modelos `Pago` y `TesoreriaMovimiento` y la vista `v_cuenta_corriente` en `app/models/`, los enumerados nuevos en `enums.py`, una migración en `alembic/versions/`, servicios `app/services/pagos.py` y `app/services/cuenta_corriente.py`, esquemas en `app/schemas/`, una ruta en `cargos.py` y otra en `familias.py`. `app/services/cargos.py` cambia la suma del saldo por la vista.
- **Contrato:** dos endpoints nuevos; la descripción de `saldo_pendiente` en `CargoRegistrado` cambia de significado, no de forma. `docs/api/openapi.json` regenerado.
- **Frontend:** llamadas y tipos en `src/lib/api.ts`, `leerMonto` y `montoParaEditar` en `src/lib/montos.ts`, la página `src/pages/CuentaCorriente.tsx`, piezas nuevas en `src/components/`, la ruta en `App.tsx` y el acceso en `Inicio.tsx`.
- **Documentación:** la pregunta abierta «Fecha del pago» en `docs/prd/aclaraciones-cliente.md`; la redacción de «El precio nunca viene del cliente» en CLAUDE.md; en `3-modelo-de-datos.md`, la nota del `CHECK` de `origen` mientras no exista `cierre_canon`.
