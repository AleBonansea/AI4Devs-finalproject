# Proposal

## Why

Es el change 6 del «Plan de changes del lote 1» y cubre dos historias del Lote 1: **HU-TAR-04** (que el sistema calcule solo el monto del cargo) y **HU-CC-01** (registrar un cargo a una familia: tipo, alumno, turno, modalidad y período). Los changes 2 y 4 dejaron el tarifario cargado por la semilla y alumnos inscriptos, pero todavía no hay forma de asentar lo que una familia tiene que pagar: hoy el cálculo se hace a mano, con la planilla de aranceles.

Es el change que concentra el riesgo del sistema (backlog, «Dónde está el riesgo»): el porcentaje único no acumulado, el tramo que alcanza a todos los hijos, el conteo de hermanos por turno y la persistencia del cálculo en el cargo. HU-CC-01 es la tercera de las historias que la Entrega 1 documentó con criterios Dado / Cuando / Entonces, y desbloquea el change 7 (`cuenta-corriente`): un pago necesita un cargo.

## What Changes

- **Esquema del cargo.** La tabla `cargo` del modelo de datos, con el cálculo congelado (categoría, cantidad de hijos, tarifa base, porcentaje y total) y los `CHECK` de forma según el tipo y la modalidad. Suma tres índices únicos parciales que impiden los cargos repetidos (ver abajo). Una migración reversible.
- **El cálculo, como función pura** en `app/services/calculo_cargo.py`: recibe la tarifa base o el monto fijo, la categoría, la modalidad, la cantidad de hijos y la tabla de descuentos de la temporada, y devuelve el desglose. Un único porcentaje, nunca acumulado; en el Mes, el del tramo `min(hijos, 4)`; el redondeo a centavos, el mismo que el `CHECK` de la base.
- **Simular un cargo** (`POST /api/v1/cargos/simulacion`): el mismo cuerpo que el registro, con las mismas reglas, devuelve el desglose sin guardar nada. Es lo que la pantalla muestra antes de confirmar (escenario 1). Reemplaza al `simular=true` de `4-especificaciones-de-la-api.md`, que era una concesión al límite de 3 endpoints de la Entrega 1.
- **Registrar un cargo** (`POST /api/v1/cargos`): el cliente dice **qué** se cobra (alumno, tipo, inscripción, modalidad, período o día) y la API calcula, guarda y devuelve el cargo con su desglose y el saldo pendiente de la familia en la temporada. Un cuerpo con un importe se rechaza.
- **Opciones para cobrar** (`GET /api/v1/cargos/opciones`): los tipos de cargo y los períodos de cobro de la temporada vigente, para llenar la pantalla.
- **Inscripciones de una familia** (`GET /api/v1/familias/{familia_id}/inscripciones`): los hijos de la familia inscriptos en la temporada vigente, con su turno y su grupo, para elegir a quién y en qué turno se cobra.
- **Permisos:** los cuatro endpoints son solo del Admin (Acl. 9). Coordinador y Profesor reciben 403.
- **Cargos repetidos: se rechazan.** **[SUPUESTO]**, decidido con el usuario y registrado como pregunta abierta en `aclaraciones-cliente.md`: el mismo Abono (alumno, turno y período, o el mismo día) no se registra dos veces, y la Preinscripción va una vez por alumno y temporada. En este lote no hay anulación de cargos, así que un duplicado quedaría como deuda sin corrección posible.
- **Todo cargo es de un alumno inscripto en la temporada** **[SUPUESTO]**, también como pregunta abierta: la Preinscripción no lleva inscripción, pero el alumno tiene que tener al menos una en la temporada del cargo. El cargo de la modalidad Día tiene que caer dentro de la temporada **[SUPUESTO]**.
- **Pantalla «Registrar cargo»** en `/cargos/nuevo`: buscar la familia, elegir alumno y turno, tipo de cargo, modalidad y período (o fecha, en Día), ver el desglose que calcula la API y confirmar. El acceso desde el inicio aparece **solo para el Admin**.
- **Montos y porcentajes como texto en un solo lugar** (`src/lib/montos.ts`), como las fechas en `fechas.ts`: `$ 85.000`, `$ 4.462,50`, `36,25 %`, sin pasar por `number`.

## Capabilities

### New Capabilities

- `cargos`: el cargo de una familia por un alumno, su cálculo de tarifa y descuento, la simulación, el registro con el cálculo congelado, las reglas que lo rechazan, sus permisos y la pantalla «Registrar cargo».

### Modified Capabilities

- `familias`: suma la consulta de las inscripciones de una familia en la temporada vigente, solo para el Admin.
- `auth`: el inicio de la zona protegida suma el acceso `Registrar cargo`, visible solo para el Admin.

## Fuera de alcance

- **Pagos, saldo y cuenta corriente** (HU-CC-02, HU-CC-03, HU-TES-01): son el change 7. Acá el saldo pendiente que devuelve el registro es la suma de los cargos de la familia en la temporada, porque todavía no hay pagos; la pantalla no muestra el saldo «actual» antes de cobrar ni la lista de cargos.
- **Anular o modificar un cargo.** Un cargo no se recalcula nunca, y la anulación que definen las fuentes es la de un pago (HU-CC-06). Corregir un cargo mal cargado queda sin solución en este lote: por eso los repetidos se rechazan.
- **Configurar el tarifario** desde la aplicación (HU-TAR-01 a HU-TAR-03, lote 2): la tarifa base, los descuentos, los períodos y los tipos de cargo siguen viniendo de la semilla.
- **Detectar superposiciones**: un Abono del Día que cae dentro de una Semana ya cobrada, o una Quincena dentro de un Mes, se registra. Solo se rechaza el cargo idéntico.
- **Cambiar la categoría de la familia** (solo Admin, sin historia en este lote). El cargo toma la categoría que la familia tiene al momento.
- **Modalidad sugerida** al inscribir (HU-CC-05, Backlog) y **asistencia** en la pantalla de cobro (Acl. 5 la descarta).
- **Recibos, medio de pago, avisos a las familias** (Acl. 6).
- **Cargos de ejemplo en la semilla.** La semilla no cambia.

## Impact

- **Backend:** modelo `Cargo` en `app/models/`, una migración en `alembic/versions/`, `app/services/calculo_cargo.py` (función pura), el servicio `app/services/cargos.py`, esquemas en `app/schemas/cargos.py`, un router `cargos.py` en `app/api/v1/` y una ruta nueva en `familias.py`.
- **Contrato:** cuatro endpoints nuevos; `docs/api/openapi.json` regenerado. Ningún endpoint existente cambia.
- **Frontend:** llamadas y tipos en `src/lib/api.ts`, `src/lib/montos.ts`, la página `src/pages/RegistrarCargo.tsx`, piezas nuevas en `src/components/` (el buscador de familia sale de `SelectorFamilia` para reusarlo), la ruta en `App.tsx` y el acceso en `Inicio.tsx`.
- **Documentación:** las tres preguntas abiertas en `docs/prd/aclaraciones-cliente.md`; los índices únicos de `cargo` en `3-modelo-de-datos.md`; la regla de `montos.ts` en CLAUDE.md, sección Frontend.
