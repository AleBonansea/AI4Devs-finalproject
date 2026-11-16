# Design

## Context

Motivación y alcance en `proposal.md`. Lo que ya existe y condiciona el enfoque:

- `backend/app/semilla.py` tiene dos negativas.
  - `verificar_base_local(url)` lee el texto de la URL, sin conectarse: el host principal y `host`/`hostaddr` de la query.
  - `cargar(sesion)` se niega si hay alguna temporada, usuario, familia o persona.
  - `cargar` hace flush y nunca commit. El commit lo hace `scripts/seed.py`.
- `Configuracion` (`app/core/config.py`) lee `DATABASE_URL` del entorno y de `backend/.env`, y el entorno manda. Apuntar la semilla a la base demo de Render es definir `DATABASE_URL` con su External Database URL.
- El docstring de `scripts/seed.py` documenta el orden: primero se comprueba la URL, recién después se abre la sesión. `create_engine` no se conecta, así que importar `app.semilla` no llega a tocar la base.

## Goals / Non-Goals

**Goals:**
- Que el permiso sea imposible de activar por descuido: un valor exacto, solo en el entorno del proceso, y con el host a la vista antes de conectarse.
- Que el permiso se pruebe sin tocar el entorno real del proceso de tests.

**Non-Goals:**
- Cerrar el pendiente técnico de la semilla con `conn.info` (sigue en el documento técnico).
- El comando de puesta en marcha (lote 2, junto a HU-UT-06).

## Decisions

### `SEMILLA_FUERA_DE_LOCAL`, valor exacto `1`, solo del entorno del proceso

Se lee de `os.environ`, no de `Configuracion`. Por eso una línea en `backend/.env` **no** da el permiso:

- El `.env` es un archivo que se queda. Una variable ahí convierte el permiso puntual en permanente.
- La próxima vez que alguien deje en ese mismo archivo una External Database URL, la red ya no está.
- En el entorno del proceso, el permiso dura lo que dura la terminal.

Solo cuenta `1`. `true`, `yes`, `0` o la cadena vacía no dan el permiso: con un único valor válido no hay que adivinar si `0` o `false` quieren decir «no».

*Alternativas:*

- **Un flag de línea de comandos** (`python tasks.py seed --remota`). Se escribe igual de fácil, pero obliga a que `tasks.py` reenvíe argumentos, y hoy no lo hace.
- **Una confirmación por teclado** («escribí el nombre del host»). Protege más, pero rompe sembrar el demo desde un comando no interactivo. Lo pedido es el aviso con el host.

### Una función nueva, `comprobar_destino(url, entorno)`, y `verificar_base_local` intacta

En `app/semilla.py`:

- `verificar_base_local(url)` no cambia. Los seis Scenarios que ya la prueban siguen valiendo.
- `comprobar_destino(url: str, entorno: Mapping[str, str]) -> str | None`:
  - si la URL es local, devuelve `None`;
  - si no lo es y `entorno.get("SEMILLA_FUERA_DE_LOCAL") == "1"`, devuelve el texto del aviso;
  - si no, deja pasar el `SemillaRechazada` de `verificar_base_local`.
- Los hosts del aviso salen del mismo recorrido que usa la verificación: el host principal y después cada elemento de `host` y `hostaddr` de la query. Se sacan los locales y los repetidos, y se conserva ese orden. El recorrido se extrae a una función privada que usan las dos, para que el aviso y la negativa no puedan diferir en qué consideran host.

El entorno llega como argumento, y por eso el permiso se prueba con un `dict`, sin tocar el entorno real del proceso de tests.

`scripts/seed.py` le pasa `os.environ` y, si hay aviso, lo imprime por la salida de errores con `flush=True`. Recién después abre la sesión. El docstring del script suma ese paso a la lista de pasos en orden.

### Con el permiso, un host vacío se rechaza en vez de avisar

Una URL sin host (`postgresql+psycopg://u:p@/escuelita`), o un elemento vacío en `host`/`hostaddr` de la query, deja que libpq tome el host de `PGHOST` o use un socket. El aviso diría «base remota: .» y la semilla escribiría en un host que nadie vio. Sin permiso ya se rechazaba, porque el vacío no es un host local. Con permiso también se rechaza, con un mensaje propio: el permiso es para un host nombrado, no para cualquier destino.

*Alternativa descartada:* avisar «host no indicado» y seguir. Es justo lo que el aviso existe para evitar.

### Los hosts de la query, sin su puerto

SQLAlchemy separa el `:puerto` de cada valor de `host` de la query antes de pasárselo a psycopg: `?host=localhost:5432` conecta a `localhost`. La comprobación y el aviso tienen que mirar el mismo host que va a usar libpq, así que `_hosts_de` le saca el puerto a esos valores. Se considera puerto:

- un `:` seguido solo de dígitos al final, cuando el valor tiene un único `:`;
- lo que viene después de `]`, en la forma `[ipv6]:puerto`.

`::1` y cualquier IPv6 sin corchetes quedan como están. El host principal ya llega sin puerto desde `make_url`.

Consecuencia sin permiso: `?host=localhost:5432` pasa a aceptarse, porque efectivamente es local.

### Cómo se prueba

- Los Scenarios del permiso van contra `comprobar_destino` con un `dict` de entorno.
- Los Scenarios de base local («Base del docker-compose», «Base en localhost», «Un host local con puerto en la query») también se prueban contra `comprobar_destino` sin permiso, porque es lo único que llama el script. Probarlos solo contra `verificar_base_local` deja en verde a un `comprobar_destino` que rechace todo.
- El de base no vacía con el permiso va contra `cargar`, como los existentes. Esa negativa no depende del entorno: el test comprueba que el permiso no la cambia.
- «El aviso sale antes de conectarse» corre `python tasks.py seed` con `subprocess`, desde la raíz, como dice el Scenario:
  - `DATABASE_URL` apunta a `dpg-noexiste.invalid` (`.invalid` es un dominio reservado que nunca resuelve, así que no sale a la red);
  - en la salida de errores, el aviso tiene que aparecer antes del error de conexión;
  - el código de salida tiene que ser distinto de cero.
- Que `backend/.env` no da el permiso queda garantizado por la estructura: el script pasa `os.environ`, nunca `Configuracion`. Lo comprueba la revisión, no un test.

## Risks / Trade-offs

- **[Con la External Database URL en la notebook, la red de `verificar_base_local` deja de proteger esa base]**
  - La protección de la semilla siempre fue leer el host en la URL. Si `DATABASE_URL` apunta a Render, la red sirve solo mientras nadie defina `SEMILLA_FUERA_DE_LOCAL=1`. Con la variable definida, lo único que queda es la negativa de base no vacía.
  - **Es aceptable para el entorno demo**, porque su base tiene solo datos inventados. Lo peor que pasa es sembrarla dos veces, y la segunda vez se rechaza.
  - **No es aceptable para la base del club.** Para esa base valen dos reglas:
    - la puesta en marcha, cuando exista, **corre en el servidor** (la shell del servicio web de Render, donde `DATABASE_URL` ya es la interna), **no desde una notebook**;
    - la External Database URL de producción no se copia a ninguna máquina de desarrollo.
  - Queda escrito en el readme y en el pendiente técnico del documento técnico.
- **[El día de la instalación, la base de producción está vacía]**
  - Si alguien define la variable apuntando ahí, las dos negativas de la semilla fallan juntas. Es el escenario que el pendiente técnico ya describe, y el permiso explícito lo vuelve más fácil, no más difícil.
  - Mitigación: no se expone la URL externa de producción hasta que la base tenga su primer Admin. Desde ahí la base ya no está vacía y la semilla se rechaza con permiso o sin él.
  - El cierre de fondo sigue siendo el de `conn.info`, fuera de este change.
- **[En PowerShell, `$env:SEMILLA_FUERA_DE_LOCAL='1'` y `$env:DATABASE_URL` duran toda la sesión de la terminal]**
  - Con `DATABASE_URL` todavía apuntando a Render, un `python tasks.py migrate` o el backend levantado en esa terminal van contra la base demo.
  - El readme da el comando con el `Remove-Item` de las dos variables y recomienda cerrar la terminal al terminar.
  - El readme advierte además que la URL, que trae la contraseña, queda en el historial de PowerShell (PSReadLine).
  - El aviso sale cada vez, así que un permiso que quedó puesto se ve.
- **[`PGHOST`, `PGHOSTADDR` o `PGSERVICE` en el entorno, o `service=` en la query, desvían la conexión sin que la URL lo muestre]**
  - Es un hallazgo de la revisión adversarial, confirmado con `PGHOSTADDR`, que le gana a `host`: con `PGHOSTADDR` apuntando a una base remota y una URL a `localhost`, la semilla pasa la comprobación **sin permiso y sin aviso**.
  - El hueco existía antes de este change. Es exactamente la clase que describe el pendiente técnico de la semilla, y su cierre (preguntarle a la conexión dónde terminó, con `conn.info`) queda fuera de alcance.
  - Mitigación en este change: el readme dice que el aviso nombra el host **de la URL**, y que esas variables no tienen que estar definidas al sembrar. El pendiente técnico suma `PGHOSTADDR`.

## Migration Plan

Sin migración de esquema. Para sembrar el entorno demo, desde la notebook y con `DATABASE_URL` apuntando a la base demo de Render:

```powershell
$env:SEMILLA_FUERA_DE_LOCAL='1'; python tasks.py seed; Remove-Item Env:SEMILLA_FUERA_DE_LOCAL
```

No hay nada que volver atrás: sin la variable, la semilla se comporta como antes.
