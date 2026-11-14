# Design

## Context

- `frontend/src/tema.ts` es el único archivo del frontend donde puede haber un valor de color. El hook `color_con_nombre.py` corta los valores escritos a mano en cualquier otro lado. Hoy en el tema `primary` es `marca` (verde `#1b5e20`), `error` es `deuda` y los grises son cálidos.
- Ninguna pantalla usa `colores.*` directamente: todas pasan por la paleta de MUI (`severity="error"`, `color="text.secondary"`, el `primary` por defecto de `Button`). Por eso, cambiar el mapeo en el tema cambia todas las pantallas sin tocarlas.
- `Ingreso.tsx` y `CambioPendiente.tsx` arman cada una su propio `Container` + `Paper`. `CambioPendiente` se muestra desde `RutaProtegida` cuando `debe_cambiar_password` está en true.
- `frontend/public/logo.png` (512×512, fondo transparente) lo provee el usuario y entra con este change. Se dibuja tal cual, sin el círculo con anillo oscuro y fondo gris que muestra el prototipo (ver tasks.md, 2.3). Vite sirve `public/` en la raíz, así que queda en `/logo.png`.

## Goals / Non-Goals

**Goals:**
- Que el tema tenga los colores del prototipo, nombrados por su función, y que `primary` sea la acción.
- Que el ingreso y el aviso de cambio pendiente compartan un encuadre con la identidad de la escuela.

**Non-Goals:**
- Sumar al tema los colores de piezas que todavía no existen (el fondo de la barra lateral, las fichas de turno mañana/tarde). Entran con la pantalla que los use.
- Un modo oscuro.

## Decisions

### 1. El catálogo de colores

| Nombre | Valor | Para qué | De dónde sale |
|---|---|---|---|
| `accion` | `#1870b0` | botones, ítem activo, enlaces | prototipo |
| `dinero` | `#d85018` | saldo a cobrar, acción de cobrar | prototipo |
| `deuda` | `= dinero` | monto adeudado | decisión 2 |
| `marca` | `#108038` | solo logotipo y título de marca | prototipo |
| `fondo` | `#eef5f9` | fondo de página | prototipo |
| `superficie` | `#ffffff` | tarjetas, campos | prototipo |
| `borde` | `#d5e4ec` | bordes y separadores | prototipo |
| `texto` | `#14303f` | texto principal | muestreado de 01 y 00 |
| `textoTenue` | `#58717f` | etiquetas, subtítulos, texto secundario | muestreado de 01 y 00 |
| `saldado` | `#108038` | estado al día / presente | muestreado de 01 (el chip «presentes») |
| `pendiente` | `#986000` | estado pendiente | prototipo |
| `anulado` | `= textoTenue` | cobro anulado | sin cambio de criterio |
| `error` | `#b3261e` | fallos de la API y de validación | decisión 2 |

`marcaClara` y `acento` se eliminan: nada los usa y el prototipo no los tiene.

`saldado` y `marca` tienen el mismo valor pero son nombres distintos: el día que el estado «al día» cambie de tono, el logotipo no se mueve. Lo mismo vale para `deuda`, que se escribe como referencia a `dinero` y no como el valor repetido: así queda a la vista que son el mismo color por decisión y no por casualidad.

Mapeo a MUI: `primary` → `accion`, `secondary` → `dinero` (la acción de cobrar es un `Button color="secondary"`), `error` → `error`, `success` → `saldado`, `warning` → `pendiente`, `background` → `fondo`/`superficie`, `text` → `texto`/`textoTenue`, `divider` → `borde`. `marca` **no** se mapea a ninguna entrada de la paleta de MUI: así ningún componente puede tomarla por defecto, y el que la use tiene que nombrarla.

**Alternativa descartada:** `primary` → `marca` con un `accion` aparte. Es lo que hay hoy, y es justamente el error: todo `Button` sin `color` sale verde.

### 2. `deuda` en el naranja del dinero, y un rojo aparte para los fallos

El prototipo validado pinta el monto adeudado y el botón «Registrar cobro» con el mismo naranja. Lo mantengo: en este sistema la deuda no es una falla, es dinero que falta cobrar, y el naranja ya significa dinero en toda la interfaz. Un rojo para la deuda se leería como un error del sistema al lado de cada familia con saldo.

El problema real era otro: hoy `palette.error` cuelga de `deuda`. Si `deuda` pasa a ser naranja sin separarlos, los errores de un formulario y los avisos de falla de la API salen naranjas. Por eso nace `error` (rojo, el mismo valor que tenía `deuda`), solo para fallos, y `palette.error` apunta ahí. El prototipo no muestra ningún error, así que este rojo no sale de él: es el valor anterior, que ya contrasta bien sobre blanco.

**Alternativa descartada:** `deuda` en rojo aparte del naranja de la acción. Distingue la deuda de la acción de cobrar, pero contradice lo que validó el cliente y le pone a un dato de negocio normal el color de una alarma.

### 3. El encuadre como componente propio

`src/components/EncuadreSinSesion.tsx` recibe `children` y dibuja, centrado:
- el `Container` angosto;
- un `Paper` con borde (`variant="outlined"`);
- el logo (`<Box component="img" src="/logo.png" alt="Logo de la Escuela de Verano">`, 96 px);
- el título (`Typography component="h1"`, con el color `marca` tomado de `colores.marca`);
- el subtítulo (`Typography` en `text.secondary`);
- debajo, `children`.

`Ingreso` pasa su formulario como `children`; `CambioPendiente` pasa su `Alert` y el botón `Salir`.

Se extrae a `components/` porque ya hay dos pantallas que lo necesitan. Lo pide la regla de CLAUDE.md: una pieza de interfaz nueva sale del catálogo o se crea ahí con nombre propio.

**Alternativa descartada:** un `palette.marca` con *module augmentation* de MUI, para escribir `color="marca"`. Agrega tipos a mantener para un color que usa un solo componente. Importar `colores.marca` es un nombre, no un valor, y el hook lo deja pasar.

### 4. El color se verifica a ojo, no con tests

Un test que compara `palette.primary.main` con `"#1870b0"` repite la constante: pasa siempre y no atrapa nada. La paleta se verifica levantando la app y comparando el ingreso con `00-ingreso.png`, y el resto de las pantallas existentes con la vista anterior, buscando valores fuera del tema. Los tests cubren lo observable desde el DOM: el encabezado y el botón único (delta de `auth`).

## Risks / Trade-offs

- [Una pantalla con un color a mano que el hook no vio] → La revisión visual de la tarea 1 recorre todas las pantallas existentes. Si aparece uno, se lo reemplaza por un nombre del tema, sin tocar el tema.
- [El test de «exactamente un botón» se rompe si el campo de contraseña suma un botón para mostrarla] → Es intencional: ese botón sería un cambio de comportamiento y tiene que pasar por la spec.
- [Contraste de `dinero`] → Medido con la fórmula de WCAG: `dinero` da 4,13:1 contra blanco y 3,75:1 sobre `fondo`. Alcanza para texto grande o en negrita (3:1), que es como lo usa el prototipo (el botón de cobrar y los montos destacados), pero no llega a AA para texto normal (4,5:1). Queda como regla de uso: `dinero` va en negrita o en tamaño grande, nunca en texto corrido. Los demás pasan 4,5:1 contra blanco: `accion` 5,27; `marca` 5,04; `error` 6,54; `pendiente` 5,24; `textoTenue` 5,14; `texto` 13,78. MUI elige texto blanco como `contrastText` en los botones `accion` y `dinero`.
