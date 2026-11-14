# Tasks

> Antes de la primera tarea: rama `feat/asistencia` salida de la rama de entrega actualizada (regla 1 de CLAUDE.md). Cada tarea que toca rutas, esquemas o modelos cierra su commit con `python tasks.py openapi-generate` (regla 5). La tarea 4.1 lo comprueba al final.

## 1. Esquema de asistencia

- [x] 1.1 Con la skill `backend-feature`, crear el modelo `Asistencia` y la migración `crear_asistencia`, según el Requirement de `asistencia` «Un registro de asistencia por inscripción y fecha» (4 Scenarios).
  - Columnas, restricciones y nombres según design, «Esquema: la tabla `asistencia` del modelo, tal cual». `presente` sin default; `registrado_en` con `server_default now()`; sin `MarcaDeCreacion`.
  - Los tests insertan directo en la base: los endpoints todavía no existen. Tests en `backend/tests/functional/asistencia/`.
  - **Se verifica con** los 4 tests en rojo por el motivo correcto (no existe la tabla) y después en verde; la skill `revisar-migracion` sobre la migración, con `upgrade head` → `downgrade -1` → `upgrade head` contra la base de pruebas; `python tasks.py test`, `lint` y `typecheck` en verde.

## 2. Endpoints

- [x] 2.1 Con la skill `backend-feature`, construir `GET /api/v1/grupos/{grupo_id}/asistencias/{fecha}` en un router `asistencias.py`, con la dependencia `grupo_asignado` y el servicio `app/services/asistencias.py`, según estos Scenarios de `asistencia`: los 7 de «Abrir la asistencia de un grupo en una fecha»; de «La fecha está dentro de la temporada del grupo», «Abrir una fecha fuera de la temporada» y «Fecha mal escrita»; de «Grupos donde no se guarda asistencia», «Abrir un grupo que no existe», «Id de grupo más grande que el máximo» y «Abrir un grupo inactivo»; de «Quién puede abrir y guardar la asistencia», «Profesor en su grupo», «Profesor abre un grupo ajeno», «Profesor con un grupo que no existe» y «Admin en cualquier grupo»: 16 Scenarios.
  - El permiso como dependencia encadenada a `exigir_rol`, la consulta con `LEFT JOIN` y el esquema `AsistenciaDelGrupo` según design, «Rutas», «El servicio» y «Una sola respuesta para abrir y para guardar». `_id_posible` pasa a `app/services/comunes.py` y el servicio de alumnos lo importa de ahí: los tests de `alumnos` siguen en verde sin tocarlos.
  - **Se verifica con** los 16 tests en rojo por el motivo correcto y después en verde, incluido el que comprueba que cada alumno trae exactamente cuatro campos; `docs/api/openapi.json` regenerado; `python tasks.py test`, `lint` y `typecheck` en verde.
- [x] 2.2 Con la skill `backend-feature`, construir `PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}` en el mismo router, según estos Scenarios de `asistencia`: los 6 de «Guardar la asistencia de un grupo en una fecha»; los 5 de «El cuerpo del guardado»; de «La fecha está dentro de la temporada del grupo», «Primer día de la temporada», «Día anterior al inicio», «Último día de la temporada» y «Día posterior al cierre»; de «Grupos donde no se guarda asistencia», «Guardar en un grupo que no existe», «Guardar en un grupo de una temporada cerrada» y «Guardar en un grupo inactivo»; de «Quién puede abrir y guardar la asistencia», «Profesor guarda en un grupo ajeno», «Profesor con un grupo ajeno de una temporada cerrada y fecha fuera de ella», «Coordinador sin grupos asignados» y «Sin sesión»: 22 Scenarios.
  - Orden de las reglas, juntado de errores del cuerpo, `field_validator` de la lista vacía y escritura con `INSERT … ON CONFLICT DO UPDATE` según design, «El servicio» y «Escribir con `INSERT … ON CONFLICT DO UPDATE`». La respuesta es la misma consulta del `GET`.
  - Los tests de «no se guarda nada» cuentan los registros de `asistencia` de esa fecha antes y después. El de «Guardar la asistencia no toca nada más» cuenta las filas de todas las tablas del esquema, leídas del catálogo, para que una tabla nueva entre sola.
  - **Se verifica con** los 22 tests en rojo por el motivo correcto y después en verde, `docs/api/openapi.json` regenerado, y `python tasks.py test`, `lint` y `typecheck` en verde.

## 3. Supuesto

- [x] 3.1 Registrar en `docs/prd/aclaraciones-cliente.md`, «Preguntas abiertas», la del grupo inactivo: ¿se le puede seguir tomando asistencia, o al desactivarlo deja de tomarse? Con el **[SUPUESTO]** vigente (se consulta, no se guarda: 409) y la referencia al change `asistencia`. **Se verifica con** la entrada escrita y el Requirement «Grupos donde no se guarda asistencia» apuntando a ella.

## 4. Contrato

- [x] 4.1 Comprobar que `docs/api/openapi.json` tiene los dos endpoints nuevos con sus esquemas, que `AlumnoEnAsistencia` tiene solo `inscripcion_id`, `nombre`, `apellido` y `presente`, y que ningún endpoint existente cambió. **Se verifica con** `python tasks.py openapi-check` en verde y el diff de `openapi.json` limitado a lo nuevo.

## 5. Pantalla «Tomar asistencia»

- [x] 5.0 Con la skill `frontend-feature`, crear `src/lib/fechas.ts` con `formatearFecha`, según design, «Frontend: las fechas como texto, en `src/lib/fechas.ts`». La regla ya está en CLAUDE.md, sección Frontend.
  - Test de la función pura en `frontend/tests/lib/fechas.test.ts`, con los cinco casos del design.
  - **Se verifica con** el test en rojo por el motivo correcto (no existe el módulo) y después en verde, la huella de `frontend/tests/` intacta, y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.
- [x] 5.1 Con la skill `frontend-feature`, construir la pantalla `/asistencia` y el acceso desde el inicio, según los Requirements de `asistencia` «Pantalla «Tomar asistencia»» (4 Scenarios) y «Guardar desde la pantalla» (5), y el Scenario nuevo de `auth` «Ir a tomar asistencia» (1): 10 Scenarios.
  - Las llamadas y sus tipos en `src/lib/api.ts`; `SelectorGrupoDeAsistencia` y `ListaAsistencia` en `src/components/`; los colores `presente` y `ausente` en `src/tema.ts`; la página en `src/pages/TomarAsistencia.tsx`; la ruta en `App.tsx` y el acceso en `Inicio.tsx` (design, «Frontend: la pantalla y sus piezas»). La fecha de hoy con la fecha local, no con `toISOString()`.
  - Tests en `frontend/tests/asistencia/` con `fetch` fingido y la fecha fijada solo en `Date`. Los tests de `frontend/tests/auth/` que ya existen no se tocan.
  - **Se verifica con** los 10 tests en rojo por el motivo correcto, la huella de `frontend/tests/` intacta después de implementar, y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.

## 6. Comprobación de punta a punta

- [x] 6.1 Con la base de desarrollo migrada y la semilla cargada, la API y el frontend levantados, comprobar a mano en el navegador:
  - como `jperez` (profesor), `Grupo` ofrece solo `Delfines · Mañana` y `Delfines · Tarde`;
  - en «Delfines» mañana, con una fecha de la temporada (la semilla va del 2027-01-04 al 2027-02-26, así que hoy queda afuera y se ve el 422), marcar a Juan Pérez presente, guardar y ver `Asistencia guardada.`;
  - volver a abrir la misma fecha y ver a Juan Pérez presente; cambiarlo a ausente, guardar, y comprobar en la base que hay un solo registro;
  - como `lrodriguez` (coordinador), tomar asistencia de «Tiburones» tarde, que no tiene asignada;
  - la pantalla a 360 px de ancho, sin scroll horizontal, con los botones `Presente` / `Ausente` cómodos de tocar y recorrible con el teclado.
  - **Se verifica con** cada punto anotado como hecho en el informe de la tarea, con lo que haya fallado.
  - **Informe (14/11/2026), contra la base de desarrollo sembrada.** En `:8000` atendía un uvicorn viejo de otra sesión (PID 14288, sin las rutas nuevas) que no es de este trabajo y no se tocó; la recorrida usó una API propia en `:8001` (con `CORS_ORIGINS` para el origen de prueba) y un Vite en `:5180` con `VITE_API_URL`. La pantalla se manejó con JavaScript en la página, como en el change anterior.
    - Hecho: como `jperez`, `Grupo` ofrece solo `Delfines · Mañana` y `Delfines · Tarde`.
    - Hecho: con la fecha de hoy (2026-11-14) se ve `La fecha está fuera de la temporada del grupo, del 04/01/2027 al 26/02/2027.`
    - Hecho: en «Delfines» mañana del 2027-01-05, Juan Pérez marcado presente → `Asistencia guardada.`; al pasar al 06 queda sin tomar y al volver al 05 sigue presente; cambiado a ausente y guardado. En la base hay un solo registro de esa inscripción y fecha, con `registrado_en` actualizado.
    - Hecho: como `lrodriguez`, `Grupo` ofrece los cuatro grupos; en «Tiburones» tarde del 2027-01-07 marcó a Valentina Torres presente y guardó. Por la API, `jperez` sobre ese grupo recibe 403.
    - Hecho, medido en un iframe de 360 px: sin scroll horizontal (`scrollWidth` = `clientWidth` = 360), ningún elemento fuera del cuadro, botones `Presente` / `Ausente` de 49 px de alto entre x=33 y x=327. Orden de tabulación: `Volver al inicio`, `Grupo`, `Fecha`, los dos botones de cada alumno y `Guardar`.
    - Observación, no falla: la pantalla agrega un botón `Volver al inicio` que la spec no nombra.
- [x] 6.2 `python tasks.py test`, `lint`, `typecheck`, `openapi-check`, `front-test` y `front-lint` en verde.
  - **Estado (14/11/2026):** en verde tras el último cambio de cada lado: backend 276 tests, lint, typecheck y `openapi-check`; frontend 78 tests, `front-lint` y build.

## 7. Revisión adversarial

- [x] 7.1 Un pase del subagente `adversarial-reviewer` sobre el change terminado, antes del pull request. Rige `REVIEW.md`, «Cuándo se deja de revisar». **Se verifica con** sus hallazgos resueltos o justificados por escrito en esta tarea.
  - **Primer pase (14/11/2026):** un grave y un menor, más tres preguntas. Reabren el change con las tareas 7.2 a 7.4.
    - [GRAVE] Ningún test distingue la fecha local de hoy de la UTC: `fijarHoy` fija las 10:00 y el huso de los tests no está fijado (el CI corre en UTC). → 7.4.
    - [Menor] La respuesta de un `PUT` que llega tarde pisa la lista de otra fecha o grupo, y los campos siguen habilitados mientras se guarda. → 7.4.
    - Pregunta: ¿se puede desmarcar lo ya tomado? Decidido: no (`aclaraciones-cliente.md`, sección 4). Además, `Asistencia guardada.` no aparece sin cambios. → 7.4.
    - Pregunta: al corregir a uno, ¿cambia el autor de los demás? Decidido: no, solo cambia lo que cambió de valor, y la regla va en el backend. → 7.3.
    - Pregunta: la inscripción de otro grupo solo se probaba con un Coordinador. Decidido: se agrega el test con un Profesor. → 7.3.
  - **Resolución:** todo resuelto en 7.2 a 7.4; nada quedó justificado sin arreglar. Según `REVIEW.md`, un segundo pase solo reabre el change por un hallazgo grave.
- [x] 7.2 Incorporar al delta de `asistencia`, al design y a `aclaraciones-cliente.md` lo decidido sobre el primer pase. **Se verifica con** los Scenarios nuevos escritos: «Corregir a uno no cambia el autor de los demás», «Guardar lo mismo no cambia nada», «Profesor cuela en su grupo una inscripción de otro grupo», «Lo ya tomado sin cambios no se guarda», «Lo ya tomado no se puede desmarcar», «Lo elegido sin guardar se puede quitar» y «Mientras se guarda», más el cambio de «Un solo grupo queda elegido y abre la asistencia de hoy».
- [x] 7.3 Con la skill `backend-feature`, el `PUT` actualiza solo los registros que cambian de valor, según los Scenarios «Corregir a uno no cambia el autor de los demás», «Guardar lo mismo no cambia nada» y «Profesor cuela en su grupo una inscripción de otro grupo»: 3 Scenarios.
  - **Hecho (14/11/2026):** los dos primeros en rojo porque el autor pasaba a ser el Coordinador (`assert 2784 == 2785`), después en verde con el `where` del upsert. El del Profesor, en verde desde el principio; sin el filtro por `grupo_id` del servicio da 200 en vez de 422, así que sostiene la frontera. Huella de los tests intacta; 279 tests, `lint`, `typecheck` y `openapi-check` en verde (el contrato no cambia).
  - `where` en el `DO UPDATE`, según design, «Escribir con `INSERT … ON CONFLICT DO UPDATE`». Los tests fijan el `registrado_en` previo a mano.
  - **Se verifica con** los dos primeros tests en rojo por el motivo correcto y después en verde (el del Profesor ya pasa: fija una frontera que existía sin test, y se comprueba que se pondría en rojo quitando el filtro por `grupo_id`); `python tasks.py test`, `lint`, `typecheck` y `openapi-check` en verde.
- [x] 7.4 Con la skill `frontend-feature`, el huso fijo de los tests y la pantalla según los Scenarios «Un solo grupo queda elegido y abre la asistencia de hoy» (modificado), «Lo ya tomado sin cambios no se guarda», «Lo ya tomado no se puede desmarcar», «Lo elegido sin guardar se puede quitar» y «Mientras se guarda»: 5 Scenarios.
  - `TZ=America/Argentina/Buenos_Aires` en `vite.config.ts`, en `tasks.py` y en el workflow del CI; `fijarHoy` a las 21:30.
  - La respuesta del `PUT` se descarta si el grupo o la fecha cambiaron mientras se guardaba (design, «Marcas y guardado»).
  - **Se verifica con** el rojo a propósito: con `hoyLocal()` reemplazada por `toISOString()`, `python tasks.py front-test` se pone en rojo, y se revierte; los tests nuevos en rojo por el motivo correcto y después en verde; la huella de `frontend/tests/` intacta después de implementar; `python tasks.py front-test` y `front-lint` en verde.
  - **Hecho (14/11/2026):**
    - Rojo a propósito, dos veces: antes de implementar y sobre el código ya implementado. Con `toISOString()`, `python tasks.py front-test` da 6 tests en rojo, entre ellos «Fecha en 2027-01-05» con `Received: 2027-01-06`. `TZ=UTC npx vitest run` también da rojo, así que `vite.config.ts` se impone al huso de la máquina. Revertido.
    - El huso iba primero como `process.env.TZ` arriba de `vite.config.ts`, pero rompió el `tsc -b` del build (`tsconfig.node.json` no tiene los tipos de Node). Pasó a `test.env` de Vitest, y el rojo a propósito se repitió después del cambio. Es la única diferencia de la huella congelada, y la hizo quien orquesta, no el implementer.
    - Tests nuevos: 3 en rojo por el motivo correcto (Guardar habilitado sin cambios, Martín desmarcable, campos habilitados al guardar). «Lo elegido sin guardar se puede quitar» estaba en verde desde antes y fija el límite de la regla.
    - En verde: frontend 82 tests, `front-lint` y build.
    - El descarte de la respuesta tardía del `PUT` no tiene test: con los campos deshabilitados no se puede provocar desde la pantalla (design, «Marcas y guardado»).

## Workflow follow-up

- Comprobar el change con `/openspec-verify-change` y archivarlo con `/openspec-archive-change`, que crea `openspec/specs/asistencia` y funde el delta de `auth`.
- Al archivar, reemplazar los criterios de HU-GA-04 en `5-historias-de-usuario.md` por un puntero a la spec de `asistencia`.
- Pull request de `feat/asistencia` hacia la rama de entrega.
