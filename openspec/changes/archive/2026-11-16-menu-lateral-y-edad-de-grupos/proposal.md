# Proposal

## Why

Hoy toda la navegación pasa por el inicio: para ir de «Registrar alumno» a «Tomar asistencia» hay que volver a `/` y elegir otro botón. Los selectores de grupo muestran solo nombre y turno, así que quien inscribe tiene que acordarse de qué rango de nacimiento cubre cada grupo. Las dos cosas salieron de la revisión de la Entrega 2 con el usuario (16/11/2026).

Historias: **HU-UT-09** (menú lateral permanente según el rol) y **HU-GA-06** (la edad que cubre cada grupo en el selector), las dos del **Lote 3**. Es el primer change del lote 3; el backlog todavía no tiene un «Plan de changes» para ese lote, y este change no depende de los otros dos (HU-AF-11, HU-CC-07).

## What Changes

- **Marco de la zona protegida.** Todas las pantallas con sesión pasan a tener un encabezado (nombre de la aplicación, usuario, rol y `Salir`) y un menú lateral permanente. En pantallas angostas el menú pasa a ser una fila desplazable debajo del encabezado, como en el prototipo (`09-mobile-inicio.png`).
- **El menú muestra solo lo que existe hoy**, filtrado por rol:
  - Escuela: `Inicio`, `Registrar alumno`, `Tomar asistencia`.
  - Administración, solo el Admin: `Registrar cargo`, `Cuenta corriente`.
  - La opción de la pantalla abierta queda marcada.
- **El inicio deja de tener los botones de acceso**, porque ahora están en el menú. Muestra un saludo con el nombre del usuario. El nombre, el rol y `Salir` siguen visibles, pero en el encabezado.
- **`GET /api/v1/grupos` suma `edad_desde` y `edad_hasta`** a cada grupo. Son años enteros calculados contra el primer año del nombre de la temporada vigente. No se guardan: se calculan en cada consulta.
- **Los dos selectores de grupo** (`Registrar alumno` y `Tomar asistencia`) escriben cada opción como `Delfines · Mañana · 5 a 6 años`, y en el alta siguen agregando `(sugerido)` al final.
- **El nombre de la temporada pasa a tener un formato fijo, `AAAA-AA`**, con una restricción en la base. El cálculo de la edad lee el primer año del nombre, así que el formato tiene que estar garantizado.

### Fuera de este change

- **El tablero del inicio** (indicadores, asistencia de hoy, documentación pendiente, familias con saldo): necesita HU-DOC-02, HU-CC-04 y un listado de grupos, que no existen.
- **Las opciones del menú del prototipo sin pantalla** (`Alumnos`, `Grupos y asistencia` como listado, `Profesores`, `Tesorería`, `Canon al club`, `Tarifario`, `Reportes`): se suman al menú en el change que construya cada pantalla.
- **El nombre de la temporada en el encabezado** («Centro Médico · Temporada 2026-27»): no hay endpoint que lo devuelva y ninguna historia lo pide.
- **El selector «Ver como»** del prototipo: es una herramienta del prototipo, no del sistema.
- **La edad del alumno** al cargar la fecha de nacimiento: se pidió la edad del grupo, no la del chico.
- **Cambiar cómo se sugiere el grupo**: la sugerencia sigue siendo por fecha exacta dentro del rango. La edad es solo una ayuda visual.

## Capabilities

### New Capabilities
- `navegacion`: el marco de la zona protegida (encabezado y menú lateral), qué opciones ve cada rol y cómo se marca la pantalla abierta. Lo van a ampliar los changes que sumen pantallas.
- `temporadas`: nace con el formato del nombre de la temporada (`AAAA-AA`). Hoy no hay spec de temporadas; la va a ampliar la apertura de temporadas (HU-UT-04).

### Modified Capabilities
- `auth`: el requisito «Inicio de la zona protegida» cambia de contenido. Los accesos pasan al menú y el inicio queda con el saludo.
- `grupos`: «Grupos donde se puede inscribir» suma `edad_desde` y `edad_hasta`, y se agrega el requisito «Edad que cubre el grupo».
- `alumnos`: «Grupos en la pantalla» cambia el texto de cada opción.
- `asistencia`: «Pantalla «Tomar asistencia»» cambia el texto de cada opción.

## Impact

- **Backend**:
  - `app/schemas/grupos.py`: `GrupoParaInscribir` suma dos campos.
  - `app/services/grupos.py`: la consulta suma el nombre de la temporada, y una función pura nueva calcula la edad.
  - `app/models/temporada.py`: restricción del formato del nombre.
  - Una migración nueva.
  - `docs/api/openapi.json` regenerado.
- **Frontend**:
  - Componentes nuevos en `src/components/` para el marco y el menú.
  - `App.tsx`: una ruta de diseño dentro de `RutaProtegida`.
  - `pages/Inicio.tsx`.
  - `components/SelectorGrupo.tsx` y `SelectorGrupoDeAsistencia.tsx`.
  - Una función compartida para el texto del grupo.
  - `lib/api.ts`: el tipo `GrupoParaInscribir`.
- **Tests**: los existentes que comparan el texto `Delfines · Mañana` de los selectores, o que pulsan los botones del inicio, se reescriben contra la spec nueva.
- **Sin cambios** en dinero, permisos de la API ni datos de alumnos.
