# Design

## Context

Ver `proposal.md` para el porqué. Lo que condiciona el cómo:

- **Dos suites que no se tocan.** El backend se prueba con pytest contra `escuelita_test`, con `conftest.py` negándose a correr contra la base de desarrollo. El frontend se prueba con Vitest sobre jsdom, con `fetch` fingido. Nada levanta la API y el frontend juntos.
- **El frontend ya sabe hablar con otro origen.** `src/lib/api.ts` arma cada URL como `${VITE_API_URL}/api/v1...`; en desarrollo `VITE_API_URL` está vacío y el proxy de Vite reenvía `/api` a `localhost:8000`. En Render, `VITE_API_URL` apunta a la API y la API habilita el origen del sitio con `CORS_ORIGINS`.
- **La configuración sale del entorno.** `Configuracion` (pydantic-settings) lee `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`; una variable de entorno pisa al `.env`. La semilla y Alembic usan la misma configuración.
- **La semilla se niega** a correr sobre una base con datos y contra un host que no sea local (`verificar_base_local`). Sus datos están fijados en `openspec/specs/semilla/spec.md`: usuarios, grupos, tarifas y descuentos con los que se calculan los montos esperados.
- **El token vive en `localStorage`** con la clave `escuelita.token` (la misma constante que usan los tests de pantalla en `frontend/tests/auth/montar.tsx`).
- **Windows es la máquina de desarrollo.** `tasks.py` existe porque `make` no viene con Windows, y ya resuelve los ejecutables del entorno virtual y `npm.cmd`.
- **El hook `sin_borrar_datos.py`** corta los comandos de `Bash` que contienen `DROP DATABASE` o el binario que borra bases. Solo mira el texto del comando.

## Goals / Non-Goals

**Goals:**
- Que `python tasks.py e2e` corra igual en Windows, en Linux y en el CI, sin pasos a mano.
- Que la corrida ejercite la configuración de producción: build estático, API en otro origen, CORS real.
- Que ningún paso pueda tocar la base de desarrollo, la de tests del backend ni una remota.
- Que cada uno de los tres tests se haya visto fallar por el motivo correcto antes de darlo por bueno.

**Non-Goals:**
- Un framework de E2E reutilizable (page objects, fixtures de datos por API). Con tres tests es abstracción sin uso; se extrae cuando haya un cuarto que repita pasos.
- Correr en paralelo, en varios navegadores o contra Render.
- Tocar `frontend/src/` para facilitar los selectores (ningún `data-testid`).

## Decisions

### 1. `e2e/` como paquete propio en la raíz

`e2e/package.json` con `@playwright/test` en versión fija y `typescript`; `playwright.config.ts`; `tsconfig.json`; `tests/camino-de-la-plata.spec.ts`, `tests/permisos.spec.ts`, `tests/sesion.spec.ts`.

- **Por qué no dentro de `frontend/`:** Playwright y Vitest buscan archivos de test con convenciones que se pisan (`*.test.ts`, `*.spec.ts`), `vite.config.ts` entra en la huella de los tests congelados de `frontend-feature`, y las dependencias de Playwright (el navegador) no tienen que bajarse para correr los tests de pantalla. Además los E2E prueban el sistema entero, no el frontend.
- **Alternativa descartada:** Playwright para Python (`pytest-playwright`) dentro de `backend/`. Unificaría el lenguaje con `tasks.py`, pero el material de entrenamiento, la documentación y el trace viewer están centrados en la versión de Node, y los tests de pantalla del proyecto ya son TypeScript.

### 2. `tasks.py` orquesta la corrida, no el `webServer` de Playwright

`python tasks.py e2e` hace, en orden y cortando en el primer fallo:

1. **Comprobar las reglas de la suite** (decisión 7).
2. **Recrear la base** `escuelita_e2e` (decisión 3).
3. **Migrar** con `alembic upgrade head` y **sembrar** con `scripts/seed.py`, ambos con `DATABASE_URL` apuntando a `escuelita_e2e`.
4. **Compilar el frontend** como en producción (decisión 4).
5. **Levantar la API** (`uvicorn app.main:app --port 8001`, sin `--reload`) y el **build servido** (`vite preview --port 4173 --strictPort`).
6. **Esperar a que respondan** `GET http://localhost:8001/salud` y `GET http://localhost:4173/`: un sondeo con tope de 60 s que corta antes si el proceso murió. No es una espera fija: termina en cuanto el servicio contesta.
7. **Correr** `npx playwright test` dentro de `e2e/`, pasándole los argumentos que sigan a `e2e` (por ejemplo `python tasks.py e2e --headed` o un archivo).
8. **Bajar los dos procesos** en un `finally`, falle lo que falle, y salir con el código de Playwright.

- **Por qué no `webServer`:** los comandos de la API y del build necesitan el Python del entorno virtual, `npm.cmd` en Windows y el entorno armado (decisión 5). Esa resolución ya vive en `tasks.py` (`ejecutable`, `correr`); repetirla en TypeScript son dos lugares que se separan. Y la base tiene que estar recreada antes de que la API abra su primera conexión, cosa que el `webServer` no ordena.
- **Puertos propios (8001 y 4173), y ocupados es un error.** Si la API de desarrollo está corriendo en el 8000 contra `escuelita`, no se reutiliza: un E2E escribiendo en la base de desarrollo es exactamente lo que se quiere evitar. Si el 8001 o el 4173 ya están en uso, la tarea corta con un mensaje que lo dice, en lugar de probar contra un proceso desconocido.
- **Bajar los procesos en Windows.** `vite` se arranca con `node` sobre `frontend/node_modules/vite/bin/vite.js`, no con `npm.cmd`, para no dejar un `node` huérfano detrás de un `cmd`. En Windows se mata el árbol con `taskkill /T /F /PID`; en POSIX los procesos se arrancan en su propia sesión y se mata el grupo. Así una corrida cortada no deja el 8001 tomado para la siguiente.

### 3. Base `escuelita_e2e`, recreada con una guarda en el código

- La URL sale de `E2E_DATABASE_URL`, con valor por defecto `postgresql+psycopg://escuelita:escuelita@localhost:5432/escuelita_e2e`, que coincide con el Postgres de `docker-compose.yml` y con el servicio del CI.
- **Antes de borrar nada**, `tasks.py` comprueba dos cosas y corta si alguna falla:
  - que el nombre de la base sea exactamente `escuelita_e2e`;
  - que el host sea `localhost`, `127.0.0.1` o `::1`. Es más estricto que `verificar_base_local` de la semilla, que acepta `db`: fuera de Docker ese nombre puede resolverse a un host de la red;
  - que la URL no traiga ningún parámetro en la query: `?dbname=` pisa el nombre de la ruta, y `?host=`, `?hostaddr=` o `?service=` pisan el host.
- **Y saca del entorno** de todos los pasos de la corrida las variables que desviarían la conexión sin que la URL lo muestre: toda `PG*` de libpq (`PGHOSTADDR` le gana al host de la URL; `PGSERVICE` trae su propio host) y `ALEMBIC_URL`, que `backend/alembic/env.py` prefiere a `DATABASE_URL`.
- Con eso se conecta a la base de mantenimiento `postgres` del mismo servidor, con `autocommit`, y ejecuta `DROP DATABASE IF EXISTS escuelita_e2e WITH (FORCE)` y `CREATE DATABASE escuelita_e2e`. `WITH (FORCE)` (PostgreSQL 13+, el proyecto usa 16) cierra las conexiones que haya dejado una corrida cortada.
- El código corre con el Python del entorno virtual (`psycopg` ya es dependencia del backend), como el guion de `openapi-generate`.
- **Sobre el hook:** `sin_borrar_datos.py` no ve este borrado porque solo lee el texto del comando de `Bash`, y `python tasks.py e2e` no lo contiene. Es deliberado: el hook es una red contra un borrado escrito a mano; acá el borrado es parte de una tarea con una guarda más estricta que el hook (un nombre exacto y un host local). No se agrega una excepción al hook.
- **Alternativa descartada:** reutilizar `escuelita_test`. `conftest.py` la usa con transacciones que se revierten; una corrida E2E que deja datos confirmados la ensuciaría para la suite del backend.
- **Alternativa descartada:** limpiar tablas en lugar de recrear la base. Habría que mantener la lista de tablas y el orden de las FK; recrear y migrar prueba además que las migraciones arrancan desde cero.

### 4. El build se compila y se sirve como en producción

- `vite build --outDir dist/e2e --emptyOutDir` con `VITE_API_URL=http://localhost:8001`, invocado con `node` sobre el binario de Vite. No pasa por `npm run build`: el `tsc -b` ya lo corre `front-lint` y acá solo suma tiempo.
- `dist/e2e` y no `dist/`: un build que apunta al 8001 no tiene que quedar donde un `npm run build` normal espera el suyo. `dist/` ya está en `.gitignore` y fuera del alcance del `test-writer`, así que no hacen falta entradas nuevas.
- `vite preview --outDir dist/e2e` sirve el build estático. Su proxy hereda el de desarrollo (al 8000), pero no se usa: con `VITE_API_URL` absoluto el navegador llama directo al 8001, en otro origen, como en Render.

### 5. Entorno de la API del E2E

`tasks.py` arma el entorno de los pasos 3 y 5 sin depender del `.env` (las variables pisan al archivo):

| Variable | Valor | Por qué |
|---|---|---|
| `DATABASE_URL` | la de `escuelita_e2e` | La única base que el E2E toca |
| `SECRET_KEY` | una clave de juguete fija | Para que la configuración valide; no firma nada que salga de la máquina |
| `CORS_ORIGINS` | `http://localhost:4173` | El origen del build servido. Si CORS se rompe, falla el E2E, que es lo que se quiere probar |
| `TZ` | `America/Argentina/Buenos_Aires`, **solo fuera de Windows** | El mismo huso que el navegador (decisión 6). En Windows no se fija: Python no entiende un nombre IANA en `TZ` y cae a UTC; la API usa la hora de la máquina |

### 6. Configuración de Playwright

- `workers: 1`, `fullyParallel: false`: los tres tests comparten una base; el orden de ejecución no tiene que importar, pero tampoco se compite por ella.
- `retries: 0`: un test que pasa al segundo intento es un test inestable, y se arregla, no se reintenta.
- `forbidOnly: !!process.env.CI`: un `test.only` olvidado no deja pasar el CI con un test.
- `use.trace: 'retain-on-failure'` y `screenshot: 'only-on-failure'`: la evidencia de un fallo queda en `e2e/test-results/`; un verde no deja nada.
- `use.baseURL` de `E2E_BASE_URL` (por defecto `http://localhost:4173`); la URL de la API, de `E2E_API_URL` (por defecto `http://localhost:8001`), solo para el pedido directo del test de permisos.
- `use.timezoneId: 'America/Argentina/Buenos_Aires'` y `locale: 'es-AR'`: la fecha del pago que propone la pantalla es la de hoy en Argentina, igual que en el huso de la API. Con el navegador en UTC, a la noche la pantalla propondría mañana y la API la rechazaría por posterior a hoy.
- Un solo proyecto: Chromium de escritorio.
- Reporter `list` en la consola y `html` con `open: 'never'` en `e2e/playwright-report/`.

### 7. Sin esperas fijas, con un control que lo hace cumplir

- Los tests esperan solo por condiciones: las aserciones `expect(...)` de Playwright reintentan hasta su tope, y `page.waitForResponse` espera un pedido concreto. Nunca `page.waitForTimeout` ni `setTimeout`.
- La regla se comprueba en el paso 1 de `python tasks.py e2e`: si algún archivo de `e2e/tests/` contiene `waitForTimeout(` o `setTimeout(`, la tarea corta antes de tocar la base. Una regla escrita sin control es una regla que no se cumple.

### 8. Selectores desde la spec, sin leer la implementación

- Se ubican los elementos por rol y por etiqueta con los textos de los Scenarios (`getByLabel('Usuario')`, `getByRole('button', { name: 'Registrar cargo' })`, `getByRole('option', { name: 'Tiburones · Mañana · 7 a 9 años (sugerido)' })`). Si la etiqueta accesible difiere de la spec, es un hallazgo: se reporta, no se acomoda el test leyendo `frontend/src/`.
- Los tests los escribe la sesión principal, no el subagente `test-writer`: este lo invocan `backend-feature` y `frontend-feature`, que no aplican porque no hay código de producción que escribir. Se sigue su regla de fondo: escribir desde la spec sin abrir `frontend/src/` ni `backend/app/`. Para ver qué nombre accesible tiene algo sirve el trace o el árbol de accesibilidad de la app corriendo, no el código.

### 9. Los tres tests y por qué cada aserción discrimina

**Camino de la plata** (`camino-de-la-plata.spec.ts`), sesión de `mgarcia`:
1. Ingresa en `/ingresar` con `mgarcia` y `Verano2026`: la dirección pasa a `/` y se ven `Admin` y el botón `Salir`. No se afirma el nombre: la spec de la semilla fija el usuario y el rol, no el nombre de pila.
2. Pulsa `Registrar alumno` en el menú. Alta de **Tomás Ibarra**, nacido el **2019-04-12**, `Familia nueva` `Empleado`, tutora **Elena Ibarra** (DNI `33444555`, teléfono `3514445566`, `Tutor` marcado). Elige `Tiburones · Mañana · 7 a 9 años (sugerido)` a mano: con 2019 quedan sugeridos los dos Tiburones y la pantalla no elige. Ve `Tomás Ibarra quedó inscripto en Tiburones (Mañana). Familia: Ibarra – Tomás.`
3. Pulsa `Registrar cargo` en el menú. Elige `Ibarra – Tomás`, `Tomás Ibarra · Mañana`, «Abono», `Mes`, «Mes 1». Ve `Total del cargo` con **`$ 75.000`**, pulsa `Registrar cargo` y ve `Cargo registrado por $ 75.000. Saldo pendiente de la familia: $ 75.000.`
4. Pulsa `Cuenta corriente` en el menú, elige `Ibarra – Tomás`, ve `Saldo pendiente` `$ 75.000`, pulsa `Registrar pago`, comprueba que `Monto` propone `75.000`, lo envía, y ve `Pago registrado por $ 75.000. Saldo pendiente de la familia: $ 0.`
5. Después de que la pantalla vuelve a pedir la cuenta corriente: `Saldo pendiente` `$ 0` y el renglón `Abono · Mes 1` dice `Saldado`.

`$ 75.000` es la tarifa del Mes a la mañana (`$ 100.000`) con el 25 % del empleado en el tramo de un hijo. Se distingue de los errores plausibles: sin descuento o con la categoría `no_socio` da `$ 100.000`, con `socio` `$ 50.000`, contando a los hijos de la semilla en el tramo 2 `$ 67.500`. El saldo en `$ 0` se lee de la cuenta corriente pedida de nuevo, no del mensaje del pago: prueba que el pago quedó guardado y que el saldo sale de la base.

**Permisos** (`permisos.spec.ts`), sesión de `jperez`:
1. Ingresa y el menú no tiene `Administración` ni `Cuenta corriente` (Scenario «Menú del Profesor»).
2. Abre `/cuenta-corriente` escribiéndolo en la barra: la dirección pasa a `/`, y en ese tiempo no salió ningún pedido a `/api/v1/familias` (se registran los pedidos con `page.on('request')`).
3. Con el token que la pantalla guardó, pide `GET {E2E_API_URL}/api/v1/familias/1/cuenta-corriente`: responde 403 con `No tenés permiso para esta operación.` y el cuerpo no tiene `saldo_pendiente` ni `cargos`. El id 1 sirve exista o no: la spec dice 403 en los dos casos.

El paso 3 es el que hace que el test pruebe la API y no solo el ocultamiento en la pantalla: una ruta que solo esconde el menú pasaría los pasos 1 y 2 con la API abierta.

**Sesión** (`sesion.spec.ts`), sin ingresar:
1. Abre `/ingresar` y guarda en `localStorage`, con la clave `escuelita.token`, un JWT bien formado, vigente hasta 2099, firmado con una clave que no es la del E2E.
2. Abre `/cuenta-corriente` y espera la respuesta de `GET /api/v1/auth/yo`: es **401**.
3. La dirección pasa a `/ingresar`, se ve el formulario de ingreso y `escuelita.token` ya no está en `localStorage`.

Sin el paso 2, el test pasaría también si la clave del token cambiara de nombre: el frontend no encontraría token, mandaría al ingreso sin llamar a la API y todo daría verde sin haber probado el rechazo. Esperar el 401 prueba que el token llegó a la API y que fue la API la que lo rechazó. Un token con firma ajena, y no un texto cualquiera, prueba que la API valida la firma y no solo la forma.

### 10. El rojo de unos tests que nacen en verde

El comportamiento ya existe, así que los tres tests pasan al escribirlos. Un guardarraíl que nunca se vio fallar no está probado (2.6, «Decisiones»), así que cada uno se ve fallar con un sabotaje temporal del código de producción, sin commitear:

| Test | Sabotaje | Falla en |
|---|---|---|
| Camino de la plata | el descuento del cálculo devuelve 0 % | el renglón del descuento dice `0 %` en lugar de `25 %` (es la primera aserción del desglose que lo ve) |
| Permisos | la ruta solo-Admin deja pasar al Profesor | la dirección se queda en `/cuenta-corriente` |
| Permisos (paso 3) | el endpoint de cuenta corriente acepta al Profesor | el 200 en lugar del 403 |
| Sesión | el frontend no borra el token ante un 401 | `escuelita.token` sigue guardado |
| Sesión | la clave del token cambia de nombre | no llega el `GET /api/v1/auth/yo` que el test espera |

El primer intento del camino de la plata falló por un motivo confuso: con el descuento en 0 % había dos `$ 100.000` en pantalla y la aserción chocaba en modo estricto. Por eso cada valor del desglose y el saldo pendiente se leen junto a su etiqueta, con el texto del renglón anclado de punta a punta.

La salida de cada rojo se guarda en `.claude/tmp/e2e-rojo-<test>.txt`. Después de cada sabotaje, `git diff --exit-code -- backend/app frontend/src` tiene que salir limpio antes de seguir.

### 11. Job `e2e` en el CI

En `.github/workflows/ci.yml`, en paralelo con `backend` y `frontend`, `timeout-minutes: 15`:

- `services.postgres` igual que el job `backend` (`postgres:16`, usuario y clave `escuelita`). La URL por defecto de `E2E_DATABASE_URL` coincide, así que no hace falta pasarla.
- `env.TZ: America/Argentina/Buenos_Aires` y `CI: true`.
- Pasos: checkout; Python 3.12 con caché de pip; Node 22 con caché de npm sobre los dos `package-lock.json`; `pip install -e ".[dev]"` en `backend/`; `npm ci` en `frontend/` y en `e2e/`; `npx playwright install --with-deps chromium` en `e2e/`; `python tasks.py e2e`.
- Si falla, `actions/upload-artifact` sube `e2e/test-results/` y `e2e/playwright-report/` con retención de 7 días: el trace se abre con `npx playwright show-trace`.

`python tasks.py install` suma `npm ci` en `e2e/` y `npx playwright install chromium`, para que en local alcance con la orden de siempre.

## Risks / Trade-offs

- [Un E2E inestable erosiona la confianza en el CI entero] → Cero reintentos, sin esperas fijas y un worker: si falla de a ratos, se nota y se arregla la causa. Las aserciones esperan por condiciones observables (texto, dirección, respuesta), nunca por tiempo.
- [Los montos esperados dependen de la semilla] → Es buscado: la semilla tiene su spec con las tarifas y los descuentos. Si alguien los cambia, el E2E falla y obliga a revisar el número, igual que los tests de la semilla.
- [La clave `escuelita.token` es un detalle interno] → El test de sesión espera el 401 de `/auth/yo` (decisión 9), así que un cambio de clave lo pone en rojo en lugar de dejarlo pasar en verde.
- [Un proceso huérfano deja tomado un puerto] → Se mata el árbol de procesos en el `finally`, y un puerto ocupado al arrancar corta con un mensaje claro en lugar de reutilizar lo que haya.
- [Borrar una base equivocada] → Nombre exacto `escuelita_e2e`, host de esta máquina y URL sin parámetros, comprobados antes de conectarse, y sin las variables de libpq que desviarían la conexión. La primera versión solo miraba el nombre y el host: la revisión adversarial mostró que `PGHOSTADDR` en el entorno o `?dbname=` en la URL la salteaban.
- [Los selectores dependen de los textos de la pantalla] → Son los textos de la spec, que es lo que manda sobre el código: si cambian sin cambiar la spec, el E2E falla con razón.
- [Tiempo de CI] → Un job paralelo; con tres tests, el grueso es instalar Chromium y compilar. Se acepta.
- [Sigue sin probarse el celular] → Fuera de alcance; la recorrida a mano en celular se mantiene y se dice así en 2.6.

## Migration Plan

Sin migración de esquema ni de datos. Para volver atrás: borrar `e2e/`, la tarea `e2e` de `tasks.py` y el job de `ci.yml`, y restituir el texto de 2.6, de `CLAUDE.md` y del readme. La base `escuelita_e2e` local puede quedar; no la usa nadie más.
