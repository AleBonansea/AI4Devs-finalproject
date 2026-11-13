# Tasks

> Cada tarea que toca rutas, esquemas o modelos cierra su commit con `python tasks.py openapi-generate` (regla 5 de CLAUDE.md). La tarea 5.1 lo comprueba al final.

## 1. Esquema de familias y alumnos

- [x] 1.1 Con la skill `backend-feature`, crear los modelos `Familia`, `Persona`, `FamiliaPersona`, `Alumno` e `Inscripcion`, la vista `v_familia_etiqueta` y la migración `crear_familias_y_alumnos`, según los Requirements de `familias` «Categoría de la familia» (3 Scenarios), «Etiqueta de la familia» (5), «Persona reutilizable entre familias» (4) y «Vínculo de una persona con una familia» (5), y los de `alumnos` «Ficha mínima del alumno» (2) e «Inscripción en un grupo y turno» (4): 23 Scenarios.
  - Columnas, restricciones e índices según design, «Esquema: las cinco tablas del modelo». La vista sobre un `MetaData()` propio y creada con `op.execute` (design, «La etiqueta es una vista»). `turno` y `categoria_familia` con `create_type=False`.
  - Los tests de la etiqueta insertan alumnos directo en la base y leen la vista: el alta todavía no existe.
  - Tests en `backend/tests/functional/familias/` y `backend/tests/functional/alumnos/`.
  - **Se verifica con** los 23 tests en rojo por el motivo correcto y después en verde; la skill `revisar-migracion` sobre la migración, con `upgrade head` → `downgrade -1` → `upgrade head` contra la base de pruebas y el downgrade sin tocar los tipos `turno` ni `categoria_familia`; `python tasks.py test`, `lint` y `typecheck` en verde.

## 2. Grupos para inscribir

- [x] 2.1 Con la skill `backend-feature`, construir `GET /api/v1/grupos` en un router `grupos.py`, según los Requirements de `grupos` «Grupos donde se puede inscribir» (5 Scenarios) y «Grupo sugerido por fecha de nacimiento» (6): 11 Scenarios.
  - El filtro del Profesor como `JOIN` en la consulta y `sugerido` calculado en SQL (design, «Endpoints, roles y filtro del Profesor»).
  - **Se verifica con** los 11 tests en rojo por el motivo correcto y después en verde, `docs/api/openapi.json` regenerado, y `python tasks.py test`, `lint` y `typecheck` en verde.

## 3. Búsquedas de familia y de persona

- [x] 3.1 Con la skill `backend-feature`, construir `GET /api/v1/familias?apellido=` y `GET /api/v1/personas?dni=`, en los routers `familias.py` y `personas.py`, según los Requirements de `familias` «Buscar familias por apellido» (9 Scenarios) y «Buscar una persona por DNI» (5): 14 Scenarios.
  - `normalizar_dni` en un solo lugar, que después reusa el alta (design, «Normalización del DNI»). El `LIKE` escapa `%` y `_`. Los esquemas de respuesta tienen solo los campos que dice la spec.
  - **Se verifica con** los 14 tests en rojo por el motivo correcto y después en verde, incluidos los que comprueban que la respuesta no trae ningún campo de más; `docs/api/openapi.json` regenerado; `python tasks.py test`, `lint` y `typecheck` en verde.

## 4. Alta de alumno y errores en castellano

- [x] 4.1 Con la skill `backend-feature`, construir `POST /api/v1/alumnos` en un router `alumnos.py` con el servicio `app/services/alumnos.py`, según los Requirements de `alumnos` «Alta de un alumno con familia nueva» (4 Scenarios), «Alta de un alumno en una familia existente» (4), «Personas en el alta» (7), «Datos del alumno en el alta» (4: todos menos «Faltan varios datos mínimos», que va en 4.2), «El grupo del alta» (4) y «Quién puede dar de alta un alumno» (5), más el de `errores-de-la-api` «Rechazos de reglas del negocio con la forma de validación» (1): 29 Scenarios.
  - Orden de las reglas, juntado de errores del paso 4 y carrera en el DNI según design, «El alta, en un servicio». `ReglaIncumplida` y su manejador según design, «Rechazos de reglas con la forma del 422».
  - Los tests de «no se crea nada» cuentan filas de `familia`, `persona`, `familia_persona`, `alumno` e `inscripcion` antes y después.
  - **Se verifica con** los 29 tests en rojo por el motivo correcto y después en verde, `docs/api/openapi.json` regenerado, y `python tasks.py test`, `lint` y `typecheck` en verde.
- [x] 4.2 Con la skill `backend-feature`, traducir los `msg` del 422 en el manejador de `app/main.py`, según el Requirement de `errores-de-la-api` «Mensajes de validación en castellano» (8 Scenarios) y el Scenario «Faltan varios datos mínimos» de `alumnos`: 9 Scenarios.
  - La tabla por `type` del design, «Traducción de los 422 de Pydantic». El 422 sigue sin `input`: los tests de `auth` sobre el 422 tienen que seguir en verde sin tocarlos.
  - **Se verifica con** los 9 tests en rojo por el motivo correcto (el `msg` llega en inglés o con el texto de otro caso) y después en verde, `docs/api/openapi.json` regenerado si cambió, y `python tasks.py test`, `lint` y `typecheck` en verde.

## 5. Contrato

- [x] 5.1 Comprobar que `docs/api/openapi.json` tiene los cuatro endpoints nuevos con sus esquemas y que ningún esquema de entrada tiene un campo de monto. **Se verifica con** `python tasks.py openapi-check` en verde.

## 6. Semilla

- [x] 6.1 Con la skill `backend-feature`, extender la semilla según los Requirements de `semilla` «La semilla solo corre sobre una base vacía» (5 Scenarios, 1 nuevo) y «Familias y alumnos de ejemplo» (1): los tests que ya existen de la base vacía no se tocan y se agregan 2.
  - **Se verifica con** los 2 tests nuevos en rojo por el motivo correcto y después en verde, los de la semilla que ya existían en verde, y `python tasks.py seed` corriendo sobre una base de desarrollo vacía.
  - **Estado (13/11/2026):** hecho y verificado: los 2 tests en rojo por el motivo correcto (la semilla no se negaba con una persona y no creaba familias) y después en verde, los 22 de la semilla en verde, la huella intacta. **Semilla sobre base vacía, hecho:** la persona a cargo recreó a mano el volumen local de Postgres (el hook `sin_borrar_datos.py` no deja hacerlo desde Claude). Después `migrate` y `seed` cargaron `Gómez – Lucía`, `Pérez – Ana` y `Ruiz – Sofía`, 4 personas y 4 inscripciones, y una segunda corrida se negó con `La base no está vacía…`.

## 7. Pantalla «Registrar alumno»

- [x] 7.1 Con la skill `frontend-feature`, construir la pantalla `/alumnos/nuevo` y el acceso desde el inicio, según los Requirements de `alumnos` «Pantalla «Registrar alumno»» (1 Scenario), «Grupos en la pantalla» (4), «Familia en la pantalla» (2), «Personas en la pantalla» (2), «Validación antes de enviar el alta» (3) y «Envío del alta desde la pantalla» (4), y el de `auth` «Inicio de la zona protegida» (2, uno nuevo): 17 Scenarios nuevos.
  - Las llamadas y sus tipos en `src/lib/api.ts`; `SelectorGrupo`, `SelectorFamilia` y `ListaPersonas` en `src/components/`; la página en `src/pages/RegistrarAlumno.tsx`; la ruta en `App.tsx` (design, «Frontend: la pantalla y sus piezas»). Los colores, si hacen falta, salen de `src/tema.ts`.
  - Tests en `frontend/tests/alumnos/`, con `fetch` fingido. El test del inicio que ya existe no se toca.
  - **Se verifica con** los 17 tests en rojo por el motivo correcto, la huella de `frontend/tests/` intacta después de implementar, y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.
- [x] 7.2 Con la skill `frontend-feature`, hacer que un 401 de cualquier llamada con token cierre la sesión, según el Requirement de `auth` «Un 401 en cualquier llamada cierra la sesión» (2 Scenarios).
  - Oyentes en `api.ts` y suscripción en `ProveedorSesion` (design, «Frontend: el aviso de 401 por suscripción»). Cierra el diferido del change 3.
  - **Se verifica con** los 2 tests en rojo por el motivo correcto, los de `frontend/tests/auth/` sin cambios en verde, y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.

## 8. Comprobación de punta a punta

- [x] 8.1 Con la base de desarrollo migrada y la semilla cargada, la API y el frontend levantados, comprobar a mano en el navegador:
  - como `lrodriguez` (coordinador), registrar un primer hijo con familia nueva, tutora nueva y un autorizado reutilizado por DNI (`30111222`), y ver el mensaje con la etiqueta;
  - registrar un segundo hijo, mayor, eligiendo esa familia por apellido, y ver que la etiqueta cambia;
  - como `jperez` (profesor), ver en `Grupo` solo «Delfines» de los dos turnos;
  - un DNI ya cargado como persona nueva muestra el error junto a su campo;
  - borrar el token a mano en el navegador con la pantalla abierta, buscar una familia y caer en el ingreso;
  - la pantalla a 360 px de ancho, sin scroll horizontal, y recorrible con el teclado.
  - **Se verifica con** cada punto anotado como hecho en el informe de la tarea, con lo que haya fallado.
  - **Informe (13/11/2026), contra la base de desarrollo recién sembrada.** Las capturas de la extensión de Chrome daban timeout, como en el change 3, así que se manejó la pantalla con JavaScript en la página (los eventos `input`, `change` y `click` que escucha React) y se midió el DOM:
    - Hecho: como `lrodriguez`, Mateo Torres (2021-02-10) con familia nueva `Socio`, tutora nueva Carla Torres y María Pérez reutilizada por DNI `30111222`. Con la fecha, «Delfines» salió sugerido en los dos turnos y `Grupo` quedó sin elegir; se eligió `Delfines · Tarde`. Mensaje: `Mateo Torres quedó inscripto en Delfines (Tarde). Familia: Torres – Mateo.` y el formulario quedó vacío.
    - Hecho: Valentina Torres (2019-04-01), buscando `Tor` en `Buscar familia por apellido`. Apareció `Torres – Mateo · Socio` y, al elegirla, `Categoría: Socio` como texto, sin el campo. Mensaje: `… Familia: Torres – Valentina.`, así que la etiqueta cambió.
    - Hecho: como `jperez`, `Grupo` ofrece solo `Delfines · Mañana` y `Delfines · Tarde`.
    - Hecho: una persona nueva con DNI `30.111.222` da `Ya hay una persona con ese DNI. Buscala por DNI para reutilizarla.` como ayuda del `DNI` de esa fila, con `aria-invalid`, sin ningún `role="alert"`, y `Nombre` conserva lo escrito.
    - Hecho, con una variación: en lugar de borrar el token se lo reemplazó por uno inválido, porque sin token la llamada no sale autenticada y no hay 401 que probar. Al buscar `Pér`, la dirección pasó a `/ingresar` y el token quedó borrado.
    - Hecho, medido en un iframe de 360 px: sin scroll horizontal (`scrollWidth` igual a `clientWidth`) y los controles entre x=22 y x=308, también con una fila de persona y los errores a la vista. El orden de tabulación sigue el del formulario: datos del alumno, grupo, familia, categoría, búsqueda por DNI, campos de la persona, `Agregar persona nueva` y `Registrar`.
    - Observación, no falla: el mensaje de éxito dice «quedó inscripto» también para Valentina. Es el texto fijo de la spec.
- [x] 8.2 `python tasks.py test`, `lint`, `typecheck`, `openapi-check`, `front-test` y `front-lint` en verde.

## 9. Revisión adversarial

- [ ] 9.1 Un pase del subagente `adversarial-reviewer` sobre el change terminado, antes del pull request. Rige `REVIEW.md`, «Cuándo se deja de revisar». **Se verifica con** sus hallazgos resueltos o justificados por escrito en esta tarea.
  - **Primer pase (13/11/2026): ningún hallazgo grave, 5 menores y 4 preguntas.** La persona a cargo decidió arreglar los cinco y resolver tres de las preguntas; los arreglos son las tareas 9.2 a 9.4:
    - Menor 1, un carácter NUL en un texto válido daba 500 (comprobado con una sonda) → 9.2.
    - Menor 2, un Profesor con un grupo ajeno inactivo, cerrado o inexistente recibía 422 y no 403 → 9.2. Se invierte el orden del design.
    - Menor 3, los tests de pantalla del alta van cerca del plazo de 5 s → 9.4, `testTimeout: 10000`.
    - Menor 4, ni el escape del `LIKE` ni la carrera del DNI tenían test → 9.2, con Scenario propio cada uno.
    - Menor 5, el design prometía un test por cada `type` de la tabla de traducción → 9.2, test de la función pura.
    - Pregunta, el DNI con guiones quedaba como otra persona → 9.2, la normalización quita también los guiones.
    - Pregunta, la sugerencia de grupo no reemplazaba lo que ella misma había elegido → 9.3.
    - Preguntas, recorrer el padrón por DNI y sumar personas de otras familias → no cambia el comportamiento: riesgos en el design y pregunta abierta en `aclaraciones-cliente.md`.
- [ ] 9.2 Con la skill `backend-feature`, los arreglos del backend según los Scenarios nuevos: de `errores-de-la-api` «Caracteres de control en los textos» (4); de `alumnos` «Profesor con un grupo ajeno inactivo», «Profesor con un grupo que no existe», «Persona nueva con un DNI ya cargado escrito con guiones» y «Dos altas a la vez con el mismo DNI nuevo»; de `familias` «Los comodines se buscan como texto» y «DNI escrito con guiones»: 10 Scenarios, más el test de la función de traducción con cada `type` de la tabla (design, «Traducción de los 422»).
  - **Se verifica con** los tests nuevos en rojo por el motivo correcto (los de comodines y carrera pueden pasar ya: protegen comportamiento que existe, y se ven fallar quitando a mano el escape o el `except` antes de congelar), en verde después, `docs/api/openapi.json` regenerado si cambió, y `python tasks.py test`, `lint` y `typecheck` en verde.
- [ ] 9.3 Con la skill `frontend-feature`, el Scenario nuevo de `alumnos` «Corregir la fecha cambia el grupo elegido por la sugerencia» (1).
  - **Se verifica con** el test en rojo por el motivo correcto, después en verde, y `python tasks.py front-test` y `front-lint` en verde.
- [x] 9.4 Subir `testTimeout` a 10000 en el bloque `test` de `frontend/vite.config.ts` y actualizar la huella de `frontend/tests/` y `vite.config.ts`. **Se verifica con** `python tasks.py front-test` en verde dos veces seguidas.

## Workflow follow-up

- Comprobar el change con `/openspec-verify-change` y archivarlo con `/openspec-archive-change`, que crea `openspec/specs/familias`, `alumnos` y `errores-de-la-api`, y funde los deltas de `grupos`, `auth` y `semilla`.
- Al archivar, reemplazar los criterios de HU-AF-01 en `5-historias-de-usuario.md` por un puntero a la spec de `alumnos`.
- Pull request de `feat/familias-y-alumnos` hacia la rama de entrega.
