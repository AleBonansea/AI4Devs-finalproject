# Proposal

## Why

**Change técnico, sin historia de usuario.** Es el change 2 del «Plan de changes del lote 1» (`docs/product/historias-backlog.md`). Desbloquea los changes 3 a 7:
- **3, `pantalla-de-ingreso`:** necesita usuarios con los que entrar.
- **4, `familias-y-alumnos`:** necesita grupos donde inscribir.
- **5, `asistencia`:** necesita grupos con profesores asignados.
- **6, `cobro`:** necesita tarifa base, descuentos, períodos y tipos de cargo para calcular un cargo.
- **7, `cuenta-corriente`:** se apoya en el 6.

En el lote 1 esos datos no se cargan desde la aplicación. El ABM de usuarios, grupos y tarifario es el lote 2 (HU-UT-02, HU-GA-01, HU-GA-02, HU-TAR-01 a HU-TAR-03). Mientras tanto los aporta `python tasks.py seed`.

Hoy la base solo tiene `temporada` y `usuario`, y `scripts/seed.py`, al que ya apunta `tasks.py`, no existe.

## What Changes

**Siete tablas nuevas**, tal como las define `3-modelo-de-datos.md`, con sus restricciones:
- **Grupos:** `grupo` y `grupo_profesor`.
- **Tarifario:** `tarifa_base`, `descuento_modalidad`, `descuento_mes`, `periodo_cobro` y `tipo_cargo`.

**Cuatro tipos enumerados nuevos:** `turno`, `modalidad`, `categoria_familia` y `calculo_cargo`.
- `categoria_familia` entra ahora porque la usan los descuentos.
- La tabla `familia` llega con el change 4.

**Una migración reversible** que crea las siete tablas y los cuatro tipos, y los borra en el `downgrade`.

**La semilla:** `python tasks.py seed` carga en una base vacía una temporada 2026-27 completa con datos inventados:
- Usuarios de los tres roles, que pueden ingresar con `POST /api/v1/auth/login` sin cambio de contraseña pendiente.
- Grupos de mañana y de tarde, con profesores asignados.
- Las 8 tarifas base.
- La tabla de descuentos completa con la política 2026-27 de Acl. 5.
- Los períodos de cobro.
- Los tipos de cargo Preinscripción y Abono.

**Límites de la semilla:**
- Si la base ya tiene datos, no hace nada y termina con error. Así no se puede pisar ni mezclar con una base en uso.

## Fuera de alcance

- **Endpoints:** no hay ninguno. Ni ABM de grupos ni de tarifario: eso es el lote 2. Por eso no hay roles que declarar ni filtro de Profesor.
- **`inscripcion` y `asistencia`:** son del bloque de grupos, pero las crean los changes 4 y 5, que son los primeros que las usan.
- **`familia`, `alumno`, `persona` y `familia_persona`:** son del change 4, que además extiende la semilla con familias y alumnos de ejemplo.
- **`cargo`, `pago` y `tesoreria_movimiento`:** son de los changes 6 y 7.
- **El cálculo del cargo** (`app/services/calculo_cargo.py`): es del change 6. Este change guarda los porcentajes y no aplica ninguno.
- **La puesta en marcha real** (el primer Admin y la primera temporada en producción): es una tarea de instalación aparte (modelo de datos, «Puesta en marcha»). La semilla no la reemplaza y no se ejecuta en producción.
- **Abrir una temporada nueva copiando los grupos** (HU-UT-04): está en el Backlog.
- **La validación del rol de un profesor asignado a un grupo:** el modelo de datos la pone en la API, y la API de asignación es HU-GA-02. La semilla asigna solo usuarios con rol profesor.

## Capabilities

### New Capabilities

- `grupos`: los grupos de cada temporada y la asignación de profesores. En este change entran las restricciones de los datos. El ABM (HU-GA-01, HU-GA-02) se suma a esta misma capability en el lote 2.
- `tarifario`: tarifa base, descuentos por modalidad y por tramo de hijos, períodos de cobro y tipos de cargo de cada temporada. En este change entran las restricciones de los datos. La carga desde la aplicación (HU-TAR-01 a HU-TAR-03) se suma en el lote 2.
- `semilla`: qué carga `python tasks.py seed`, con qué valores y cuándo se niega a correr.

### Modified Capabilities

Ninguna. La capability `auth` no cambia: la semilla crea usuarios que el login existente ya sabe atender.

## Impact

- **Código nuevo:**
  - `app/models/grupo.py`, `app/models/tarifario.py` y los tipos enumerados compartidos, todos registrados en `app/models/__init__.py`;
  - una migración en `backend/alembic/versions/`;
  - la lógica de la semilla dentro del paquete `app`, para poder probarla;
  - `scripts/seed.py`, que solo la invoca.
- **API:** sin rutas nuevas. `docs/api/openapi.json` no debería cambiar, y se comprueba con `python tasks.py openapi-check`.
- **Dependencias de paquetes:** ninguna nueva.
- **Datos:** la migración solo agrega. `temporada` y `usuario` no se tocan.
- **Lo que este change fija para los que siguen:**
  - la FK compuesta de `inscripcion` apunta a `grupo (id, temporada_id, turno)`, que este change declara único;
  - la de `cargo` apunta a `periodo_cobro (id, modalidad)`.
