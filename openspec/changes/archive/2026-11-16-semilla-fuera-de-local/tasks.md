# Tasks

## 1. Semilla: permiso explícito para una base remota

- [x] 1.1 Con la skill `backend-feature`: escribir los tests de los Scenarios nuevos y modificados de `specs/semilla/spec.md` en `backend/tests/functional/semilla/`, salvo «El aviso sale antes de conectarse». Van contra `comprobar_destino(url, entorno)` con un `dict`, y contra `cargar` para la base no vacía con el permiso. Ver el rojo por el motivo correcto, congelar e implementar `comprobar_destino` en `backend/app/semilla.py` sin cambiar el comportamiento de `verificar_base_local`. Verifica: `cd backend && pytest tests/functional/semilla -x` en verde, con los Scenarios previos de base local intactos.
- [x] 1.2 Con la skill `backend-feature`: escribir el test del Scenario «El aviso sale antes de conectarse» (el script corrido con `subprocess`, con `DATABASE_URL` apuntando a `dpg-noexiste.invalid`) y cambiar `scripts/seed.py`. El script le pasa `os.environ` a `comprobar_destino` e imprime el aviso por la salida de errores antes de abrir la sesión, y su docstring suma ese paso. Verifica: el test en verde y, a mano, `python tasks.py seed` contra la base local sigue sembrando como antes, sin aviso.

## 2. Documentación

- [x] 2.1 `readme.md`:
  - junto a los pasos de arranque: que la semilla es solo para desarrollo y demo, y cómo se siembra el entorno demo con `SEMILLA_FUERA_DE_LOCAL=1` (el comando de PowerShell con su `Remove-Item`, y que la variable en `backend/.env` no cuenta);
  - la regla de que la External Database URL de producción no va a una notebook;
  - la nota «Puesta en marcha real», corregida: el comando va con el lote 2, junto a HU-UT-06, porque sin el cambio de contraseña el primer Admin no puede operar.

  Verifica: los comandos documentados corren tal como están escritos.
- [x] 2.2 `1-descripcion-general-del-producto.md`, `2-arquitectura-del-sistema.md` (despliegue y pendientes) y `3-modelo-de-datos.md` («Puesta en marcha»): corregir, sin borrar, las notas sobre el comando de puesta en marcha para que digan que va con el lote 2, junto a HU-UT-06, porque sin el cambio de contraseña el primer Admin no puede operar. Verifica: ninguna de esas notas dice ya que el comando «llega con el lote 2, junto con el alta de usuarios» ni que «se define en la Entrega 2».
- [x] 2.3 `docs/product/historias-backlog.md`: en la sección del lote 2, agregar la línea «Puesta en marcha: el comando que crea el primer Admin y la primera temporada. No es una historia de usuario, pero sin él una instalación nueva no se puede usar. Va junto a HU-UT-06, porque el Admin nace con el cambio de contraseña pendiente.», y ajustar el párrafo «Puesta en marcha» de esa sección para que no la contradiga. Verifica: la línea está en la lista del lote 2.
- [x] 2.4 `CLAUDE.md`: en la fila de «Datos de ejemplo» de la tabla de comandos, aclarar que es solo para desarrollo y demo. `docs/architecture/documento-tecnico.md`: el pendiente «Que la semilla no pueda escribir en la base de producción» suma el permiso `SEMILLA_FUERA_DE_LOCAL` (que no cierra el pendiente) y la regla de que la puesta en marcha de la base del club corre en el servidor. Verifica: el pendiente sigue sin marcar y nombra este change.

## 3. Cierre

- [x] 3.1 Comprobaciones completas: `python tasks.py test`, `python tasks.py lint`, `python tasks.py typecheck` y `python tasks.py openapi-check` en verde. No se regenera `docs/api/openapi.json`, porque el change no toca rutas, esquemas ni modelos: `openapi-check` lo confirma.
- [x] 3.2 Pase del subagente `adversarial-reviewer` sobre la change completa, una sola vez, antes de abrir el pull request. Corregir lo que confirme. Verifica: su informe, con cada hallazgo resuelto o justificado.

## 4. Hallazgos de la revisión adversarial

- [x] 4.1 Con la skill `backend-feature`: el `test-writer` suma los tests que faltan, para:
  - «Base del docker-compose», «Base en localhost» y «Un host local con puerto en la query», contra `comprobar_destino` sin permiso;
  - «El aviso nombra cada host remoto una sola vez» y «El aviso nombra el host sin su puerto»;
  - los dos Scenarios de «Con el permiso, un host vacío se rechaza»;
  - «El aviso sale antes de conectarse», cuyo test pasa a correr `python tasks.py seed`.

  Después, rojo, congelar, `implementer` y verde. Verifica: `cd backend && pytest tests/functional/semilla -x` en verde y la huella intacta.
- [x] 4.2 `readme.md` y `docs/architecture/documento-tecnico.md`:
  - en el readme, el comando del entorno demo saca también `DATABASE_URL` y advierte que la URL queda en el historial de PowerShell;
  - en el readme, el aviso nombra el host de la URL, y al sembrar no tienen que estar definidas `PGHOST`, `PGHOSTADDR` ni `PGSERVICE`;
  - en el documento técnico, el pendiente de la semilla suma `PGHOSTADDR`.

  Verifica: el comando de PowerShell es válido tal como está escrito.
- [x] 4.3 Repetir las comprobaciones de la 3.1: `python tasks.py test`, `lint`, `typecheck` y `openapi-check` en verde.

## Workflow follow-up

- `/openspec-verify-change` y `/openspec-archive-change`, que funde el delta en `openspec/specs/semilla/spec.md`.
- Pull request de `feat/semilla-fuera-de-local` hacia `feature/entrega-3-AlexisBonansea`, dentro del fork.
