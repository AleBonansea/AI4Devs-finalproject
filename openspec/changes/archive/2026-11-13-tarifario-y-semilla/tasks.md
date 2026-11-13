# Tasks

## 1. Tablas de grupos y tarifario

- [x] 1.1 Con la skill `backend-feature`, construir el esquema según todos los requirements de `specs/grupos/spec.md` (11 Scenarios) y de `specs/tarifario/spec.md` (22 Scenarios al cerrar la 1.1).
  - Tipos enumerados compartidos en `app/models/enums.py`.
  - Modelos en `app/models/grupo.py` y `app/models/tarifario.py`, registrados en `app/models/__init__.py`.
  - **Una sola migración** `crear grupos y tarifario`, generada con `--autogenerate`. Va revisada con la skill `revisar-migracion` y con el `DROP TYPE` de los cuatro enums escrito a mano en el `downgrade` (design, «Reversibilidad»).
  - Los tests van en `backend/tests/functional/grupos/` y `backend/tests/functional/tarifario/`, contra Postgres, con SQL crudo para los valores de enum inválidos (design, «Cómo se prueban las restricciones»).
  - **Se verifica con:**
    - los tests de las dos carpetas en verde, tras el rojo;
    - la migración probada en los dos sentidos contra la base de pruebas (`alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head`).

## 2. La semilla

- [x] 2.1 Con la skill `backend-feature`, construir la semilla según todos los requirements de `specs/semilla/spec.md` (19 Scenarios al cerrar la 2.1).
  - `verificar_base_local(url)` y `cargar(sesion)` en `app/semilla.py`, con la excepción `SemillaRechazada`. `cargar` hace `flush` y nunca `commit`.
  - `scripts/seed.py` comprueba el host antes de la primera conexión, hace el único `commit` y sale con código 1 ante `SemillaRechazada` (design, «La semilla vive en `app/semilla.py`»).
  - Los tests van en `backend/tests/functional/semilla/`. El Scenario de login usa el fixture `cliente` después de `cargar(sesion)`.
  - **Se verifica con** los tests de esa carpeta en verde, tras el rojo.
- [x] 2.2 Correr la semilla de punta a punta, sobre una base de desarrollo recién migrada y vacía.
  - `python tasks.py seed` termina con código 0 e imprime los cuatro usuarios.
  - Un segundo `python tasks.py seed` termina con código 1 y el mensaje de base no vacía.
  - Con la API levantada (`cd backend && uvicorn app.main:app`; `python tasks.py up` solo levanta Postgres), `POST /api/v1/auth/login` con `mgarcia` / `Verano2026` responde 200.

## 3. Contrato y calidad

- [x] 3.1 Correr `python tasks.py openapi-generate` y comprobar que `docs/api/openapi.json` no cambió, porque el change no agrega rutas ni esquemas, y que `python tasks.py openapi-check` pasa.
- [x] 3.2 Correr la suite completa con `python tasks.py test`, más `python tasks.py lint` y `python tasks.py typecheck`, todo en verde. Incluye los tests de `auth` y `test_migracion_inicial.py`, que no pueden romperse con las tablas nuevas.

## 4. Revisión adversarial

- [x] 4.1 Un pase del subagente `adversarial-reviewer` sobre el change terminado, antes del pull request. Rige `REVIEW.md`, «Cuándo se deja de revisar»: desde el segundo pase solo un hallazgo grave reabre el change. Se verifica con sus hallazgos resueltos o justificados por escrito. Sin graves; los dos menores (host remoto en la query de la URL y escala de los decimales sin test) y la pregunta sobre `monto_fijo` se resuelven en 4.2. No hay segundo pase.
- [x] 4.2 Con la skill `backend-feature`, resolver los hallazgos de 4.1 según los Scenarios nuevos: «Un host remoto escondido en la query» y «Una dirección remota escondida en la query» (en `specs/semilla/spec.md`, tests en `semilla/`); «Un monto con tres decimales se guarda con dos», «Un porcentaje con tres decimales se guarda con dos», «El monto fijo mínimo positivo» y «Monto fijo cero» (en `specs/tarifario/spec.md`, tests en `tarifario/`). Implementación: `verificar_base_local` revisa `host` y `hostaddr` de la query, y una migración nueva agrega `CHECK (monto_fijo > 0)` a `tipo_cargo` (design, «Una segunda migración»), probada en los dos sentidos. Se verifica con la suite completa en verde tras el rojo.
- [x] 4.3 `python tasks.py openapi-check` sin cambios, y `python tasks.py test`, `lint` y `typecheck` en verde.

## Workflow follow-up

- Comprobar el change con `/openspec-verify-change` y archivarlo con `/openspec-archive-change`, que crea `openspec/specs/grupos/`, `openspec/specs/tarifario/` y `openspec/specs/semilla/`.
- El change no tiene historias con criterios en `5-historias-de-usuario.md`, así que al archivar no hay nada que reemplazar ahí.
