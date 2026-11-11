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

Recorre `frontend/src/components/` y anota que existe. Despues escribi
el plan de la pantalla **nombrando que componente del catalogo usas
para cada parte**, y cuales faltan.

Una pieza que falta se crea en `components/` con nombre propio, no se
improvisa dentro de la pantalla.

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
