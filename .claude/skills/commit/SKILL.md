---
name: commit
description: Cierra una peticion con un commit limpio en la rama correcta. Usala al terminar cada peticion.
---

# Commit

## 1. La rama

```bash
git branch --show-current
```

- Si ya estas en una rama de trabajo (`feat/*`), seguí ahi.
- Si estas en `main` o en una rama de entrega (`feature/entrega-*`),
  **no commitees**: crea la rama de trabajo primero.

```bash
git checkout -b feat/<slug>
```

## 2. Mirar lo que entra

```bash
git status
git diff
git diff --staged
```

Leelo. Si aparece algo que no corresponde a la peticion, sacalo del
commit. Un commit que arrastra cosas de paso es un commit que despues no
se puede revertir solo.

**Nunca entran:** `.env`, credenciales, volcados de base, archivos de
`uploads/`, `.claude/tmp/`, archivos de scratch.

## 3. Comprobaciones

Si se toco backend:

```bash
make test && make lint && make typecheck
```

Si se tocaron rutas, esquemas o modelos, `docs/api/openapi.json`
regenerado y dentro del commit.

Si se toco frontend:

```bash
cd frontend && npm run lint && npm run build
```

En rojo no se commitea.

## 4. El mensaje

En castellano, en imperativo, una linea de hasta 72 caracteres con
prefijo:

```
feat: registrar el cobro de un abono mensual
fix: contar los hermanos por turno en el calculo del tramo
docs: actualizar el contrato de la API
test: cubrir el borde del tramo de 4 o mas hijos
chore: ajustar la configuracion de ruff
```

Si hace falta explicar **por que**, va un parrafo despues de una linea
en blanco. El que no hace falta: el diff ya dice que cambio.

No pongas en el mensaje lo que no esta en el commit.
