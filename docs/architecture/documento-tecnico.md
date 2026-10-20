# Documento técnico — Escuelita de Verano

Oct 12, 2026 · @Ale

Cómo se construye y despliega el sistema. Qué tiene que hacer y por qué está en el PRD (ver `docs/prd/prd-escuelita-de-verano.md`).

## Stack

Backend en Python con FastAPI, frontend en React y base PostgreSQL. Se eligió FastAPI sobre Django a sabiendas de que autenticación, permisos y pantallas de configuración se programan a mano.

| Capa | Tecnología | Para qué |
|---|---|---|
| API | FastAPI + Pydantic | Endpoints REST y validación de datos de entrada |
| Acceso a datos | SQLAlchemy 2 (o SQLModel) | Modelos y consultas a la base |
| Migraciones | Alembic | Cambios de esquema versionados |
| Base de datos | PostgreSQL | Datos de la aplicación |
| Contraseñas | pwdlib con argon2 | Hash de contraseñas |
| Sesión | JWT | Token de acceso y de renovación |
| Tests | pytest | Pruebas, en especial del cálculo de cargos y descuentos |
| Frontend | React + Vite | Aplicación web, publicada como sitio estático |
| Componentes de UI | MUI o Mantine (a elegir) | Pantallas responsive, usables desde el celular |

## Despliegue en Render

Todo corre en una sola cuenta de Render a nombre del cliente, con Ale como miembro con acceso de administración.

Componentes y cómo se conectan: el navegador (computadora o celular) carga la app desde el sitio estático (frontend React + Vite) y usa la API (servicio web FastAPI). La API es la única que accede a PostgreSQL y al disco persistente de archivos; la base y los documentos no se alcanzan directo desde el navegador.

- **Sitio estático** (frontend React): gratis, con dominio propio y HTTPS automático.
- **Servicio web** (API FastAPI): plan pago. El gratis se apaga a los 15 minutos sin uso y tarda cerca de un minuto en despertar.
- **PostgreSQL**: plan pago. El gratis vence a los 30 días y no tiene backups. El pago permite recuperar la base a cualquier momento de los últimos 3 días (workspace Hobby) o 7 (Pro), y guarda los exports 7 días.
- **Disco persistente** para los documentos, adjunto al servicio web: copia automática cada 24 horas, guardada al menos 7 días. Con disco, el servicio no puede tener más de una instancia y cada deploy tiene un corte breve; con menos de 10 usuarios no es un problema.
- **Deploy**: automático desde GitHub en cada push a la rama principal.
- **Migraciones**: `alembic upgrade head` corre como paso previo al arranque del servicio web (pre-deploy command de Render), antes de que la nueva versión reciba tráfico.

## Autenticación, permisos y archivos privados

Todo control de acceso se hace en la API; el frontend solo oculta lo que el usuario no puede usar.

### Contraseñas y sesión

- Hash con argon2 (pwdlib); nunca se guardan ni se registran en texto.
- El login devuelve un token de acceso de vida corta y un token de renovación en una cookie httpOnly. Mientras hay actividad la sesión se renueva; sin actividad vence (30 minutos en computadora, más en el celular del profesor, a ajustar).
- **Dominio y cookie:** el sitio estático y la API son dos servicios distintos de Render, así que con los dominios que Render asigna por defecto la cookie de renovación sería de terceros. La solución es registrar un dominio propio y publicar la API en un subdominio (por ejemplo, `app.<dominio>` y `api.<dominio>`), de modo que la cookie quede same-site. Queda atado al pendiente de registrar el dominio.
- El usuario tiene un indicador `debe_cambiar_password`. Se activa al crearlo y al blanquearlo; mientras esté activo, la API rechaza todo salvo el cambio de contraseña.
- Validación de la nueva contraseña: mínimo 8 caracteres, al menos una letra y un número, distinta del nombre de usuario y de la anterior (se guarda el hash de la anterior para comparar).
- Contador de intentos fallidos: al quinto seguido el usuario queda bloqueado; el blanqueo lo desbloquea.
- Nombre de usuario: inicial del nombre + apellido, en minúsculas y sin acentos; si existe, se agrega un número.
- Los usuarios desactivados no pueden ingresar, pero se conservan para las referencias de quién cobró, anuló o abonó el canon.

### Permisos

- Cada endpoint declara, con una dependencia de FastAPI, qué roles pueden usarlo (Admin, Coordinador, Profesor).
- Para el Profesor, una segunda dependencia comprueba que el grupo o el alumno pertenezca a sus grupos asignados.
- Los listados se filtran en la consulta a la base, no después: un profesor nunca recibe datos de otros grupos.

### Archivos privados

- Los documentos se guardan en el disco del servidor, fuera de cualquier carpeta pública, con un nombre aleatorio.
- Se descargan solo por un endpoint que valida el permiso sobre ese alumno antes de entregar el archivo.
- Al subir se valida el tipo (PDF, JPG, PNG) y el tamaño (**hasta 5 MB**, según Acl. 11; este documento decía 10 MB y se corrigió).

## Fuera de temporada

De marzo a noviembre el sistema no se usa. El cliente elige una de estas tres opciones; la recomendada es la A.

> **Corregido:** este documento recomendaba borrar los archivos de documentación al cerrar la temporada. La Acl. 10 define lo contrario —no se borra nada entre temporadas— y prevalece. Los documentos quedan guardados y vuelven a figurar como pendientes hasta que se presente uno nuevo. Como los datos sensibles de menores se conservan de forma indefinida, los controles de la sección de seguridad pasan a ser más importantes.

| Opción | Qué se conserva | Riesgo y trabajo |
|---|---|---|
| **A. Suspender el servidor y dejar la base prendida (recomendada)** | Todo: alumnos, tutores, profesores, usuarios e historial de cobros, sueldos y canon | Ninguno; no requiere tareas manuales |
| B. Exportar la base, guardarla en el Drive del cliente y borrarla; restaurarla en diciembre | Todo, si la restauración sale bien | 1 a 2 horas de trabajo por año. Render guarda los exports solo 7 días, así que hay que descargarlo; si el backup falla o se pierde, se pierden los datos |
| C. Borrar todo y empezar de cero en diciembre | Nada | Hay que recargar alumnos, tutores, profesores y usuarios; se pierde el historial de cobros y canon, y cambia lo definido en Temporada en el PRD |

## Gestión del trabajo

No se usa ningún gestor de tickets. Para la entrega del curso, las unidades de trabajo son el archivo `6-tickets-de-trabajo.md` del repo; el template oficial no pide Jira, Azure DevOps ni ningún otro sistema, solo el fork de GitHub.

**Render no gestiona tickets**: es solo hosting (builds, deploys, base de datos, sitio estático). El gestor de tickets y la plataforma de despliegue son independientes y no se comunican entre sí, así que usar cualquier gestor no condiciona el despliegue en Render. Lo único que Render observa es el repositorio de GitHub, de donde dispara el deploy en cada push a la rama principal.

**Si más adelante el proyecto real necesita un gestor**, la opción recomendada es **GitHub Issues**, por tres razones concretas: el repositorio ya está ahí, los commits y los pull requests se enlazan de forma nativa (`Closes #12`), y la Entrega 3 exige documentar pull requests de GitHub, con lo cual ese flujo se usa igual. Adoptar un sistema externo implicaría mantener dos herramientas que no se conocen entre sí. Decisión no tomada todavía y reversible en cualquier momento.

## Pendientes técnicos

- [ ] **Fuera de temporada**: el cliente elige la opción A, B o C.
- [ ] **Retención de backups**: el PRD pide al menos 30 días y Render cubre 3 o 7 según el plan. Opciones: un export semanal automático a un almacenamiento externo, o bajar el requisito a 7 días.
- [ ] **Plan del workspace de Render**: Hobby o Pro (define si la recuperación de la base cubre 3 o 7 días).
- [ ] **Región de Render**: elegir la más cercana disponible.
- [ ] **Dominio**: registrar el nombre.
- [ ] **Librería de UI**: MUI o Mantine.
- [ ] **Gestor de issues para el proyecto real**: adoptar GitHub Issues o seguir sin gestor. No afecta a la entrega del curso.
