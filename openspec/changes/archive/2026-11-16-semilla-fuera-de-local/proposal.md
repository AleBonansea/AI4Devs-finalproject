# Proposal

## Why

La Entrega 3 despliega el sistema en Render, con un **entorno demo** cuya base tiene que tener los datos inventados de la semilla. Hoy esa base no se puede sembrar: `verificar_base_local` rechaza cualquier host remoto, y está bien que lo haga, pero no hay ninguna forma de pasarla a propósito.

**Change técnico, sin historia de usuario.** No figura en el «Plan de changes» del lote 1 ni es una de las historias del lote 2: es herramienta de despliegue. Desbloquea el entorno demo de la Entrega 3.

## What Changes

- **Permiso explícito para una base remota.** La variable de entorno `SEMILLA_FUERA_DE_LOCAL`, con el valor exacto `1`, permite que `python tasks.py seed` siembre una base cuyo host no es local. Antes de conectarse avisa por pantalla nombrando el host al que va a escribir. La variable se lee solo del entorno del proceso: una línea en `backend/.env` no da el permiso.
- **Sin la variable, nada cambia.** Una base remota se rechaza igual que hoy, y también con cualquier valor que no sea `1`. La negativa de base no vacía sigue igual con permiso o sin él.
- **Documentación.**
  - En `readme.md` y `CLAUDE.md`: que la semilla es solo para desarrollo y demo, y cómo se siembra el entorno demo.
  - Las notas sobre el comando de puesta en marcha se corrigen, no se borran: va con el lote 2, junto a HU-UT-06, porque sin el cambio de contraseña el primer Admin no puede operar. Son las de `readme.md`, `1-descripcion-general-del-producto.md`, `2-arquitectura-del-sistema.md` y `3-modelo-de-datos.md`.
  - El backlog suma esa tarea a la sección del lote 2.
  - El pendiente técnico de la semilla, en el documento técnico, suma el permiso.

**Queda fuera:**

- **El comando de puesta en marcha** (primer Admin y primera temporada vigente, Acl. 9 y 10). Se propuso en este change y se sacó: el Admin nace con `debe_cambiar_password` en true y, sin HU-UT-06, la API le responde 403 en todo salvo `GET /auth/yo`. Un Admin que no puede cambiar su contraseña no puede operar. Va con el lote 2, junto a HU-UT-06.
- Cerrar la clase entera del pendiente técnico «Que la semilla no pueda escribir en la base de producción» (preguntarle a la conexión dónde terminó, con `conn.info`). Este change agrega un permiso explícito, no un candado nuevo.
- Una confirmación por teclado antes de sembrar, un flag de línea de comandos, o cualquier cambio a los datos que carga la semilla.
- Endpoints, pantallas y migraciones: no cambia ni el esquema ni la API.

## Capabilities

### New Capabilities
<!-- Ninguna. -->

### Modified Capabilities
- `semilla`: el requirement «La semilla solo corre contra una base local» admite una excepción explícita por variable de entorno, que se especifica en un requirement nuevo, con aviso del host antes de conectarse.

## Impact

- **Código:** `backend/app/semilla.py` (comprobación del destino con el permiso) y `scripts/seed.py` (le pasa el entorno del proceso e imprime el aviso).
- **Tests:** `backend/tests/functional/semilla/` suma los Scenarios del permiso.
- **API y esquema:** sin cambios. `docs/api/openapi.json` no se regenera, y `python tasks.py openapi-check` tiene que seguir en verde.
- **Dependencias:** ninguna nueva.
- **Documentación:** `readme.md`, `CLAUDE.md`, `1-descripcion-general-del-producto.md`, `2-arquitectura-del-sistema.md`, `3-modelo-de-datos.md`, `docs/product/historias-backlog.md`, `docs/architecture/documento-tecnico.md`.
