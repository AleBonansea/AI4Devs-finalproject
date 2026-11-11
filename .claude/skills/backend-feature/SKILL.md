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

## 1. Entender, sin escribir nada

Lee la historia y sus criterios de aceptacion en
`5-historias-de-usuario.md`. Lee las reglas que la tocan en
`docs/prd/aclaraciones-cliente.md`. Mira que hay ya en `backend/app/`
y en `backend/tests/`.

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
- Un renglon por test que vas a pedir, apuntando a su criterio.

**Presentalo y esperá el visto bueno.** No sigas por tu cuenta. Es la
parada mas barata del proceso: corregir un plan cuesta un minuto,
corregir una capability implementada cuesta una tarde.

## 3. Tests — subagente `test-writer`

Invoca al subagente `test-writer` pasandole la historia, los criterios
y la ruta `backend/tests/functional/<capability>/`.

No le pases rutas de `backend/app/` ni fragmentos de implementacion. Si
se los pasas, rompiste la separacion con tus propias manos.

Cuando vuelva, comproba que su informe tiene la frase de confirmacion de
que no leyo la implementacion, y que hay un test por criterio.

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

Si algo de esto no se cumple, volve al paso 3. No sigas.

## 5. Congelar los tests

```bash
git add backend/tests/functional/<capability>
git ls-files -s -- backend/tests/functional/<capability> > .claude/tmp/congelados.txt
```

Eso deja guardada la huella del contenido de cada archivo de prueba.

Esa huella es la garantia. No hay hook ni permiso que la sustituya: un
hook mira el texto del comando y se esquiva, la huella mira el
contenido y no.

## 6. Implementar — subagente `implementer`

Invoca al subagente `implementer` pasandole la ruta de los tests y la
historia. Tiene prohibido escribir dentro de `backend/tests/`.

**Si vuelve diciendo que un test esta mal, no lo arregles vos y no le
digas que lo arregle el.** Traemelo a mi con el argumento. Lo resuelve
una persona, y si hay que corregir el test lo corrige `test-writer`, que
es quien lo escribio. Que el implementador toque el test que lo esta
midiendo es el agujero entero.

## 7. Verde, y la huella intacta

Las dos cosas, en este orden:

```bash
git add backend/tests/functional/<capability>
git ls-files -s -- backend/tests/functional/<capability> | diff - .claude/tmp/congelados.txt
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
  unidad de trabajo, antes de abrir el pull request, no al cerrar cada
  capability.
- No abre el pull request.
- No despliega.
