# Tasks

## 1. Ingreso: `POST /api/v1/auth/login`

- [x] 1.1 Con la skill `backend-feature`, construir el login según los requirements «Ingreso con usuario y contraseña», «Credenciales rechazadas sin revelar la causa», «Contador de intentos fallidos» y «Usuario bloqueado no ingresa», más el Scenario «Ingresa con el cambio pendiente», de `specs/auth/spec.md` (15 Scenarios): esquemas en `app/schemas/auth.py`, servicio en `app/services/auth.py` (hash ficticio para inexistente y desactivado, bloqueo sin verificar contraseña, incremento atómico con commit antes del 401) y router en `app/api/v1/auth.py` incluido en `app/api/v1/router.py`. Los tests van en `backend/tests/functional/auth/test_login.py` (con `backend/tests/functional/auth/__init__.py`), un test por Scenario. Se verifica con `cd backend && pytest tests/functional/auth/test_login.py` en verde, tras haberlo visto en rojo por el motivo correcto.

## 2. Usuario actual

- [x] 2.1 Con la skill `backend-feature`, construir `obtener_usuario_actual` en `app/core/deps.py` y `GET /api/v1/auth/yo` con respuesta `UsuarioActual`, según el requirement «Identificación del usuario actual por token» y el Scenario «Con el cambio pendiente igual puede saber quién es» de `specs/auth/spec.md` (10 Scenarios). Los tokens vencidos, los firmados con otra clave y los de `sub` inexistente se fabrican en el test con PyJWT. Tests en `backend/tests/functional/auth/test_usuario_actual.py`; se verifica con `pytest` de ese archivo en verde tras el rojo.

## 3. Cambio pendiente y declaración de roles

- [x] 3.1 Con la skill `backend-feature`, construir `usuario_habilitado` y `exigir_rol(*roles)` en `app/core/deps.py` según el requirement «Declaración de roles por endpoint» y los Scenarios «Con el cambio pendiente no puede hacer nada más» y «Con el cambio pendiente tampoco pasa un endpoint de su rol» (6 Scenarios). Los tests montan un router de sonda en una app de FastAPI propia del test (ver design, «Cómo se prueba `exigir_rol`»), sin agregar rutas a la aplicación real. Tests en `backend/tests/functional/auth/test_roles.py`; se verifica con `pytest` de ese archivo en verde tras el rojo.

## 4. Contrato y calidad

- [x] 4.1 Regenerar `docs/api/openapi.json` con `python tasks.py openapi-generate` y comprobar que aparecen `POST /api/v1/auth/login`, `GET /api/v1/auth/yo`, el esquema de seguridad bearer y, declarados con `responses=`, el 401 y el 403 del login y el 401 de `/yo` con sus mensajes exactos (`/yo` no tiene 403: está exento del cambio pendiente y no exige rol), sin ninguna ruta de sonda; `python tasks.py openapi-check` pasa.
- [x] 4.2 Correr `python tasks.py test`, `python tasks.py lint` y `python tasks.py typecheck` en verde, con la suite completa (incluidos `test_salud.py` y `test_migracion_inicial.py`).

## 5. Revisión adversarial

- [ ] 5.1 Un único pase del subagente `adversarial-reviewer` sobre el change terminado, antes de abrir el pull request de `feat/auth-ingreso` hacia `feature/entrega-2-AlexisBonansea`. Se verifica con sus hallazgos resueltos o justificados por escrito.

- [ ] 5.2 Con la skill `backend-feature`, resolver los hallazgos del pase 5.1 según los Scenarios nuevos de `specs/auth/spec.md`: «El usuario trae un carácter de control» y «El usuario es solo espacios» (requirement «Pedido de ingreso malformado», en `test_login.py`), «Token cuyo sub está fuera del rango de los ids» (en `test_usuario_actual.py`) y «Con el cambio pendiente, el 403 de cambio gana al de rol» (en `test_roles.py`). En el mismo ciclo, sin Scenario: `LoginEntrada` normaliza y valida `username` (1 a 60, sin caracteres de control) y `password` (1 a 128), y el login lee el usuario con `with_for_update()` (design, «Concurrencia»; excepción sin test documentada). Se verifica con la suite completa en verde tras el rojo de los Scenarios nuevos.
- [ ] 5.3 Regenerar `docs/api/openapi.json` (`python tasks.py openapi-generate`) y comprobar `python tasks.py openapi-check`.
- [ ] 5.4 Segundo y último pase del `adversarial-reviewer` sobre el change con los hallazgos resueltos; lo que quede se justifica por escrito.

## Workflow follow-up

- Comprobar el change con `/openspec-verify-change` y archivarlo con `/openspec-archive-change`, que funde el delta en `openspec/specs/auth/spec.md`.
- HU-UT-01 no tiene criterios en `5-historias-de-usuario.md`, así que al archivar no hay nada que reemplazar ahí.
