# Proposal

## Why

Es el change 4 del «Plan de changes del lote 1» y cubre cuatro historias del Lote 1: **HU-AF-02** (crear o elegir la familia), **HU-AF-04** (categoría al crear la familia), **HU-AF-03** (personas autorizadas, con al menos un tutor) y **HU-AF-01** (registrar un alumno con grupo y turno). Hoy hay temporada, usuarios, grupos y tarifario, pero no hay a quién inscribir: sin familias ni alumnos no se puede tomar asistencia (change 5) ni registrar un cargo (change 6).

Además salda dos deudas que el change 3 dejó atadas a este, porque acá aparecen el primer formulario con muchos campos y la primera llamada a la API después de `/yo`: los 422 de validación llegan en inglés, y un 401 fuera de `/yo` no cierra la sesión del navegador.

## What Changes

- **Esquema de familias y alumnos.** Las tablas `familia`, `alumno`, `persona`, `familia_persona` e `inscripcion` del modelo de datos, más la etiqueta «Apellido – Hijo mayor» calculada, nunca guardada. Una migración reversible.
- **Alta de alumno** (`POST /api/v1/alumnos`): en una sola operación atómica registra al alumno con sus datos mínimos (Acl. 3), lo inscribe en un grupo de la temporada vigente (el turno sale del grupo) y, según el caso:
  - **familia nueva**: la crea con su categoría y exige al menos un tutor;
  - **familia existente**: la reutiliza sin pedir categoría ni permitir cambiarla, y el alumno queda cubierto por los tutores que ya tiene.
  En los dos casos acepta personas autorizadas a retirar, nuevas o reutilizadas por su id.
- **Búsqueda de familias por apellido** (`GET /api/v1/familias?apellido=`): para elegir la familia de un hijo que no es el primero. Cualquier rol busca en todas las familias y la respuesta trae solo id, etiqueta y categoría.
- **Búsqueda de persona por DNI exacto** (`GET /api/v1/personas?dni=`): para reutilizar a un adulto ya cargado en otra familia. Devuelve solo id, nombre y apellido. **[SUPUESTO]**, registrado como pregunta abierta en `aclaraciones-cliente.md`.
- **Listado de grupos para inscribir** (`GET /api/v1/grupos`): los grupos activos de la temporada vigente (el Profesor recibe solo los suyos), con la marca del grupo sugerido para una fecha de nacimiento (Acl. 4).
- **Errores de validación en castellano**: el 422 conserva su forma, pero cada `msg` llega en castellano.
- **Pantalla «Registrar alumno»** en `/alumnos/nuevo`, con un acceso desde el inicio.
- **Un 401 en cualquier llamada cierra la sesión** del navegador y manda al ingreso.
- **Semilla con familias de ejemplo**, como anunció la propuesta de `tarifario-y-semilla`, para que los changes 5 a 7 tengan con qué demostrarse.

## Capabilities

### New Capabilities

- `familias`: la familia como unidad de facturación (categoría, etiqueta calculada), las personas adultas reutilizables entre familias y su vínculo con cada familia (tutor, autorizado a retirar), y las búsquedas de familia por apellido y de persona por DNI.
- `alumnos`: la ficha mínima del alumno, su inscripción en un grupo y turno de la temporada vigente, el alta que arma todo eso en una operación, y la pantalla que la usa.
- `errores-de-la-api`: la forma y el idioma de los rechazos por validación que emite la API, comunes a todos los endpoints.

### Modified Capabilities

- `grupos`: se agrega el listado de grupos de la temporada vigente, filtrado por profesor, con el grupo sugerido por fecha de nacimiento.
- `auth`: el inicio suma el acceso a «Registrar alumno»; un 401 de cualquier llamada, no solo de `/yo`, cierra la sesión del navegador.
- `semilla`: carga también familias, personas, alumnos e inscripciones de ejemplo.

## Fuera de alcance

- **Gestión posterior de personas autorizadas**: agregar o desvincular autorizados de una familia ya creada. En este change las personas se cargan solo dentro del alta de un alumno.
- **Buscar personas por nombre o apellido.** Solo por DNI exacto; quien no tiene DNI cargado se carga de nuevo como persona nueva.
- **Modificar la categoría de una familia** (HU-AF-05, Backlog).
- **Ficha completa y datos médicos** (HU-AF-06), **consentimiento** (HU-AF-07) y **contactos de emergencia** (HU-AF-08). Las columnas médicas no se crean; la marca de contacto de emergencia se crea apagada, sin forma de encenderla.
- **Inscribir en el segundo turno** a un alumno ya registrado (HU-AF-09) y **reinscribir en otra temporada** (HU-AF-11). El alta crea una sola inscripción.
- **Listado, consulta o edición de alumnos y familias.** No hay pantalla de ficha ni de familia.
- **Detección de alumnos duplicados.** Registrar dos veces al mismo chico crea dos alumnos.
- **Alias manual de familia** (Acl. 1, «a futuro»).
- **Documentación** (bloque HU-DOC). El alta no la pide.
- **Cualquier cálculo de cargo o cuenta corriente.** La «cuenta corriente única» de la familia es su id: no hay tabla ni saldo en este change.

## Impact

- **Backend:** modelos nuevos en `app/models/`, una migración en `alembic/versions/`, esquemas en `app/schemas/`, servicios en `app/services/`, routers nuevos `alumnos`, `familias`, `personas` y `grupos` en `app/api/v1/`, y el manejador de 422 de `app/main.py`.
- **Contrato:** cuatro endpoints nuevos y el `msg` del 422 en castellano; `docs/api/openapi.json` regenerado.
- **Frontend:** llamadas nuevas en `src/lib/api.ts`, el aviso de 401 a `src/lib/sesion.tsx`, la pantalla nueva en `src/pages/`, la ruta en `App.tsx`, el acceso en `Inicio.tsx`, y las primeras piezas de `src/components/`.
- **Semilla:** `scripts/seed.py`.
- **Documentación:** la pregunta abierta de la búsqueda por DNI en `docs/prd/aclaraciones-cliente.md`.
