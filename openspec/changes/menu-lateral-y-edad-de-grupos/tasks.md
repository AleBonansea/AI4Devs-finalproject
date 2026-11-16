# Tasks

> Rama: `feat/menu-lateral-y-edad-de-grupos`, ya creada desde la rama de entrega actualizada (regla 1 de CLAUDE.md). Toda tarea que toca rutas, esquemas o modelos cierra con `python tasks.py openapi-generate` (regla 5).
>
> **Antes de la tarea 1:** el usuario revisa en pantalla el texto de las opciones (`Delfines · Mañana · 5 a 6 años`, `Tiburones · Mañana · 7 a 9 años`). Si no es como el club llama a esos grupos, se corrigen la spec y el design antes de escribir código.

## 1. Formato del nombre de la temporada

- [x] 1.1 Con la skill `backend-feature`, agregar al modelo `Temporada` el CHECK `ck_temporada_nombre_formato` y la migración `temporada_nombre_formato`, según el Requirement de `temporadas` «Formato del nombre de la temporada» (4 Scenarios).
  - Los tests insertan directo en la base, en `backend/tests/functional/temporadas/`.
  - Revisión y reversibilidad según design, «Reversibilidad».
  - **Se verifica con:**
    - los 4 tests en rojo por el motivo correcto (los tres nombres inválidos se guardan) y después en verde;
    - la skill `revisar-migracion` con `upgrade head` → `downgrade -1` → `upgrade head` contra la base de pruebas;
    - `python tasks.py test`, `lint` y `typecheck` en verde.

## 2. Edad del grupo en la API

- [x] 2.1 Con la skill `backend-feature`, sumar `edad_desde` y `edad_hasta` a `GET /api/v1/grupos`, según el Requirement modificado de `grupos` «Grupos donde se puede inscribir» (5 Scenarios, ya cubiertos por los tests existentes, que suman los dos campos) y el nuevo «Edad que cubre el grupo» (6 Scenarios).
  - Función pura en `app/services/grupos.py`, `Temporada.nombre` en el `select` y los campos en `GrupoParaInscribir` (design, decisiones 1 y 2).
  - Los tests del Requirement nuevo van en `backend/tests/functional/grupos/`. El de la temporada «2027-28» crea esa temporada como vigente, sin la 2026-27.
  - **Se verifica con:**
    - los 6 tests nuevos en rojo por el motivo correcto (la respuesta no trae los campos) y después en verde;
    - los de `grupos` que ya existían, en verde;
    - `docs/api/openapi.json` regenerado y `python tasks.py openapi-check` en verde, con el diff limitado a los dos campos;
    - `python tasks.py test`, `lint` y `typecheck` en verde.

## 3. Edad en los selectores de grupo

- [x] 3.1 Con la skill `frontend-feature`, escribir la edad en los dos selectores, según el Requirement modificado de `alumnos` «Grupos en la pantalla» (7 Scenarios) y el de `asistencia` «Pantalla «Tomar asistencia»» (4 Scenarios).
  - `textoDelGrupo` en `src/lib/nombres.ts` (design, decisión 4).
  - Los dos campos en el tipo `GrupoParaInscribir` de `src/lib/api.ts`.
  - `SelectorGrupo` y `SelectorGrupoDeAsistencia` usan la función.
  - Los tests existentes de `frontend/tests/alumnos/` y `frontend/tests/asistencia/` que comparan `Delfines · Mañana` los reescribe el test-writer contra los deltas, incluidos los `fetch` fingidos con los dos campos nuevos.
  - **Se verifica con:**
    - los tests en rojo por el motivo correcto (las opciones no traen la edad);
    - la huella de `frontend/tests/` intacta después de implementar;
    - `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.

## 4. Menú lateral

- [x] 4.1 Con la skill `frontend-feature`, construir el marco de la zona protegida, según los 5 Requirements de `navegacion` (12 Scenarios) y el Requirement modificado de `auth` «Inicio de la zona protegida» (8 Scenarios).
  - `MarcoZonaProtegida` y `MenuLateral` en `src/components/`, con la lista de opciones declarativa.
  - La ruta de diseño en `App.tsx`, dentro de `RutaProtegida`.
  - El inicio queda con `Hola, <nombre>`.
  - `Salir` se mueve al encabezado.
  - Todo según design, decisiones 5 y 6. Colores solo de `src/tema.ts`.
  - Tests en `frontend/tests/navegacion/`. Los de `frontend/tests/auth/inicio-*.test.tsx` los reescribe el test-writer contra el delta de `auth`.
  - **Se verifica con:**
    - los tests en rojo por el motivo correcto (no hay menú);
    - la huella de `frontend/tests/` intacta después de implementar;
    - `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.
- [ ] 4.2 Revisar a ojo el marco en ancho de escritorio y de teléfono (360 px) con `python tasks.py up` y la semilla, contra `docs/previews/01-inicio.png` y `09-mobile-inicio.png`. **Se verifica con** capturas de `/`, `/alumnos/nuevo` y `/asistencia` en los dos anchos: en teléfono el menú es una fila desplazable y no hay desplazamiento horizontal de la página.

## 5. Cierre

- [ ] 5.1 Comprobación completa: `python tasks.py test`, `lint`, `typecheck`, `openapi-check`, `front-test`, y `cd frontend && npm run lint && npm run build`, todo en verde.
- [ ] 5.2 Pase del subagente `adversarial-reviewer` sobre el change completo, una sola vez, antes del pull request. **Se verifica con** su informe y cada hallazgo resuelto o descartado con motivo.

## Workflow follow-up

- `/openspec-verify-change`, `/openspec-archive-change` y pull request de `feat/menu-lateral-y-edad-de-grupos` hacia la rama de entrega, dentro del fork.
- Al archivar, sumar el change al registro del backlog, en la entrada del lote 3.
