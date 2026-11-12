---
name: backend-feature
description: Construye una capability del backend con los tests primero, por pasos y con separacion de poderes. Usala para cualquier trabajo de backend que agregue o cambie comportamiento, aunque nadie la nombre.
---

# Capability del backend

Esta skill ordena el trabajo. No lo hace: reparte el trabajo entre dos
subagentes que no pueden pisarse, y vos comprobas cada paso.

La separacion es el punto. Quien escribe los tests no ve la
implementacion, asi los tests dicen lo que la historia pide y no lo que
el codigo hace. Quien implementa no puede tocar los tests, asi el verde
se consigue escribiendo codigo y no bajando la vara. Si una sola cabeza
hace las dos cosas, las dos se acomodan sin que nadie lo note.

**No saltees pasos y no los juntes.** Cada parada existe porque en ese
punto se cuela un error que despues no se ve.

---

## 0. De donde viene la tarea

Esta skill se invoca desde una tarea de `tasks.md` de un change de
OpenSpec (`openspec-apply-change`), nunca suelta. Si no hay change, pará:
primero `openspec-propose`. El codigo de produccion que no sale de un
change no tiene spec, y sin spec no hay contra que escribir el test.

## 1. Entender, sin escribir nada

Lee el Requirement entero en `openspec/specs/<capability>/spec.md`, o en
el delta del change (`openspec/changes/<change>/specs/<capability>/spec.md`)
si la tarea viene de uno. Conta sus Scenarios: habra **un test por
Scenario**. Si la tarea solo cubre algunos Requirements, anota cuales
quedan fuera.

Lee las reglas que la tocan en `docs/prd/aclaraciones-cliente.md`. Mira
que hay ya en `backend/app/` y en `backend/tests/`.

Si algo del criterio de aceptacion es ambiguo, **pará y preguntá
ahora**. Despues ya es tarde: la ambiguedad se convierte en test, el
test en codigo, y nadie se acuerda de que fue una suposicion.

## 2. Plan, y PARAR

Escribi en no mas de una pantalla:

- Que endpoints entran, con metodo y ruta.
- Que esquemas de Pydantic entran y salen.
- Que cambia en los modelos, y si hace falta migracion.
- Donde va la regla de negocio (`app/services/`).
- Que roles pueden usar cada endpoint y como se filtra para el Profesor.
- Un renglon por test que vas a pedir, apuntando a su Scenario.

**Presentalo y esperá el visto bueno.** No sigas por tu cuenta. Es la
parada mas barata del proceso: corregir un plan cuesta un minuto,
corregir una capability implementada cuesta una tarde.

## 3. Tests — subagente `test-writer`

Invoca al subagente `test-writer` pasandole la ruta de la spec (o del
delta), el nombre de la capability y la ruta
`backend/tests/functional/<capability>/`.

No le pases rutas de `backend/app/` ni fragmentos de implementacion. Si
se los pasas, rompiste la separacion con tus propias manos.

Cuando vuelva, comproba que su informe tiene la frase de confirmacion de
que no leyo la implementacion, y que hay un test por Scenario.

## 4. Ver el rojo — vos, no el subagente

```bash
make test
```

Mira la salida completa, test por test:

- **Todos los tests nuevos tienen que fallar.** Uno que ya este en verde
  no esta probando nada nuevo: o el comportamiento ya existia, o el test
  esta vacio. Averigua cual de las dos antes de seguir.
- **Tienen que fallar por el motivo correcto.** Un `ImportError` o un
  404 de una ruta inexistente son rojo de que el codigo no existe, y
  esta bien. Un error de sintaxis en el test, o una fixture rota, es
  rojo de que el test esta mal, y no sirve.
- **El control positivo tiene que fallar.** Si da verde, la suite no se
  esta corriendo y todo lo que sigue es humo.

Una vez visto fallar, quita el control positivo y volve a correr.

Guarda la salida completa del rojo en `.claude/tmp/rojo-<capability>.txt`.
Despues de implementar ya no se puede reproducir, y es la unica evidencia
de que este paso se hizo de verdad.

### Lee los tests, no solo el rojo

El rojo dice que los tests fallan. No dice que comprueben algo. Antes de
congelar, leelos buscando dos cosas que el rojo no muestra:

1. **Aserciones que se aprueban con una constante.** Si el estado inicial
   que prepara el test ya es el valor que despues afirma, el test pasa
   aunque el codigo no haga nada. Un test que crea el usuario con el
   contador en 0 y comprueba que quedo en 0 no prueba que el login lo
   resetee.
2. **Efectos que las fixtures no pueden distinguir.** Si la spec dice
   "quedo guardado en la base", comproba que el test lo pueda ver fallar.
   Una fixture que comparte estado con la API hace indistinguible un
   servicio que guarda de uno que no.

Lo que encuentres no lo arregles vos. Si es la spec la que esta floja,
va por `openspec-update-change`; si es el test, lo corrige `test-writer`.

Si algo de esto no se cumple, volve al paso 3. No sigas.

## 5. Formatear y congelar

**Formatea primero.** Si no, el primer `ruff format` posterior cambia la
huella por un espacio y hay que volver a invocar a `test-writer` para
corregirlo, porque un test solo lo toca quien lo escribio.

```bash
cd backend && .venv/Scripts/ruff format tests/functional/<capability> tests/conftest.py && cd ..
```

(en Linux y macOS, `.venv/bin/ruff`)

Despues congela:

```bash
git add backend/tests/functional/<capability> backend/tests/conftest.py
git ls-files -s -- backend/tests/functional/<capability> backend/tests/conftest.py > .claude/tmp/congelados.txt
```

**`conftest.py` entra en la huella.** Sin el, la forma mas facil de hacer
pasar un test sin tocarlo es aflojarle la fixture, y eso quedaba fuera del
congelado.

Esa huella es la garantia. No hay hook ni permiso que la sustituya: un
hook mira el texto del comando y se esquiva, la huella mira el
contenido y no.

## 6. Implementar — subagente `implementer`

Invoca al subagente `implementer` pasandole la ruta de los tests y la de
la spec. Tiene prohibido escribir dentro de `backend/tests/`, `conftest.py`
incluido.

**Si vuelve diciendo que un test esta mal, no lo arregles vos y no le
digas que lo arregle el.** Traemelo a mi con el argumento. Lo resuelve
una persona, y si hay que corregir el test lo corrige `test-writer`, que
es quien lo escribio. Que el implementador toque el test que lo esta
midiendo es el agujero entero.

## 7. Verde, y la huella intacta

Las dos cosas, en este orden:

```bash
git add backend/tests/functional/<capability> backend/tests/conftest.py
git ls-files -s -- backend/tests/functional/<capability> backend/tests/conftest.py | diff - .claude/tmp/congelados.txt
make test
make lint
make typecheck
```

- Si el `diff` devuelve algo, **los tests se tocaron**. No importa que
  este todo en verde: ese verde no vale. Mira que cambio, revertilo y
  volve al paso 6.
- Si `make test` tiene rojo, volve al paso 6.

## 8. Contrato y cierre

Si tocaste rutas, esquemas o modelos:

```bash
make openapi-generate
```

y el `docs/api/openapi.json` regenerado entra en el mismo commit. El CI
lo comprueba, asi que no es opcional.

Despues, con la skill `/commit`.

## Lo que esta skill no hace

- **No invoca al revisor adversarial.** Ese pase va una sola vez por
  change, antes de abrir el pull request, no al cerrar cada tarea.
- **No verifica ni archiva el change.** Eso es `openspec-verify-change` y
  `openspec-archive-change`, cuando todas las tareas del `tasks.md` esten
  hechas. Archivar es lo que funde el delta en la spec principal: hasta
  ahi la spec vigente es la de antes.
- No abre el pull request.
- No despliega.
