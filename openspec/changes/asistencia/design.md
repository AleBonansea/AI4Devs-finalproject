# Design

## Context

- Existen `grupo`, `grupo_profesor` e `inscripcion` (changes 2 y 4). `inscripcion` tiene `UNIQUE (alumno_id, temporada_id, turno)` e índice por `grupo_id`; cada turno es una inscripción distinta, así que la asistencia cuelga de la inscripción y no del alumno.
- `GET /api/v1/grupos` ya devuelve los grupos activos de la temporada vigente, con el filtro del Profesor como `JOIN` a `grupo_profesor`. La pantalla lo reusa sin cambios.
- El alta de alumnos fijó dos patrones que acá se repiten: el permiso del Profesor se mira **antes** que el grupo, para que un grupo ajeno dé 403 exista o no; y `ReglaIncumplida` responde reglas atribuibles a un campo del cuerpo con la forma del 422 de Pydantic (su manejador antepone `body` al `loc`).
- `4-especificaciones-de-la-api.md` (Entrega 1) documentó el `PUT` con un recorte de 3 endpoints. Este change sigue su ruta, su cuerpo y sus códigos, salvo dos desvíos explicados abajo.
- `api.ts` ya tiene `api.put` y reparte los 422 por campo. Un `detail` de texto llega como mensaje general.

## Goals / Non-Goals

**Goals:**
- Guardar es idempotente y seguro ante dos personas guardando a la vez: nunca un `IntegrityError` ni un registro duplicado.
- Un Profesor no aprende nada de un grupo ajeno: ni si existe, ni de qué temporada es, ni quién está inscripto.
- Una sola forma de respuesta para abrir y para guardar, que la pantalla pinta tal cual.

**Non-Goals:**
- Historial de correcciones. `registrado_por` y `registrado_en` dicen quién y cuándo tocó el registro por última vez, como dice el modelo; no hay tabla de auditoría.
- Optimizar para grupos grandes: un grupo tiene decenas de alumnos, no miles.

## Decisions

### Esquema: la tabla `asistencia` del modelo, tal cual

| Columna | Tipo | Restricción |
|---|---|---|
| `id` | bigint | PK |
| `inscripcion_id` | bigint | NOT NULL, FK `fk_asistencia_inscripcion` → `inscripcion.id`, sin cascada |
| `fecha` | date | NOT NULL |
| `presente` | boolean | NOT NULL, sin default: que nadie quede presente por omisión |
| `registrado_por` | bigint | NOT NULL, FK `fk_asistencia_registrado_por` → `usuario.id` |
| `registrado_en` | timestamptz | NOT NULL, `server_default now()` |

- `UNIQUE (inscripcion_id, fecha)` como `uq_asistencia_inscripcion_fecha`. Es la regla del escenario 2 y además el índice de las dos consultas (por inscripción y fecha). No hace falta otro índice: `registrado_por` no se consulta.
- No usa `MarcaDeCreacion`: `creado_en` diría cuándo se tomó por primera vez, y el modelo pide cuándo se tocó por última vez. Por eso `registrado_en` se reescribe en cada corrección con la hora de la base (`func.now()`), no con la de Python, por la misma razón que `MarcaDeCreacion`.
- La regla «la fecha dentro de la temporada» no es un `CHECK`: cruza tablas. La valida la API.

### Rutas: un router `asistencias.py` bajo `/grupos/{grupo_id}/asistencias/{fecha}`

| Ruta | Roles | Filtro del Profesor |
|---|---|---|
| `GET /api/v1/grupos/{grupo_id}/asistencias/{fecha}` | Admin, Coordinador, Profesor | Dependencia `grupo_asignado`: 403 si no existe `grupo_profesor (grupo_id, usuario.id)`. Después, la consulta trae solo inscripciones con `grupo_id` igual al del path, así que nunca sale una fila de otro grupo. |
| `PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}` | Admin, Coordinador, Profesor | La misma dependencia. Las inscripciones del cuerpo se comprueban contra ese `grupo_id` en la consulta. |

- **El permiso es una dependencia de FastAPI**, encadenada sobre `exigir_rol(...)`. FastAPI resuelve las subdependencias antes que el cuerpo y que los demás parámetros, y una `HTTPException` en ellas corta ahí: el 403 gana a cualquier 404, 409 o 422, como piden los Scenarios del Profesor. Admin y Coordinador pasan sin consulta.
- Un `grupo_id` fuera del rango de `bigint` se trata como inexistente (404) o, para el Profesor, como no asignado (403), sin llegar a Postgres. `_id_posible` del servicio de alumnos se mueve a un lugar común (`app/services/comunes.py`) para no copiarlo.
- `fecha` es un parámetro `date` del path. Mal escrita, la valida FastAPI y el manejador existente la traduce a `La fecha no es válida.`

### El servicio: reglas en un orden fijo

`app/services/asistencias.py`, con dos funciones, `abrir_asistencia` y `guardar_asistencia`.

1. Rol y permiso del Profesor (dependencias): 401, 403.
2. El grupo existe: 404 `El grupo no existe.` Se lee junto con su temporada (`fecha_inicio`, `fecha_cierre`, `estado`) en una sola consulta.
3. Solo al guardar: temporada cerrada → 409; grupo inactivo → 409 **[SUPUESTO]**.
4. La fecha está en `[fecha_inicio, fecha_cierre]`: si no, 422 con `detail` de texto y las fechas en `DD/MM/AAAA`.
5. Solo al guardar, el cuerpo: se juntan **todos** los errores por elemento (repetida: el segundo y siguientes; ajena o inexistente: una consulta `SELECT id FROM inscripcion WHERE id IN (...) AND grupo_id = :g`) y se devuelven en un solo `ReglaIncumplida`, como el paso 4 del alta.
6. Escribe y relee (ver abajo).

**Por qué 409 y no 422 para el grupo cerrado o inactivo**, cuando el alta de alumnos responde 422 en `grupo_id`: allá el grupo es un campo del cuerpo que la persona eligió y puede cambiar en el formulario; acá está en el path y no hay campo donde pegar el error. Es un conflicto con el estado del recurso, que es lo que dice `4-especificaciones-de-la-api.md`.

**Por qué la fecha fuera de temporada es un `detail` de texto y no un `ReglaIncumplida`:** su manejador antepone `body` al `loc`, y la fecha no está en el cuerpo. En la pantalla aparece como mensaje general, que es donde tiene sentido.

**Lista vacía**: un `field_validator` en el esquema lanza `PydanticCustomError("regla_de_negocio", "Tiene que haber al menos un alumno.")`. Con `Field(min_length=1)` el `type` sería `too_short` y el manejador lo traduciría al genérico `El valor no es válido.` No se pone tope de largo: cada elemento tiene que ser una inscripción distinta del grupo, así que una lista más larga que el grupo ya falla en el paso 5. Un tope traería además el problema conocido de `too_long`, que habla de «caracteres» (deuda anotada en `familias-y-alumnos`, tarea 9.1).

### Escribir con `INSERT … ON CONFLICT DO UPDATE`

Un solo `insert(Asistencia).values([...]).on_conflict_do_update(constraint="uq_asistencia_inscripcion_fecha", set_={presente, registrado_por, registrado_en: func.now()})` del dialecto de PostgreSQL.

- Alternativa descartada: leer los registros existentes y decidir insert o update en Python. Dos personas guardando la misma fecha a la vez pasarían las dos el «no existe» y la segunda chocaría con el `UNIQUE` (500). El upsert lo resuelve la base: gana la última escritura, que es lo esperable al corregir.
- Es una sola sentencia, así que todo o nada sin manejo extra. Las validaciones del paso 5 corren antes, y si alguna falla no se escribe nada.

### Una sola respuesta para abrir y para guardar

`AsistenciaDelGrupo { grupo_id, grupo, turno, fecha, alumnos: [AlumnoEnAsistencia { inscripcion_id, nombre, apellido, presente: bool | None }] }`.

- La consulta: `inscripcion JOIN alumno LEFT JOIN asistencia ON asistencia.inscripcion_id = inscripcion.id AND asistencia.fecha = :fecha WHERE inscripcion.grupo_id = :grupo_id ORDER BY alumno.apellido, alumno.nombre, inscripcion.id`. El `LEFT JOIN` da el `presente` null de quien no se tomó; el `inscripcion.id` final desempata dos homónimos para que el orden sea estable.
- El `PUT` responde con la misma consulta corrida después del upsert. **Desvío de `4-especificaciones-de-la-api.md`**, que devolvía solo los registros enviados con `registrado_por`: la pantalla vuelve a pintar la lista entera, y con una sola forma hay un esquema y un tipo menos. `registrado_por` no se expone: la historia no pide mostrarlo.
- `AlumnoEnAsistencia` declara solo esos cuatro campos: el esquema es lo que impide que un dato médico o de familia se cuele cuando lleguen esas columnas.
- El orden lo da la intercalación de la base. Ver riesgos.

### Frontend: la pantalla y sus piezas

- `src/lib/api.ts`: tipos `AsistenciaDelGrupo`, `AlumnoEnAsistencia`, `AsistenciaEntrada`, y las funciones `abrirAsistencia(grupoId, fecha)` y `guardarAsistencia(grupoId, fecha, asistencias)`.
- `src/components/SelectorGrupoDeAsistencia.tsx`: el campo `Grupo` de esta pantalla, con la misma escritura que el del alta (`Delfines · Mañana`, con `NOMBRE_DEL_TURNO`) y la regla de elegir el único grupo. No se reusa `SelectorGrupo`: su regla es la sugerencia por fecha de nacimiento y la elección a mano que no se pisa, que acá no existe; meterle un modo más lo vuelve dos componentes en uno.
- `src/components/ListaAsistencia.tsx`: una fila por alumno con `Nombre Apellido` y un `ToggleButtonGroup` exclusivo `Presente` / `Ausente`, de ancho completo en el celular y con al menos 44 px de alto por botón, para el dedo. Los colores de lo elegido salen de `tema.ts`: se agregan `presente` (igual a `marca`) y `ausente` (igual a `deuda`), con nombre por uso. Sin elegir, ninguno de los dos está marcado (`value={null}`).
- `src/pages/TomarAsistencia.tsx` en `/asistencia`: estado `marcas: Record<inscripcion_id, boolean | null>` que arranca de la respuesta del `GET`; `Guardar` deshabilitado si ninguna marca es distinta de null; el `PUT` lleva las marcas no null. Al cambiar grupo o fecha se vuelve a pedir y se descartan las marcas sin guardar. Mensajes en un `Alert`: éxito `Asistencia guardada.`, error con el `mensaje` del `ErrorDeApi`.
- **La fecha de hoy se arma con la fecha local**, año, mes y día del `Date` del dispositivo, nunca con `toISOString()`, que da la fecha en UTC: en Argentina, después de las 21 h sería mañana.
- `Fecha` es un `TextField type="date"`, como `Fecha de nacimiento` en el alta.
- Ruta en `App.tsx` dentro de `RutaProtegida`; acceso `Tomar asistencia` en `Inicio.tsx`, junto a `Registrar alumno`.
- Tests en `frontend/tests/asistencia/` con `fetch` fingido y la fecha fijada con `vi.useFakeTimers({ toFake: ["Date"] })`, para no dormir los temporizadores de `userEvent`.

### Frontend: las fechas como texto, en `src/lib/fechas.ts`

Regla nueva de CLAUDE.md, sección Frontend: toda fecha que se muestra como texto, fuera de un campo de formulario, pasa por `src/lib/fechas.ts` y sale en `dd/mm/aaaa`. Nunca se usa `toLocaleDateString` suelto ni se arma el texto a mano. Es el mismo criterio que `nombres.ts`: un solo lugar. Los campos siguen con `<input type="date">`, cuyo valor es siempre ISO.

- `formatearFecha(fecha: string | Date): string`.
  - Con un texto `AAAA-MM-DD`, que es como la API manda las fechas, lo corta por partes y **no pasa por `Date`**. `new Date("2027-01-05")` es la medianoche UTC, que en Argentina todavía es el 04/01.
  - Con un `Date`, usa el día, el mes y el año locales.
  - Con cualquier otro texto lanza `Error`: es un error de programación y tiene que verse en los tests, no convertirse en una fecha rara en pantalla.
- El test es de la función pura, en `frontend/tests/lib/fechas.test.ts`, con estos casos:
  - `"2027-01-05"` da `05/01/2027`.
  - `"2027-02-26"` da `26/02/2027`: el día es mayor que 12, así que un día y un mes invertidos no pasan.
  - `new Date(2027, 0, 5, 23, 30)` da `05/01/2027`. Con `toISOString` en un huso detrás de UTC daría el 06.
  - `"05/01/2027"` y `"2027-1-5"` lanzan `Error`.
- **Asistencia no muestra ninguna fecha como texto.** La fecha está en el campo `Fecha`, y el 422 de fecha fuera de temporada llega ya formateado desde la API. Así que en este change `fechas.ts` se crea sin usarse en ninguna pantalla. Ninguna pantalla existente muestra fechas como texto (se buscó `toLocaleDateString`, `toLocaleString`, `toISOString` e `Intl.DateTimeFormat` en `frontend/src`, sin resultados), así que no hay nada que migrar.
- La fecha de hoy para el valor inicial de `Fecha` no es una fecha para mostrar y queda fuera de este módulo. Sigue la regla de la sección anterior: fecha local, nunca `toISOString()`.

### Supuesto registrado

Grupo inactivo: se consulta, pero no se le toma asistencia nueva (409). Va como pregunta abierta en `docs/prd/aclaraciones-cliente.md`, con referencia a este change. Si el cliente dice lo contrario, se borra un `if` y se invierte un Scenario.

## Reversibilidad

- **Migración**: `crear_asistencia`, con `--autogenerate` y revisada con la skill `revisar-migracion`. `upgrade` crea la tabla, sus dos FK y la `UNIQUE`. No crea tipos enumerados.
- **Downgrade**: `op.drop_table("asistencia")`, que se lleva sus restricciones. No toca `inscripcion` ni `usuario`.
- **Filas existentes**: ninguna tabla existente cambia, así que no hay datos que migrar. Bajar la migración con asistencia cargada **pierde esa asistencia**; es aceptable solo antes de producción, que es donde se prueba el ida y vuelta.
- Se prueba `upgrade head` → `downgrade -1` → `upgrade head` contra la base de pruebas.

## Risks / Trade-offs

- [El orden alfabético depende de la intercalación de la base: con `C`, «Álvarez» quedaría después de «Zárate»] → Los datos actuales no lo muestran. Si aparece, se ordena por una expresión con `unaccent` o una intercalación ICU en la consulta, sin tocar la spec.
- [Un Profesor puede probar ids de grupo y distinguir los suyos de los ajenos] → No aprende nada más que eso: el 403 es el mismo para un grupo ajeno, inexistente, cerrado o inactivo, y no trae datos.
- [Quien corrige pisa a quien tomó: `registrado_por` pasa a ser el último] → Es lo que dice el modelo. Si el cliente pide historial, es otra tabla.
- [Al cambiar grupo o fecha con marcas sin guardar, se pierden sin aviso] → Aceptado para este lote; un aviso de «cambios sin guardar» es una mejora de pantalla que no pide ninguna historia.
- [Sin red en el club, el guardado falla] → `api.ts` ya da `No se pudo conectar con el servidor. Revisá tu conexión.` y las marcas se conservan para reintentar.

## Migration Plan

1. `python tasks.py migrate` aplica `crear_asistencia`. No requiere datos ni pasos manuales; la semilla no cambia.
2. Rollback: `alembic downgrade -1` desde `backend/`, con la pérdida de asistencia de la sección anterior.
