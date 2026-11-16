# Design

## Context

- **Navegación.** Cada pantalla protegida arma su propio `Container`, y la única navegación son los botones de `pages/Inicio.tsx`, filtrados por rol a mano. `RutaProtegida` decide entre el indicador de carga, el aviso de cambio pendiente (`CambioPendiente`) y el `<Outlet />`. `RutaSoloAdmin` redirige a `/` las pantallas de cobro.
- **Grupos.** `GET /api/v1/grupos` (`app/services/grupos.py`) ya hace el join con `temporada` para filtrar la vigente, así que el nombre de la temporada está a mano en la misma consulta. Los dos selectores del frontend (`SelectorGrupo` y `SelectorGrupoDeAsistencia`) arman cada uno su propio texto: `${nombre} · ${turno}`.
- **Temporada.** `temporada.nombre` es `varchar(20) UNIQUE` sin formato. Todas las filas conocidas (semilla, fixtures de los tests) usan `AAAA-AA`: `2024-25`, `2025-26`, `2026-27`, `2027-28`.

## Goals / Non-Goals

**Goals:**
- Que el texto de la edad sea el que el club usa para cada grupo («5 a 6 años», «7 a 9 años», como el prototipo), igual durante todo el verano y para cualquier usuario.
- Que la edad se calcule en un solo lugar.
- Que la lista de opciones del menú esté en un único lugar, para que el change que sume una pantalla agregue una línea.

**Non-Goals:**
- Tocar la sugerencia de grupo: sigue siendo por fecha exacta, con `BETWEEN`.
- Comportamiento responsive verificable en los tests: el cambio de menú lateral a fila desplazable es CSS y se revisa a ojo.

## Decisions

### 1. Edad en años enteros contra el primer año del nombre de la temporada

`edad_desde = año_ref − año(nacimiento_hasta)` y `edad_hasta = año_ref − año(nacimiento_desde)`, con `año_ref` = los cuatro primeros dígitos del nombre de la temporada vigente. Para «2026-27», `año_ref` es 2026.

**Por qué no a una fecha exacta.** Se evaluó calcular la edad cumplida a una fecha (el inicio de la temporada, o hoy) y se descartó con los números de la semilla:

| Grupo | Rango de nacimiento | Edad cumplida al 2027-01-04 (inicio) | Años enteros, ref. 2026 | Prototipo |
|---|---|---|---|---|
| Delfines | 2020-01-01 a 2021-12-31 | 5 a 7 | **5 a 6** | 5 a 6 |
| Tiburones | 2017-01-01 a 2019-12-31 | 7 a 10 | **7 a 9** | 7 a 9 |

Al 2027-01-04, el más chico de Delfines (nacido el 2021-12-31) tiene 5 y el más grande (2020-01-01) tiene 7. Una ventana de dos años calendario completos abarca tres edades cumplidas en cualquier instante, salvo el 1 de enero. Con edad cumplida el texto dice «5 a 7» para un grupo que el club llama «5 a 6». Además cambia según el día en que se mire: el mismo grupo daría otro texto en enero y en febrero.

Los años enteros dan exactamente lo del prototipo y no dependen de ninguna fecha del calendario: el mismo grupo dice lo mismo todo el verano. Es la convención de las categorías por año de nacimiento («los nacidos en 2020 son de 6»).

**Alternativas descartadas:**
- **`año(fecha_inicio)` como referencia.** Para «2026-27» la temporada arranca el 2027-01-04 y la referencia sería 2027: Delfines daría «6 a 7».
- **`año(fecha_inicio) − 1`.** Acierta solo si la temporada arranca en enero; una que arranque el 15 de diciembre corre todo un año. El usuario fijó la referencia en el nombre, que no tiene esa ambigüedad.

### 2. La edad la calcula la API, no el frontend

El frontend no conoce el nombre de la temporada. Para calcularla ahí habría que mandárselo igual, y la regla quedaría en TypeScript, sin los tests funcionales del backend. `GrupoParaInscribir` suma `edad_desde` y `edad_hasta` (enteros, no nulos). El frontend solo los escribe.

- **Dónde vive el cálculo.** Una función pura en `app/services/grupos.py`: recibe el año de referencia y las dos fechas, y devuelve el par. No toca la base.
- **Quién la llama.** `listar_grupos_para_inscribir` suma `Temporada.nombre` al `select` y la llama por cada fila.
- **Estado derivado.** Por la regla del estado derivado, no hay columnas de edad.
- **Roles.** No cambian. El endpoint sigue siendo de Admin, Coordinador y Profesor, y el filtro del Profesor sigue en la consulta (join con `grupo_profesor`): la edad se calcula sobre filas ya filtradas.

### 3. El formato del nombre se garantiza en la base

El cálculo hace `int(nombre[:4])`. Para que eso nunca falle, `temporada` suma `ck_temporada_nombre_formato CHECK (nombre ~ '^[0-9]{4}-[0-9]{2}$')`.

**Alternativas descartadas:**
- **Parsear con un respaldo** (edad nula si el nombre no encaja). Suma una rama que en la práctica nunca corre y que el frontend tendría que dibujar.
- **Validar solo en la API de alta de temporadas.** Esa API todavía no existe (HU-UT-04), y la temporada hoy la crean la puesta en marcha y la semilla.

No se exige que el segundo par de dígitos sea el año siguiente: nada lo lee, y un CHECK con aritmética sobre texto es frágil.

La regla queda en una capability nueva, `temporadas`, no en `grupos`: es una regla de la temporada, y es donde va a vivir la apertura de temporadas.

### 4. Texto del grupo en una sola función del frontend

`textoDelGrupo(grupo)` va en `src/lib/nombres.ts`, junto a `NOMBRE_DEL_TURNO`, y la usan los dos selectores. Devuelve `Delfines · Mañana · 5 a 6 años`, o `Pulpos · Mañana · 7 años` si las dos edades son iguales. `SelectorGrupo` le agrega ` (sugerido)`. Hoy cada selector arma el texto por su cuenta; con la edad, la duplicación pasaría a ser una regla.

### 5. Marco como ruta de diseño dentro de `RutaProtegida`

```
<Route element={<RutaProtegida />}>
  <Route element={<MarcoZonaProtegida />}>   ← encabezado + menú + <Outlet />
    /, /alumnos/nuevo, /asistencia, (RutaSoloAdmin) /cargos/nuevo, /cuenta-corriente
  </Route>
</Route>
```

`RutaProtegida` sigue resolviendo antes la carga y el cambio pendiente, así que el marco no aparece en esos estados sin que haga falta ninguna condición nueva. Esto cumple «Sin menú fuera de la zona habilitada». `/ingresar` queda fuera de las dos rutas.

**Componentes nuevos en `src/components/`:**
- `MarcoZonaProtegida`: el encabezado, con el logo existente (`LogoConAro`), `Escuela de Verano`, el usuario, el rol y `Salir`, más el menú.
- `MenuLateral`: dibuja una lista declarativa de secciones y opciones (`{ texto, a, soloAdmin? }`). Esa lista es el único lugar donde un change futuro suma una pantalla.

Las opciones son `NavLink` de react-router, que ya pone `aria-current="page"` en la activa. `Inicio` lleva `end`, para que no quede marcada en todas las direcciones.

`Salir` se mueve del inicio al encabezado con la misma lógica: `salir()` y navegar a `/ingresar`. El inicio queda con el saludo `Hola, <nombre>`.

**Alternativa descartada:** que cada página monte el marco. Repite el envoltorio cinco veces, y una pantalla nueva podría olvidarlo.

### 6. Responsive solo con CSS

Desde `md` en adelante, el menú es una columna fija a la izquierda. Por debajo, es una fila con desplazamiento horizontal bajo el encabezado, como en `09-mobile-inicio.png`. Se resuelve con breakpoints en `sx`, sin `useMediaQuery`: el DOM es el mismo en los dos tamaños, así que los tests de jsdom ven las mismas opciones y la revisión del tamaño es visual.

Los colores salen de `tema.ts`: la opción activa usa `accion` sobre `accionSuave`, como el prototipo.

## Reversibilidad

- **Migración nueva:** `temporada_nombre_formato`.
  - `upgrade` agrega `ck_temporada_nombre_formato`.
  - `downgrade` la quita con `op.drop_constraint("ck_temporada_nombre_formato", "temporada", type_="check")`.
  - No cambia ninguna columna ni ningún dato.
- **Filas existentes.** Todas las conocidas cumplen el formato. Si una base local tuviera una temporada con otro nombre, el `upgrade` falla con la violación del CHECK y no aplica nada: hay que renombrar esa temporada antes de migrar. No se renombra sola, porque el nombre es un dato que alguien eligió.
- **Prueba en los dos sentidos** contra la base de pruebas, con la skill `revisar-migracion`.
- **Los dos campos nuevos de la API se agregan**, no se renombra ni se quita nada, así que no rompen a ningún cliente. Revertir el change vuelve a la respuesta anterior sin tocar datos.

## Risks / Trade-offs

- **[Riesgo] Los años enteros pueden no coincidir con cómo el club llama a un grupo con un rango que no empiece el 1 de enero** (por ejemplo, 2020-07-01 a 2021-06-30 daría «5 a 6»). → La semilla y el prototipo usan años completos. Si el usuario, al verlo en pantalla, nombra los grupos de otra manera, se cambia antes de escribir el código, como pidió.
- **[Riesgo] Una edad de 1 se escribiría «1 años».** → No hay grupos de menores de 3 años en una escuelita de verano. Si apareciera, es una línea en `textoDelGrupo`.
- **[Costo] Varios tests existentes del frontend comparan `Delfines · Mañana` o pulsan los botones del inicio**, y se rompen a propósito. → Los reescribe el test-writer contra los deltas de `alumnos`, `asistencia` y `auth`. Es parte del paso de tests, no del implementer.
- **[Costo] El CHECK obliga a HU-UT-04 a respetar `AAAA-AA`** al abrir una temporada. → Es lo deseado. Queda escrito en la spec `temporadas`, que es donde va a mirar ese change.
