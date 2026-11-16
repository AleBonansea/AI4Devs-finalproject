# Design

## Context

La base tiene una sola migración (`17e635c64a3e`), con `temporada` y `usuario`. Los modelos siguen tres patrones ya establecidos:

- **SQLAlchemy 2** con `Mapped[...]`.
- **`creado_en` del servidor de base**, a través de `MarcaDeCreacion` en `app/models/base.py`.
- **Tipos enumerados nativos con `values_callable`**, para que la base guarde los valores en minúsculas y no los nombres de los miembros (`app/models/temporada.py`).

La migración inicial borra a mano los tipos enumerados en el `downgrade`: Alembic no los borra solo.

Las tablas y sus restricciones están definidas en `3-modelo-de-datos.md`, que este change sigue tal cual. Los valores de la semilla salen de dos fuentes:
- la tarifa base, la Preinscripción y las fechas del «Mes 1», «Mes 2» y «Semana 1», del contexto común de HU-CC-01 (`5-historias-de-usuario.md`);
- los descuentos, de la política 2026-27 de Acl. 5.

`tasks.py` ya tiene la tarea `seed`, que corre `scripts/seed.py` con el Python del entorno virtual y `cwd=backend/`. Ese archivo todavía no existe.

## Goals / Non-Goals

**Goals:**
- Que los changes 4 a 7 encuentren sus tablas de referencia creadas, con las claves que sus FK compuestas necesitan.
- Que la semilla sea probable desde los tests sin dejar datos en la base de pruebas.
- Que la semilla no pueda dañar una base en uso ni dejar un Admin con contraseña conocida en producción.

**Non-Goals:**
- **Endpoints, esquemas de Pydantic y roles.** Este change no expone nada por la API, así que no hay qué roles declarar ni cómo filtrar para el Profesor. Por la misma razón las specs de `grupos` y `tarifario` no tienen un Scenario de «quién no puede»: no hay operación que negar. En `semilla` ese papel lo cumplen las dos negativas, base no vacía y base no local.
- **Validar que un usuario asignado a un grupo tenga rol profesor.** El modelo de datos lo pone en la API (HU-GA-02). La semilla lo respeta por construcción.

## Decisions

### Tipos enumerados compartidos en `app/models/enums.py`

`Turno` y `Modalidad` los usan grupos, tarifario y, más adelante, inscripción y cargo. `CategoriaFamilia` la usan los descuentos ahora y `familia` en el change 4. Por eso van en un módulo propio y no en el modelo de una tabla. Cada uno se declara una sola vez como objeto `Enum` de SQLAlchemy (`native_enum=True`, `values_callable`, nombre fijo: `turno`, `modalidad`, `categoria_familia`, `calculo_cargo`) y ese mismo objeto se reutiliza en cada columna. Así Postgres tiene un solo tipo `turno`, no uno por tabla, y la migración lo crea una vez.

Alternativa descartada: declararlos junto a la tabla que los usa primero, como `EstadoTemporada`. Funciona para un tipo de una sola tabla. Con cuatro tipos compartidos, obliga a que `tarifario.py` importe de `grupo.py` solo por el turno.

### Dos módulos de modelos: `grupo.py` y `tarifario.py`

- **`grupo.py`:** `Grupo` y `GrupoProfesor`.
- **`tarifario.py`:** `TarifaBase`, `DescuentoModalidad`, `DescuentoMes`, `PeriodoCobro` y `TipoCargo`.

Todos llevan `MarcaDeCreacion` y se registran en `app/models/__init__.py`, sin el cual autogenerate no los ve.

Las claves siguen el modelo de datos:
- `id` `BigInteger` en `grupo`, `periodo_cobro` y `tipo_cargo`, como en `temporada`;
- clave compuesta en `grupo_profesor`, `tarifa_base`, `descuento_modalidad` y `descuento_mes`.

Las restricciones van con nombre explícito (`ck_…`, `uq_…`), como en la migración inicial, para que no dependan del entorno. Las dos claves únicas que existen solo para FK futuras se declaran ya:
- `uq_grupo_id_temporada_turno` (`id`, `temporada_id`, `turno`), que usará la FK compuesta de `inscripcion` (change 4);
- `uq_periodo_cobro_id_modalidad` (`id`, `modalidad`), que usará la de `cargo` (change 6).

### Sin `ON DELETE CASCADE`

Las FK usan el comportamiento por defecto de Postgres (`NO ACTION`). Borrar un grupo con profesores asignados falla, que es el Scenario «Borrar un grupo con un profesor asignado». Es la convención del modelo de datos: nada se borra físicamente, y una cascada borraría en silencio lo que cuelga.

### Montos y porcentajes en `Numeric`, comparados como `Decimal`

Montos en `Numeric(12, 2)` y porcentajes en `Numeric(5, 2)`, con `CHECK (porcentaje BETWEEN 0 AND 100)`, y `CHECK (monto > 0)` en `tarifa_base` y `CHECK (monto_fijo > 0)` en `tipo_cargo`. El segundo lo agregó el pase adversarial: sin él la base aceptaba una Preinscripción de −20000, y cada cargo de ese tipo habría bajado la deuda de la familia en vez de subirla. Es una decisión de integridad del dato, no una regla del cliente, así que va al modelo de datos y no a `aclaraciones-cliente.md`. La escala se comprueba con un valor de tres decimales que tiene que releerse redondeado: con `numeric` sin escala, Postgres lo guardaría tal cual. En Python son `Decimal`, nunca `float`: 36.25 y 57.50 tienen que releerse exactos, y el change 6 multiplica con ellos.

### La semilla vive en `app/semilla.py` y el script solo la invoca

`app/semilla.py` expone dos funciones. Son la interfaz que usan los tests:

- **`verificar_base_local(url: str) -> None`:**
  - Lanza `SemillaRechazada` con el mensaje `La semilla solo corre contra una base local.` si el host de la URL no es exactamente `localhost`, `127.0.0.1`, `::1` o `db`.
  - El host sale de `sqlalchemy.engine.make_url(url).host`, no de buscar texto en la URL. Así `localhost.ejemplo.com` no pasa.
  - También mira `host` y `hostaddr` en la query de la URL (`make_url(url).query`), que psycopg usa por encima del host principal: `postgresql+psycopg://u:p@localhost/db?host=<remoto>` se conecta al remoto. Cada valor que traigan, incluida una lista separada por comas, tiene que ser uno de los hosts locales. Lo encontró el pase adversarial.
- **`cargar(sesion: Session) -> None`:**
  - Lanza `SemillaRechazada` con el mensaje `La base no está vacía: la semilla solo corre sobre una base vacía.` si existe alguna temporada o algún usuario.
  - Si no, agrega todas las filas y hace `flush`, pero **no hace commit**. Así un test la corre dentro de su transacción revertida y la base de pruebas queda limpia.

`scripts/seed.py` es el único que hace commit, y su orden es fijo:
1. Agrega `backend/` a `sys.path`, porque Python pone en el path la carpeta del script y no el `cwd`.
2. Llama a `verificar_base_local` con `DATABASE_URL`, **antes de abrir la primera conexión**, así no llega a conectarse a una base remota. El motor ya existe en ese momento, porque `app.semilla` importa los modelos y los modelos importan `app.core.db`, pero `create_engine` no se conecta: la primera conexión la abre la sesión, después de verificar.
3. Abre una sesión, llama a `cargar` y hace `commit`.
4. Imprime los cuatro usuarios con su rol y la contraseña de demostración.

Ante `SemillaRechazada`, el script escribe el mensaje en stderr y sale con código 1.

Todo pasa en una sola transacción: si algo falla a mitad de camino, no queda una temporada a medias.

Alternativas descartadas:
- **Toda la lógica en `scripts/seed.py`:** no se puede importar desde los tests sin trucos de path.
- **`python -m app.semilla`:** contradice la ruta que ya documentan `CLAUDE.md` y `tasks.py`.

### Por qué base vacía y no «reiniciar»

La semilla no borra ni actualiza: si la base tiene una temporada o un usuario, se niega. Hay dos alternativas descartadas:
- **Hacerla idempotente con upserts:** mezcla datos inventados con datos cargados a mano y deja la base en un estado que nadie eligió.
- **Darle un `--reiniciar` que vacíe las tablas:** contradice «nada se borra» y es justo la herramienta que no se quiere tener cerca de una base en uso.

Para volver a sembrar en desarrollo se recrea la base: `docker compose down -v`, luego `python tasks.py migrate` y `python tasks.py seed`.

### Usuarios de la semilla sin cambio de contraseña pendiente

El documento técnico dice que `debe_cambiar_password` se activa al crear un usuario, pero la semilla lo deja en false. Con true, y con el cambio de contraseña en el lote 2 (HU-UT-06), ninguno de los cuatro podría hacer nada más que `GET /api/v1/auth/yo` y la semilla no desbloquearía ningún change. Los usuarios de la semilla no son personas reales y la base no es de producción.

Cuando llegue HU-UT-06, la semilla puede seguir igual: es una herramienta de demostración, no la puesta en marcha.

La contraseña `Verano2026` cumple la regla del documento técnico: 8 o más caracteres, con letra y número. Se hashea con el mismo `hashear` del login. Los usernames siguen la regla de inicial y apellido en minúsculas.

### Por qué la política de Acl. 5 y no la tabla de HU-CC-01

La tabla de descuentos del contexto común de HU-CC-01 es anterior a la decisión del cliente del 11/11/2026. Esa tabla trae socio 50 en todo, y empleado 10/15/20/25 en el Mes y 10 en el resto. Acl. 5 prevalece sobre las historias, así que la semilla carga los porcentajes efectivos de la política 2026-27.

La tarifa base, la Preinscripción y las fechas sí salen de HU-CC-01, porque Acl. 5 no las contradice. Su ejemplo de «una familia socia con 3 hijos paga $42.500» supone el mismo Mes de mañana de $100.000.

Los tests del change 6 arman su propio tarifario, así que esta diferencia no afecta a ningún test. Lo que sí cambia es el número que se ve en una demostración.

### Datos de la semilla en una estructura, no repartidos en el código

Los valores van en constantes al principio de `app/semilla.py`, con una tabla por bloque: usuarios, grupos, tarifas, descuentos, períodos y tipos de cargo. `cargar` recorre esas tablas. Las semanas se generan desde el lunes 2027-01-04 sumando 7 días, para no escribir ocho pares de fechas a mano. Los meses y las quincenas van explícitos, porque son pocos y se leen mejor así.

### Cómo se prueban las restricciones

Los tests van en tres carpetas: `tests/functional/grupos/`, `tests/functional/tarifario/` y `tests/functional/semilla/`. Siguen el patrón de `test_migracion_inicial.py`: insertan con la `sesion` de conftest y esperan `IntegrityError` o `DataError` en el `flush`, contra Postgres real.

Un valor de enum inexistente (`noche`) se inserta con SQL crudo (`text(...)`). El ORM lo rechazaría antes de llegar a la base, y el Scenario dice que la rechaza la base.

Cada test de rechazo comprueba una sola fila por `flush`. Si un Scenario pide varias filas rechazadas, como los porcentajes fuera de rango, se parametriza o se usa `sesion.begin_nested()` por fila. Si no, el primer error aborta la transacción y las demás filas no se llegan a probar.

El Scenario de login de `semilla` corre `cargar(sesion)` y después usa el fixture `cliente`, que comparte la conexión: los usuarios recién sembrados son visibles para el login real.

## Reversibilidad

**Qué entra:** dos migraciones. La segunda solo agrega el CHECK de `monto_fijo` (ver «Una segunda migración para el CHECK de `monto_fijo`»). La primera es una migración generada con `alembic revision --autogenerate -m "crear grupos y tarifario"` y revisada con la skill `revisar-migracion`.
- Crea los cuatro tipos enumerados.
- Crea las siete tablas en orden de dependencia: `grupo` y `grupo_profesor` después de `temporada` y `usuario`; las cinco del tarifario después de `temporada`.

**Cómo se vuelve atrás:**
1. El `downgrade()` borra las siete tablas en orden inverso: `grupo_profesor` antes que `grupo`.
2. Después borra a mano los cuatro tipos con `sa.Enum(name=...).drop(op.get_bind(), checkfirst=True)`, como hace la migración inicial. Autogenerate no escribe esas líneas, y sin ellas el `upgrade` siguiente falla con «type already exists».
3. Se prueba en los dos sentidos contra la base de pruebas: `upgrade head`, `downgrade -1` y `upgrade head`.

**Filas existentes:**
- `temporada` y `usuario` no se modifican: no se agregan columnas ni restricciones.
- Las siete tablas nuevas arrancan vacías.
- El `downgrade` borra las filas de las tablas nuevas, y con ellas los datos de la semilla. En desarrollo no hay otros datos ahí, porque el ABM es del lote 2 y en producción el change todavía no corrió. Una vez que haya tarifarios cargados de verdad, revertir esta migración significaría perderlos: a partir de ahí no se revierte, se corrige con una migración nueva.

### Una segunda migración para el CHECK de `monto_fijo`

El CHECK va en una migración nueva, `tipo_cargo monto fijo positivo`, y no editando `a64e83ff89ab`: esa ya está aplicada en la base de desarrollo, y editar una migración aplicada deja a la base con un esquema distinto del que dice su versión. El `upgrade` agrega la restricción y el `downgrade` la saca. Si hubiera filas con `monto_fijo <= 0`, el `upgrade` fallaría; hoy no las hay, porque la tabla solo tiene lo que carga la semilla.

## Risks / Trade-offs

- **[La semilla corre contra una base de producción recién creada, todavía vacía.]** Dejaría un Admin con contraseña conocida.
  - **Mitigación:** la negativa por host no local, comprobada antes de conectarse. Las bases de Render tienen host remoto. Además, en una base ya puesta en marcha nunca correría, porque tiene temporada y Admin.
- **[El host `db` del docker-compose es un nombre genérico]** y podría resolver a otra cosa en un entorno ajeno.
  - **Mitigación:** se acepta. Fuera del docker-compose de este repo nadie corre `tasks.py seed`, y la segunda negativa (base no vacía) sigue en pie.
- **[La lista de hosts locales es corta]** y una base local con otro nombre, por ejemplo una IP de la red de Docker, queda rechazada.
  - **Mitigación:** preferible a que pase una remota. Si hace falta otro host, se agrega a la lista con su Scenario.
- **[Diferido] La URL puede redirigir la conexión con `service=`**, que libpq resuelve desde `pg_service.conf`. `verificar_base_local` mira el host principal y `host`/`hostaddr` de la query, pero no ese parámetro.
  - **Por qué se difiere:** es menor. Hace falta un `pg_service.conf` armado a propósito en la máquina que corre la semilla, y la negativa por base no vacía sigue en pie. Va a un change de seguimiento si alguna vez se usa `service` en este proyecto (`REVIEW.md`, «Cuándo se deja de revisar»).
- **[Los porcentajes de socio y empleado los calculó una persona a mano]**, como dice Acl. 5, y la semilla los trae escritos.
  - **Mitigación:** el Scenario de los 12 descuentos del Mes fija cada celda. Un error de transcripción falla el test, no la demostración.
- **[El tipo `categoria_familia` se crea antes que la tabla `familia`.]**
  - **Mitigación:** el change 4 reutiliza el mismo objeto `Enum` de `enums.py`. Su migración no lo vuelve a crear, y el revisor de la migración lo comprueba.

## Migration Plan

1. `python tasks.py migrate` aplica la migración nueva.
2. En desarrollo, sobre una base recién migrada, `python tasks.py seed` carga la temporada.
3. En producción solo se aplica la migración: la semilla no corre, y si alguien la corre, se niega.
4. Volver atrás es `alembic downgrade -1` y revertir el commit. Ver «Reversibilidad».
