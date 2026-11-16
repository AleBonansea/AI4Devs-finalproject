---
name: frontend-feature
description: Construye una pantalla del frontend contra la API ya existente, con catalogo primero y los tests antes que el codigo. Usala para cualquier trabajo de interfaz, aunque nadie la nombre.
---

# Pantalla del frontend

Esta skill ordena el trabajo igual que `backend-feature`: quien escribe
los tests (`test-writer`) no ve la implementacion, y quien implementa
(`ui-implementer`) no puede tocar los tests. Vos comprobas cada paso.

**No saltees pasos y no los juntes.**

---

## 0. De donde viene la tarea

Esta skill se invoca desde una tarea de `tasks.md` de un change de
OpenSpec (`openspec-apply-change`), nunca suelta. Si no hay change,
pará: primero `openspec-propose`.

## 1. El contrato manda

Lee `docs/api/openapi.json` para los endpoints que la pantalla usa. Lo
que la API devuelve es lo que la pantalla muestra: no inventes campos
ni supongas formas.

Si la pantalla necesita algo que la API no da, **pará**. Eso es una
historia de backend, no un arreglo en el componente.

Lee el Requirement entero en el delta del change y conta sus Scenarios:
habra **un test por Scenario**. Si algo es ambiguo, pará y preguntá
ahora.

## 2. Catalogo primero

El catalogo es **MUI** (`@mui/material` y `@mui/x-data-grid`) mas lo
que haya en `frontend/src/components/`. Una carpeta vacia no es falta
de catalogo: es que todavia no se extrajo nada propio.

Escribi el plan de la pantalla **nombrando que componente de MUI (o de
`components/`) cubre cada parte**, y si falta alguno. Un elemento HTML
con estilos a mano donde MUI ya tiene un componente es un defecto, no
una variante.

Una pieza que falta no se improvisa dentro de la pantalla ni se inventa
por las dudas: se señala en el plan y la decide una persona. A
`components/` se extrae lo que ya se repitio, no lo que podria
repetirse.

## 3. Plan, y PARAR

Media pantalla: la ruta, que datos pide, que componentes usa, que
componentes nuevos hacen falta, como se comporta en carga, vacio y
error, y **un renglon por test que vas a pedir, apuntando a su
Scenario**. Presentalo y esperá el visto bueno.

## 4. Tests — subagente `test-writer`

Invocalo pasandole:

- la ruta del delta (`openspec/changes/<change>/specs/<capability>/spec.md`)
  y que Requirements cubre la tarea;
- que es una tarea **de frontend**;
- la carpeta de destino, `frontend/tests/<capability>/`.

No le pases rutas de `frontend/src/` ni fragmentos de implementacion.
Lo unico que necesita saber del codigo es lo que dice su propia
definicion: la aplicacion se monta con el `App` de `src/App.tsx`
dentro de un `MemoryRouter`, y la API se finge en `fetch`.

Cuando vuelva, comproba la frase de que no leyo la implementacion y que
hay un test por Scenario.

## 5. Ver el rojo — vos, no el subagente

```bash
python tasks.py front-test
```

Mira la salida test por test:

- **Todos los tests nuevos tienen que fallar**, y por el motivo
  correcto: un modulo que no existe, un texto o un rol que no aparece.
  Un error de sintaxis o de tipos en el test, o una preparacion rota, es
  rojo de que el test esta mal y no sirve.
- **El control positivo tiene que fallar.** Despues se quita y se vuelve
  a correr.
- Los tests de tareas anteriores siguen en verde.

Guarda la salida completa en `.claude/tmp/rojo-front-<capability>.txt`.

### Lee los tests, no solo el rojo

Antes de congelar, busca:

1. **Aserciones que se aprueban con una constante**: un `queryByText`
   que afirma que algo *no* esta pasa igual si la pantalla no renderiza
   nada. Todo "no aparece" necesita al lado algo que si aparezca.
2. **Esperas que no esperan**: una afirmacion sobre lo que se ve despues
   de una respuesta de la API tiene que ir con `findBy...` o `waitFor`.
   Sin eso, el test mira la pantalla antes de que llegue la respuesta.
3. **El `fetch` fingido que no se comprueba**: si la spec dice "no se
   llama a la API", el test tiene que afirmar que el stub no se llamo.

Lo que encuentres no lo arregles vos: la spec va por
`openspec-update-change`, el test lo corrige `test-writer`.

## 6. Formatear y congelar

```bash
cd frontend && npx prettier --write tests && cd ..
git add frontend/tests frontend/vite.config.ts
git ls-files -s -- frontend/tests frontend/vite.config.ts > .claude/tmp/congelados-front.txt
```

**`vite.config.ts` entra en la huella** porque tiene el bloque `test`:
achicar el `include` o cambiar el entorno es la forma de hacer pasar un
test sin tocarlo, igual que aflojar una fixture en `conftest.py`.

## 7. Construir — subagente `ui-implementer`

Invocalo con el plan aprobado, la lista de componentes de MUI, la ruta
del delta y la de los tests. Tiene prohibido escribir en
`frontend/tests/` y en `vite.config.ts`.

Si vuelve diciendo que un test esta mal, no lo arregles vos: traelo a
una persona, con el argumento.

## 8. Verde, y la huella intacta

```bash
git add frontend/tests frontend/vite.config.ts
git ls-files -s -- frontend/tests frontend/vite.config.ts | diff - .claude/tmp/congelados-front.txt
python tasks.py front-test
python tasks.py front-lint
```

Si el `diff` devuelve algo, los tests se tocaron y ese verde no vale.

## 9. Comprobar a ojo

En el navegador: los tres estados (cargando, sin datos, con error), el
formulario con un campo invalido, y la pantalla a ancho de telefono. El
Admin va a cargar cobros desde la computadora del club, pero el
Profesor toma asistencia desde el telefono.

## 10. Cierre

Con la skill `/commit`.

## Lo que esta skill no hace

- No invoca al revisor adversarial: va una vez por change.
- No verifica ni archiva el change.
- No toca el backend.

## Alcance diferido

Storybook, regresion visual y comprobaciones automaticas de
accesibilidad llegan cuando el catalogo propio de `components/` tenga
piezas, no antes. Fundar esa infraestructura por adelantado, sobre un
catalogo que todavia no existe, suele salir mal.
