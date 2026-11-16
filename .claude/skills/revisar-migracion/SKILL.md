---
name: revisar-migracion
description: Revisa a mano una migracion de Alembic generada con autogenerate antes de aplicarla. Usala cada vez que se genere una migracion.
---

# Revisar una migracion

`--autogenerate` compara modelos contra base y escribe lo que cree que
falta. Se equivoca de forma predecible, y el error no se ve hasta que ya
borro algo.

## 1. Leer el archivo entero

Abri `backend/alembic/versions/<nueva>.py` y lee `upgrade()` y
`downgrade()` completos. No alcanza con mirar el nombre.

## 2. Lo que autogenerate hace mal

- **Renombrar una columna lo ve como borrar una y crear otra.** El
  resultado es que los datos de esa columna se pierden. Si fue un
  renombre, reescribi la operacion como `op.alter_column(...,
  new_column_name=...)`.
- **Renombrar una tabla, lo mismo.** Usa `op.rename_table`.
- **Los tipos enumerados de Postgres no se crean ni se borran solos.**
  Si aparece un enum nuevo, agregá su creacion en `upgrade()` y su
  `DROP TYPE` en `downgrade()` a mano.
- **Los indices y las restricciones con nombre por defecto** salen con
  nombres distintos segun el entorno. Poneles nombre explicito.
- **Una columna nueva `NOT NULL` sobre una tabla con filas falla.** Van
  tres pasos: agregarla nullable, rellenarla con un `UPDATE` dentro de
  la migracion, y recien ahi ponerle `NOT NULL`.
- **Los cambios de precision en numeric** pueden truncar importes en
  silencio. Si toca una columna de dinero, mirala dos veces.

## 3. El reverso tiene que existir y funcionar

`downgrade()` vacio o con `pass` no vale. Si no se puede revertir, la
migracion esta mal planteada.

## 4. Probarla en los dos sentidos

```bash
cd backend
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

Contra la base de pruebas, nunca contra una con datos reales.

## 5. Si borra datos

Si la migracion tira una columna o una tabla que tiene datos, **pará y
preguntá**. En este sistema no se borra nada: lo que ya no se usa se
deja de leer, no se elimina.
