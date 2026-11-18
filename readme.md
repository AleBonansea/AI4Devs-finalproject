# Escuelita de Verano — Sistema de administración

Sistema web para administrar una escuela de verano que funciona en el club de una mutual de médicos. Centraliza la ficha de cada alumno (datos, tutores autorizados y documentación), los grupos por edad y turno con su asistencia, el tarifario con descuentos por categoría de familia y cantidad de hijos, la cuenta corriente de cada familia, la tesorería general y el canon que se paga al club.

Proyecto Final del máster **AI4Devs (LIDR)**, desarrollado con **Spec-Driven Development** y asistentes de IA en todas las fases.

## Documentación del proyecto

0. [Ficha del proyecto](0-ficha-del-proyecto.md)
1. [Descripción general del producto](1-descripcion-general-del-producto.md)
2. [Arquitectura del Sistema](2-arquitectura-del-sistema.md)
3. [Modelo de Datos](3-modelo-de-datos.md)
4. [Especificación de la API](4-especificaciones-de-la-api.md)
5. [Historias de Usuario](5-historias-de-usuario.md)
6. [Tickets de Trabajo](6-tickets-de-trabajo.md)
7. [Pull Requests](7-pull-requests.md)

**Fuentes y documentos de trabajo**

- [PRD — Producto (versión de relevamiento, PDF)](docs/prd/PRD%20Escuelita%20de%20Verano.pdf)
- [PRD transcripto a Markdown](docs/prd/prd-escuelita-de-verano.md): transcripción fiel del PDF, que no se modifica.
- [Aclaraciones del cliente](docs/prd/aclaraciones-cliente.md): decisiones de negocio posteriores al PRD. Prevalecen sobre el PRD cuando se contradicen.
- [Documento técnico](docs/architecture/documento-tecnico.md): stack, despliegue en Render, seguridad y pendientes técnicos.
- [Backlog de historias de usuario](docs/product/historias-backlog.md): todas las historias, con prioridad y sustento, los lotes y el plan de changes.
- [Especificaciones vigentes](openspec/specs/): el comportamiento del sistema, un Scenario por caso, cada uno con su test.
- [Contrato de la API](docs/api/openapi.json): generado desde el código y comprobado en cada pull request.
- [Registro de uso de IA (prompts.md)](prompts.md)

## Estado

**Entrega 3 — Entrega final.** El lote 1 está implementado: la «espina del dinero» completa, de punta a punta — ingreso al sistema, alta de alumno con su familia, grupos y asistencia, tarifario, cargo con el cálculo de descuentos, pagos y cuenta corriente. Está desplegado en Render como entorno demo (ver [Probarlo en línea](#probarlo-en-línea)) y cubierto por tests unitarios, de integración y de punta a punta.

Se construyó con **Spec-Driven Development** sobre [OpenSpec](openspec/): cada funcionalidad pasó por propuesta, especificación, diseño y tareas antes de escribir una línea de código. Los ocho *changes* del lote, y los tres que se sumaron después (menú lateral, tests de punta a punta y semilla del entorno demo), están archivados en [`openspec/changes/archive/`](openspec/changes/archive/) y sus especificaciones vigentes viven en [`openspec/specs/`](openspec/specs/).

Las historias que faltan para poner el sistema en producción están en el [backlog](docs/product/historias-backlog.md), identificadas como «Lote 2».

| | |
|---|---|
| Tests del backend | 482 |
| Tests del frontend | 164 |
| Tests de punta a punta | 3 |
| Specs vigentes | 14 |
| Pull requests | 17, con CI y, desde la #3, revisión automática |

## Probarlo en línea

**https://escuelita-cm.onrender.com/ingresar**

Es un **entorno demo** en Render, con datos inventados que cargó la semilla. No tiene datos reales de familias ni de alumnos.

> **Antes de empezar:**
> - **El primer ingreso tarda.** Es el plan gratuito de Render: la API se duerme después de un rato sin uso y tarda cerca de un minuto en despertar. Si el ingreso parece colgado, esperá; no es un error. Después responde normal.
> - **Disponible hasta el 16/12/2026.** La base gratuita de Render vence a los 30 días de creada.
> - **La base es compartida.** Lo que cargues lo ven los demás evaluadores. Para las familias nuevas usá un apellido propio, por ejemplo el tuyo.
> - **Las fechas de los campos** las muestra el navegador según el idioma de tu sistema: en inglés aparecen como mm/dd/aaaa.

### Usuarios de prueba

Todos con la contraseña **`Verano2026`**:

| Usuario | Rol | Qué puede hacer |
|---|---|---|
| `mgarcia` | Admin | Todo: alumnos, asistencia, cargos, pagos y cuenta corriente |
| `lrodriguez` | Coordinador | Alumnos y asistencia en cualquier grupo; nada de dinero |
| `jperez` | Profesor | Asistencia solo en sus grupos (los dos Delfines); nada de dinero |

### Qué trae cargado

**Temporada 2026-27**, del 04/01/2027 al 26/02/2027.

| Grupo | Turno | Nacidos | Profesor |
|---|---|---|---|
| Delfines | Mañana y Tarde | 2020 a 2021 | `jperez` |
| Tiburones | Mañana y Tarde | 2017 a 2019 | `cfernandez` |

| Familia | Categoría | Hijos inscriptos |
|---|---|---|
| Pérez | Empleado | Ana (Tiburones · Mañana) y Juan (Delfines · Mañana) |
| Gómez | Socio | Lucía (Delfines · Tarde) |
| Ruiz | No socio | Sofía (Tiburones · Tarde) |

**Tarifa base:**

| | Mes | Quincena | Semana | Día |
|---|---|---|---|---|
| Mañana | $ 100.000 | $ 55.000 | $ 30.000 | $ 8.000 |
| Tarde | $ 80.000 | $ 45.000 | $ 25.000 | $ 7.000 |

**Descuento.** Se aplica un único porcentaje, nunca acumulado:

| Categoría | Día, Semana, Quincena | Mes, 1 hijo | Mes, 2 hijos | Mes, 3 hijos | Mes, 4 o más |
|---|---|---|---|---|---|
| No socio | 0 % | 0 % | 10 % | 15 % | 20 % |
| Socio | 50 % | 50 % | 55 % | 57,5 % | 60 % |
| Empleado | 25 % | 25 % | 32,5 % | 36,25 % | 40 % |

En el Mes, los hijos se cuentan **por turno**, y el porcentaje del tramo alcanza a todos los hermanos.

**Tipos de cargo:** *Abono*, que se calcula con la tarifa y el descuento, y *Preinscripción*, con monto fijo de $ 20.000 y sin descuento.

### Recorrido de verificación

Unos 15 minutos. Cada paso dice qué hacer y qué tenés que ver. Los montos salen de las tablas de arriba, así que se pueden comprobar a mano.

#### 1. El flujo principal: alta → cargo → pagos → saldo en cero

Ingresá como **`mgarcia`** (Admin).

| # | Hacé esto | Tenés que ver |
|---|---|---|
| 1.1 | Menú **Registrar alumno**. Cargá nombre *Tomás*, apellido *tu apellido* y fecha de nacimiento **12/04/2019**. | En **Grupo** aparecen sugeridos los dos Tiburones, porque 2019 cae en su rango de edad. |
| 1.2 | Elegí **Tiburones · Mañana**. Dejá **Familia nueva** y elegí la categoría **Empleado**. | — |
| 1.3 | Probá **Registrar** sin cargar ninguna persona. | El alta se rechaza: la familia nueva necesita al menos un tutor. |
| 1.4 | **Agregar persona nueva**: nombre, apellido, teléfono y DNI, y marcá **Tutor**. **Registrar**. | «Tomás *Apellido* quedó inscripto en Tiburones (Mañana). Familia: *Apellido* – Tomás.» |
| 1.5 | Menú **Registrar cargo**. En **Familia** escribí tu apellido y elegila. | «Categoría: Empleado». |
| 1.6 | **Alumno y turno**: Tomás · Mañana. **Tipo de cargo**: Abono. **Modalidad**: Mes. **Período**: Mes 1. | El desglose, que calcula la API: tarifa base **$ 100.000**, descuento Empleado **25 %**, total **$ 75.000**. |
| 1.7 | **Registrar cargo**. | «Cargo registrado por $ 75.000. Saldo pendiente de la familia: $ 75.000.» |
| 1.8 | Repetí el mismo cargo: Abono, Mes, Mes 1, mismo alumno. | «El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana.»: un cargo no se cobra dos veces. |
| 1.9 | Menú **Cuenta corriente**, elegí tu familia. | Saldo pendiente **$ 75.000** y el renglón «Abono · Mes 1». |
| 1.10 | **Registrar pago**. Cambiá el monto a **$ 30.000** y confirmá. | Saldo pendiente **$ 45.000**: los pagos parciales se permiten. |
| 1.11 | **Registrar pago** otra vez, por **$ 50.000**. | Se rechaza: el pago no puede superar lo que se debe. |
| 1.12 | **Registrar pago** con el monto que propone la pantalla, **$ 45.000**. | Saldo pendiente **$ 0**, el cargo figura **Saldado** y desaparece el botón de pago. |

#### 2. El cálculo: descuento por tramo de hijos y monto fijo

Seguí como **`mgarcia`**, en **Registrar cargo**. En cada caso mirá el desglose antes de registrar. Para comprobar solo el cálculo no hace falta registrar.

| # | Familia · alumno | Cargo | Total esperado | Por qué |
|---|---|---|---|---|
| 2.1 | Pérez · Ana · Mañana | Abono · Mes · Mes 1 | **$ 67.500** | Empleado con 2 hijos a la mañana: 32,5 %, no 25 % |
| 2.2 | Pérez · Juan · Mañana | Abono · Mes · Mes 1 | **$ 67.500** | El tramo alcanza a los dos hermanos, no solo al segundo |
| 2.3 | Gómez · Lucía · Tarde | Abono · Quincena · Quincena 1 | **$ 22.500** | Socio en Quincena: 50 %. La cantidad de hijos no cuenta fuera del Mes |
| 2.4 | Ruiz · Sofía · Tarde | Abono · Mes · Mes 1 | **$ 80.000** | No socio con 1 hijo: sin descuento |
| 2.5 | Ruiz · Sofía · Tarde | Abono · Día, con una fecha de la temporada | **$ 7.000** | El Día no tiene período: se elige la fecha |
| 2.6 | Cualquiera | Preinscripción | **$ 20.000** | Monto fijo, sin descuento, aunque la familia sea Socio |

Si otro evaluador ya registró uno de estos cargos, la pantalla lo va a rechazar por repetido. Elegí otro período, por ejemplo Mes 2 o Quincena 2, y el total tiene que dar igual.

#### 3. Asistencia y permisos por rol

| # | Usuario | Hacé esto | Tenés que ver |
|---|---|---|---|
| 3.1 | `jperez` (Profesor) | Mirá el menú. | Solo **Inicio**, **Registrar alumno** y **Tomar asistencia**. No aparece la sección **Administración**. |
| 3.2 | `jperez` | **Tomar asistencia**: abrí el selector de grupo. | Solo sus grupos, Delfines Mañana y Delfines Tarde. Los Tiburones no aparecen. |
| 3.3 | `jperez` | Delfines · Mañana, una fecha de la temporada (enero o febrero de 2027). Marcá a Juan Pérez y guardá. | «Asistencia guardada.» |
| 3.4 | `jperez` | Escribí a mano en la barra del navegador `…onrender.com/cuenta-corriente`. | Te devuelve al inicio: la cuenta corriente es solo del Admin, aunque se conozca la dirección. |
| 3.5 | `lrodriguez` (Coordinador) | **Tomar asistencia**. | Ve los cuatro grupos. Tampoco tiene **Administración**: el Coordinador no ve dinero. |
| 3.6 | Cualquiera | **Salir**, y volvé a ingresar con una contraseña incorrecta. | Se rechaza el ingreso, con un mensaje que no dice si lo que falló fue el usuario o la contraseña. |

#### 4. Lo que no se ve en la pantalla

- **La documentación de la API:** https://escuelita-cm-api.onrender.com/docs *(ver la nota del final)*. Probá `POST /api/v1/cargos` mandando un `monto`: la API lo ignora o lo rechaza, porque **el precio nunca viene del cliente**.
- **Los tests:** el último run del CI en GitHub Actions muestra los cuatro jobs (backend, frontend, contrato y punta a punta) en verde. Los tres recorridos de punta a punta (`e2e/tests/`) automatizan los pasos 1 y 3 de este recorrido.

## Cómo levantarlo en local

**Requisitos:** [Docker](https://www.docker.com/products/docker-desktop/) (para PostgreSQL 16), **Python 3.12 o superior** y **Node 20 o superior**.

```bash
# 1. Configuración del backend.
cp backend/.env.example backend/.env
```

Abrí `backend/.env` y reemplazá el valor de `SECRET_KEY` por una cadena larga y aleatoria. Es la clave con la que se firman los tokens de sesión; cualquier valor sirve para desarrollo, pero no dejes el del ejemplo. El resto de las variables ya apunta al PostgreSQL del `docker-compose.yml`.

`frontend/.env` no hace falta en desarrollo: Vite reenvía `/api` al backend.

```bash
# 2. Dependencias del backend y del frontend.
python tasks.py install

# 3. PostgreSQL en Docker, con la base de desarrollo y la de pruebas.
python tasks.py up

# 4. Estructura de la base.
python tasks.py migrate

# 5. Datos de ejemplo (temporada, tarifario, usuarios y tres familias).
python tasks.py seed
```

Después, en dos terminales:

```bash
python tasks.py api        # API en http://localhost:8000 (documentación en /docs)
python tasks.py front-dev  # aplicación en http://localhost:5173
```

Entrá a **http://localhost:5173** con cualquiera de los usuarios de ejemplo, todos con la contraseña `Verano2026`:

| Usuario | Rol | Qué ve |
|---|---|---|
| `mgarcia` | Admin | Todo, incluidos el tarifario y la cuenta corriente |
| `lrodriguez` | Coordinador | Alumnos, familias, grupos y asistencia |
| `jperez` | Profesor | Solo sus grupos y su asistencia |

> Los usuarios y los montos de la semilla son de ejemplo. **La semilla es solo para desarrollo y demo**: se niega a correr sobre una base que ya tiene datos y, salvo permiso explícito, sobre una base que no sea local.

**Sembrar el entorno demo.** Para sembrar una base remota con datos inventados (la del entorno demo en Render), apuntá `DATABASE_URL` a esa base y dale a la semilla el permiso explícito, solo para ese comando. En PowerShell:

```powershell
$env:DATABASE_URL='<External Database URL de la base demo>'; $env:SEMILLA_FUERA_DE_LOCAL='1'; python tasks.py seed; Remove-Item Env:DATABASE_URL, Env:SEMILLA_FUERA_DE_LOCAL
```

Las dos variables se sacan al terminar. Si `DATABASE_URL` queda puesta, un `python tasks.py migrate` o el backend levantado en esa misma terminal van contra la base demo. La URL trae la contraseña y queda en el historial de PowerShell, así que conviene cerrar la terminal después.

Antes de conectarse, la semilla avisa a qué host va a escribir: el host que nombra la URL. Una URL sin host se rechaza aun con permiso. Las variables de libpq `PGHOST`, `PGHOSTADDR` y `PGSERVICE` no tienen que estar definidas al sembrar: desvían la conexión sin que la URL lo muestre, y la semilla no las mira.

El permiso vale solo con el valor exacto `1`, y solo desde el entorno de la terminal. Una línea en `backend/.env` no lo da, para que no quede puesto para siempre.

**Nunca con la base del club:** la External Database URL de producción no se copia a ninguna máquina de desarrollo.

**Comprobar que todo está en orden:**

```bash
python tasks.py test        # tests del backend (necesita el paso 3)
python tasks.py front-test  # tests del frontend
python tasks.py lint        # ruff check y ruff format
python tasks.py typecheck   # mypy
python tasks.py front-lint  # eslint, prettier y build
python tasks.py e2e         # tests de punta a punta en Chromium (necesita el paso 3)
```

`python tasks.py e2e` no toca la base de desarrollo: recrea, migra y siembra una propia, `escuelita_e2e`, compila el frontend como en producción y levanta la API en el puerto 8001 y el build en el 4173, que tienen que estar libres. `python tasks.py install` ya deja instalados Playwright y Chromium. Si un test falla, su trace queda en `e2e/test-results/` y se abre con `cd e2e && npx playwright show-trace <trace.zip>`.

`python tasks.py` sin argumentos lista todas las tareas.

> **Puesta en marcha real.** En producción no se corre la semilla: el primer Admin y la primera temporada vigente se crean al instalar el sistema (Acl. 9 y 10). El comando que hace eso va con el lote 2, junto a HU-UT-06 (cambio de contraseña): el primer Admin nace con el cambio de contraseña pendiente y, sin esa historia, no puede operar. Cuando exista, corre en la shell del servidor, no desde una notebook.
