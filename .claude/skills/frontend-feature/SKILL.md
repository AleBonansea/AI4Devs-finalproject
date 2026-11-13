---
name: frontend-feature
description: Construye una pantalla del frontend contra la API ya existente, con catalogo primero. Usala para cualquier trabajo de interfaz, aunque nadie la nombre.
---

# Pantalla del frontend

## 1. El contrato manda

Lee `docs/api/openapi.json` para los endpoints que la pantalla usa. Lo
que la API devuelve es lo que la pantalla muestra: no inventes campos
ni supongas formas.

Si la pantalla necesita algo que la API no da, **pará**. Eso es una
historia de backend, no un arreglo en el componente.

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
componentes nuevos hacen falta, y como se comporta en carga, vacio y
error. Presentalo y esperá el visto bueno.

## 4. Construir — subagente `ui-implementer`

Invocalo con el plan aprobado y la lista del catalogo.

## 5. Comprobar

```bash
cd frontend && npm run lint && npm run build
```

Y despues, a ojo, en el navegador: los tres estados (cargando, sin
datos, con error), el formulario con un campo invalido, y la pantalla a
ancho de telefono. El Admin va a cargar cobros desde la computadora del
club, pero el Profesor toma asistencia desde el telefono.

## 6. Cierre

Con la skill `/commit`.

## Alcance diferido

Storybook, regresion visual y comprobaciones automaticas de
accesibilidad llegan cuando el catalogo propio de `components/` tenga
piezas, no antes. Fundar esa infraestructura por adelantado, sobre un
catalogo que todavia no existe, suele salir mal.
