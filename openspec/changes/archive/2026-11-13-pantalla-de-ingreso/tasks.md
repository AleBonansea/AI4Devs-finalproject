# Tasks

> **Precondición, fuera del change:** antes de la tarea 2.1, el commit de arnés que agrega a `frontend-feature` el ciclo `test-writer` → rojo → congelar → `ui-implementer` → verde, y que habilita a `test-writer` a escribir en `frontend/tests/`. Sin él, las tareas 2.x no tienen con qué ejecutarse. Ver proposal, «Impact».

## 1. Montaje de los tests del frontend

- [x] 1.1 Instalar Vitest 3.x, jsdom, `@testing-library/react`, `@testing-library/user-event` y `@testing-library/jest-dom` con versiones exactas en `devDependencies`. Agregar el bloque `test` a `vite.config.ts` (`environment: "jsdom"`, `setupFiles: ["./tests/preparar.ts"]`), el script `"test": "vitest run"`, `tests` en el `include` de `tsconfig.app.json` y en el `prettier --check` de `npm run lint` (design, «Vitest con jsdom y Testing Library» y «Dónde viven los tests»). `tests/preparar.ts` carga los matchers de jest-dom, limpia `localStorage` y restaura los stubs después de cada test.
  - **Se verifica con:**
    - un control positivo que monta `App` y afirma un texto que no existe: `npm run test` tiene que fallar por esa aserción y no por la configuración. Después se borra.
    - `frontend/tests/preparar.test.tsx`, que se queda: comprueba que la preparación hace lo que promete. Un test escribe en `localStorage` y el siguiente lo encuentra vacío, y un elemento montado se afirma con un matcher de jest-dom (`toBeInTheDocument`). Así la suite nunca está vacía, `vitest run` no sale con error por falta de tests y el CI de la tarea 1.2 no queda en rojo hasta la 2.1.
    - `npm run test`, `npm run lint` y `npm run build` en verde.
- [x] 1.2 Agregar la tarea `front-test` a `tasks.py` (corre `npm run test` en `frontend/`) y el paso `python tasks.py front-test` al job `frontend` de `.github/workflows/ci.yml`, después de `front-lint`. Agregar la fila a la tabla de comandos de `CLAUDE.md`.
  - **Se verifica con** `python tasks.py front-test` saliendo con código distinto de 0 cuando hay un test en rojo y con 0 cuando no, porque un lanzador que siempre devuelve 0 apaga el CI. `python tasks.py` sola lista la tarea nueva.

## 2. Sesión e ingreso

- [x] 2.1 Con la skill `frontend-feature`, construir la zona protegida según los Requirements «La zona protegida exige sesión» (4 Scenarios), «Sesión rechazada por la API» (3), «Inicio de la zona protegida» (1), «Salir» (3) y los Scenarios «Recarga con el cambio pendiente» y «Sin el cambio pendiente no hay aviso» de «Aviso de cambio de contraseña pendiente»: 13 Scenarios.
  - `usuarioActual()` y los tipos `UsuarioActual` y `LoginRespuesta` en `src/lib/api.ts`, más las tildes de sus mensajes (design, «Mensajes en castellano con tildes»).
  - El contexto de sesión en `src/lib/sesion.tsx`, `src/routes/RutaProtegida.tsx`, `src/pages/Inicio.tsx`, `src/pages/CambioPendiente.tsx` y el router en `App.tsx` y `main.tsx` (design, «La sesión, en un contexto» y «Rutas»). Composición con MUI según la tabla del design; nada nuevo en `components/`.
  - Los tests van en `frontend/tests/auth/`, con `fetch` fingido y la aplicación montada en un `MemoryRouter` (design, «La API se finge en `fetch`»).
  - **Se verifica con** los 13 tests en rojo por el motivo correcto, la huella de `frontend/tests/` intacta después de implementar, `python tasks.py front-test` en verde y `npm run lint && npm run build` en verde.
- [x] 2.2 Con la skill `frontend-feature`, construir la pantalla de ingreso según los Requirements «Pantalla de ingreso» (3 Scenarios), «Campos vacíos no se envían» (4), «Ingreso correcto guarda la sesión» (2), «Estado de carga del ingreso» (3), «Error general del ingreso» (5), «Error por campo del ingreso» (2) y el Scenario «Ingresa con el cambio pendiente» de «Aviso de cambio de contraseña pendiente»: 20 Scenarios.
  - `ingresar(username, password)` en `src/lib/api.ts` y `src/pages/Ingreso.tsx` en la ruta `/ingresar`, con la validación local, el freno al doble envío y el reparto de errores entre el campo y el aviso general (design, «La pantalla de ingreso»).
  - Los tests van en `frontend/tests/auth/`, junto a los de 2.1. La huella de 2.1 se actualiza con los archivos nuevos y los de 2.1 no se tocan.
  - **Se verifica con** los 20 tests nuevos en rojo por el motivo correcto, los 13 de 2.1 sin cambios en la huella, `python tasks.py front-test` con los 33 en verde y `npm run lint && npm run build` en verde.

## 3. Comprobación de punta a punta

- [x] 3.1 Con la base de desarrollo migrada y la semilla cargada (`python tasks.py up`, `python tasks.py migrate`, `python tasks.py seed`), la API levantada (`python tasks.py api`) y el frontend en desarrollo (`cd frontend && npm run dev`), comprobar a mano en el navegador:
  - ingresar con un usuario de la semilla y ver su nombre y su rol en el inicio;
  - recargar y seguir adentro; salir y volver a `/ingresar`; abrir `/` después de salir y caer en el ingreso;
  - una contraseña incorrecta muestra `Usuario o contraseña incorrectos.`;
  - con la API apagada, el ingreso muestra el mensaje de conexión;
  - poner a mano `debe_cambiar_password` en true para ese usuario en la base de desarrollo, recargar y ver el aviso de cambio pendiente; volverlo a false después;
  - la pantalla de ingreso a ancho de teléfono (360 px), con el teclado: Tab recorre usuario, contraseña e `Ingresar`, y Enter envía.
  - **Se verifica con** cada punto anotado como hecho en el informe de la tarea, con lo que haya fallado.
  - **Informe (13/11/2026), contra la base de desarrollo con la semilla, usuario `mgarcia`.** Las capturas de la extensión de Chrome daban timeout, así que se manejó la pantalla con JavaScript en la página (los eventos `input` y `click` que escucha React) y se midió el DOM:
    - Hecho: ingresa y muestra `María García` y `Admin`; al recargar sigue adentro; Salir lleva a `/ingresar`; abrir `/` después de salir cae en el ingreso sin llamar a `/yo`.
    - Hecho: la contraseña incorrecta muestra `Usuario o contraseña incorrectos.`, conserva el usuario y vacía la contraseña. Los campos vacíos muestran los dos mensajes.
    - Hecho: con `debe_cambiar_password` en true, el ingreso y la recarga muestran solo el aviso y Salir; Salir lleva al ingreso. Se volvió a false.
    - **Distinto de lo esperado:** con la API apagada, el aviso es `El servidor tuvo un problema. Intentá de nuevo.`, no el de conexión. En desarrollo el proxy de Vite convierte la conexión rechazada en un 500. El código cumple la spec (un `fetch` sin respuesta da el mensaje de conexión, cubierto por los tests); el mensaje de conexión aparece de verdad sin red, no con un proxy delante. Ver design, «Risks / Trade-offs».
    - Hecho, medido en un iframe de 360 px (la ventana no se dejó redimensionar): sin scroll horizontal, la tarjeta con 16 px de margen a cada lado, tampoco con los errores a la vista. El orden de tabulación es `Usuario` → `Contraseña` → `Ingresar` y los dos campos tienen su etiqueta asociada. Que Enter envíe no se probó con una tecla real; lo cubre el test «Se envía con Enter» sobre el `<form>`.
- [x] 3.2 `python tasks.py openapi-check` sin cambios (el change no toca el backend), `python tasks.py front-test` y `python tasks.py front-lint` en verde.

## 4. Revisión adversarial

- [x] 4.1 Un pase del subagente `adversarial-reviewer` sobre el change terminado, antes del pull request. Rige `REVIEW.md`, «Cuándo se deja de revisar». Se verifica con sus hallazgos resueltos o justificados por escrito en esta tarea.
  - **Primer pase: 1 grave, 4 menores.** El código cumplía los 33 Scenarios. Los problemas estaban en los tests.
    - Grave, resuelto: los tests de «Error por campo del ingreso» se aprobaban con el mensaje en el aviso general o en el campo equivocado. `test-writer` los ató a la descripción accesible y al `aria-invalid` del campo que corresponde, y verificó que no haya un `role="alert"` con ese texto. Lo mismo para «Campos vacíos no se envían».
    - Menor 1, resuelto: la ref contra el doble envío no la ejercitaba ningún test (user-event no hace clic sobre un botón deshabilitado). Hay un test nuevo con dos `submit` en el mismo tick, colgado de «Un doble clic no manda dos ingresos».
    - Menor 3, resuelto: los tests de 403, 500 y sin conexión ahora comprueban, como el de 401, todo el Requirement: el aviso en `role="alert"`, el usuario conservado, la contraseña vacía, sin token y en `/ingresar`.
    - Menores 2 y 4, diferidos en el design: el 401 fuera de `/yo` (se resuelve a más tardar en el change 4) y los errores 422 de otros campos.
    - Pregunta sobre el título del Inicio: se aclaró la spec («Además del nombre de la aplicación, no tiene otro contenido»). Las otras dos preguntas, si un 422 vacía la contraseña y si `/ingresar` con sesión vigente muestra el formulario, quedan como están: la spec no lo pide y el design ya lo decide.
  - **Verificación de los tests endurecidos, con mutaciones de `Ingreso.tsx`.** Sin el reparto por campo caen 2; con el reparto invertido, 2; sin la ref, 1; sin vaciar la contraseña en 403 y 500, 2. Con el código original pasan los 37, la huella se recongeló, y `front-test` y `front-lint` pasan.

## Workflow follow-up

- Comprobar el change con `/openspec-verify-change` y archivarlo con `/openspec-archive-change`, que funde el delta en `openspec/specs/auth/spec.md`.
- Al archivar, si HU-UT-01 todavía tiene criterios en `5-historias-de-usuario.md`, reemplazarlos por un puntero a la spec.
- Pull request de `feat/pantalla-de-ingreso` hacia `feature/entrega-2-AlexisBonansea`.
