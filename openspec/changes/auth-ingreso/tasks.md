# Tasks

## 1. Ingreso: `POST /api/v1/auth/login`

- [ ] 1.1 Con la skill `backend-feature`, construir el login según los requirements «Ingreso con usuario y contraseña», «Credenciales rechazadas sin revelar la causa», «Contador de intentos fallidos» y «Usuario bloqueado no ingresa» de `specs/auth/spec.md`: esquemas en `app/schemas/auth.py`, servicio en `app/services/auth.py` (hash ficticio para inexistente y desactivado, bloqueo sin verificar contraseña, incremento atómico con commit antes del 401) y router en `app/api/v1/auth.py` incluido en `app/api/v1/router.py`. Los tests van en `backend/tests/functional/test_auth_login.py`, un test por Scenario. Se verifica con `cd backend && pytest tests/functional/test_auth_login.py` en verde, tras haberlo visto en rojo por el motivo correcto.

## 2. Usuario actual

- [ ] 2.1 Con la skill `backend-feature`, construir `obtener_usuario_actual` en `app/core/deps.py` y `GET /api/v1/auth/yo` con respuesta `UsuarioActual`, según el requirement «Identificación del usuario actual por token» y el Scenario «Con el cambio pendiente igual puede saber quién es» de `specs/auth/spec.md`. Los tokens vencidos, los firmados con otra clave y los de `sub` inexistente se fabrican en el test con PyJWT. Tests en `backend/tests/functional/test_auth_usuario_actual.py`; se verifica con `pytest` de ese archivo en verde tras el rojo.

## 3. Cambio pendiente y declaración de roles

- [ ] 3.1 Con la skill `backend-feature`, construir `usuario_habilitado` y `exigir_rol(*roles)` en `app/core/deps.py` según el requirement «Declaración de roles por endpoint» y los Scenarios «Con el cambio pendiente no puede hacer nada más» y «Con el cambio pendiente tampoco pasa un endpoint de su rol». Los tests montan un router de sonda en una app de FastAPI propia del test (ver design, «Cómo se prueba `exigir_rol`»), sin agregar rutas a la aplicación real. Tests en `backend/tests/functional/test_auth_roles.py`; se verifica con `pytest` de ese archivo en verde tras el rojo.

## 4. Contrato y calidad

- [ ] 4.1 Regenerar `docs/api/openapi.json` con `make openapi-generate` y comprobar que aparecen `POST /api/v1/auth/login`, `GET /api/v1/auth/yo` y el esquema de seguridad bearer, sin ninguna ruta de sonda; `make openapi-check` pasa.
- [ ] 4.2 Correr `make test`, `make lint` y `make typecheck` en verde, con la suite completa (incluidos `test_salud.py` y `test_migracion_inicial.py`).

## 5. Revisión adversarial

- [ ] 5.1 Un único pase del subagente `adversarial-reviewer` sobre el change terminado, antes de abrir el pull request de `feat/auth-ingreso` hacia `feature/entrega-2-AlexisBonansea`. Se verifica con sus hallazgos resueltos o justificados por escrito.

## Workflow follow-up

- Comprobar el change con `/openspec-verify-change` y archivarlo con `/openspec-archive-change`, que funde el delta en `openspec/specs/auth/spec.md`.
- HU-UT-01 no tiene criterios en `5-historias-de-usuario.md`, así que al archivar no hay nada que reemplazar ahí.
