# Tasks

## 1. Paleta del prototipo

- [x] 1.1 Reescribir el catálogo y el mapeo de `frontend/src/tema.ts` según design.md, decisiones 1 y 2 (`primary` → `accion`, `deuda` = `dinero`, `error` aparte, se eliminan `marcaClara` y `acento`). Se hace directo, sin `frontend-feature` ni subagentes: la skill solo tiene el camino de los tests primero, y esta tarea no tiene Scenario porque el color no se comprueba desde el DOM (design.md, decisión 4). Sin tests no hay nada que el implementador pueda acomodar, así que la separación de poderes no protege nada acá. Decidido con el usuario al aplicar. Verificación: `cd frontend && npm run lint && npm run build` y `python tasks.py front-test` en verde, sin tocar ningún test.
  - Resultado: build en verde y 57 de 57 tests en verde, sin tocar ningún test. ESLint en verde. `prettier --check` falla en 14 archivos que este change no toca, solo por CRLF: el índice está en LF, pero `core.autocrlf=true` los saca con CRLF y el frontend no tiene `.gitattributes`. Con `--end-of-line auto` pasan todos. Es un defecto del entorno, previo a este change.
- [x] 1.2 Revisar a ojo, con la app levantada (`python tasks.py up`), las pantallas existentes: ingreso, aviso de cambio pendiente, inicio y registrar alumno. Buscar colores que no salgan del tema. Si aparece uno, reemplazarlo por un nombre del tema en esa pantalla, sin tocar el tema. Verificación: capturas de cada pantalla en el informe de la tarea, más `grep` de valores a pelo en `frontend/src/` fuera de `tema.ts`, sin resultados.
  - Resultado: el `grep` de `#hex`, `rgb(` y `hsl(` en `frontend/src/` fuera de `tema.ts` no devuelve nada. Capturas a 1360×900 con Chrome headless, por CDP: ingreso, inicio, registrar alumno y aviso de cambio pendiente. Para el aviso se reescribió en el navegador la respuesta de `/auth/yo`, sin tocar la base. Las cuatro toman el tema: acción azul, fondo y bordes fríos, aviso en `pendiente`. No hay que reemplazar ningún color.
  - Diferencias con el prototipo que no son de color y quedan fuera de esta tarea: los botones salen en mayúsculas (el `textTransform` por defecto de MUI) y en el prototipo van en minúsculas con negrita; y la fuente `Inter` que declara el tema no se carga, así que se ve la del sistema.

## 2. Encuadre de las pantallas sin sesión

- [ ] 2.1 Con la skill `frontend-feature`: tests de los Requirements «Encabezado de las pantallas sin sesión» y «Un solo botón de ingreso» del delta de `auth`, escritos por el `test-writer` en `frontend/tests/auth/`, un test por Scenario (5). Verificación: `python tasks.py front-test` los muestra en rojo por la razón correcta (falta el encabezado o el título, no un error de montaje), y quedan congelados por hash.
- [ ] 2.2 Con la skill `frontend-feature`: crear `frontend/src/components/EncuadreSinSesion.tsx` (design.md, decisión 3) y hacer que `Ingreso.tsx` y `CambioPendiente.tsx` lo usen, sin cambiar su comportamiento. Verificación: los 5 tests nuevos en verde, toda la suite de frontend en verde con los tests congelados sin cambios, `npm run lint && npm run build` en verde.
- [ ] 2.3 Comparar `/ingresar` en la app levantada con `docs/previews/00-ingreso.png`, en este orden: logo, título verde, subtítulo sin año, campos, un único botón `Ingresar`. No tiene que aparecer el recuadro de prototipo ni los botones por rol. Verificación: captura de `/ingresar` en el informe de la tarea, al lado de la del prototipo.

## 3. Documentación

- [ ] 3.1 Referenciar `docs/previews/00-ingreso.png` en `1-descripcion-general-del-producto.md`, sección 1.3, debajo del punto «1. Ingreso», con el mismo formato que las otras capturas. Aclarar que el recuadro y los botones por rol de la captura son del prototipo y que el sistema tiene un solo botón. Verificación: la imagen se ve en la vista previa del Markdown y la ruta existe.

## 4. Cierre

- [ ] 4.1 Pase único del subagente `adversarial-reviewer` sobre el change terminado, antes de abrir el pull request. Verificación: hallazgos resueltos o justificados en este archivo.

## Workflow follow-up

- `/openspec-verify-change` y `/openspec-archive-change`, que funde el delta en `openspec/specs/auth/spec.md`.
- Pull request de `feat/paleta-y-encuadre` hacia `feature/entrega-2-AlexisBonansea`. Lleva también los dos commits del arnés de agentes (modelo del implementer y candado del test-writer).
