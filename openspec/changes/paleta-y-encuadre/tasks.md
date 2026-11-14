# Tasks

## 1. Paleta del prototipo

- [x] 1.1 Reescribir el catálogo y el mapeo de `frontend/src/tema.ts` según design.md, decisiones 1 y 2 (`primary` → `accion`, `deuda` = `dinero`, `error` aparte, se eliminan `marcaClara` y `acento`). Se hace directo, sin `frontend-feature` ni subagentes: la skill solo tiene el camino de los tests primero, y esta tarea no tiene Scenario porque el color no se comprueba desde el DOM (design.md, decisión 4). Sin tests no hay nada que el implementador pueda acomodar, así que la separación de poderes no protege nada acá. Decidido con el usuario al aplicar. Verificación: `cd frontend && npm run lint && npm run build` y `python tasks.py front-test` en verde, sin tocar ningún test.
  - Resultado: build en verde y 57 de 57 tests en verde, sin tocar ningún test. ESLint en verde. `prettier --check` falla en 14 archivos que este change no toca, solo por CRLF: el índice está en LF, pero `core.autocrlf=true` los saca con CRLF y el frontend no tiene `.gitattributes`. Con `--end-of-line auto` pasan todos. Es un defecto del entorno, previo a este change.
- [x] 1.2 Revisar a ojo, con la app levantada (`python tasks.py up`), las pantallas existentes: ingreso, aviso de cambio pendiente, inicio y registrar alumno. Buscar colores que no salgan del tema. Si aparece uno, reemplazarlo por un nombre del tema en esa pantalla, sin tocar el tema. Verificación: capturas de cada pantalla en el informe de la tarea, más `grep` de valores a pelo en `frontend/src/` fuera de `tema.ts`, sin resultados.
  - Resultado: el `grep` de `#hex`, `rgb(` y `hsl(` en `frontend/src/` fuera de `tema.ts` no devuelve nada. Capturas a 1360×900 con Chrome headless, por CDP: ingreso, inicio, registrar alumno y aviso de cambio pendiente. Para el aviso se reescribió en el navegador la respuesta de `/auth/yo`, sin tocar la base. Las cuatro toman el tema: acción azul, fondo y bordes fríos, aviso en `pendiente`. No hay que reemplazar ningún color.
  - Diferencias con el prototipo que no son de color y quedan fuera de esta tarea: los botones salen en mayúsculas (el `textTransform` por defecto de MUI) y en el prototipo van en minúsculas con negrita; y la fuente `Inter` que declara el tema no se carga, así que se ve la del sistema.

## 2. Encuadre de las pantallas sin sesión

- [x] 2.1 Con la skill `frontend-feature`: tests de los Requirements «Encabezado de las pantallas sin sesión» y «Un solo botón de ingreso» del delta de `auth`, escritos por el `test-writer` en `frontend/tests/auth/`, un test por Scenario (5). Verificación: `python tasks.py front-test` los muestra en rojo por la razón correcta (falta el encabezado o el título, no un error de montaje), y quedan congelados por hash.
  - Resultado: `frontend/tests/auth/encabezado-sin-sesion.test.tsx`, 5 tests. Los 3 del encabezado fallan porque no encuentran el logo: falta lo que piden, no es un error de montaje. El control positivo falló como debía y se quitó. Salida en `.claude/tmp/rojo-front-auth.txt`; huella en `.claude/tmp/congelados-front.txt`.
  - El control «todos los tests nuevos fallan» no se cumple al pie de la letra: «El único botón es Ingresar» y «No se puede elegir el rol al entrar» ya pasan, porque la pantalla actual ya tiene un solo botón. Quedan como tests de regresión. Para comprobar que no son vacíos, se agregó a `Ingreso.tsx` de forma temporal un botón «Entrar como Administrador» y el texto «Prototipo»: los dos fallaron, y se restauró el archivo.
- [x] 2.2 Con la skill `frontend-feature`: crear `frontend/src/components/EncuadreSinSesion.tsx` (design.md, decisión 3) y hacer que `Ingreso.tsx` y `CambioPendiente.tsx` lo usen, sin cambiar su comportamiento. Verificación: los 5 tests nuevos en verde, toda la suite de frontend en verde con los tests congelados sin cambios, `npm run lint && npm run build` en verde.
- [x] 2.3 Comparar `/ingresar` en la app levantada con `docs/previews/00-ingreso.png`, en este orden: logo, título verde, subtítulo sin año, campos, un único botón `Ingresar`. No tiene que aparecer el recuadro de prototipo ni los botones por rol. Verificación: captura de `/ingresar` en el informe de la tarea, al lado de la del prototipo.
  - Resultado: capturas a 1360×900 y a 390×844 (teléfono) del ingreso, del ingreso enviado vacío y del aviso de cambio pendiente. El orden coincide con el prototipo: logo, título verde, subtítulo sin año, campos, un solo botón `Ingresar`. No aparece el recuadro de prototipo ni los botones por rol. Los errores por campo salen en el rojo `error`.
  - Defecto encontrado y corregido: a ancho de teléfono, el título y el subtítulo se partían en dos renglones alineados a la izquierda. Se agregó `textAlign="center"` en `EncuadreSinSesion`. Los tests siguen en verde y la huella intacta.
  - Diferencias con el prototipo que quedan para decidir:
    - el logo del prototipo va dentro de un círculo con anillo `#14303f` y fondo gris, y `logo.png` es transparente alrededor del dibujo;
    - las etiquetas del prototipo van arriba del campo, y las de MUI flotan dentro;
    - los botones salen en mayúsculas;
    - la fuente `Inter` no se carga.

- [ ] 2.4 Con la skill `frontend-feature`: el `test-writer` agrega el test del Scenario «En el aviso, el encabezado va antes del aviso» (Requirement «Encabezado de las pantallas sin sesión»), que se sumó por el hallazgo 2 del pase adversarial. Como el encuadre ya está hecho, se espera que pase. Se comprueba que no es vacío alterando el orden de `CambioPendiente.tsx` de forma temporal, y se restaura. Verificación: el test falla con el orden alterado y pasa con el real; toda la suite en verde y la huella nueva congelada.
- [ ] 2.5 Reemplazar «Escuelita de Verano» por «Escuela de Verano» en `frontend/src/pages/Inicio.tsx` y en el `<title>` de `frontend/index.html`. Es un texto que ningún Scenario fija, así que se hace directo, sin subagentes. Verificación: un `grep -rn "Escuelita de Verano" frontend/src frontend/index.html` sin resultados, y la suite, el lint (`eslint` más `prettier --check --end-of-line auto`) y el build en verde.

## 3. Documentación

- [x] 3.1 Referenciar `docs/previews/00-ingreso.png` en `1-descripcion-general-del-producto.md`, sección 1.3, debajo del punto «1. Ingreso», con el mismo formato que las otras capturas. Aclarar que el recuadro y los botones por rol de la captura son del prototipo y que el sistema tiene un solo botón. Verificación: la imagen se ve en la vista previa del Markdown y la ruta existe.

## 4. Cierre

- [ ] 4.1 Pase único del subagente `adversarial-reviewer` sobre el change terminado, antes de abrir el pull request. Verificación: hallazgos resueltos o justificados en este archivo.
  - Pase hecho: 0 graves, 5 menores, 2 preguntas.
    1. *El candado dejaba leer `frontend/dist/`* → **resuelto**. `frontend/dist` entra en las rutas protegidas del hook y en la prosa del test-writer.
    2. *El orden del encabezado se exige en las dos pantallas y solo se prueba en el ingreso* → **pendiente de decisión del usuario**: requiere un Scenario nuevo.
    3. *El Requirement nuevo choca con «Aviso de cambio de contraseña pendiente» («solo un aviso»)* → **pendiente de decisión del usuario**: requiere pasarlo a MODIFIED.
    4. *El proposal y el design decían que los assets «ya estaban en el repo» y prometían un «logo circular»* → **resuelto**: se corrigió el texto.
    5. *El hook fallaba abierto ante un error propio* → **resuelto**: ahora falla cerrado. Con `python` fuera del PATH no se puede cubrir, y quedó documentado en el hook y en CLAUDE.md.
    - Pregunta *¿el test-writer puede escribir en la implementación?* → **resuelto**: el hook corta también `Write`, `Edit` y `NotebookEdit` sobre esas rutas.
    - Pregunta *¿«Escuela» o «Escuelita» de Verano?* → **pendiente de decisión del usuario**.
  - Comprobaciones del hook después de los cambios: 18 casos con el resultado esperado, entre ellos un JSON roto y una entrada con forma inesperada, que bloquean.

## Workflow follow-up

- `/openspec-verify-change` y `/openspec-archive-change`, que funde el delta en `openspec/specs/auth/spec.md`.
- Pull request de `feat/paleta-y-encuadre` hacia `feature/entrega-2-AlexisBonansea`. Lleva también los dos commits del arnés de agentes (modelo del implementer y candado del test-writer).
