# Design

## Context

- El tarifario existe desde el change 2 (`tarifa_base`, `descuento_modalidad`, `descuento_mes`, `periodo_cobro`, `tipo_cargo`) y la semilla lo llena. `periodo_cobro` ya tiene `UNIQUE (id, modalidad)`, que es la clave a la que apunta la FK compuesta de `cargo`. Los montos se leen como `Decimal`.
- `familia.categoria` e `inscripcion (alumno_id, temporada_id, turno)` existen desde el change 4. Un alumno está a lo sumo en una inscripción por turno y temporada, así que contar inscripciones de la familia en un turno es contar hijos.
- El alta de alumnos fijó cómo se rechaza una regla atribuible a un campo: `ReglaIncumplida`, que sale como 422 con `loc` en el campo y `type` `regla_de_negocio`, todos los errores juntos (spec `errores-de-la-api`). El grupo de una temporada cerrada es ahí un 422 en `grupo_id`, no un 409.
- `exigir_rol(...)` corta antes del cuerpo y de cualquier consulta. Un endpoint solo de Admin no necesita filtro por grupo: el Profesor nunca llega a la consulta.
- `4-especificaciones-de-la-api.md` (Entrega 1) documentó `POST /api/v1/cargos` con el recorte de 3 endpoints. Este change sigue su cuerpo y su respuesta, con los desvíos explicados abajo.
- Ver proposal.md para el porqué y el alcance; las reglas observables están en las specs de `cargos`, `familias` y `auth`.

## Goals / Non-Goals

**Goals:**
- Un solo lugar para el cálculo, sin acceso a la base, probado con montos que separan el resultado correcto del plausible.
- El mismo número en la simulación, en el registro y en el `CHECK` de la base: el redondeo de Python y el de Postgres coinciden.
- Un cargo repetido no entra nunca, tampoco con dos pedidos simultáneos.

**Non-Goals:**
- La vista `v_cuenta_corriente` y los pagos: llegan con el change 7. El saldo de este change es una suma en la consulta.
- Integridad entre tablas por FK compuestas (alumno ↔ familia, inscripción ↔ temporada): la valida el servicio, que es el único que escribe cargos. Ver «Esquema».

## Decisions

### Esquema: la tabla `cargo` del modelo, más tres índices únicos parciales

Columnas, tipos y nulabilidad según `3-modelo-de-datos.md`, «`cargo`». Con `MarcaDeCreacion` (`creado_en`), porque en una cuenta corriente el orden de los asientos importa. Reusa los tipos enumerados `modalidad` y `categoria_familia`; la migración no los crea.

| Restricción | Qué dice |
|---|---|
| FK `fk_cargo_temporada`, `fk_cargo_familia`, `fk_cargo_alumno`, `fk_cargo_tipo_cargo`, `fk_cargo_inscripcion`, `fk_cargo_creado_por` | Sin cascada. |
| FK `fk_cargo_periodo_cobro` `(periodo_cobro_id, modalidad)` → `periodo_cobro (id, modalidad)` | El período es de la modalidad del cargo. |
| `ck_cargo_monto_fijo_sin_abono` | `modalidad IS NOT NULL OR (inscripcion_id, periodo_cobro_id, fecha_dia, cantidad_hijos_aplicada todos NULL)`. Hace falta porque la FK compuesta es `MATCH SIMPLE`: con `modalidad` NULL no comprueba el período. |
| `ck_cargo_abono_con_inscripcion` | `modalidad IS NULL OR inscripcion_id IS NOT NULL`. |
| `ck_cargo_periodo_o_fecha` | Día: fecha y sin período; Mes, Quincena y Semana: período y sin fecha. |
| `ck_cargo_hijos_solo_mes` | `(modalidad IS NOT DISTINCT FROM 'mes') = (cantidad_hijos_aplicada IS NOT NULL)`. Con `=` a secas, una modalidad NULL daría NULL y el `CHECK` pasaría. |
| `ck_cargo_hijos_positivo` | `cantidad_hijos_aplicada >= 1`. |
| `ck_cargo_monto_base_positivo` | `monto_base > 0`. La tarifa y el monto fijo ya lo son; esto lo fija en el cargo. |
| `ck_cargo_porcentaje_rango` | `porcentaje_aplicado BETWEEN 0 AND 100`. |
| `ck_cargo_total` | `monto_total = round(monto_base * (1 - porcentaje_aplicado / 100), 2)`. |
| `uq_cargo_inscripcion_periodo` | Único `(inscripcion_id, periodo_cobro_id) WHERE periodo_cobro_id IS NOT NULL`. |
| `uq_cargo_inscripcion_fecha` | Único `(inscripcion_id, fecha_dia) WHERE fecha_dia IS NOT NULL`. |
| `uq_cargo_alumno_tipo_monto_fijo` | Único `(alumno_id, tipo_cargo_id) WHERE modalidad IS NULL`. El tipo es de una temporada, así que es «uno por alumno, tipo y temporada». |
| `ix_cargo_familia_temporada` | `(familia_id, temporada_id)`: la suma del saldo, y después la cuenta corriente. |

- **Los repetidos, en índices y no solo en el servicio.** Comprobarlo con un `SELECT` antes de insertar deja pasar dos pedidos simultáneos (el doble clic que motivó la regla). El servicio igual consulta antes, para responder el 409 con su mensaje y para que la simulación avise; el índice es el que garantiza. Un `IntegrityError` de esos tres nombres se traduce al mismo 409.
- **Cuando llegue la anulación de cargos**, los tres índices suman `AND anulado_en IS NULL` a su `WHERE`. Queda anotado en la regla de `3-modelo-de-datos.md`.
- **Alternativa descartada: FK compuestas para la coherencia entre tablas** (`(alumno_id, familia_id)` → `alumno`, `(inscripcion_id, temporada_id)` → `inscripcion`, `(tipo_cargo_id, temporada_id)` → `tipo_cargo`). Exigen `UNIQUE` nuevos en tres tablas existentes y, en el caso de la familia, bloquearían mover un alumno de familia si algún día se pide. El servicio es el único que escribe cargos y lo comprueba.

### El cálculo, en `app/services/calculo_cargo.py`, como función pura

```
TablaDescuentos(por_modalidad: Mapping[(categoria, modalidad), Decimal], mes: Mapping[(categoria, tramo), Decimal])
Desglose(categoria_aplicada, cantidad_hijos_aplicada: int | None, monto_base, porcentaje_aplicado, monto_total)

calcular_abono(tarifa_base, categoria, modalidad, cantidad_hijos: int | None, descuentos) -> Desglose
calcular_monto_fijo(monto_fijo, categoria) -> Desglose
FaltaDescuento(categoria, modalidad, tramo | None)   # excepción
```

- **Qué decide la función**: qué celda de la tabla corresponde (`mes[(categoria, min(hijos, 4))]` o `por_modalidad[(categoria, modalidad)]`), que hay un solo porcentaje, y el redondeo. Es donde vive el riesgo, así que es lo que se prueba sin base.
- **Qué no decide**: cuántos hijos hay ni cuál es la tarifa base. Los cuenta y la lee el servicio, que es quien toca la base. Si falta la tarifa, el servicio responde antes de llamar a la función.
- `cantidad_hijos` es obligatoria en el Mes (menor que 1 o None da `ValueError`: es un error de programación, no del usuario) y se ignora en las demás modalidades; el desglose la devuelve solo en el Mes.
- **El redondeo**: `(tarifa * (100 - porcentaje) / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)`. Es exactamente lo que calcula el `CHECK`: un porcentaje con dos decimales dividido por 100 es exacto en `numeric`, y `round()` de Postgres redondea la mitad alejándose de cero, que para montos positivos es `ROUND_HALF_UP`. El redondeo por defecto de Python (`ROUND_HALF_EVEN`) daría 500.02 donde la base exige 500.03, y el insert fallaría con 500: el Scenario «Medio centavo se redondea hacia arriba» lo atrapa pasando por la base.
- **Se persiste del cálculo**: `categoria_aplicada`, `cantidad_hijos_aplicada` (solo Mes), `monto_base`, `porcentaje_aplicado` y `monto_total`, además de qué se cobró (tipo, inscripción, modalidad, período o fecha). Con eso un cargo se explica solo, aunque el tarifario cambie.
- Tests de la función pura en `backend/tests/functional/cargos/test_calculo_cargo.py`, con la tabla de HU-CC-01:
  - empleado, Mes, 1 / 2 / 3 hijos → 10 / 15 / 20 %; no socio con 4 y con 7 hijos → tramo 4;
  - empleado, Semana, con 1 y con 3 hijos → el mismo 10 %, y `cantidad_hijos_aplicada` None;
  - socio con todo en 50 → 50000.00, no 25000.00;
  - 1000.05 al 50 % → 500.03; 100000.00 al 36.25 % → 63750.00;
  - celda faltante → `FaltaDescuento` con categoría y tramo; monto fijo → porcentaje 0.00 para las tres categorías;
  - Mes sin cantidad de hijos → `ValueError`.

### El servicio: `app/services/cargos.py`, con las reglas en un orden fijo

Una función `preparar_cargo(sesion, entrada)` que hace los pasos 1 a 6 y devuelve el desglose más lo que hace falta para guardar; `simular_cargo` la llama y responde; `registrar_cargo` la llama, inserta y suma el saldo. Así simulación y registro no pueden divergir.

1. **Rol** (dependencia `exigir_rol(ADMIN)`): 401, 403.
2. **Cuerpo** (Pydantic, `extra="forbid"`): tipos y campos desconocidos. Un `monto_total` en el cuerpo da 422 aquí: el esquema no tiene dónde ponerlo.
3. **Alumno y tipo de cargo existen**, con `id_posible` para los ids fuera de `bigint`. Se juntan los dos errores. Si alguno falta, se responde: sin tipo no se sabe qué forma pedir.
4. **Temporada del tipo cerrada**: 422 en `tipo_cargo_id`, y se responde.
5. **Forma y referencias**, juntando todos los errores en un `ReglaIncumplida`:
   - monto fijo: cada uno de `inscripcion_id`, `modalidad`, `periodo_cobro_id`, `fecha_dia` presente es un error; el alumno tiene que tener alguna inscripción en la temporada;
   - tarifario: `inscripcion_id` y `modalidad` obligatorios; la inscripción existe, es del alumno y de la temporada; según la modalidad, período (existe, de la temporada, de esa modalidad) o fecha (dentro de la temporada), y el otro ausente.
6. **Repetido**: un `SELECT exists` con la misma condición del índice que corresponda → 409.
7. **Cálculo**: categoría de la familia del alumno; si es Mes, `SELECT count(DISTINCT alumno.id) FROM inscripcion JOIN alumno … WHERE alumno.familia_id = :f AND inscripcion.temporada_id = :t AND inscripcion.turno = :turno`; tarifa base (si falta, 409); la tabla de descuentos de la temporada (21 filas a lo sumo) y la función pura (`FaltaDescuento` → 409).
8. **Solo al registrar**: `INSERT`, `flush`; un `IntegrityError` de los índices únicos → el 409 del paso 6. Después `SELECT sum(monto_total) FROM cargo WHERE familia_id = :f AND temporada_id = :t`, cuantizado a dos decimales.

- **Por qué el 409 de repetido va antes que el de configuración**: si el cargo ya existe, avisar que falta una tarifa empujaría a cargarla para después chocar con el repetido.
- **Mensajes con texto para personas**: turno `mañana` / `tarde`; modalidad `Mes`, `Quincena`, `Semana`, `Día`; categoría `socio`, `empleado`, `no socio`; tramo 4 como `con 4 o más hijos`; fechas en `DD/MM/AAAA`. Los textos exactos están en la spec.
- Un inscripto en un grupo inactivo cuenta como hijo: la inscripción existe y el grupo inactivo conserva sus datos. Hoy no hay forma de desactivar un grupo.

### Rutas y roles

| Ruta | Roles | Profesor |
|---|---|---|
| `POST /api/v1/cargos` → 201 `CargoRegistrado` | Admin | 403 por `exigir_rol`, antes de leer nada. |
| `POST /api/v1/cargos/simulacion` → 200 `CargoSimulado` | Admin | Ídem. |
| `GET /api/v1/cargos/opciones` → 200 `OpcionesDeCargo` | Admin | Ídem. |
| `GET /api/v1/familias/{familia_id}/inscripciones` → 200 `list[InscripcionDeFamilia]` | Admin | Ídem: el 403 llega antes de buscar la familia, así que no revela si existe. |

- Ningún endpoint de este change devuelve filas a un Profesor, así que no hay filtro por grupo en las consultas. Si un día el Coordinador o el Profesor necesitan las inscripciones de una familia, esa ruta tendrá que filtrar con un `JOIN` a `grupo_profesor`, como `GET /api/v1/grupos`.
- **Desvíos de `4-especificaciones-de-la-api.md`:**
  - `POST /api/v1/cargos/simulacion` en lugar de `?simular=true`: aquel era una concesión al límite de 3 endpoints. Un endpoint aparte tiene su propio `response_model` y su propio código (200), en lugar de un endpoint con dos formas de respuesta. Es `POST` y no el `GET` que proponía aquel documento porque lleva el mismo cuerpo que el registro; con parámetros de consulta habría que duplicar el esquema.
  - Las referencias inexistentes y las incoherencias son 422 por campo, no 404 ni `detail` de texto, y la temporada cerrada es 422 en `tipo_cargo_id`: es lo que ya hacen el alta de alumnos y la spec `errores-de-la-api`, y deja que la pantalla pegue cada error junto a su campo.
  - El 403 dice `No tenés permiso para esta operación.`, el de `exigir_rol`, y no un texto propio.
- Las dos rutas de apoyo existen porque la pantalla las necesita y ninguna existente sirve: `GET /api/v1/familias` devuelve solo id, etiqueta y categoría (a propósito, porque la usa el Profesor), y no hay forma de leer los tipos y períodos.

### Esquemas

- `CargoEntrada` (`extra="forbid"`): `alumno_id: int`, `tipo_cargo_id: int`, `inscripcion_id: int | None`, `modalidad: Modalidad | None`, `periodo_cobro_id: int | None`, `fecha_dia: date | None`. Ningún campo de dinero.
- `CargoSimulado`: `familia_id`, `categoria_aplicada`, `cantidad_hijos_aplicada`, `monto_base`, `porcentaje_aplicado`, `monto_total`.
- `CargoRegistrado`: lo de la tabla (`id`, `temporada_id`, `familia_id`, `alumno_id`, `tipo_cargo_id`, `inscripcion_id`, `modalidad`, `periodo_cobro_id`, `fecha_dia`, el desglose, `creado_por`, `creado_en`) más `saldo_pendiente`.
- `OpcionesDeCargo { tipos_cargo: [{id, nombre, calculo, monto_fijo}], periodos: [{id, modalidad, nombre, fecha_desde, fecha_hasta}] }`. Períodos por `modalidad` (el orden del enumerado: mes, quincena, semana), `fecha_desde` e `id`.
- `InscripcionDeFamilia { inscripcion_id, alumno_id, nombre, apellido, turno, grupo }`: solo esos seis campos, para que nada médico se cuele cuando lleguen esas columnas.
- Montos y porcentajes como `Decimal`: Pydantic v2 los serializa como texto en JSON, con la escala que traen. Todo valor que sale ya tiene dos decimales (las columnas son `numeric(_, 2)` y la función cuantiza); el saldo se cuantiza a mano porque `sum()` sobre una lista vacía daría `0` sin decimales.

### Frontend

- **`src/lib/api.ts`**: tipos `CargoEntrada`, `CargoSimulado`, `CargoRegistrado`, `OpcionesDeCargo`, `InscripcionDeFamilia`, con los montos como `string`, nunca `number`; funciones `opcionesDeCargo()`, `inscripcionesDeFamilia(familiaId)`, `simularCargo(entrada)`, `registrarCargo(entrada)`.
- **`src/lib/montos.ts`** (regla nueva de CLAUDE.md, sección Frontend, como `fechas.ts`): todo monto o porcentaje que se muestra pasa por aquí. Trabaja sobre el texto que manda la API, sin `Number` ni `parseFloat`, para que un centavo nunca se pierda en un `float`.
  - `formatearMonto("85000.00")` → `$ 85.000`; `"4462.50"` → `$ 4.462,50`; `"500.03"` → `$ 500,03`; `"1000000.00"` → `$ 1.000.000`; `"0.00"` → `$ 0`. Los centavos se muestran solo si no son cero.
  - `formatearPorcentaje("15.00")` → `15 %`; `"36.25"` → `36,25 %`; `"57.50"` → `57,5 %`; `"0.00"` → `0 %`.
  - Un texto que no sea `\d+\.\d{2}` (`"85000"`, `"85000.5"`, `"1e5"`) lanza `Error`: es un error de programación.
  - Test de las funciones puras en `frontend/tests/lib/montos.test.ts`, con esos casos.
- **`src/lib/nombres.ts`** suma `NOMBRE_DE_LA_MODALIDAD` (`Mes`, `Quincena`, `Semana`, `Día`).
- **`src/routes/RutaSoloAdmin.tsx`**: dentro de `RutaProtegida`, deja pasar al Admin y lleva a cualquier otro rol a `/` con `Navigate replace`, antes de montar la página, así que no se dispara ningún pedido. Sirve después para tesorería y canon.
- **`src/components/BuscadorFamilia.tsx`**: el `Autocomplete` por apellido que hoy vive dentro de `SelectorFamilia` (2 caracteres, 300 ms, `Pérez – Ana` como etiqueta), sacado con nombre propio. `SelectorFamilia` pasa a usarlo y los tests de `frontend/tests/alumnos/` no se tocan: son el control de que la extracción no cambió nada.
- **`src/components/DesgloseCargo.tsx`**: recibe el `CargoSimulado`, el turno y la modalidad, y pinta los renglones (`Tarifa base · Mañana · Mes`, `Descuento Empleado · 2 hijos en el turno` o `Descuento Empleado · Semana`, o `Monto fijo` y `Sin descuento`) y `Total del cargo` con el color `dinero` de `tema.ts`. No calcula: el descuento se muestra como porcentaje, no como un monto restado, porque restar sería calcular en el cliente.
- **`src/pages/RegistrarCargo.tsx`** en `/cargos/nuevo`, dentro de `RutaSoloAdmin`:
  - Al montar pide las opciones. Al elegir familia pide sus inscripciones y muestra la categoría con `NOMBRE_DE_LA_CATEGORIA`.
  - `Alumno y turno` es un `TextField select` de inscripciones (`Juan Pérez · Mañana`); `Tipo de cargo`, `Modalidad` y `Período` también. `Período` filtra por la modalidad y escribe las fechas con `formatearFecha`. `Fecha` es `type="date"`.
  - Cuando el cargo está completo, pide la simulación. Cada pedido lleva un número; al llegar, se descarta si no es el último (mismo criterio que la apertura de asistencia y `SelectorGrupo`). Cambiar cualquier campo borra el desglose y los errores de la simulación anterior.
  - Cambiar `Tipo de cargo` o `Modalidad` vacía los campos que dejan de corresponder, para no mandar un `periodo_cobro_id` con una Preinscripción.
  - `Registrar cargo` habilitado solo con desglose del cargo actual y sin pedido en curso. Manda la misma `CargoEntrada` que se simuló. Al 201, `Alert` de éxito con `formatearMonto(saldo_pendiente)` y vuelve a vacío todo menos la familia. Los errores se muestran como en el alta: el `mensaje` del `ErrorDeApi` en un `Alert` y los errores por campo junto a cada campo.
- Ruta en `App.tsx`; acceso `Registrar cargo` en `Inicio.tsx` solo si `usuario.rol === "admin"`.
- Tests en `frontend/tests/cargos/` con `fetch` fingido, como asistencia. El test de «solo vale el último» controla el orden en que se resuelven las dos promesas.

### Supuestos registrados

Tres entradas nuevas en `docs/prd/aclaraciones-cliente.md`, «Preguntas abiertas», con referencia a este change:

- **Cargos repetidos**: el mismo Abono (inscripción y período, o inscripción y fecha) y el mismo cargo de monto fijo por alumno y temporada se rechazan. Decidido con el usuario el 14/11/2026, porque sin anulación de cargos un duplicado no tiene corrección. Si el cliente pide permitirlos, primero hace falta la anulación.
- **Cargo de un alumno sin inscripción**: todo cargo exige que el alumno esté inscripto en la temporada, también la Preinscripción, que no lleva inscripción. Si el cliente cobra la Preinscripción antes de inscribir, se borra una comprobación y se invierte un Scenario.
- **Fecha del cargo del Día**: tiene que caer dentro de la temporada, como la asistencia.

## Reversibilidad

- **Migración**: `crear_cargo`, con `--autogenerate` y revisada con la skill `revisar-migracion`. `upgrade` crea la tabla con sus siete FK, sus `CHECK`, los tres índices únicos parciales y el índice por familia y temporada. **No crea tipos enumerados**: `modalidad` y `categoria_familia` existen; autogenerate tiende a emitir `CREATE TYPE` para un `Enum` en una tabla nueva, y hay que verificar que no lo haga (el objeto compartido de `enums.py` ya lo evitó en `asistencia`, pero se revisa igual). También hay que comprobar que los índices parciales salgan con su `postgresql_where`, que autogenerate a veces pierde.
- **Downgrade**: borra los índices y `op.drop_table("cargo")`, que se lleva FK y `CHECK`. No toca los tipos enumerados ni las tablas del tarifario, de familias o de alumnos.
- **Filas existentes**: ninguna tabla existente cambia, así que no hay datos que migrar. Bajar la migración con cargos registrados **los pierde**: es aceptable solo antes de producción, que es donde se prueba el ida y vuelta.
- Se prueba `upgrade head` → `downgrade -1` → `upgrade head` contra la base de pruebas.

## Risks / Trade-offs

- [El redondeo de Python y el de Postgres divergen y un cargo legítimo da 500] → Mismo método en los dos lados (`ROUND_HALF_UP` y `round()`), y el Scenario del medio centavo pasa por la base. Los montos son positivos, así que «alejarse de cero» y «hacia arriba» coinciden.
- [La simulación y el registro dan números distintos si el tarifario cambia en el medio] → El registro recalcula y lo que se guarda es lo que devuelve. En este lote el tarifario solo cambia por la semilla; cuando llegue su ABM, se puede mostrar el total registrado en el mensaje de éxito.
- [Un cargo mal registrado no se puede corregir] → Aceptado y anotado: no hay anulación de cargos en las fuentes. El rechazo de repetidos cubre el error más probable (el doble envío); un tipo o un período equivocados quedan como deuda hasta que llegue la anulación.
- [Superposiciones no detectadas: un Día dentro de una Semana ya cobrada] → Fuera de alcance; las fuentes no lo piden. Se cobra lo que el Admin registra.
- [Dos Admin registran a la vez el mismo cargo] → El índice único rechaza el segundo y se responde el mismo 409.
- [La cantidad de hijos cambia entre la simulación y el registro, porque alguien inscribe a un hermano] → El registro cuenta de nuevo y guarda lo que contó. Es la regla de Acl. 5: el cargo usa el tramo del momento en que se genera.
- [Extraer `BuscadorFamilia` rompe el alta de alumnos] → La extracción va en su propia tarea, con los tests de alumnos sin tocar como control.

## Migration Plan

1. `python tasks.py migrate` aplica `crear_cargo`. No requiere datos ni pasos manuales; la semilla no cambia.
2. Rollback: `alembic downgrade -1` desde `backend/`, con la pérdida de cargos de la sección anterior.
