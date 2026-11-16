# Proposal

## Why

HU-UT-01 (Lote 1) está construida solo del lado de la API: el change `auth-ingreso` dejó `POST /api/v1/auth/login` y `GET /api/v1/auth/yo` funcionando, pero desde el navegador todavía no se puede entrar. Es el change 3 del «Plan de changes del lote 1» y lo que falta para que los changes 4 a 7, que traen cada uno su pantalla, tengan una sesión sobre la que montarse.

Es también el estreno de `frontend-feature`. El frontend no tiene hoy ni un test, así que antes de la primera pantalla hay que montar con qué escribirlos y verlos fallar.

## What Changes

- **Tests del frontend.** Vitest con jsdom y Testing Library, una tarea `python tasks.py front-test` y el paso correspondiente en el job `frontend` del CI. Es infraestructura: no agrega comportamiento, pero sin ella `frontend-feature` no puede hacer el ciclo tests → rojo → congelar → implementar → verde.
- **Pantalla de ingreso** en `/ingresar`: usuario y contraseña contra `POST /api/v1/auth/login`, con estado de carga, error por campo y error general, todos con los mensajes que ya traduce `src/lib/api.ts`.
- **Guardado del token** con las funciones que ya existen en `src/lib/api.ts` (`guardarToken`, `leerToken`, `borrarToken`).
- **Zona protegida.** Toda ruta que no sea `/ingresar` exige sesión: sin token, o con un token que la API rechaza, manda al ingreso. La sesión se comprueba con `GET /api/v1/auth/yo` al cargar, no solo con que haya un token guardado.
- **Inicio mínimo**: la única pantalla de la zona protegida por ahora. Dice quién ingresó y con qué rol, y tiene un botón **Salir** que borra el token del navegador y vuelve al ingreso.
- **Aviso de cambio de contraseña pendiente.** Si `debe_cambiar_password` viene en true, la zona protegida muestra solo un aviso de que la contraseña se tiene que cambiar y que hasta que eso esté disponible hay que pedírselo a un Admin, más el botón Salir. No muestra el inicio.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `auth`: se agregan los requirements de lo que ve y hace el navegador al ingresar: la pantalla, la sesión guardada, la zona protegida, el aviso de cambio pendiente y la salida. Los requirements de la API no cambian.

## Fuera de alcance

- **La pantalla de cambio de contraseña (HU-UT-06, Lote 2).** El aviso dice que el cambio está pendiente, pero no lleva a ninguna pantalla ni ofrece hacerlo.
- **El ABM de usuarios** (HU-UT-02, HU-UT-03) y el blanqueo (HU-UT-07).
- **Una pantalla propia de usuario bloqueado** (HU-UT-08). El 403 de bloqueo se muestra como cualquier error general del ingreso, con el mensaje que manda la API.
- **Cualquier pantalla de dominio.** El inicio no tiene menú, accesos ni datos: cada change del 4 en adelante trae su pantalla.
- **Navegación según rol.** Ocultar lo que el rol no puede usar llega con las primeras pantallas que haya que ocultar.
- **Token de renovación, cookie httpOnly y vencimiento por inactividad** (documento técnico, «Contraseñas y sesión»). Siguen atados al dominio propio, igual que en `auth-ingreso`. La sesión es el token de acceso en el almacenamiento del navegador, con el vencimiento que ya tiene.
- **Endpoint de logout.** Salir borra el token del navegador y nada más; el token sigue valiendo hasta su vencimiento (riesgo en el design).
- **Traducir los mensajes de validación de Pydantic.** Lo que la API manda en un 422 se muestra como llega.
- **Tests E2E con Playwright**, **Storybook**, **regresión visual** y **comprobaciones automáticas de accesibilidad**. Los tres últimos llegan cuando el catálogo propio de `components/` tenga piezas.
- **Un sistema de diseño propio.** La pantalla se compone con MUI; a `components/` se extrae solo lo que ya se repitió, y en este change probablemente no haya nada.
- **Cambios en el backend y en `docs/api/openapi.json`.** El change usa los dos endpoints tal como están.

## Impact

- `frontend/`: `package.json` y `package-lock.json` (Vitest, jsdom, Testing Library), `vite.config.ts` (bloque `test`), un archivo de preparación de los tests, `src/main.tsx` y `src/App.tsx` (router), las pantallas nuevas en `src/pages/`, la ruta protegida en `src/routes/`, y las llamadas de ingreso y de usuario actual en `src/lib/api.ts`.
- `tasks.py`: tarea `front-test`.
- `.github/workflows/ci.yml`: el job `frontend` corre `python tasks.py front-test`.
- Sin cambios en el backend, en el esquema ni en el contrato OpenAPI.
- **Precondición de arnés, fuera del change:** `frontend-feature` todavía no tiene el paso de tests ni `test-writer` conoce `frontend/`. Se corrige en un commit de arnés aparte, antes de aplicar este change.
