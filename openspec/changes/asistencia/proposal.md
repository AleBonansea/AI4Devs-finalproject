# Proposal

## Why

Es el change 5 del «Plan de changes del lote 1» y cubre una historia del Lote 1: **HU-GA-04** (tomar asistencia por grupo, día y turno, desde el celular o la PC). El change 4 dejó alumnos inscriptos en grupos, pero no hay dónde registrar quién vino: hoy se lleva en papel. Es la segunda de las tres historias que la Entrega 1 documentó con criterios Dado / Cuando / Entonces (HU-AF-01, HU-GA-04, HU-CC-01) y, sin ella, una queda documentada y sin construir.

La asistencia es **solo control**: no interviene en el cobro ni dispara avisos (Acl. 5; PRD «Grupos, turnos y asistencia»).

## What Changes

- **Esquema de asistencia.** La tabla `asistencia` del modelo de datos: un registro por inscripción y fecha (`UNIQUE (inscripcion_id, fecha)`), con quién la tomó o corrigió por última vez y cuándo. Una migración reversible.
- **Abrir la asistencia de un grupo en un día** (`GET /api/v1/grupos/{grupo_id}/asistencias/{fecha}`): la lista de los alumnos inscriptos en ese grupo, con lo registrado para esa fecha (presente, ausente o sin tomar). Sirve también para un grupo de una temporada cerrada, que queda para consulta. Es el endpoint que la Entrega 1 dejó afuera por el límite de 3 endpoints, y es el que cubre el escenario 4 (grupo sin alumnos).
- **Guardar la asistencia** (`PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}`): crea o corrige un registro por inscripción y fecha, sin duplicar. Las inscripciones que no vienen en el pedido no se tocan. Rechaza fechas fuera de la temporada, inscripciones de otro grupo o repetidas, y grupos de una temporada cerrada.
- **Permisos:** Admin y Coordinador en cualquier grupo, aunque no tengan grupos asignados; el Profesor solo en los suyos, y sobre un grupo ajeno recibe 403 exista o no, como en el alta de alumnos.
- **Grupo inactivo: no se toma asistencia nueva.** **[SUPUESTO]**, registrado como pregunta abierta en `aclaraciones-cliente.md`: el modelo dice que un grupo inactivo conserva su asistencia, pero no si se le puede tomar una nueva. Hoy no hay forma de desactivar un grupo (llega con HU-GA-01), así que el caso solo se alcanza por la base.
- **Pantalla «Tomar asistencia»** en `/asistencia`, pensada primero para el celular: elegir grupo (los de `GET /api/v1/grupos`, que ya filtra los del Profesor) y fecha (hoy por defecto), marcar a cada alumno como presente o ausente, y guardar. Con un acceso desde el inicio.

## Capabilities

### New Capabilities

- `asistencia`: la presencia de cada alumno inscripto por día y turno, la apertura y el guardado de la asistencia de un grupo en una fecha, sus permisos por grupo, y la pantalla que los usa.

### Modified Capabilities

- `auth`: el inicio de la zona protegida suma el acceso `Tomar asistencia`, que lleva a `/asistencia`.

## Fuera de alcance

- **Consultar la asistencia acumulada** de un grupo o de un alumno a lo largo de varios días (HU-GA-05, Should-have). Este change abre un solo día por vez.
- **Mostrar la asistencia en la pantalla de cobro.** Acl. 5 lo descarta: la asistencia no se muestra al cobrar.
- **Cualquier efecto sobre cargos, saldos o avisos a los padres** (Acl. 5). No hay notificaciones de ningún tipo.
- **Restringir días**: no se bloquean fines de semana, feriados ni fechas futuras. La única regla de fecha es la del modelo de datos: dentro de la temporada del grupo.
- **Borrar un registro de asistencia** o volver un alumno a «sin tomar». Corregir es cambiar presente por ausente o al revés; nada se borra.
- **Marcar a todos de una vez**, observaciones por alumno, tardanzas o retiros anticipados. Solo presente o ausente.
- **Funcionar sin conexión** desde el celular. Si no hay red, el guardado falla y se informa.
- **Datos médicos en la lista.** La lista de asistencia trae nombre y apellido, nada más, aunque el Profesor tenga permiso de verlos en sus grupos.
- **Asistencia de ejemplo en la semilla.** La semilla no cambia.

## Impact

- **Backend:** modelo `Asistencia` en `app/models/`, una migración en `alembic/versions/`, esquemas en `app/schemas/asistencias.py`, servicio en `app/services/asistencias.py` y las dos rutas en un router `asistencias.py` de `app/api/v1/`.
- **Contrato:** dos endpoints nuevos; `docs/api/openapi.json` regenerado. Ningún endpoint existente cambia.
- **Frontend:** llamadas y tipos nuevos en `src/lib/api.ts`, la página `src/pages/TomarAsistencia.tsx`, las piezas que haga falta en `src/components/`, la ruta en `App.tsx` y el acceso en `Inicio.tsx`.
- **Documentación:** la pregunta abierta del grupo inactivo en `docs/prd/aclaraciones-cliente.md`.
