# Design

## Context

El frontend está en el andamiaje: `src/main.tsx` monta el tema de MUI y un `App.tsx` de bienvenida, `src/components/` está vacía y no hay router en uso, aunque `react-router-dom` 7.1.1 ya figura en las dependencias. `src/lib/api.ts` ya guarda, lee y borra el token en `localStorage`, adjunta `Authorization: Bearer`, borra el token ante cualquier 401 y traduce los errores de FastAPI a un `ErrorDeApi` con `estado`, `message` y `porCampo`. No hay ningún test ni dependencia de tests.

Del lado de la API, todo está en `openspec/specs/auth/spec.md`: el login devuelve `access_token` y `usuario` (con `debe_cambiar_password`), y `GET /api/v1/auth/yo` devuelve el mismo `usuario` aunque el cambio esté pendiente, que es justamente lo que el frontend necesita al recargar. El token dura 480 minutos (`access_token_expire_minutes`) y no se renueva.

`package.json` fija versiones exactas y usa React 18.3.1. El «React 19» que nombra CLAUDE.md en «Versiones» no coincide con lo instalado. Este change no lo cambia: sigue con 18.3.1.

## Goals / Non-Goals

**Goals:**
- Un montaje de tests de frontend que los changes 4 a 7 reutilicen sin tocarlo: mismo lugar, mismo arranque, misma forma de fingir la API.
- La sesión resuelta en un solo lugar, para que las pantallas siguientes la lean y no la vuelvan a resolver.

**Non-Goals:**
- Un cliente generado desde `openapi.json`. Los dos tipos de respuesta se escriben a mano en `api.ts`.
- Piezas propias en `components/`. Ver «Composición con MUI».

## Decisions

### Vitest con jsdom y Testing Library

- **Vitest 3.x**, porque es la versión que soporta Vite 6, que es la que está instalada. La configuración va en el bloque `test` de `vite.config.ts` (con `defineConfig` de `vitest/config`), con `environment: "jsdom"`. Así los tests resuelven los módulos igual que el build y no hay una segunda configuración que se desincronice.
- **`@testing-library/react`**, **`@testing-library/user-event`** y **`@testing-library/jest-dom`**. Las consultas son por rol y por etiqueta (`getByRole("button", { name: "Ingresar" })`, `getByLabelText("Usuario")`). Es la misma forma en que lo encuentra un lector de pantalla: si el test no encuentra el campo por su etiqueta, la etiqueta no está asociada.
- Versiones **exactas** en `devDependencies`, igual que el resto del `package.json`. Se eligen al instalar, de las ya publicadas hace más de dos semanas.
- Script `"test": "vitest run"` en `package.json` y tarea `python tasks.py front-test`, que lo corre en `frontend/`. El job `frontend` del CI la agrega después de `front-lint`.
- Alternativa descartada: **Jest**. Necesita su propio transformador de TypeScript y su propia resolución de módulos, que es la configuración duplicada que Vitest evita.

### Dónde viven los tests

En `frontend/tests/<capability>/`, que acá es `frontend/tests/auth/`, con un archivo de preparación en `frontend/tests/preparar.ts`: carga los matchers de jest-dom, limpia `localStorage` y restaura los stubs entre tests. Es la forma de `backend/tests/functional/<capability>/`, y por la misma razón: una carpeta entera se congela con `git ls-files -s`, y si los tests estuvieran desparramados junto a cada componente, la huella tendría que listar archivo por archivo.

`tests` se suma al `include` de `tsconfig.app.json`, así `npm run build` también comprueba los tipos de los tests, y al `prettier --check` de `npm run lint`.

### La API se finge en `fetch`, no en `api.ts`

Los tests reemplazan el `fetch` global con `vi.stubGlobal` y responden con `Response` armadas a mano. No reemplazan las funciones de `api.ts`. Así un test de error por campo pasa de verdad por `traducirError`: si alguien rompe la traducción, la pantalla deja de mostrar el mensaje y el test se entera. Las aserciones sobre la llamada (método, ruta, cuerpo, encabezado `Authorization`) miran los argumentos con que se llamó al stub.

Alternativa descartada: **MSW**. Es una dependencia más, con su propio service worker, para dos endpoints. Se reconsidera si los changes de dominio terminan escribiendo a mano un enrutador de respuestas falsas.

«Recargar la página» se representa dejando el token en `localStorage` y montando la aplicación de cero. Los tests montan `App` dentro de un `MemoryRouter` con la dirección inicial del Scenario, y `main.tsx` monta la misma `App` dentro de un `BrowserRouter`.

### La sesión, en un contexto

`src/lib/sesion.tsx` expone un proveedor y un hook `useSesion()` con el usuario actual y dos acciones:

- `ingresar(respuesta)`: guarda el token con `guardarToken` y deja el `usuario` del login como usuario actual. No vuelve a llamar a `/yo` (spec, «Ingreso correcto guarda la sesión»).
- `salir()`: `borrarToken()` y usuario en nulo. No llama a la API: no hay endpoint de logout.

La sesión vive en `src/lib/` y no en `src/components/` porque no es una pieza de interfaz: es estado compartido, igual que el token en `api.ts`.

`api.ts` suma dos funciones con sus tipos: `ingresar(username, password): Promise<LoginRespuesta>` y `usuarioActual(): Promise<UsuarioActual>`, con los mismos campos que el contrato. Son las únicas llamadas nuevas al backend.

### Rutas

```
/ingresar        Ingreso                 (pública)
<RutaProtegida>
  /              Inicio
  *              redirige a /
```

`src/routes/RutaProtegida.tsx` decide qué se muestra en toda la zona protegida:

1. Sin token guardado → `<Navigate to="/ingresar" replace>`, sin llamar a la API.
2. Con token y sin usuario en el contexto (recarga) → llama a `usuarioActual()` y muestra un `CircularProgress` mientras tanto.
3. Un 401 → `api.ts` ya borró el token. Se limpia la sesión y se manda al ingreso.
4. Otro error → `Alert` con el mensaje y un botón `Reintentar`. Se conserva el token: un corte de red en el club no puede cerrar la sesión del Profesor.
5. Usuario con `debe_cambiar_password` → `src/pages/CambioPendiente.tsx`, en lugar del `<Outlet>`. Así ninguna pantalla futura puede asomar con el cambio pendiente, porque todas pasan por este mismo punto.
6. Si no → `<Outlet>`.

Una dirección desconocida con sesión redirige a `/`. Sin sesión, la atrapa el paso 1 y va a `/ingresar`. Entrar a `/ingresar` con sesión vigente muestra el formulario igual: redirigir de ahí no está pedido.

### La pantalla de ingreso

- La validación local de vacíos corre antes de llamar a la API: `username.trim() === ""` y `password === ""`. La contraseña no se recorta porque la API tampoco la normaliza.
- Contra el doble envío, además del botón deshabilitado, hay un `useRef` que marca el envío en curso. El estado de React se actualiza en el próximo render, y dos clics en el mismo tick pasarían los dos con solo el `disabled`.
- Con un `ErrorDeApi`: si `porCampo` trae `username` o `password`, esos mensajes van al `helperText` de su campo. Si no, `message` va al `Alert` general. Ante el error general se vacía la contraseña y se conserva el usuario.
- `autoComplete="username"` y `autoComplete="current-password"`, para que el gestor de contraseñas del navegador funcione.

### Composición con MUI

El catálogo es MUI. Cada parte sale de un componente:

| Parte | Componente |
|---|---|
| Contenedor centrado del ingreso y del aviso | `Container` + `Paper` + `Stack` |
| Campos | `TextField` (con `error` y `helperText` para el error por campo) |
| Botón con progreso | `Button` deshabilitado con `CircularProgress` en `startIcon`. `Button` con `loading` llega en MUI 6.4 y está instalada la 6.3.0 |
| Error general y error de conexión | `Alert severity="error"` |
| Aviso de cambio pendiente | `Alert severity="warning"` con `AlertTitle` |
| Carga de la sesión | `CircularProgress` |
| Nombre y rol del inicio | `Typography` |

No se extrae nada a `components/`. El contenedor centrado aparece en dos pantallas del mismo change, pero son dos usos de una composición de tres componentes de MUI y no hay todavía una tercera pantalla que confirme la forma. Si el change 4 lo repite, ahí se decide extraerlo.

### Mensajes en castellano con tildes

Los mensajes de respaldo de `traducirError` y el de conexión están hoy sin tildes (`Revisa tu conexion`). Como la spec los cita textuales, se corrigen en `api.ts` a `Revisá tu conexión.`, `Intentá de nuevo.`, `Tu sesión venció. Volvé a ingresar.`, `No tenés permiso para hacer esto.`, `Revisá los datos ingresados.` y `Valor inválido`. Es el único cambio a lo que `api.ts` ya hacía.

### El rol, escrito para personas

`admin` → `Admin`, `coordinador` → `Coordinador`, `profesor` → `Profesor`. Es un mapa en la pantalla de inicio, porque es el único lugar que lo muestra. Si otra pantalla lo necesita, se mueve.

## Risks / Trade-offs

- [Token en `localStorage`, legible por cualquier script de la página] → Un XSS se lo lleva. Es lo que `api.ts` ya hacía y lo que permite la API sin cookie. La cookie httpOnly del documento técnico espera al dominio propio. Mitiga que React escapa el contenido y que no hay HTML de terceros.
- [Salir no revoca el token] → Quien copió el token lo puede usar hasta que venza (8 horas). La API no tiene revocación. Desactivar o bloquear al usuario sí corta la sesión al instante, porque la API relee el usuario en cada petición.
- [Los 422 de Pydantic llegan en inglés (`String should have at most 128 characters`)] → Se muestran como llegan. En la práctica el formulario solo ve un 422 con caracteres de control o texto de más de 60 o 128 caracteres, porque los vacíos los corta la validación local. Traducirlos es trabajo de backend y queda fuera.
- [El aviso de cambio pendiente deja al usuario sin salida en el sistema] → Es lo que pide HU-UT-01 mientras HU-UT-06 sea del lote 2. En el lote 1 los usuarios salen de la semilla, y la semilla los deja sin el cambio pendiente.
- [Los tests fingen `fetch` y no prueban la integración con la API real] → Las formas de las respuestas falsas se copian del contrato y de la spec de `auth`. La prueba contra la API real es la comprobación a mano de la última tarea, con la semilla cargada. Los tests E2E quedan fuera.

## Migration Plan

No hay migración ni datos. Se despliega como cualquier build del sitio estático, y volver atrás es volver al build anterior: el backend no cambia.

## Open Questions

Ninguna que cambie la spec o las tareas.
