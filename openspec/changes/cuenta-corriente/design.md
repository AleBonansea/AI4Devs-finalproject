# Design

## Context

- `cargo` existe desde el change 6, con el cálculo congelado y `ix_cargo_familia_temporada`. Su servicio devuelve hoy un `saldo_pendiente` que es `sum(monto_total)` de la familia en la temporada, sin pagos (`app/services/cargos.py`, paso 8).
- `pago` y `tesoreria_movimiento` están definidas en `3-modelo-de-datos.md` pero no existen en la base ni en `app/models/`. Tampoco los enumerados `tipo_movimiento` y `origen_movimiento`.
- Hay precedente de vista: `v_familia_etiqueta` vive en un `MetaData` propio (`metadata_vistas`, en `app/models/familia.py`) para que autogenerate no la proponga como tabla, y la migración la crea y la borra con SQL escrito a mano.
- `exigir_rol(ADMIN)` corta antes del cuerpo y de cualquier consulta: un Profesor nunca llega a buscar el cargo ni la familia, así que el 403 no revela si existen. `id_posible` evita que un id fuera de `bigint` dé 500.
- Rechazos atribuibles a un campo: `ReglaIncumplida` → 422 con `loc` y `type` `regla_de_negocio` (spec `errores-de-la-api`). Un validador de Pydantic que levanta `PydanticCustomError("regla_de_negocio", …)` pasa su mensaje intacto (precedente: la fecha de nacimiento en `app/schemas/alumnos.py`).
- En el frontend ya existen `RutaSoloAdmin`, `BuscadorFamilia`, `formatearMonto`/`formatearPorcentaje` y `formatearFecha`, y el criterio de «solo vale la última respuesta» de `RegistrarCargo` y asistencia.
- Ver proposal.md para el porqué y el alcance; las reglas observables están en las specs de `pagos`, `cuenta-corriente`, `tesoreria`, `cargos` y `auth`.

## Goals / Non-Goals

**Goals:**
- Una sola definición del saldo de una familia, usada por el registro de cargos, el registro de pagos y la cuenta corriente.
- Nunca dos pagos que juntos superen el total del cargo, tampoco si llegan a la vez.
- El pago y su ingreso en tesorería, juntos o ninguno.

**Non-Goals:**
- La vista `v_tesoreria_saldo` (llega con la pantalla, HU-TES-03).
- `cierre_canon_id` en `tesoreria_movimiento` (llega con `cierre_canon`).
- Escribir las columnas de anulación de `pago`: existen y se respetan al sumar, nadie las llena.

## Decisions

### Esquema: `pago`, `tesoreria_movimiento` y dos enumerados

Columnas, tipos y nulabilidad según `3-modelo-de-datos.md`, «`pago`» y «`tesoreria_movimiento`». Los dos con `MarcaDeCreacion` (`creado_en`), como `cargo`.

**`pago`**

| Restricción | Qué dice |
|---|---|
| FK `fk_pago_cargo`, `fk_pago_registrado_por`, `fk_pago_anulado_por` | Sin cascada. |
| `ck_pago_monto_positivo` | `monto > 0`. |
| `ck_pago_anulacion_completa` | `(anulado_en IS NULL) = (anulado_por IS NULL) AND (anulado_en IS NULL) = (motivo_anulacion IS NULL)`. |
| `ix_pago_cargo` | `(cargo_id)`: la suma de pagos de un cargo y la cuenta corriente. |

- `registrado_en timestamptz NOT NULL DEFAULT now()`. Es distinto de `fecha_pago` (cuándo pagó la familia, lo escribe el Admin) y de `creado_en` (convención de auditoría). Quedan los dos timestamps porque el modelo pide `registrado_en` con nombre de negocio y la convención pide `creado_en` en todas las tablas; tienen el mismo valor.
- **Las columnas de anulación se crean ahora**, vacías: la convención del modelo dice que las columnas «de después» de una tabla de la Entrega 1 nacen nullable para no migrar. Así, además, toda suma de pagos se escribe desde el principio con `anulado_en IS NULL`, y los Scenarios de «un pago anulado no cuenta» se prueban insertando la fila a mano.
- **Alternativa descartada: un `CHECK` o trigger que impida superar el total.** Un `CHECK` no puede mirar otras filas. Un trigger que sume y bloquee el cargo sí garantizaría la regla en la base, pero duplica la lógica del servicio en PL/pgSQL y el modelo ya eligió validarlo en la API con `SELECT … FOR UPDATE` (ver «El servicio»). El servicio es el único que escribe pagos.

**`tesoreria_movimiento`**

| Restricción | Qué dice |
|---|---|
| FK `fk_movimiento_temporada`, `fk_movimiento_pago`, `fk_movimiento_registrado_por` | Sin cascada. |
| `ck_movimiento_monto_positivo` | `monto > 0`. El signo lo da `tipo`. |
| `ck_movimiento_origen` | `(origen = 'pago' AND tipo = 'ingreso' AND pago_id IS NOT NULL) OR (origen = 'anulacion_pago' AND tipo = 'egreso' AND pago_id IS NOT NULL) OR (origen = 'manual' AND tipo = 'egreso' AND descripcion IS NOT NULL AND pago_id IS NULL)`. |
| `uq_movimiento_pago_origen` | `UNIQUE (pago_id, origen)`. Con `pago_id` NULL no choca (los manuales). |
| `ix_movimiento_temporada` | `(temporada_id)`: el saldo de tesorería, después. |

- **`origen` nace con sus cuatro valores**, `canon` incluido. Agregar un valor a un enumerado de Postgres después (`ALTER TYPE … ADD VALUE`) no se puede revertir en un downgrade; crearlo completo ahora sí. Pero mientras no exista `cierre_canon` no hay a qué referenciar, así que `ck_movimiento_origen` **no admite** `canon`: la migración que cree `cierre_canon` agrega la columna y reemplaza el `CHECK` por el de cuatro ramas del modelo. Se anota en la regla de `tesoreria_movimiento` de `3-modelo-de-datos.md`.
- `descripcion varchar(200)`, nullable: obligatoria solo en `manual`.
- Los enumerados nuevos van en `app/models/enums.py` como `TipoMovimiento` y `OrigenMovimiento`, con `TIPO_TIPO_MOVIMIENTO` y `TIPO_ORIGEN_MOVIMIENTO` declarados una vez. Esta migración **sí** crea esos dos tipos.

### La vista `v_cuenta_corriente`: una sola definición del saldo

```sql
CREATE VIEW v_cuenta_corriente AS
SELECT c.familia_id, c.temporada_id,
       sum(c.monto_total)                    AS total_cargos,
       coalesce(sum(p.pagado), 0)            AS total_pagos,
       sum(c.monto_total) - coalesce(sum(p.pagado), 0) AS saldo_pendiente
FROM cargo c
LEFT JOIN (SELECT cargo_id, sum(monto) AS pagado
           FROM pago WHERE anulado_en IS NULL GROUP BY cargo_id) p
       ON p.cargo_id = c.id
GROUP BY c.familia_id, c.temporada_id;
```

- **Los pagos se agregan por cargo antes del `JOIN`.** Un `JOIN` directo de `cargo` con `pago` repetiría el `monto_total` de un cargo por cada pago, y un cargo con dos pagos contaría doble. El Scenario «Dos cargos con pagos parciales» (un cargo con dos pagos y otro con uno) da 105000.00 y no 190000.00 solo si esto está bien.
- La declara `app/models/cuenta_corriente.py` sobre `metadata_vistas` (que se mueve de `familia.py` a `app/models/base.py`, porque ya no es de una sola entidad), igual que `v_familia_etiqueta`.
- Una familia sin cargos en la temporada no tiene fila: quien la consulta usa `coalesce(…, 0)` y cuantiza a dos decimales.
- La usan tres lugares: el paso final de `registrar_cargo` (reemplaza la suma de hoy), `registrar_pago` y la cuenta corriente. Es la que va a usar el reporte de deudas (HU-CC-04).
- **Alternativa descartada: la suma escrita en cada servicio.** Es lo que hay hoy en `cargos.py`, y con pagos serían tres copias de la misma resta con el filtro de anulados. La vista la deja en un solo lugar, en la base, como el modelo ya preveía.
- El saldo **de un cargo** (`monto_total − sum(pagos no anulados)`) no va en la vista: se calcula en la consulta de la cuenta corriente y en `registrar_pago`, con el mismo subselect por cargo.

### El servicio de pagos: `app/services/pagos.py`, en un orden fijo

`registrar_pago(sesion, usuario, cargo_id, entrada) -> PagoRegistrado`:

1. **Rol** (`exigir_rol(ADMIN)`): 401, 403. Antes del cuerpo y de buscar el cargo.
2. **Cuerpo** (Pydantic, `extra="forbid"`): formato del monto, monto mayor que cero, fecha obligatoria y no posterior a hoy. Campos desconocidos → 422.
3. **El cargo existe**: `id_posible` y `SELECT … FROM cargo WHERE id = :id FOR UPDATE` → si no, 404 `El cargo no existe.`
4. **Temporada del cargo cerrada** → 409. No es un supuesto: lo dicen las fuentes. Acl. 10 dice que la temporada anterior queda «solo para consulta» y que, si quedó algo pendiente de ella, «lo gestiona el Admin por fuera del sistema». `3-modelo-de-datos.md`, «`temporada`», lo baja a la API: «rechaza cualquier alta o modificación en tablas que cuelgan de ella». Que «no debería quedar deuda al terminar la temporada» (Acl. 6) es una expectativa, no la regla; la regla es la de Acl. 10.
5. **Saldo del cargo**, con `saldo_de_cargos(sesion, [cargo_id])` (ver «Un solo cálculo del saldo de un cargo»). Si es 0 → 409 `El cargo ya está saldado.`; si `monto > saldo` → `ReglaIncumplida` en `monto`.
6. **`INSERT` del pago y de su movimiento**, en la misma sesión: `ingreso`, origen `pago`, `pago_id`, mismo monto, `fecha = fecha_pago`, `temporada_id = cargo.temporada_id`, `registrado_por` el Admin. Un `flush` entre los dos para tener el id del pago.
7. **Saldos de respuesta**, después del `flush`: `saldo_cargo` con `saldo_de_cargos` otra vez (ya ve el pago nuevo dentro de la transacción), y el `saldo_pendiente` de la familia desde `v_cuenta_corriente`. Un solo `commit` al final: si falla cualquier cosa antes, no queda ni pago ni movimiento.

- **Por qué `FOR UPDATE` sobre el cargo y en el paso 3**: dos pagos simultáneos del mismo cargo pasarían los dos la comprobación del paso 5 si se leyera sin bloquear. Con la fila del cargo bloqueada, el segundo espera al `commit` del primero y, al seguir, su suma ya ve el primer pago. Se bloquea el cargo y no los pagos porque el primer pago de un cargo no tiene ninguna fila de pago que bloquear. Es lo que dice el modelo.
- **409 de saldado vs. 422 de monto**: con saldo cero ningún monto sirve, así que no es un error del campo y la pantalla no tendría qué corregir; con saldo positivo, el monto es lo que hay que cambiar.
- **Por qué `saldo_cargo` se vuelve a consultar y no se resta en Python** (`saldo − monto`): una resta propia sería un segundo cálculo del saldo de un cargo, que puede divergir del de la cuenta corriente. Una consulta más, con el cargo ya bloqueado, cuesta menos que esa divergencia.

### Un solo cálculo del saldo de un cargo

- El saldo de un cargo (`monto_total − coalesce(sum(monto), 0)` de sus pagos con `anulado_en IS NULL`) se necesita en dos lugares: `registrar_pago` (pasos 5 y 7) y la cuenta corriente (`pagado` y `saldo` de cada cargo). Si cada uno escribiera su consulta, podrían divergir: uno olvida el filtro de anulados o suma con un `JOIN` que multiplica.
- Vive en un solo lugar, `app/services/cuenta_corriente.py`: un subselect `pagado_por_cargo()` (`cargo_id`, `sum(monto)` de los no anulados, agrupado) y `saldo_de_cargos(sesion, cargo_ids) -> dict[int, Decimal]` sobre él. `registrar_pago` usa `saldo_de_cargos`; la consulta de la cuenta corriente hace `LEFT JOIN` al mismo subselect. `v_cuenta_corriente` repite la agregación en SQL, porque una vista no puede llamar a Python; el Scenario «El saldo del cargo coincide con la cuenta corriente» y los de saldo de la familia atan los tres.
- El Scenario usa un cargo con dos pagos previos y montos con centavos (85000.00 − 30000.00 − 12345.50 − 10000.25 = 32654.25), así que una resta que pierde un pago o los centavos no coincide de casualidad.
- **La fecha de hoy** es `date.today()` del servidor, como la fecha de nacimiento del alta. Ver «Risks / Trade-offs».

### El servicio de la cuenta corriente: `app/services/cuenta_corriente.py`

`obtener_cuenta_corriente(sesion, familia_id) -> CuentaCorriente`:

1. `id_posible` y la familia existe → si no, 404 `La familia no existe.`, el mismo texto que las inscripciones.
2. Temporada vigente.
3. Una consulta de los cargos de la familia en esa temporada con `JOIN` a `alumno` (nombre, apellido), `tipo_cargo` (nombre), `LEFT JOIN` a `inscripcion` (turno) y a `periodo_cobro` (nombre y fechas), y `LEFT JOIN` a `pagado_por_cargo()` para `pagado` y `saldo` (el mismo subselect que usa `registrar_pago`). Orden `creado_en, id`.
4. Una consulta de los pagos no anulados de esos cargos, por `fecha_pago, id`, agrupados en Python por cargo. Dos consultas en total, no una por cargo.
5. Totales desde `v_cuenta_corriente`, con `coalesce` a 0.

- **Los montos no se suman en Python**: `pagado` sale del subselect y los totales de la vista. Así el `saldo_pendiente` de la consulta es exactamente el mismo número que devuelve el registro de un cargo o de un pago.
- Solo para el Admin: no hay filtro por grupo en ninguna consulta, porque el Profesor no llega.

### Rutas y roles

| Ruta | Roles | Profesor |
|---|---|---|
| `POST /api/v1/cargos/{cargo_id}/pagos` → 201 `PagoRegistrado` | Admin | 403 por `exigir_rol`, antes de buscar el cargo: no revela si existe. |
| `GET /api/v1/familias/{familia_id}/cuenta-corriente` → 200 `CuentaCorriente` | Admin | Ídem. |

- **El pago cuelga del cargo** (`/cargos/{id}/pagos`) porque es de un cargo y no de la familia: así el cuerpo no repite el `cargo_id` y el 404 es del recurso de la URL.
- **La cuenta corriente cuelga de la familia**, junto a `/familias/{id}/inscripciones`, que tiene los mismos roles y el mismo 404.
- **El monto del pago viene del cuerpo, y está bien.** La regla «el precio nunca viene del cliente» protege el precio de un cargo, que calcula la API. El pago es lo que la familia entregó: solo el Admin lo sabe. La API lo acota (positivo, dos decimales, no más que el saldo). Se aclara la redacción de esa regla en CLAUDE.md para que un revisor no la lea como «ningún endpoint acepta un importe».

### Esquemas

- `PagoEntrada` (`extra="forbid"`): `monto: str` y `fecha_pago: date`.
  - `monto` se valida con `^\d{1,10}(\.\d{1,2})?$` y se convierte a `Decimal` cuantizado a centavos; un número JSON no es un `str` y cae en el mismo error. Se pide texto, igual que lo que devuelve la API, para que un centavo nunca pase por un `float` en ningún lado del contrato. Con el patrón cumplido, `0`/`0.00` → `Tiene que ser mayor que cero.`; si no, `Tiene que ser un monto con hasta dos decimales.` Los dos como `PydanticCustomError("regla_de_negocio", …)`.
  - `fecha_pago > date.today()` → `La fecha del pago no puede ser posterior a hoy.`, igual.
  - Diez cifras enteras es lo que cabe en `numeric(12,2)`; más que eso nunca pasaría el saldo, pero así no llega a Postgres.
- `PagoRegistrado`: `id`, `cargo_id`, `monto`, `fecha_pago`, `registrado_por`, `registrado_en`, `saldo_cargo`, `saldo_pendiente`.
- `CuentaCorriente`: `familia_id`, `etiqueta`, `categoria`, `total_cargos`, `total_pagado`, `saldo_pendiente`, `cargos: list[CargoEnCuenta]`.
- `CargoEnCuenta`: exactamente los catorce campos de la spec. `periodo: PeriodoDeCargo | None` con `nombre`, `fecha_desde`, `fecha_hasta`; `pagos: list[PagoEnCuenta]` con exactamente `id`, `monto`, `fecha_pago`. Nada del alumno más que nombre y apellido, para que nada médico se cuele cuando lleguen esas columnas.
- `CargoRegistrado.saldo_pendiente` no cambia de tipo; cambia lo que significa, y su comentario.

### El cambio en `cargos`

- El paso 8 de `registrar_cargo` cambia el `SELECT sum(monto_total)` por la fila de `v_cuenta_corriente` de la familia y la temporada. Nada más del servicio cambia.
- Los dos Scenarios existentes siguen valiendo (no tienen pagos). El nuevo, «La familia ya pagó una parte», distingue los dos errores plausibles: ignorar los pagos (105000.00) y contar el anulado (97000.00).

### Frontend

- **`src/lib/api.ts`**: tipos `PagoEntrada`, `PagoRegistrado`, `CuentaCorriente`, `CargoEnCuenta`, `PagoEnCuenta`, con los montos como `string`; funciones `cuentaCorriente(familiaId)` y `registrarPago(cargoId, entrada)`.
- **`src/lib/montos.ts`** suma dos funciones, sin `Number` ni `parseFloat`:
  - `montoParaEditar("55000.00")` → `55.000`; `"4462.50"` → `4.462,50`; `"0.05"` → `0,05`. Es `formatearMonto` sin el `$ `: lo que se propone en el campo.
  - `leerMonto(texto)` → el texto de la API o `null`. Admite espacios alrededor, miles con punto en grupos de tres y hasta dos decimales con coma: `55.000` → `"55000.00"`, `55000` → `"55000.00"`, `4.462,50` → `"4462.50"`, `4462,5` → `"4462.50"`, `0,01` → `"0.01"`. Devuelve `null` para `4,462.50`, `4462.50` (el punto es de miles), `44.62`, `1.2345`, `4462,505`, `-10`, `abc` y el texto vacío.
  - Tests en `frontend/tests/lib/montos.test.ts`, que ya existe: el test-writer suma los casos.
- **`src/lib/nombres.ts`**: nada nuevo; turnos y categorías ya están.
- **`src/components/RenglonDeCargo.tsx`**: un cargo de la cuenta corriente. Descripción (`Abono · Mes 1`, `Abono · Día 08/01/2027`, `Preinscripción`) y a quién (`Juan Pérez · Mañana`, o solo `Ana Pérez` si no hay turno), `Total`, `Pagado` y `Saldo` con `formatearMonto`, la lista de pagos (`02/11/2026 · $ 30.000`), y `Registrar pago` o `Saldado`. `Saldado` con el color `saldado` de `tema.ts`; el saldo de un cargo con deuda, con `dinero`. Ningún color nuevo. «Saldado» se decide por `saldo === "0.00"`, una comparación de texto, no una cuenta.
- **`hoyLocal()` pasa a `src/lib/fechas.ts`.** Hoy vive privada en `src/pages/TomarAsistencia.tsx`: arma `AAAA-MM-DD` con `getFullYear`/`getMonth`/`getDate`, la fecha **local** del dispositivo. Se mueve sin cambios a `fechas.ts`, exportada, y la usan `TomarAsistencia` y `FormularioPago`. **Nunca** `new Date().toISOString().slice(0, 10)`: da la fecha de UTC, y a las 21:30 en Argentina ya es el día siguiente. Es el hallazgo grave del pase adversarial de asistencia; una sola función evita que el formulario de pago lo repita. Los tests ya corren con `TZ=America/Argentina/Buenos_Aires` (`vite.config.ts`), así que el Scenario «Fecha propuesta a la noche», con el reloj fingido a las 21:30 del 05/01/2027, falla con `toISOString`. Los tests de `frontend/tests/asistencia/` no se tocan: son el control de que mover la función no cambió asistencia.
- **`src/components/FormularioPago.tsx`**: un `Dialog` de MUI con el cargo, `Saldo del cargo`, `Monto` (texto, propuesto con `montoParaEditar(saldo)`), `Fecha del pago` (`type="date"`, propuesta con `hoyLocal()`) y `Registrar pago` / `Cancelar`. Valida con `leerMonto` antes de enviar; los errores por campo de la API van junto a cada campo, como en el alta. Recibe el cargo y un `alRegistrar(pago)`.
- **`src/pages/CuentaCorriente.tsx`** en `/cuenta-corriente`, dentro de `RutaSoloAdmin`:
  - `BuscadorFamilia` arriba. Al elegir, pide la cuenta corriente; cada pedido lleva un número y se descarta la respuesta que no sea del último (mismo criterio que `RegistrarCargo`).
  - Con la respuesta: categoría con `NOMBRE_DE_LA_CATEGORIA`, `Saldo pendiente` y un `RenglonDeCargo` por cargo, o `La familia no tiene cargos en la temporada.`
  - Al registrar un pago: cierra el diálogo, muestra `Pago registrado por $ M. Saldo pendiente de la familia: $ S.` y vuelve a pedir la cuenta corriente. **No** actualiza los números a mano con la respuesta del pago: eso sería restar en el cliente.
- Ruta en `App.tsx`; acceso `Cuenta corriente` en `Inicio.tsx` solo si `usuario.rol === "admin"`, junto a `Registrar cargo`.
- Tests en `frontend/tests/cuenta-corriente/` con `fetch` fingido; el del acceso en `frontend/tests/auth/`. El de «Los montos son los de la API» manda a propósito un saldo que no es la resta, para atrapar una pantalla que calcule.

### Supuestos registrados

Una entrada nueva en `docs/prd/aclaraciones-cliente.md`, «Preguntas abiertas», con referencia a este change:

- **Fecha del pago** (sección 6): ¿la fecha del cobro es la del día en que se registra o la escribe el Admin? Importa porque el cierre de canon suma por `fecha_pago`. **[SUPUESTO]**, decidido con el usuario el 14/11/2026: la escribe el Admin, propuesta con la de hoy; no puede ser posterior a hoy; no tiene límite hacia atrás ni se ata a la temporada, porque se paga por adelantado. Si el cliente prefiere que sea siempre la de hoy, el campo sale del cuerpo y se invierten dos Scenarios.

## Reversibilidad

- **Migración**: `crear_pago_y_tesoreria`, con `--autogenerate` y revisada con la skill `revisar-migracion`. `upgrade`:
  1. crea los tipos `tipo_movimiento` y `origen_movimiento` (autogenerate los emite con la tabla; se revisa que salgan una sola vez y con sus valores en minúscula);
  2. crea `pago` con sus FK, `CHECK` e índice;
  3. crea `tesoreria_movimiento` con sus FK, `CHECK`, el único y el índice;
  4. crea `v_cuenta_corriente` con SQL escrito a mano (autogenerate no ve las vistas).
- **Downgrade**, en el orden inverso: `DROP VIEW v_cuenta_corriente`, `drop_table("tesoreria_movimiento")`, `drop_table("pago")`, y `DROP TYPE` de los dos enumerados, que autogenerate **no** escribe y hay que agregar a mano. No toca `cargo` ni los tipos que ya existían.
- **Filas existentes**: ninguna tabla existente cambia; los cargos ya registrados quedan con saldo igual a su total, que es lo correcto porque no tienen pagos. Bajar la migración con pagos registrados **los pierde, junto con sus ingresos de tesorería**: aceptable solo antes de producción, que es donde se prueba el ida y vuelta.
- **Después del downgrade, el registro de cargos falla**, porque el servicio lee `v_cuenta_corriente`. Bajar esta migración exige volver también el código al del change 6; es el mismo acople que tiene cualquier migración con el código que la usa.
- Se prueba `upgrade head` → `downgrade -1` → `upgrade head` contra la base de pruebas.

## Risks / Trade-offs

- [Dos pagos simultáneos del mismo cargo superan el total] → `SELECT … FOR UPDATE` sobre el cargo. Los tests no lo pueden probar: corren en una sola transacción por test (`conftest.py`) y dos conexiones no se ven. Se comprueba a mano en la tarea de punta a punta, con dos pedidos en paralelo contra la base de desarrollo: uno 201 y otro 422.
- [Un reintento después de un corte de red registra el pago dos veces] → Si el primer pedido llegó y se guardó pero la respuesta se perdió, reenviarlo registra un segundo pago igual, siempre que el saldo del cargo lo permita (si no, el tope del saldo lo rechaza). No hay clave de idempotencia ni índice que lo distinga: dos pagos iguales del mismo cargo el mismo día son legítimos (dos cuotas iguales). Se acepta para el lote 1; el arreglo es la anulación del pago duplicado (HU-CC-06), o una clave de idempotencia por envío si el caso aparece.
- [El saldo de un cargo se calcula distinto en el pago y en la cuenta corriente] → Un solo subselect para los dos (ver «Un solo cálculo del saldo de un cargo») y un Scenario que compara las dos respuestas.
- [El pago se guarda y su ingreso no, o al revés] → Una sola transacción con un solo `commit`. El Scenario «Pago rechazado, sin ingreso» cubre el rechazo antes del `INSERT`; un fallo entre los dos `INSERT` no tiene cómo provocarse desde la API, y la garantía es el `commit` único.
- [«Hoy» es el del servidor] → Si el servidor corre en UTC, entre las 21 y las 24 de Argentina «hoy» ya es mañana y se aceptaría una fecha un día adelantada. Es el mismo criterio que la fecha de nacimiento. Si molesta, se fija la zona `America/Argentina/Buenos_Aires` en una función compartida para los dos; queda fuera de este change porque no lo piden las fuentes y tocaría el alta.
- [Un Admin antedata un pago y lo saca de un cierre de canon ya abonado] → Hoy no hay canon. Cuando llegue, un pago con `fecha_pago` dentro de un rango ya cerrado entra en el próximo cierre, porque la regla de `cierre_canon_pago` es «no incluido en otro cierre», no «fecha en el rango». Se anota para el change del canon.
- [La pantalla muestra un saldo viejo si otro Admin registra un pago en el medio] → Después de cada pago se vuelve a pedir la cuenta corriente; el 422 por saldo superado protege el dato aunque la pantalla esté desactualizada.
- [Bajar la migración rompe el registro de cargos] → Ver «Reversibilidad».
- [Dos timestamps con el mismo valor en `pago` (`registrado_en` y `creado_en`)] → Aceptado: uno es dato de negocio con el nombre del modelo, el otro la convención de auditoría.

## Migration Plan

1. `python tasks.py migrate` aplica `crear_pago_y_tesoreria`. No requiere datos ni pasos manuales; la semilla no cambia.
2. Rollback: `alembic downgrade -1` desde `backend/` y volver el código al change 6, con la pérdida de pagos de «Reversibilidad».
