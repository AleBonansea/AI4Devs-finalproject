# CLAUDE.md

## Producto

Sistema de administración para la escuelita de verano del club sede: gestiona fichas de alumnos, documentación, asistencia por grupo y turno, cuenta corriente por familia, tesorería general y canon al club, por temporada.

**Fuentes de verdad, en este orden:**

1. `docs/prd/aclaraciones-cliente.md` — decisiones del cliente posteriores al PRD. **Prevalece** cuando contradice al PRD.
2. `docs/prd/prd-escuelita-de-verano.md` — transcripción fiel del PRD original. No se modifica.
3. `docs/architecture/documento-tecnico.md` — stack, despliegue y seguridad.
4. `openspec/specs/<capability>/spec.md` — el comportamiento especificado, un Scenario por caso. Es lo que los tests comprueban y manda sobre el código. Mientras una capability está dentro de un change, manda el delta en `openspec/changes/<change>/specs/`.
5. `docs/product/historias-backlog.md` y `5-historias-de-usuario.md` — las historias y el alcance: qué entra en este lote. Los criterios de las historias ya construidas viven en las specs, no acá.

**El prototipo no es especificación.** Las capturas de `docs/previews/` son de un prototipo anterior al modelo de datos y tienen diferencias conocidas con él (campo de medio de pago, asistencia dentro del cálculo, cargo de día por rango). Sirven para ver la intención visual, nunca para deducir comportamiento.

## Comandos

Todo con `python tasks.py <tarea>` desde la raíz. `python tasks.py` sola lista las tareas.

No es un `Makefile` porque `make` no viene con Windows, que es donde se programa esto: todo comando documentado que no se puede correr es una regla que no se cumple. El lanzador no tiene dependencias propias y las resuelve del entorno virtual de `backend/`. `pytest`, `alembic` y `uv`/`pip` se ejecutan dentro de `backend/`; `npm` dentro de `frontend/`.

| Qué | Comando |
|---|---|
| Levantar todo en local | `python tasks.py up` |
| Instalar dependencias | `python tasks.py install` |
| Tests del backend | `python tasks.py test` |
| Un solo test | `cd backend && pytest tests/functional/<archivo>.py::<test> -x` |
| Lint y formato del backend | `python tasks.py lint` (ruff check + ruff format) |
| Tipos del backend | `python tasks.py typecheck` (mypy) |
| Nueva migración | `cd backend && alembic revision --autogenerate -m "<mensaje>"` |
| Aplicar migraciones | `python tasks.py migrate` |
| Datos de ejemplo | `python tasks.py seed` |
| Regenerar el contrato OpenAPI | `python tasks.py openapi-generate` |
| Comprobar que el contrato está al día | `python tasks.py openapi-check` |
| Frontend en desarrollo | `cd frontend && npm run dev` |
| Lint y build del frontend | `cd frontend && npm run lint && npm run build` |
| Tests del frontend | `python tasks.py front-test` |

## Estructura

```
backend/
  app/
    main.py            arranque de FastAPI
    core/              config, seguridad, dependencias de permisos
    models/            SQLAlchemy 2
    schemas/           Pydantic v2 — entra y sale de la API
    api/v1/            un router por capability
    services/          reglas de negocio; calculo_cargo.py tiene el cálculo
  alembic/versions/
  tests/
    conftest.py        fixtures; aislamiento por transacción
    functional/        tests de contrato, por capability
frontend/src/
  tema.ts              el catálogo de color — único lugar con valores
  lib/api.ts           único punto de contacto con el backend
  components/  pages/  routes/
scripts/seed.py        datos de ejemplo
docs/api/openapi.json  contrato versionado — generado, no se edita
```

## Convenciones del backend

### El cálculo vive en un solo lugar

Todo el cálculo de un cargo está en `app/services/calculo_cargo.py`, como **función pura**: recibe tarifa base, categoría, modalidad y cantidad de hijos, y devuelve el desglose. No toca la base, no lee el request y no tiene efectos. Ningún endpoint, modelo ni componente recalcula un precio por su cuenta.

### El precio nunca viene del cliente

El frontend manda **qué** se cobra (alumno, tipo, modalidad, período). El monto lo calcula y lo guarda la API. Un endpoint que acepte un importe del cuerpo de la petición es un error.

### Todo cargo guarda su cálculo

Al crear un cargo se persisten la tarifa base, el porcentaje aplicado, la categoría y la cantidad de hijos usadas. El cargo **no se recalcula nunca**: el tarifario cambia y lo ya cobrado no se toca.

### Nada se borra

No hay `DELETE` sobre datos del negocio. Un cobro mal cargado **se anula** (motivo, usuario y fecha) y su ingreso en tesorería se contraasienta con un egreso por el mismo monto. Un usuario o un grupo **se desactivan**. Los movimientos de tesorería y los cierres de canon abonados son inmutables.

### El estado derivado no se almacena

Si se puede calcular, se calcula. El saldo de una familia sale de sus cargos y pagos; que un usuario esté bloqueado sale del contador de intentos fallidos. No hay columnas que dupliquen eso.

### Toda respuesta pasa por un esquema

Nunca se devuelve un modelo de SQLAlchemy. Cada endpoint declara su `response_model` de Pydantic. Es lo que impide que se filtren el hash de la contraseña o datos médicos de un alumno que no corresponde.

### Los permisos se declaran y se filtran en la consulta

Cada endpoint declara qué roles pueden usarlo con una dependencia de FastAPI. Para el Profesor, una segunda dependencia comprueba que el grupo o el alumno sean de los suyos. **Los listados se filtran en la consulta, no después**: un profesor nunca recibe filas de otros grupos ni siquiera para descartarlas.

### Migraciones

Una migración por cambio de esquema, con `--autogenerate` y **revisando el diff a mano**: autogenerate se equivoca con los índices, los tipos enumerados y los renombres. Tiene que ser reversible y probarse en los dos sentidos contra la base de pruebas. Ver la skill `revisar-migracion`.

## Versiones por delante de la documentación conocida

El stack va en versiones más nuevas que la documentación que te sabés, y varias APIs cambiaron:

- **SQLAlchemy 2**: los modelos se declaran con `Mapped[...]` y `mapped_column(...)`, no con `Column(...)`. Las consultas van con `select()` y `session.execute()`, no con `session.query()`.
- **Pydantic v2**: `model_config = ConfigDict(...)` en vez de `class Config`, `model_validate` en vez de `from_orm`, `field_validator` en vez de `validator`.
- **FastAPI** con `lifespan` en vez de `@app.on_event`.

Antes de dar por buena una firma de memoria, comprobala en el paquete instalado (`backend/.venv/lib/python3.*/site-packages/...`).

## Frontend

React 18 + Vite + TypeScript, con **MUI 6** y `@mui/x-data-grid` para los listados. Se eligió MUI sobre Mantine porque tiene mucho más material de entrenamiento, así que un agente genera MUI correcto con bastante más fiabilidad.

El único punto de contacto con el backend es `src/lib/api.ts`: envuelve `fetch`, adjunta el token, y traduce los errores de FastAPI a un error con mensaje en castellano más los errores por campo que las pantallas pegan al lado de cada campo. Toda llamada nueva se agrega ahí, nunca en un componente — hay una regla de eslint que corta un `fetch` suelto.

Los colores salen de `src/tema.ts`, el único archivo del frontend donde un valor de color puede estar escrito; un hook corta los valores a pelo en el resto. Los nombres dicen **para qué** sirve el color, no cómo se ve: `deuda`, no `rojo`.

Las fechas que se muestran como texto se formatean en `src/lib/fechas.ts`, en dd/mm/aaaa. En los campos de formulario se usa `<input type="date">`, cuyo valor es siempre ISO.

Los montos y porcentajes que se muestran se formatean en `src/lib/montos.ts` (`$ 85.000`, `$ 4.462,50`, `36,25 %`). Trabaja sobre el texto con dos decimales que manda la API, sin pasar por `Number` ni `parseFloat`: un centavo no se pierde en un `float`. Un monto nunca se calcula en el frontend: se muestra el que devolvió la API.

Una pieza de interfaz nueva sale del catálogo de `src/components/` o se crea ahí con nombre propio, nunca improvisada dentro de una pantalla.

## Roles

- **Admin** (puede haber varios; el primero se crea en la puesta en marcha):
  - Da de alta usuarios de cualquier rol, puede desactivarlos y les blanquea la contraseña.
  - Administra profesores y grupos.
  - Registra alumnos en cualquier grupo, carga documentación y gestiona asistencia.
  - Es el único rol que registra cobros y ve la cuenta corriente familiar y la tesorería.
  - Es el único que modifica la categoría de una familia ya asignada.
  - Configura el tarifario, los descuentos, las fechas de Mes, Quincena y Semana, y el % del canon.
  - Hace el cierre del canon y lo abona, lo que genera un egreso en tesorería.
- **Coordinador**:
  - Administra profesores (incluye dar de alta su usuario con rol Profesor y asignarles grupos) y grupos.
  - Registra alumnos en cualquier grupo, crea familias, carga documentación y gestiona asistencia.
  - **No** ve la cuenta corriente familiar, la tesorería ni los cobros.
- **Profesor**:
  - Registra alumnos, carga documentación y gestiona asistencia solo en los grupos que tiene asignados.
  - Puede crear familias y asignar la categoría al registrar.
  - Ve alergias y condiciones médicas solo de los alumnos de sus grupos. De los hijos de la misma familia en otros grupos ve los datos de familia y las personas autorizadas, pero no los datos médicos ni los documentos.
  - No administra profesores ni grupos, y no ve nada contable.

## Entidades principales

Los datos se conservan entre temporadas: no se borra nada.

**Personas y estructura**
- **Temporada**:
  - La primera se crea en la puesta en marcha, junto con el primer Admin.
  - Tiene fecha de inicio y de cierre.
  - Tiene su propia configuración: tarifa base, tabla de descuentos, % de canon, tipos de cargo y documentos obligatorios.
  - Al abrir una nueva: se pueden copiar los grupos de la anterior; se conservan alumnos, tutores y profesores con sus usuarios; las inscripciones a grupos se hacen de nuevo; toda la documentación vuelve a quedar pendiente; y las cuentas corrientes y la tesorería arrancan en cero.
  - La temporada anterior queda solo para consulta.
- **Usuario**:
  - Tiene un rol: Admin, Coordinador o Profesor.
  - Se puede activar y desactivar.
  - Acceso: cambio obligatorio de contraseña en el primer ingreso y después de un blanqueo. Solo un Admin blanquea contraseñas. El usuario queda bloqueado tras 5 intentos fallidos seguidos, hasta que se le blanquee la contraseña.
  - Un Profesor se asigna a uno o más grupos, y un grupo puede tener varios profesores.
- **Grupo**:
  - Nombre, turno (mañana o tarde) y rango de fechas de nacimiento (desde/hasta). El rango se usa para sugerir el grupo al cargar un alumno.
  - Es por temporada, porque el rango se corre cada año. Al abrir una temporada nueva se pueden copiar los grupos de la anterior.

**Familia y alumnos**
- **Familia**:
  - ID interno que nunca cambia.
  - Etiqueta visible "Apellido – Hijo mayor", que se recalcula sola y no se edita.
  - Categoría: socio, empleado o no socio.
  - Tiene una única cuenta corriente.
  - Se crea al cargar el primer hijo.
- **Alumno (hijo)**:
  - Pertenece a una familia.
  - Datos personales, fecha de nacimiento y datos sensibles (alergias, condiciones médicas).
  - Registro del consentimiento del tutor para cargar datos médicos.
  - Datos mínimos del alta: nombre, apellido, fecha de nacimiento, familia, **al menos un tutor**, y grupo y turno. La documentación no forma parte del mínimo.
  - Si vuelve en otra temporada, reutiliza su ficha, su familia y sus tutores, pero se lo inscribe de nuevo en los grupos.
- **Inscripción**: alumno × grupo/turno × temporada. Cada turno es una inscripción independiente.
- **Persona autorizada a retirar**: incluye a los tutores. Puede estar autorizada en más de una familia.
- **Contacto de emergencia**: lista aparte de las personas autorizadas. Es de la familia: los hijos lo comparten.
- **Documento**:
  - Archivo privado (PDF, JPG o PNG, hasta 5 MB) adjunto a la ficha.
  - Checklist configurable: el Admin define por temporada qué documentos son obligatorios (por ejemplo, ficha médica, DNI o autorización de salidas). También se pueden adjuntar otros no obligatorios.
  - La ficha está completa cuando tiene todos los obligatorios de la temporada. Al abrir una temporada nueva todos vuelven a quedar pendientes, incluido el carnet de socio.
  - Se puede cobrar aunque la ficha esté incompleta.
  - Se guarda quién lo subió o modificó, y cuándo.
- **Asistencia**: presencia por alumno, día y turno. No interviene en el cobro.

**Tarifario y cobros**
- **Período de cobro**: fechas desde/hasta de cada Mes (4 semanas), Quincena y Semana, definidas por los Admin. La modalidad Día no tiene rango.
- **Tarifa base**: por temporada, turno y modalidad (Mes, Quincena, Semana, Día).
- **Descuento**: tabla paramétrica por temporada, con una fila por categoría (socio, empleado, no socio).
  - Un % por categoría para Día, Semana y Quincena. La cantidad de hijos no interviene.
  - Un % por categoría y tramo de hijos (1, 2, 3, 4 o más), solo para el Mes.
  - Se aplica un único porcentaje a la tarifa base, nunca acumulado.
  - El % del tramo alcanza a todos los hijos de la familia, no solo al que supera el tramo.
  - Los hijos se cuentan por turno.
- **Tipo de cargo**: catálogo configurable por temporada (por ejemplo, Preinscripción o Abono).
- **Cargo**: lo que se le cobra a la familia, según tipo, modalidad y monto.
- **Pago**:
  - Se permiten pagos parciales por cargo.
  - Lo registra solo un Admin.
  - Cada pago genera un ingreso en tesorería.
- **Cuenta corriente familiar**: cargos y pagos de la familia, con su saldo pendiente. Es la fuente del reporte de deudas.

**Tesorería y canon**
- **Movimiento de tesorería**:
  - Ingreso (automático por cada pago) o egreso (descripción y monto, sin categorías).
  - Anular un cobro no borra su ingreso: se contraasienta con un egreso automático por el mismo monto, y el neto queda en cero.
  - Ningún movimiento se modifica ni se borra. El saldo disponible sale de los movimientos.
- **Cierre de canon**:
  - Rango desde/hasta, total cobrado en ese rango, % configurable y monto a abonar.
  - Se guarda qué Admin lo abonó.
  - Al abonarlo se genera un egreso en tesorería.

## Arnés de agentes

Los subagentes de `.claude/agents/` separan quién escribe los tests de quién escribe el código. La separación tiene candado en las dos direcciones:

- **El implementer no toca los tests**: `backend-feature` y `frontend-feature` los congelan por hash (`git ls-files -s`) antes de implementar y lo comparan al terminar.
- **El test-writer no lee ni toca la implementación**: un hook `PreToolUse` en su frontmatter (`.claude/hooks/sin_ver_implementacion.py`) corta `Read`, `Grep`, `Glob`, `Write` y `Edit` sobre `backend/app/`, `backend/alembic/versions/`, `frontend/src/` y `frontend/dist/` (el bundle compilado), y también las búsquedas lanzadas desde una carpeta que las contiene. Se probó con un agente de juguete sin la prohibición escrita: frenó los cuatro caminos de lectura (`Read`, `Grep`, `Glob` y `cat` por `Bash`) y dejó pasar los de control.
  - Falla cerrado: si no entiende la entrada, bloquea.
  - Dos huecos que el hook no cubre:
    - en `Bash` solo mira el texto del comando, así que ahí es una red: `cd backend && cat app/main.py` pasa;
    - si `python` no está en el PATH, el hook ni arranca y la herramienta corre.
  - La regla escrita en el prompt sigue siendo la otra mitad.

Cómo funciona el arnés, aprendido a fuerza de probar:

- **Al tocar un archivo de `.claude/agents/`, reiniciá la sesión.** Las definiciones de los agentes se cargan al arrancar: un agente nuevo da «Agent type not found» y un cambio a uno existente no se aplica hasta la sesión siguiente. Para probar sin cerrar la sesión, `claude -p "..." --output-format stream-json --verbose` arranca una nueva, y la salida dice qué modelo usó cada mensaje.
- **El frontmatter no acepta `permissions`**: lo ignora sin dar error. Los permisos por agente van con `hooks`.
- **Un hook bloquea solo si sale con código 2.** Con cualquier otro código distinto de cero, la herramienta corre igual.
- `implementer` y `ui-implementer` corren con `model: sonnet` (verificado). `test-writer` y `adversarial-reviewer` usan el modelo de la sesión.

## Reglas de proceso

1. **Una rama por change, no por petición.** Cada change de OpenSpec, es decir cada fila del «Plan de changes» (una historia, varias o ninguna si es técnico), tiene su propia rama `feat/<nombre-del-change>`. Antes de tocar código mirá en qué rama estás:
   - Si es la rama `feat/*` del change en curso, seguí en ella.
   - Si es la rama de **otro** change, aunque ya esté archivado o mergeado, no sigas ahí: se arranca una nueva.
   - La rama nueva sale de la rama de entrega **actualizada** (`git fetch` y `git merge --ff-only origin/<rama-de-entrega>`), nunca de la rama de otro change: `git checkout -b feat/<nombre-del-change>`. Si el change anterior todavía no se mergeó y el nuevo depende de él, pará y preguntá antes de apilar una rama sobre otra.
   - Nunca se commitea directo en `main` ni en una rama de entrega.
2. **El commit sí es por petición**: al cerrar cada una, usar la skill `/commit`.
3. **Toda unidad de trabajo es un change de OpenSpec.** Arranca con `/openspec-propose`, se construye con `/openspec-apply-change`, se comprueba con `/openspec-verify-change` y se cierra con `/openspec-archive-change`, que funde el delta en la spec. No se escribe código de producción fuera de un change: sin spec no hay contra qué escribir el test.
4. **Dentro del change, cada tarea de backend usa la skill `backend-feature`** y cada pieza de interfaz usa `frontend-feature`, aunque nadie lo pida. Definen el orden tests → rojo → congelar → implementar → verde.
5. **Un cambio que toque rutas, esquemas o modelos se cierra en el mismo commit con `docs/api/openapi.json` regenerado** (`python tasks.py openapi-generate`). El CI lo comprueba.
6. **El pase del subagente `adversarial-reviewer` va una sola vez, al terminar la change**, antes de abrir el pull request. No al cerrar cada tarea.
7. **Los pull requests se abren dentro de este fork**, de `feat/*` hacia la rama de entrega. Ahí corre el revisor automático; en los PR hacia el repositorio de LIDR no corre, porque un fork no recibe los secretos.
8. Todo en español: código comentado en español, mensajes de error en español, nombres de dominio en español (`familia`, `cargo`, `tarifa`).
9. **Lo que no esté en las fuentes de verdad se marca como [SUPUESTO]**:
   - Lo **confirmado** en `aclaraciones-cliente.md` es fuente de verdad y no lleva la marca.
   - Lo que ahí figura como **[SUPUESTO]** o como pregunta abierta no es fuente de verdad: se sigue marcando, pero referenciando esa entrada.
   - Una **regla de negocio** que no aparece en ninguna fuente se marca **[SUPUESTO]** y se registra como pregunta abierta en `aclaraciones-cliente.md`.
   - Las **decisiones de diseño** (nulabilidad, tipos, índices, estructura) no son preguntas para el cliente: se deciden, se documentan con su justificación donde se toman, y no pasan por `aclaraciones-cliente.md`.
