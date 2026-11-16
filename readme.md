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

**Entrega 2 — Código funcional.** El lote 1 está implementado: la «espina del dinero» completa, de punta a punta — ingreso al sistema, alta de alumno con su familia, grupos y asistencia, tarifario, cargo con el cálculo de descuentos, pagos y cuenta corriente.

Se construyó con **Spec-Driven Development** sobre [OpenSpec](openspec/): cada funcionalidad pasó por propuesta, especificación, diseño y tareas antes de escribir una línea de código. Los ocho *changes* del lote están archivados en [`openspec/changes/archive/`](openspec/changes/archive/) y sus especificaciones vigentes viven en [`openspec/specs/`](openspec/specs/).

Las historias que faltan para poner el sistema en producción están en el [backlog](docs/product/historias-backlog.md), identificadas como «Lote 2».

| | |
|---|---|
| Tests del backend | 467 |
| Tests del frontend | 164 |
| Tests de punta a punta | 3 |
| Specs vigentes | 14 |
| Pull requests | 15, con CI y, desde la #3, revisión automática |

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

> Los usuarios y los montos de la semilla son de ejemplo. `python tasks.py seed` se niega a correr sobre una base que ya tiene datos.

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

> **Puesta en marcha real.** En producción no se corre la semilla: el primer Admin y la primera temporada vigente se crean al instalar el sistema (Acl. 9 y 10). El comando que hace eso es parte del lote 2, junto con el alta de usuarios desde la aplicación.
