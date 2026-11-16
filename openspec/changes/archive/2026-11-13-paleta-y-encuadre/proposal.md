# Proposal

Change **técnico, sin historia**. No agrega funciones: alinea la interfaz que ya existe con el prototipo que validó el cliente (`docs/previews/`), antes de que el change 5 (`asistencia`, HU-GA-04) sume pantallas sobre una paleta equivocada. Lo desbloquea: cada pantalla nueva hereda el tema, y corregirlo después significa revisar más pantallas.

## Why

El tema actual (`frontend/src/tema.ts`) usa el verde de la marca como color de acción y grises cálidos. En el prototipo validado, el verde es **solo el logotipo**: los botones, el ítem activo y los enlaces son azules, el naranja es el dinero, y los grises son fríos. Además, la pantalla de ingreso es una tarjeta sin identidad, cuando en el prototipo lleva el logo, el nombre de la escuela y un subtítulo.

## What Changes

- **Paleta del prototipo en `tema.ts`**. Los valores salen de muestrear `docs/previews/01-inicio.png` y `00-ingreso.png`. `palette.primary` pasa a ser el color de acción (azul `#1870b0`), no la marca. La marca (`#108038`) queda para el logotipo y el título de las pantallas sin sesión, nunca para un botón. El naranja `#d85018` es el dinero: el saldo a cobrar y la acción de cobrar. Los grises pasan a ser fríos.
- **`deuda` se unifica con el naranja del dinero**, como en el prototipo. El rojo deja de ser `deuda` y pasa a llamarse `error`, solo para fallos (errores de la API y de validación). Ver design.md, decisión 2.
- **Encuadre de las pantallas sin sesión**, como pieza propia en `src/components/`: el logo de la escuela, título `Escuela de Verano` en el color de marca, subtítulo `Centro Médico · Administración de la temporada`, y debajo el contenido de cada pantalla. Lo usan el ingreso y el aviso de cambio de contraseña pendiente.
- **El nombre de la aplicación es «Escuela de Verano»**, decidido por el usuario al aplicar. «Escuelita de Verano» se reemplaza en el inicio y en el `<title>` de `frontend/index.html`, para que no se vea un nombre antes de ingresar y otro después. La spec del inicio no fija el nombre, así que esto no cambia ningún Requirement.
- **Logo** servido como `/logo.png` desde `frontend/public/logo.png`. Lo provee el usuario y entra al repo con este change.
- **Captura del ingreso** (`docs/previews/00-ingreso.png`, exportada del prototipo por el usuario, entra al repo con este change) referenciada en `1-descripcion-general-del-producto.md`, en la sección 1.3, junto a las otras capturas.

### Fuera de este change

- **El andamiaje del prototipo**: el recuadro «Prototipo. Entrá con cualquiera de los tres roles» y los botones «Entrar como Administrador / Coordinadora / Profesor». El sistema tiene un solo botón `Ingresar` y el rol sale del usuario.
- **La temporada en el subtítulo** (`2026-27` en el prototipo): la pantalla de ingreso es anterior al login y no puede consultar la temporada vigente.
- **El usuario de ejemplo `diego.ruiz`**: no se agrega un placeholder. El formato real del usuario es la inicial del nombre más el apellido, sin punto (`jperez`).
- **Cambios de color en pantallas**: no se toca ninguna pantalla por color. Si alguna se ve mal con el tema nuevo, el defecto es un valor fuera del tema y se arregla ahí, dentro de este change.
- **Encabezado y menú de la zona protegida** (la barra con logo y el menú lateral del tablero): son de los changes que construyan esas pantallas.
- El comportamiento del ingreso (validación, envío, errores, sesión) no cambia.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `auth`: se agregan dos Requirements de interfaz, el encabezado de las pantallas sin sesión y el botón único de ingreso.
  - Se modifica «Aviso de cambio de contraseña pendiente»: decía «solo un aviso» y ahora el aviso va debajo del encabezado. Sin ese cambio, la spec archivada se contradecía (pase adversarial, hallazgo 3).
  - Sus Scenarios no cambian.
  - La pantalla de ingreso no cambia.

## Impact

- `frontend/src/tema.ts`: catálogo de colores y mapeo a la paleta de MUI.
- `frontend/src/components/`: componente nuevo, el encuadre de las pantallas sin sesión.
- `frontend/src/pages/Ingreso.tsx` y `frontend/src/pages/CambioPendiente.tsx`: pasan a usar el encuadre.
- `frontend/public/logo.png`: asset nuevo, servido por Vite.
- `frontend/tests/auth/`: tests nuevos para los dos Requirements.
- `1-descripcion-general-del-producto.md`: referencia a `docs/previews/00-ingreso.png`.
- Sin cambios en la API, en el esquema ni en `docs/api/openapi.json`.
