# Proposal

## Why

**Change técnico, sin historia del backlog.** No agrega comportamiento: prueba en un navegador real tres recorridos que ya están especificados en `auth`, `navegacion`, `alumnos`, `cargos`, `pagos` y `cuenta-corriente`. No está en el «Plan de changes del lote 1» porque el lote ya se cerró; se suma como fila técnica, igual que `paleta-y-encuadre`.

**Revierte una decisión registrada.** `2-arquitectura-del-sistema.md`, sección 2.6, dice: «Sin tests de punta a punta en el navegador. Las pantallas se prueban contra una API simulada y la API contra la base real; el recorrido completo en un navegador real se verifica a mano». Esa decisión era razonable mientras cada change se demostraba en local con `vite dev` y su proxy. Hoy deja tres huecos que ninguna de las dos suites puede ver:

1. **La costura entre frontend y API no la prueba nadie.** Los 148 tests del frontend fingen `fetch` con respuestas copiadas a mano del contrato. Si una forma real se separa de la fingida (un campo renombrado, un monto como número en lugar de texto, un 401 con otro cuerpo), las dos suites siguen en verde y la pantalla se rompe.
2. **La configuración de producción no se ejecuta nunca antes de producción.** En Render el frontend es un build estático en un origen y la API está en otro, con `VITE_API_URL` y CORS. En desarrollo todo pasa por el proxy de Vite, en el mismo origen. La Entrega 3 lleva el sistema a Render: lo primero que se rompería es justamente lo que ninguna prueba ejercita.
3. **La verificación a mano no se repite.** Se hizo al cerrar cada change, pero no corre en cada pull request: un cambio en `lib/api.ts` o en una ruta protegida puede romper el cobro sin que nadie vuelva a recorrerlo.

La decisión no se revierte entera. Se eligen **tres recorridos** —el que mueve dinero, el que protege lo contable y el que corta la sesión— porque son los de mayor costo si se rompen y los que más dependen de la costura. El resto sigue cubierto por las suites de pantalla y de API, y la recorrida a mano en celular sigue siendo la que valida lo visual. Tres tests mantienen acotado lo que los E2E cuestan: tiempo de CI, fragilidad y mantenimiento.

**Qué desbloquea:** el despliegue de la Entrega 3 llega con la configuración de origen cruzado ya probada, y los changes del lote 2 que toquen la sesión (HU-UT-06 a HU-UT-08) o el cobro tienen una red que los atrapa en el pull request.

## What Changes

- **Carpeta `e2e/` en la raíz**, con su propio `package.json` y Playwright, separada de `frontend/` para no mezclar sus dependencias ni su configuración de Vitest. Tres tests:
  1. **Camino de la plata:** el Admin ingresa, da de alta un alumno con familia nueva, le registra un cargo, le registra un pago por el saldo completo y la cuenta corriente de la familia queda en `$ 0`, con el cargo `Saldado`.
  2. **Permisos:** un Profesor ingresa, no ve `Cuenta corriente` en el menú, al abrir `/cuenta-corriente` es llevado a `/`, y la API le responde 403 si pide la cuenta corriente directo.
  3. **Sesión:** con un token inválido guardado en el navegador, abrir una pantalla protegida lleva a `/ingresar` y el token queda borrado.
- **Base propia `escuelita_e2e`**, recreada, migrada y sembrada en cada corrida. Nunca la de desarrollo ni la de los tests del backend.
- **`python tasks.py e2e`**: una sola orden que prepara la base, compila el frontend como en producción, levanta la API y el build servido, corre Playwright y baja todo.
- **Reglas de la suite:** un worker, cero reintentos, sin esperas fijas, trace `retain-on-failure`.
- **Un job `e2e` nuevo en `.github/workflows/ci.yml`**, con Postgres, la API y el build servido; sube el trace y el reporte cuando falla.
- **Documentación:** `2-arquitectura-del-sistema.md` (la decisión revertida y el nivel nuevo en la tabla de 2.6), la tabla de comandos de `CLAUDE.md`, `readme.md` y la fila del change en el «Plan de changes» del backlog.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna. Los recorridos ya están especificados; los tests E2E comprueban Scenarios existentes, no agregan Requirements. El change declara `skip_specs: true`.

Scenarios que los tests recorren, sin cambiarlos:

- `auth`: «Pantalla de ingreso», «Ingreso correcto guarda la sesión», «La zona protegida exige sesión», «Sesión rechazada por la API» (Scenario «Token vencido o inválido»).
- `navegacion`: «Opciones del menú según el rol» (Scenario «Menú del Profesor»).
- `alumnos`: «Pantalla "Registrar alumno"», «Grupos en la pantalla», «Envío del alta desde la pantalla».
- `cargos`: «Pantalla "Registrar cargo"», «El desglose en la pantalla», «Registrar desde la pantalla».
- `pagos`: «Registrar un pago desde la pantalla», «Enviar el pago desde la pantalla».
- `cuenta-corriente`: «Pantalla "Cuenta corriente"» (Scenario «Cargo saldado») y «Solo el Admin ve la cuenta corriente».

## Fuera de alcance

- **Más recorridos E2E**: asistencia, búsqueda de personas por DNI, rechazos de validación, cargo del Día. Siguen en las suites de pantalla y de API, que los cubren por Scenario. Un E2E nuevo entra solo con un change que lo justifique.
- **Otros navegadores y el celular**: solo Chromium de escritorio. La vista de celular sigue verificándose a mano.
- **Regresión visual, accesibilidad automática y Storybook**: siguen fuera, como dijo `pantalla-de-ingreso`.
- **Correr los E2E contra el despliegue de Render**: corren contra un build local servido, nunca contra un entorno publicado ni su base.
- **Cambios de comportamiento o de código de producción**: si un test E2E falla por un bug real, el arreglo va en su propio change, con su Scenario. Este change no toca `backend/app/` ni `frontend/src/`.
- **Datos reales**: la base `escuelita_e2e` solo tiene la semilla y lo que crean los tests.

## Impact

- **Nuevo:** `e2e/` (`package.json`, `package-lock.json`, `playwright.config.ts`, `tsconfig.json`, `tests/*.spec.ts`).
- **Modificado:** `tasks.py` (tarea `e2e`), `.github/workflows/ci.yml` (job `e2e`), `.gitignore` (los reportes y las trazas de Playwright; el build del E2E va a `frontend/dist/e2e`, ya ignorado).
- **Documentación:** `2-arquitectura-del-sistema.md`, `CLAUDE.md`, `readme.md`, `docs/product/historias-backlog.md`.
- **Sin cambios:** `backend/app/`, `frontend/src/`, el esquema y `docs/api/openapi.json`. No hay migración ni endpoints nuevos.
- **Dependencia nueva:** `@playwright/test` en `e2e/`, con versión fija, y el Chromium que instala Playwright.
- **CI:** un job más, en paralelo con `backend` y `frontend`. Suma tiempo de pared solo si es el más lento.
