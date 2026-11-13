# Design

## Context

Ver proposal.md, «Why». Lo que ya existe y condiciona el enfoque:

- `grupo` y `grupo_profesor` existen (change 2). `grupo` ya tiene `uq_grupo_id_temporada_turno (id, temporada_id, turno)`, pensada para la FK compuesta de `inscripcion`.
- Los tipos `turno` y `categoria_familia` ya existen en la base; los creó la migración `a64e83ff89ab`, que también los borra en su downgrade. Este change los usa y no los vuelve a crear ni a borrar.
- `exigir_rol(...)` en `app/core/deps.py` declara los roles por endpoint. No hay todavía ninguna dependencia de «grupo propio» del Profesor.
- El 422 de validación ya pasa por un manejador propio en `app/main.py` que quita `input`. Los `msg` llegan en inglés.
- No hay ningún endpoint de grupos: el Profesor no tiene de dónde sacar sus grupos para elegir.
- En el frontend, `api.ts` borra el token ante un 401, pero `sesion.tsx` no se entera (diferido del change 3). No hay nada en `src/components/`.

## Goals / Non-Goals

**Goals:**
- El alta completa en una sola transacción: o queda todo (familia, personas, vínculos, alumno, inscripción) o no queda nada.
- El permiso del Profesor resuelto antes de escribir, y los listados filtrados en la consulta.
- Que cada rechazo de la API llegue en castellano y atado a su campo, para que la pantalla lo pegue donde corresponde.

**Non-Goals:**
- Endpoints de lectura o edición de alumnos y familias, más allá de las dos búsquedas.
- Búsqueda tolerante a tildes (ver Risks).
- Un componente de fecha propio o una librería de selectores de fecha.

## Decisions

### Esquema: las cinco tablas del modelo, sin las columnas «después»

Se crean `familia`, `persona`, `alumno`, `familia_persona` e `inscripcion` como dice `3-modelo-de-datos.md`, con estas decisiones:

- **Columnas que no entran:** `alumno.alergias`, `alumno.condiciones_medicas` y las de consentimiento (llegan juntas con HU-AF-06/07, con su `CHECK`), e `inscripcion.modalidad_sugerida` (HU-CC-05). Una columna sin quien la escriba es una columna que nadie prueba.
- **Columna que sí entra aunque sea «después»:** `familia_persona.contacto_emergencia`, `NOT NULL DEFAULT false`. Los dos `CHECK` del vínculo (`NOT es_tutor OR autorizado_retiro` y `es_tutor OR autorizado_retiro OR contacto_emergencia`) quedan así en su forma final, y HU-AF-08 no tiene que reescribir restricciones con datos adentro.
- **FK compuesta** `inscripcion (grupo_id, temporada_id, turno) → grupo (id, temporada_id, turno)` y `UNIQUE (alumno_id, temporada_id, turno)`. `temporada_id` y `turno` los copia la API del grupo; la FK impide que no coincidan.
- `inscripcion.creado_por` → `usuario`, `NOT NULL`. Ninguna FK con `ON DELETE CASCADE`.
- **Índices:** `alumno (familia_id)`, `familia_persona (persona_id)` (la PK ya cubre `familia_id` primero), `inscripcion (grupo_id)`, y uno funcional `lower(apellido) varchar_pattern_ops` sobre `alumno` para la búsqueda por prefijo. `persona.dni` ya es `UNIQUE`, que es su índice.
- `persona.dni varchar(15) NULL UNIQUE` y `persona.telefono varchar(30) NOT NULL`, con la justificación de nulabilidad del modelo de datos.

Alternativa descartada: crear todas las columnas del modelo de una vez. Ahorra una migración más adelante, pero deja columnas médicas de menores en la base sin pantalla, sin permiso y sin test.

### La etiqueta es una vista, no una columna ni un cálculo en Python

`v_familia_etiqueta (familia_id, etiqueta)` con `DISTINCT ON (familia_id) … ORDER BY familia_id, fecha_nacimiento, id`, y la etiqueta como `apellido || ' – ' || nombre`. El desempate por `id` es el «se registró primero» de la spec (mellizos).

- La búsqueda ordena por etiqueta y corta en 20: tiene que pasar en SQL. Calcularla en Python obligaría a traer todas las coincidencias para ordenarlas.
- En SQLAlchemy se declara como `Table` sobre un `MetaData()` **propio**, no sobre `Base.metadata`: si estuviera en `Base.metadata`, `autogenerate` propondría crearla como tabla en cada migración futura.
- La vista se crea y se borra con `op.execute` escrito a mano en la migración: autogenerate no la ve.

### El alta, en un servicio, con las reglas en un orden fijo

`app/services/alumnos.py` expone `registrar_alumno(sesion, usuario, entrada)`. El router solo traduce. Orden de comprobación:

1. **Pydantic** valida forma y largos (422 con los mensajes traducidos).
2. **Permiso del Profesor:** existe la fila `grupo_profesor (grupo_id, usuario.id)`; si no, 403 y fin, exista o no el grupo. Va primero para que el Profesor no use el alta como oráculo de los grupos ajenos (si existen, si están activos, de qué temporada son: hallazgo del pase adversarial, que dejaba un 422 por grupo inactivo antes del 403), y antes del 4 para que tampoco lo use para saber qué familias o personas existen fuera de sus grupos.
3. **Grupo:** existe, está activo, es de la temporada vigente (422 en `grupo_id`). Para el Profesor solo se alcanza con un grupo propio.
4. **Familia y personas:** `familia_id` xor `categoria`; la familia existe; cada `persona_id` existe y no está repetido ni ya vinculado; cada DNI nuevo no está cargado; con familia nueva, al menos un tutor. Estas reglas cruzan campos, así que viven acá y no en un `model_validator` de Pydantic, que las pegaría a la raíz del cuerpo en lugar de al campo. **Se juntan todas** las de este paso y se devuelven en un solo 422, para que la pantalla marque todos los campos de una vez.
5. **Escritura:** familia (si es nueva), personas nuevas, vínculos, alumno, inscripción. Un `flush` por cada inserción cuyo id hace falta después (los modelos no declaran `relationship()`) y un único commit: todo queda en la transacción de la petición. El `flush` de cada persona nueva es donde se atrapa la carrera del DNI, con el índice de esa persona en el alta.

La regla de Profesor no es una dependencia de FastAPI, a diferencia de lo que sugiere CLAUDE.md para «el grupo o el alumno de los suyos»: el grupo viene en el cuerpo, y una dependencia que lea el cuerpo antes que el endpoint duplica la validación. Cuando haya rutas con el grupo en la URL (asistencia, change 5), ahí sí va una dependencia.

**Carrera en el DNI.** Dos altas simultáneas con el mismo DNI nuevo pasan el paso 4 las dos; la segunda choca con el `UNIQUE`. El servicio captura ese `IntegrityError` (por el nombre de la restricción) y responde el mismo 422 en `personas.N.dni`.

**Todas las personas del alta quedan con `autorizado_retiro` en true.** La sección se llama «Personas autorizadas a retirar» y el change no carga contactos de emergencia.

### Rechazos de reglas con la forma del 422

Una excepción `ReglaIncumplida(errores: list[tuple[loc, msg]])` en `app/core/` y su manejador en `main.py`, que responde `{"detail": [{"loc": [...], "msg": ..., "type": "regla_de_negocio"}]}`. Es la misma forma del 422 de Pydantic, así `traducirError` de `api.ts` la reparte por campo sin cambios. Las reglas sin campo (el permiso del Profesor, la persona que no aparece por DNI) siguen siendo `HTTPException` con `detail` como texto.

### Traducción de los 422 de Pydantic: por `type`, en el manejador

El manejador de `RequestValidationError` que ya existe reemplaza `msg` según `type`:

| `type` de Pydantic | `msg` |
|---|---|
| `missing` | `Este dato es obligatorio.` |
| `string_too_long`, `too_long` | `Puede tener hasta {max_length} caracteres.` (de `ctx`) |
| `string_too_short` con `min_length` 1 | `No puede quedar vacío.` |
| `string_too_short` con `min_length` mayor que 1 | `Tiene que tener al menos {min_length} caracteres.` (de `ctx`). Si no, un apellido de una letra en la búsqueda diría «vacío». |
| `date_parsing`, `date_from_datetime_parsing`, `date_type` | `La fecha no es válida.` |
| `int_parsing`, `int_type` | `Tiene que ser un número entero.` |
| `enum`, `literal_error` | `El valor no es una de las opciones válidas.` |
| `regla_de_negocio` (propio) | se deja el `msg` |
| cualquier otro | `El valor no es válido.` |

Los validadores propios (fecha futura) levantan `PydanticCustomError("regla_de_negocio", "<mensaje>")`, así su mensaje pasa intacto. Los textos se recortan antes de medir con `Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]`.

La tabla se prueba entera: además de los Scenarios, un test llama a la función pura con cada `type` de la tabla (y con uno desconocido) y comprueba su mensaje. Un `type` mal escrito en la tabla cae al genérico sin que ningún Scenario lo note (hallazgo del pase adversarial).

**Caracteres de control.** Todo texto que llega a la base (nombre, apellido y teléfono del alta, el apellido y el DNI de las búsquedas) pasa por el mismo validador que ya usa el login: un carácter de control da `PydanticCustomError("regla_de_negocio", "No puede tener caracteres de control.")`. Sin eso, un NUL llega a Postgres y la API responde 500 (hallazgo del pase adversarial, comprobado con una sonda).

Alternativa descartada: traducir en el frontend. El contrato quedaría en inglés y cada cliente tendría que repetir la tabla.

### Normalización del DNI en un solo lugar

Una función `normalizar_dni` (quita espacios, puntos y guiones, pasa a mayúsculas; admite letras por los documentos extranjeros) la usan el esquema del alta y el parámetro de la búsqueda. Se guarda normalizado; el largo de 15 se mide después de normalizar.

### Endpoints, roles y filtro del Profesor

| Endpoint | Roles | Filtro del Profesor |
|---|---|---|
| `GET /api/v1/grupos[?fecha_nacimiento=]` | Admin, Coordinador, Profesor | `JOIN grupo_profesor ON … AND usuario_id = :yo` en la misma consulta. |
| `GET /api/v1/familias?apellido=` | Admin, Coordinador, Profesor | Ninguno, por decisión del usuario en la propuesta: el hermano puede estar en un grupo ajeno y Acl. 9 le deja ver los datos de familia. Lo que se limita es la respuesta: solo `id`, `etiqueta`, `categoria`. |
| `GET /api/v1/personas?dni=` | Admin, Coordinador, Profesor | Ninguno: coincidencia exacta y solo `id`, `nombre`, `apellido`. No se puede recorrer el padrón. |
| `POST /api/v1/alumnos` | Admin, Coordinador, Profesor | Paso 3 del alta. |

Todos con `exigir_rol(...)`, un router por capability (`grupos.py`, `familias.py`, `personas.py`, `alumnos.py`) y `response_model` propio. La búsqueda de familias escapa `%` y `_` del texto antes del `LIKE`. `sugerido` se calcula en la consulta como `:fecha BETWEEN nacimiento_desde AND nacimiento_hasta` (false sin fecha). El orden por turno sale del orden del tipo `turno` (`manana` antes que `tarde`).

### Frontend: el aviso de 401 por suscripción

`api.ts` mantiene un conjunto de oyentes (`alPerderSesion(fn)`, que devuelve la función para desuscribirse) y los llama cuando una llamada **que salió con token** recibe 401. `ProveedorSesion` se suscribe y hace lo mismo que `salir()`. `RutaProtegida` ya manda al ingreso cuando no hay token. El 401 del login no avisa, porque sale sin token.

Alternativa descartada: que cada pantalla atrape el 401. Es exactamente el olvido que el diferido del change 3 quería evitar.

### Frontend: la pantalla y sus piezas

- `src/pages/RegistrarAlumno.tsx` en `/alumnos/nuevo`, dentro de `RutaProtegida`. El acceso desde `Inicio.tsx` es un `Button` con `component={Link}`.
- Piezas nuevas en `src/components/`, porque son de interfaz y se van a reusar (la ficha y la reinscripción de HU-AF-11 eligen grupo y familia):
  - `SelectorGrupo`: `TextField select` con los grupos, la marca `(sugerido)` y la elección automática cuando hay un solo sugerido.
  - `SelectorFamilia`: el `RadioGroup` nueva/existente, la `Categoría` y el `Autocomplete` de búsqueda (desde 2 caracteres, con 300 ms de espera entre teclas).
  - `ListaPersonas`: las filas de personas nuevas o reutilizadas, la búsqueda por DNI y la casilla `Tutor`.
- La fecha es un `TextField type="date"`: el navegador da el selector y el valor ya llega como `AAAA-MM-DD`. Sin dependencias nuevas.
- Los textos `Mañana`/`Tarde` y `Socio`/`Empleado`/`No socio` van junto al texto del rol que ya existe, una sola tabla por enumerado.
- Errores: `porCampo` trae claves como `nombre` o `personas.0.dni`. La lista de personas se manda en el orden en que se ve, así el índice de la clave es la fila. Lo que no tiene campo va a un `Alert` general. Esto resuelve, para este formulario, el diferido del change 3 de los 422 con varios campos.
- `api.ts` suma `listarGrupos(fecha?)`, `buscarFamilias(apellido)`, `buscarPersonaPorDni(dni)` y `registrarAlumno(entrada)`, con los tipos copiados del contrato. Ningún campo de monto.
- Tests en `frontend/tests/alumnos/`, con `fetch` fingido y el montaje de `frontend/tests/auth/montar.tsx`.
- `SelectorGrupo` distingue el grupo elegido a mano del elegido por la sugerencia: este último lo reemplaza la sugerencia de una fecha nueva; el primero, nunca.
- El bloque `test` de `vite.config.ts` fija `testTimeout: 10000`. Los tests que completan el alta tardan entre 2 y 4 s con la suite entera (jsdom con las hojas de estilo de MUI), demasiado cerca del plazo por defecto de 5 s para un CI más lento. Lo decidió la persona a cargo, porque el archivo entra en la huella.

### Semilla

Las tres familias se cargan con los modelos, en la misma transacción que el resto, después de los grupos. La comprobación de base vacía suma `familia` y `persona`.

### Supuesto registrado

La reutilización solo por DNI exacto es **[SUPUESTO]**. Se agrega a «Preguntas abiertas» de `aclaraciones-cliente.md` como «Reutilizar una persona ya cargada»: si el cliente quiere buscar por nombre, cambia el endpoint de personas y su Requirement, no el alta.

## Reversibilidad

- **Entra** una migración, `crear_familias_y_alumnos`: las cinco tablas, sus restricciones e índices, y la vista `v_familia_etiqueta`. Los tipos `turno` y `categoria_familia` se referencian con `create_type=False`.
- **Downgrade:** `DROP VIEW v_familia_etiqueta`, después las tablas en orden inverso a sus FK (`inscripcion`, `familia_persona`, `alumno`, `persona`, `familia`). **No** borra `turno` ni `categoria_familia`: son de la migración anterior y los siguen usando `grupo` y los descuentos.
- **Filas existentes:** no hay; las tablas son nuevas y ninguna tabla existente cambia. Un downgrade con datos cargados los pierde: es aceptable porque no hay producción todavía, y queda dicho acá para cuando la haya.
- Se prueba en los dos sentidos contra la base de pruebas (`upgrade head` → `downgrade -1` → `upgrade head`), con la skill `revisar-migracion`.

## Risks / Trade-offs

- [La búsqueda no ignora tildes: `Perez` no encuentra `Pérez`] → Se documenta; la pantalla muestra «Sin resultados» y el staff prueba con la tilde. `unaccent` requiere una extensión de PostgreSQL y un índice distinto; se agrega si el uso lo pide.
- [Un Profesor puede listar etiquetas de familias de todo el club, 20 por vez] → Decisión del usuario: hace falta para el hermano en otro grupo. La respuesta no trae nada más que la etiqueta (un apellido y un nombre) y la categoría.
- [Quien no tiene DNI cargado se duplica si lo cargan dos familias] → Consecuencia del [SUPUESTO]. Sin DNI no hay forma segura de saber que es la misma persona.
- [Dos altas del mismo chico crean dos alumnos] → Fuera de alcance (proposal). La etiqueta de familia lo deja a la vista.
- [La vista se recalcula en cada lectura] → Con cientos de familias es irrelevante; el índice sobre `alumno (familia_id)` la mantiene barata.
- [Un `msg` traducido por `type` puede no calzar con un validador nuevo] → El caso por defecto (`El valor no es válido.`) nunca sale en inglés; un test de la tabla cubre cada `type` conocido.
- [Un Profesor puede probar DNIs consecutivos en `GET /personas` y juntar nombre y apellido de los adultos que encuentre] → No hay límite de pedidos en el sistema. Se acepta para el lote 1 y queda registrado en la pregunta abierta «Reutilizar una persona ya cargada» de `aclaraciones-cliente.md`; un límite de pedidos va antes de producción, junto con la mitigación de HU-UT-08.
- [Un Profesor puede sumar como autorizado, en una familia de su grupo, a una persona de cualquier otra familia] → Es lo que pide Acl. 3 (una persona autorizada en varias familias). La persona solo se identifica por su DNI exacto.

## Migration Plan

`python tasks.py migrate` aplica la migración. Volver atrás es `alembic downgrade -1`, ver «Reversibilidad». La semilla se vuelve a correr sobre una base vacía.
