> Detalla en esta sección los prompts principales utilizados durante la creación del proyecto, que justifiquen el uso de asistentes de código en todas las fases del ciclo de vida del desarrollo. Esperamos un máximo de 3 por sección, principalmente los de creación inicial o  los de corrección o adición de funcionalidades que consideres más relevantes.
Puedes añadir adicionalmente la conversación completa como link o archivo adjunto si así lo consideras


## Índice

0. [Herramientas, modelos y contexto](#herramientas-modelos-y-contexto)
1. [Descripción general del producto](1-descripcion-general-del-producto.md)
2. [Arquitectura del sistema](2-arquitectura-del-sistema.md)
3. [Modelo de datos](3-modelo-de-datos.md)
4. [Especificación de la API](4-especificaciones-de-la-api.md)
5. [Historias de usuario](5-historias-de-usuario.md)
6. [Tickets de trabajo](6-tickets-de-trabajo.md)
7. [Pull requests](7-pull-requests.md)

---

## Herramientas, modelos y contexto

Cómo se trabajó con IA en todo el proyecto. Las secciones que siguen recogen los prompts clave de cada fase; esta dice con qué se hicieron.

### Herramientas

| Herramienta | Para qué |
|---|---|
| **Claude Code (CLI)**, sobre el repo | Todo el ciclo de construcción: proponer y especificar cada *change* de OpenSpec, escribir los tests, implementar, revisar, commitear, abrir las pull requests y mirar el CI con `gh`. |
| **Claude (chat y Cowork)** | Fuera del repo: el relevamiento que terminó en el PRD (sección 1), revisar planes antes de pasárselos a Claude Code, comparar el estado del proyecto contra las consignas del curso y preparar el entorno de una segunda máquina. |
| **`claude-code-action`** en GitHub Actions | Revisor automático de cada pull request ([`.github/workflows/revisor.yml`](.github/workflows/revisor.yml)), con el criterio de [`REVIEW.md`](REVIEW.md). |

No se usaron otros asistentes ni IDE con IA.

### Modelos

| Dónde | Modelo | Por qué |
|---|---|---|
| Sesión principal de Claude Code: propuestas, specs, design, `test-writer`, `adversarial-reviewer` | **Opus** | Es donde se decide qué se construye y si está bien: razonar sobre reglas de negocio, encontrar el caso que falta, desconfiar de un test en verde. |
| Subagentes `implementer` y `ui-implementer` | **Sonnet** | Escriben código contra tests ya congelados: la especificación está cerrada y el test dice cuándo terminaron. Es trabajo acotado, y Sonnet lo hace más rápido y más barato. |
| Revisor automático de las pull requests | **Sonnet** | Una palanca de costo: corre en cada push y no necesita el modelo grande para aplicar un criterio escrito. |
| Claude en el chat | **Opus** | Análisis y revisión de documentos y planes. |

### Contexto avanzado

- **[`CLAUDE.md`](CLAUDE.md):** las fuentes de verdad y su precedencia, los comandos, las convenciones del backend que no son sugerencias (el cálculo en una función pura, el precio nunca viene del cliente, nada se borra), los roles, las entidades y las reglas de proceso (una rama por *change*, todo en castellano, lo no confirmado se marca [SUPUESTO]).
- **OpenSpec** ([`openspec/config.yaml`](openspec/config.yaml)): el contexto que cada propuesta recibe sin pedirlo, con las fuentes de verdad y lo que tiene que incluir cada artefacto. Cada funcionalidad pasó por `propose` → revisión humana → `apply` → `verify` → `archive`.
- **Once skills** en [`.claude/skills/`](.claude/skills/): las siete de OpenSpec, más cuatro propias:
  - `backend-feature` y `frontend-feature` fijan el orden *tests → rojo → congelar → implementar → verde* y reparten el trabajo entre subagentes;
  - `revisar-migracion`, para el diff de cada migración de Alembic;
  - `commit`, para cerrar cada petición en la rama correcta.
- **Cuatro subagentes** en [`.claude/agents/`](.claude/agents/), con separación de poderes:
  - `test-writer` escribe los tests desde los Scenarios **sin poder leer la implementación**;
  - `implementer` y `ui-implementer` escriben el código **sin poder tocar los tests**, congelados por hash;
  - `adversarial-reviewer` revisa una vez al final de cada *change*, buscando lo que está mal.
- **Cinco hooks** en [`.claude/hooks/`](.claude/hooks/):
  - `sin_ver_implementacion` es el candado del `test-writer`;
  - `sin_borrar_datos` y `datos_que_no_salen` cortan comandos que destruirían datos o los sacarían del proyecto, porque el sistema guarda datos de salud de menores;
  - `color_con_nombre` corta los colores escritos a pelo fuera del tema;
  - `formato` formatea cada archivo escrito.
- **[`REVIEW.md`](REVIEW.md):** el criterio común del revisor adversarial y del revisor automático, incluido cuándo se deja de revisar.

---

## 1. Descripción general del producto

> Los prompts 1 y 3 son de la sesión de relevamiento en Claude (chat) donde se armó el PRD. El prompt 2 es de la sesión de Claude Code (CLI) sobre el repo, ya con el PRD transcripto. Se transcriben tal cual se escribieron (extractos marcados con [...]).

**Prompt 1: Arranque del relevamiento, con la IA como analista que pregunta y contradice**

*Contexto:* primer mensaje de la sesión. Planteé la idea y fijé la forma de trabajo: que la IA me hiciera preguntas, me contradijera y me recomendara funcionalidades.

```
quiero armar un sistema para mi cuñado, para administracion de una escuelita de verano.
Necesito que me hagas preguntas y me contradigas en cosas que te parecen no estar
correctas, que me recomiendes funcionalidades.
En principio lo que tenemos es...
Distintos usuarios, uno general que puede ver todo y puede registrar niños y profes y
asignarlos a un grupo. Ver las cuentas corrientes y todos los accionables q se hagan.
Otro usuario es para los profes, para q puedan gestionar sus grupos.
Modulos:
* Ingreso al sistema.
* Registro de alumnos y profes.
* Visualizacion de datos de alumnos, carga de documentacion.
* Visualizacion de grupos, generalmente dividido por edades. Se debe poder cargar las
  faltas o asistencias.
Que mas se te ocurre?
```

*Respuesta clave:* la IA devolvió preguntas agrupadas por tema (alumnos y familias, grupos y asistencia, comunicación, alcance temporal) y una lista de funcionalidades para discutir prioridad: personas autorizadas a retirar, salidas/excursiones, novedades/incidentes, reportes, alergias y recordatorios de pago.

*Ajuste humano / impacto:* respondí cada pregunta y decidí qué entraba y qué no. Agregué el rol coordinador, la cuenta corriente única por familia sin comprobantes ARCA, el canon al club y la temporada como unidad de uso. Novedades/incidentes y recordatorios de pago quedaron como mejora futura, la comunicación con padres sigue por WhatsApp y las autorizaciones de salidas se resuelven como documentación del alumno, sin módulo propio.

---

**Prompt 2: Auditoría adversarial del PRD**

*Contexto:* el PRD ya estaba transcripto al repo como `docs/prd/prd-escuelita-de-verano.md`. Este prompt se corrió en Claude Code (CLI), no en el chat del relevamiento. Le pedí a la IA que cambiara de rol: en vez de ayudarme a escribir el PRD, que lo atacara.

```
Cambiá de sombrero: actuá como revisor de producto adversarial. Leé
@docs/prd/prd-escuelita-de-verano.md y atacalo. ¿Qué requisitos son ambiguos o no
testables? ¿Qué supuesto, si es falso, tumba el sistema entero? ¿Dónde hay scope creep
escondido? ¿Qué parte es demasiado ambiciosa para un MVP de 3 historias y unas 30 horas?
Priorizá por riesgo y citá la sección del PRD. No cambies ningún archivo: solo el
informe.
```

*Respuesta clave (resumida):* la IA encontró 14 hallazgos ordenados por riesgo, cada uno con la sección del PRD que lo origina.
- **5 de riesgo crítico** (supuestos que, si son falsos, tumban el sistema):
  - "Familia" no estaba definida, y de ella dependen la cuenta corriente, el descuento por hermanos y la categoría socio.
  - La categoría "empleado" no tenía regla.
  - Faltaba una ventana de tiempo para contar hermanos.
  - "Cada temporada arranca de cero" chocaba con las deudas pendientes.
  - Había datos sensibles de menores (alergias, DNI) sin ningún requisito de seguridad.
- **9 de riesgo alto** (requisitos ambiguos o no testables). Entre ellos: la regla "más de 3 días sueltos se cobra la semana" contradecía "no hay cálculo automático en base a la asistencia"; "Período" tenía cuatro significados distintos; y el canon no definía el %, ni los rangos, ni qué pasa con los pagos parciales.

Además señaló el scope creep oculto, con frases cortas que en realidad son módulos enteros: reporte de deudas, subida de archivos, ABM del tarifario, cierre de canon, multi-temporada y gestión de usuarios. Y propuso un recorte de MVP en 3 historias (alta de alumno, asistencia y cobro), dejando afuera canon, tesorería, documentación y multi-temporada.

*Ajuste humano / impacto:* respondí los 14 hallazgos uno por uno. Todas las decisiones quedaron en `docs/prd/aclaraciones-cliente.md`, que prevalece sobre el PRD sin modificarlo. Las decisiones más importantes fueron mías, no de la IA:
- **Rechacé el recorte de MVP que proponía y definí el alcance por lotes.** El sistema completo se construye igual, porque es para un cliente real. Lo que se recorta es el orden: un primer lote de desarrollo en cadena, sin datos semilla (usuarios, grupos, alta de alumno, asistencia, tarifario y cobro), y aparte las 3 historias que se documentan para la entrega. La IA proponía cortar funcionalidad; yo corté secuencia.
- **Eliminé la regla "más de 3 días sueltos se cobra la semana",** que era una propuesta del cliente. La IA solo la había marcado como ambigua. En lugar de aclararla, la saqué: se cobra la modalidad contratada, asista o no el chico, y la tarifa diaria queda más cara que la semanal. Así el incentivo a contratar la semana lo da el precio, y el sistema no tiene que calcular nada a partir de la asistencia.
- **Resolví la identificación de familias con un ID interno y una etiqueta recalculada.** No usé el apellido ni el hijo mayor como identificador, porque ninguno de los dos es estable: hay medio hermanos con otro apellido, y el hijo mayor cambia si se suma uno más grande. La familia la arma a mano quien carga al alumno, y la etiqueta "Apellido – Hijo mayor" se recalcula sola y no se edita.

---

**Prompt 3: Rediseño del arancel (propuesta mía) y categoría a nivel familia**

*Contexto:* el arancel de la temporada 2025-26 estaba escrito a mano en una hoja, sin un criterio de porcentajes y con inconsistencias (en algunos casos ni siquiera había descuento). Llevé al relevamiento las definiciones que había obtenido ese día y les adjunté la imagen del arancel con el caso de hermanos en turnos distintos marcado.

```
DEfiniciones que obtuve hoy.
1, Esto no recuerdo si te lo dije. El club es como de una mutual de centro medico, son
Medicos asociados, por lo tanto si un familiar, padre o madre es medico asociado, todos
los hijos corren como socios, no son socios individuales, todo entran en la misma bolsa.
2 adjunto imagen . Si un hermano va doble turno y el otro solo va a la mañana, se
cobraria como esta marcado en la imagen.
3 Aplicaremos un valor fijo por dia, semana, quincena y mes, luego aplicaremos % de
descuentos que podemos ir registrandolos en una tabla.
Por ej, el Socio obtiene el 50% de descuento de la tarifa general para todos los hijos y
no va decreciendo a mas hijos que tenga.
El empleado por ej, en el 1er hijo ya arranca con un descuento, por ej del 10%, 2do hijo
15% a cada uno, 3ero 20% 4to o mas 25%...
por ej...
y el no socio arranca con tarifa de lista y tmb aplica 10% para 2do hijo, 15% al 3ero
hijo y 20% a mas de 4...
esto va a ser configurable por el administrador, tanto los montos a cobrar como los
porcentajes de descuentos
```

*Ajuste humano / impacto:* el modelo de tarifas fue una decisión mía, no de la IA: en lugar de replicar los precios cargados a mano, propuse una tarifa base por turno y modalidad (día / semana / quincena / período) más una tabla de % de descuento por categoría y cantidad de hermanos, ambas configurables por el administrador. Esto ordena un arancel que era inconsistente y permite ajustarlo cada temporada sin tocar el sistema. Además corregí la propuesta de la IA de manejar la categoría por alumno: es un dato único de la familia (si algún tutor es médico asociado, todos los hermanos entran como socios). Con el caso marcado en la imagen quedó la regla de que cada turno se factura de forma independiente, contando solo a los hermanos anotados en ese turno.

---

## 2. Arquitectura del Sistema

> Prompt de la sesión de Claude Code (CLI) sobre el repo. Se transcribe tal cual se escribió (extractos marcados con [...]). Un solo prompt generó las seis subsecciones: va completo en la 2.1, y las demás remiten a él.

### **2.1. Diagrama de arquitectura:**

**Prompt 1: Arquitectura completa a partir del documento técnico, sin contradecirlo**

*Contexto:* el documento técnico ya definía el stack, el despliegue en Render y la seguridad. Pedí volcarlo a las seis subsecciones del template, con diagramas Mermaid simples, la justificación del stack con lo que se sacrifica, y la aclaración explícita de que la estructura de ficheros y los tests son lo planificado, porque todavía no hay código.

```
[...] Completá 2-arquitectura-del-sistema.md, en la raíz. La fuente principal es
docs/architecture/documento-tecnico.md, que ya tiene el stack, el despliegue en Render
y la seguridad: no inventes nada que lo contradiga.

2.1 Diagrama de arquitectura en Mermaid, con los componentes y las tecnologías. Explicá
    por qué este stack y qué se sacrifica: FastAPI sobre Django implica programar a mano
    la autenticación, los permisos y las pantallas de configuración.
2.2 Componentes principales con su tecnología.
2.3 Estructura de ficheros propuesta para el backend FastAPI y el frontend React+Vite.
    Todavía no hay código, así que es la estructura planificada: decilo explícitamente.
2.4 Infraestructura y despliegue, con el diagrama de Render en Mermaid: sitio estático,
    servicio web, PostgreSQL y disco persistente, y el deploy automático desde GitHub.
2.5 Seguridad, a partir de la sección correspondiente del documento técnico.
2.6 Estrategia de tests. No hay tests todavía, así que es el plan: pytest con foco en el
    cálculo de cargos y descuentos, que es donde está la lógica de negocio.

Mantené los diagramas Mermaid simples y sin caracteres raros en las etiquetas.
```

*Respuesta clave:* la IA describió la arquitectura como SPA + API REST, con un backend monolito modular en capas, y justificó el stack. El sacrificio de FastAPI sobre Django lo bajó a lo concreto: autenticación, permisos y pantallas de configuración hechas a mano, que en el backlog son historias propias. Además:
- armó dos diagramas Mermaid (arquitectura y Render) y los validó con el CLI oficial;
- propuso la estructura de ficheros del backend y el frontend, marcada como planificada;
- armó un plan de tests en cinco niveles: unitario del motor de cálculo, integración de endpoints, permisos, constraints y migraciones, siempre con PostgreSQL real y no SQLite.

Al cruzar el documento técnico con las aclaraciones encontró dos contradicciones, y aportó dos puntos que el documento técnico no cubría.

*Ajuste humano / impacto:*
- **Las dos contradicciones con las aclaraciones se resolvieron a favor de las aclaraciones,** y además se corrigieron en el propio documento técnico, para que las dos fuentes digan lo mismo:
  - el límite de los documentos es **5 MB**, no 10 MB (Acl. 11);
  - **no se borran los documentos** al cerrar la temporada, aunque el documento técnico lo recomendaba (Acl. 10). Quedan guardados y vuelven a figurar como pendientes en la temporada nueva.
- **Se aceptó la propuesta de correr `alembic upgrade head` en el pre-deploy** del servicio web en Render, para que la nueva versión nunca reciba tráfico con un esquema viejo. Quedó incorporada al documento técnico.
- **El hallazgo de la cookie de renovación entre dos servicios distintos** se resolvió publicando la API en un subdominio del dominio propio (por ejemplo, `app.<dominio>` y `api.<dominio>`). El sitio estático y la API son dos servicios de Render, y con los dominios que Render asigna por defecto la cookie httpOnly sería de terceros. Así queda same-site. Quedó atado al pendiente de registrar el dominio.

### **2.2. Descripción de componentes principales:**

Cubierto por el prompt 1 de la 2.1.

### **2.3. Descripción de alto nivel del proyecto y estructura de ficheros**

Cubierto por el prompt 1 de la 2.1, que la dejó como estructura planificada. En la Entrega 2 se reemplazó por la estructura real del repositorio con el prompt 3 de la 2.4.

### **2.4. Infraestructura y despliegue**

El despliegue en Render está cubierto por el prompt 1 de la 2.1, con dos ajustes: el pre-deploy con `alembic upgrade head`, y no borrar los documentos fuera de temporada.

Los dos prompts que siguen son de **mantenimiento**, la fase que en la Entrega 1 quedó sin plan: cómo se revisa cada cambio y cómo la documentación sigue al código. Las dos piezas están descriptas en `2-arquitectura-del-sistema.md`, 2.4, «Mantenimiento: revisión de pull requests y documentación viva». La pieza diaria de la documentación viva no necesita prompt propio: es `/openspec-archive-change <change>`, que al cerrar cada change funde su delta en `openspec/specs/` y se corrió una vez por change.

**Prompt 2: Cuándo se deja de revisar**

*Contexto:* en el primer change, `auth-ingreso`, el `adversarial-reviewer` hizo dos pases y cada uno encontró bordes nuevos de la entrada del login: un carácter de control, un *surrogate* suelto, largos medidos antes de normalizar. Cada arreglo tocaba la entrada y abría otro borde. Al cerrar el segundo ciclo le pedí al agente, además de los arreglos, una regla para que la revisión terminara. Se transcribe el cierre del mensaje; antes venían los cuatro Scenarios del último ciclo.

```
[...]
Después del ciclo, verify y archive SIN un tercer pase adversarial.

Y agregá a REVIEW.md, en una sección "Cuándo se deja de revisar": a partir
del segundo pase solo los hallazgos graves reabren el change; los menores
se anotan en el design y van a un change de seguimiento. Sin eso, un
change de auth se revisa para siempre.
```

*Respuesta clave:* `REVIEW.md` sumó la sección «Cuando se deja de revisar»: el primer pase puede reabrir el change por cualquier hallazgo; desde el segundo, solo uno grave. Los menores quedan como diferidos en el design del change.

*Ajuste humano / impacto:* `REVIEW.md` es el criterio común del subagente que revisa antes de la PR y del revisor automático que comenta cada PR (`.github/workflows/revisor.yml`), así que la regla vale para los dos. Dejó dos aprendizajes:
- **Un revisor sin criterio de corte no termina nunca**, y uno que reporta todo esconde lo grave entre lo menor. Por eso `REVIEW.md` limita lo grave a cuatro categorías y pone un tope a las sugerencias.
- **El criterio se corrige cuando la revisión se equivoca, no se ignora el comentario.** En el change `cuenta-corriente` la revisión señaló como posible contradicción que el monto de un pago viniera del cliente. No lo era: la regla protege el precio de un cargo, y un pago es un hecho que informa el Admin. La regla se acotó en `REVIEW.md` (`docs: acotar en REVIEW.md la regla del monto al precio de un cargo`), y la revisión siguiente ya no lo repite.

**Prompt 3: La documentación contra el código, antes de entregar**

*Contexto:* con el lote 1 terminado y las PRs mergeadas, una revisión previa a la entrega encontró que la documentación numerada seguía diciendo que no había código. Le pasé esa revisión al agente con este pedido, en una rama propia de documentación.

```
[pegué la revisión: la 2 dice «todavía no hay código», «estructura
planificada» y «todavía no hay tests»; sigue «MUI o Mantine, pendiente de
elegir»; la 1.4 dice que la instalación «se confirma en la Entrega 2»; y
el feedback de la Entrega 1 dejó Mantenimiento «sin plan aún», cuando hoy
están el revisor de cada PR y las specs de OpenSpec como documentación
viva]

Revisa la documentacion del proyecto contra lo que se hizo en entrega 2 y
actualiza todo para poder entregarlo
```

*Respuesta clave:* el agente no se quedó con la lista: contrastó cada documento contra el código, el contrato generado, las specs, las migraciones y el historial de PRs, y encontró contradicciones que la revisión no nombraba:
- la sección 4 documentaba `?simular=true` y `404` para las referencias inexistentes, cuando la API construida tiene `POST /cargos/simulacion` y `422` por campo. Se reescribió con un extracto del contrato generado (`docs/api/openapi.json`) en lugar del OpenAPI escrito a mano, y con una sección «Qué cambió respecto de la Entrega 1»;
- el modelo de datos decía que las columnas *(después)* se crean desde el principio, y el código decidió lo contrario;
- la sesión con cookie de renovación figuraba como hecha, y lo construido es un token de 8 horas en `localStorage`, con la renovación esperando al dominio propio;
- `7-pull-requests.md` decía que las nueve PRs pasaron por el revisor automático, y la #2 no tiene informe: el revisor recién publicó desde la #3.

La sección 2 pasó a describir la estructura real, los 605 tests por nivel y capability, el CI, y la nueva subsección de mantenimiento.

*Ajuste humano / impacto:* **la documentación también se verifica contra el código, no contra la memoria.** Las specs no se desfasan porque cada Scenario tiene un test; los documentos numerados, que no tienen test, se habían quedado en la Entrega 1 en casi todo lo que el código cambió.

---

#### Entrega 3: el entorno demo en Render

> La sesión de Claude Code de este trabajo no se conservó, así que no hay prompt textual. Lo que sigue se reconstruye desde el *change* `semilla-fuera-de-local` ([`openspec/changes/archive/2026-11-16-semilla-fuera-de-local/`](openspec/changes/archive/2026-11-16-semilla-fuera-de-local/)) y la PR #17.

**Una red de seguridad que hacía su trabajo demasiado bien**

*Contexto:* el sistema se desplegó en Render como **entorno demo**, para que se pueda probar desde una URL pública. Hubo que fijar Python 3.12 para el build (`eb67eb8`). La base demo quedó vacía y la semilla no la cargaba: `verificar_base_local` rechaza cualquier base cuyo host no sea local. Es la red que impide sembrar datos inventados en la base del club, y estaba bien que rechazara. Lo que faltaba era una forma de saltearla **a propósito**.

*Respuesta clave:* un *change* técnico, con spec, tests y revisión adversarial como cualquier otro:

- **Un permiso explícito y difícil de dejar puesto por descuido.** La semilla siembra una base remota solo si la variable de entorno `SEMILLA_FUERA_DE_LOCAL` vale exactamente `1`, y la lee del entorno de la terminal. Una línea en `backend/.env` no da el permiso: el `.env` es un archivo que se queda, y el permiso tiene que durar lo que dura la terminal.
- **El host a la vista antes de conectarse.** La semilla avisa a qué host va a escribir, y una URL sin host se rechaza aun con permiso.
- **15 tests nuevos**, que prueban el permiso con un `dict` de entorno, sin tocar el entorno real. Uno corre el comando de verdad contra un dominio `.invalid` para comprobar que el aviso sale antes del error de conexión.
- La base demo se sembró desde la notebook, con la External Database URL de Render solo para ese comando. El readme quedó con el comando exacto para PowerShell, que borra las dos variables al terminar.

*Ajuste humano / impacto:*

- **No se aflojó la red: se le agregó una puerta con llave.** Lo rápido era borrar la comprobación o sembrar a mano con SQL. Las dos opciones dejaban sin protección la base del club, que va a guardar datos de salud de menores.
- **El alcance se recortó.** El *change* llegó a incluir el comando de puesta en marcha real, con el primer Admin y la primera temporada, y se sacó: ese Admin nace con el cambio de contraseña pendiente y, sin HU-UT-06, la API le responde 403 en todo. Un comando que deja un Admin que no puede operar no sirve. Quedó en el lote 2, junto a HU-UT-06.
- **El riesgo que abre el permiso quedó escrito, no escondido.** Con la URL externa en una notebook, la red de la semilla deja de proteger esa base. Para la base demo es aceptable, porque solo tiene datos inventados y la semilla igual se niega a sembrar dos veces. Para la del club no lo es, y quedaron dos reglas: la puesta en marcha corre en el servidor, nunca desde una notebook, y la URL externa de producción no se copia a ninguna máquina de desarrollo.
- **La revisión adversarial encontró un hueco anterior.** Con `PGHOSTADDR` definida, libpq conecta a otro host sin que la URL lo muestre, y la semilla pasaba la comprobación sin permiso y sin aviso. No se cerró en este *change*, porque cerrarlo es preguntarle a la conexión dónde terminó, una clase de problema más amplia. Quedó documentado en el readme y sumado al pendiente técnico de la semilla.

### **2.5. Seguridad**

Cubierto por el prompt 1 de la 2.1. Le corresponden dos ajustes: el límite de 5 MB y la cookie de renovación resuelta con un subdominio.

### **2.6. Tests**

El plan de la Entrega 1 salió del prompt 1 de la 2.1. En la Entrega 2 se reemplazó por los tests reales con el prompt 3 de la 2.4. Cómo se escriben los tests, con la separación entre `test-writer` e `implementer`, está en los prompts de la sección 7. En la Entrega 3 se sumaron los tests de punta a punta, con los dos prompts que siguen.

#### Entrega 3: tests de punta a punta

> El prompt 1 se armó en Claude (Cowork) revisando un plan previo y se corrió en Claude Code (CLI) sobre el repo. El prompt 2 es de Claude (Cowork), al preparar una segunda máquina. Se transcriben tal cual se escribieron.

**Prompt 1: Tres recorridos E2E, y revertir la decisión de no tenerlos**

*Contexto:* hasta la Entrega 2, `2-arquitectura-del-sistema.md` decía «Sin tests de punta a punta en el navegador»: las pantallas se probaban contra una API simulada y la API contra la base real, pero nada probaba la unión de las dos. Un primer plan de Claude ya traía lo central: Playwright en `e2e/`, tres recorridos, una base propia sembrada en cada corrida, un solo worker y cero reintentos. Antes de pedírselo a Claude Code lo pasé por una revisión en Cowork, que le sumó tres cosas: que fuera un *change* de OpenSpec como cualquier otro trabajo, que el test de sesión usara un token inválido en lugar de esperar las 8 horas del vencimiento, y que se guardara la traza solo cuando un test falla. Además señaló que el plan contradecía una decisión ya escrita en la arquitectura. Con eso armé el prompt:

```
/openspec-propose pruebas-e2e: change técnico, sin historias. Agrega tres tests E2E con Playwright en e2e/ (raíz):
1) camino de la plata: ingresar → alta de alumno → registrar cargo → registrar pago → saldo en cero;
2) permisos: un Profesor no llega a Cuenta corriente;
3) sesión: con un token inválido en localStorage, una pantalla protegida vuelve al ingreso.
Base propia escuelita_e2e recreada, migrada y sembrada en cada corrida, vía `python tasks.py e2e`. Un worker, cero reintentos, sin esperas fijas, trace retain-on-failure. Un job nuevo en ci.yml con Postgres, API y build servido.
Revierte la decisión «Sin tests de punta a punta en el navegador» de 2-arquitectura-del-sistema.md: el proposal tiene que justificarlo y las tasks tienen que actualizar ese documento, la tabla de comandos de CLAUDE.md y el readme.
No agrega comportamiento: los flujos ya están especificados en auth, cargos y cuenta-corriente.
```

*Respuesta clave:*

- El *change* salió sin deltas de spec, porque no agrega comportamiento. El `proposal.md` justifica la reversión con tres huecos: la unión entre el frontend y la API no se probaba, la configuración de dos orígenes de producción nunca se ejercitaba, y la verificación manual no se podía repetir.
- Quedó un paquete aparte en `e2e/` con su configuración y los tres recorridos, la tarea `python tasks.py e2e` y un tercer job en el CI. La tarea recrea la base con candados para no pisar otra, migra, siembra, compila el frontend como en producción, levanta la API y el build en puertos propios y los baja al terminar.
- Cada test se vio fallar por el motivo correcto: el agente rompió el código de producción a propósito, comprobó el rojo y revirtió.
- Durante la implementación encontró que la sección de tests de la arquitectura tenía los conteos de un *change* anterior (457 y 148 en lugar de 467 y 164).

*Ajuste humano / impacto:*

- **Un plan de la IA se revisa con otra mirada antes de ejecutarlo.** De las reglas del prompt, la base propia, un worker y cero reintentos ya venían en el plan. La revisión sumó el token inválido, sin el cual el test de sesión habría tardado 8 horas o habría tocado el código para acortar el vencimiento, y la traza al fallar, que es lo único que deja entender un fallo del CI cuando no hay reintentos.
- **Una decisión escrita no se contradice en silencio.** El proposal dice por qué se revierte y el mismo *change* actualiza la arquitectura, `CLAUDE.md` y el readme.
- **Se corrigió también el desfase heredado,** en lugar de sumar 3 a números que ya estaban mal. Quedaron 634 tests documentados con su detalle por capability.
- **Se vio el job en rojo en el CI, no solo en local.** Autoricé un commit que rompe un test a propósito (`2c731b1`) y su reversión (`23bdc79`): el job falló con el mensaje esperado y subió la traza, la captura y los logs como *artifact*. Es la misma regla de la sección 7: un guardarraíl que nunca se vio frenar nada no está probado.

---

**Prompt 2: 148 tests en rojo en una máquina nueva**

*Contexto:* para trabajar desde una segunda computadora cloné el repo y Claude preparó un script que instalaba Python, Node, OpenSpec y Docker con `winget`. Con `OpenJS.NodeJS.LTS`, winget instaló la LTS más reciente de Node. En esa máquina, `python tasks.py front-test` dio:

```
TypeError: Cannot read properties of undefined (reading 'clear')
 ❯ tests/preparar.ts:20:16
     18|   vi.unstubAllGlobals();
     19|   vi.restoreAllMocks();
     20|   localStorage.clear();
       |                ^
     21| });

 Test Files  20 failed (20)
      Tests  148 failed (148)

no pasó ningun test
```

*Respuesta clave:* el error no era del código. Las versiones recientes de Node traen un `localStorage` global propio, que sin un archivo configurado vale `undefined` y tapa al de jsdom. Se rompía la preparación común, así que caían los 148 tests a la vez. El CI no lo veía porque fija Node 22. La solución fue instalar Node 22, reinstalar `node_modules` y volver a instalar OpenSpec, porque los paquetes globales de npm quedan atados a la versión de Node.

*Ajuste humano / impacto:*

- **El entorno local tiene que coincidir con el CI.** La versión que manda es la del CI, y «la última LTS» no es una versión. Que todos los tests fallen por la misma línea apunta al entorno antes que al código.
- **Las dos máquinas trabajan sobre el mismo remoto, no sobre una carpeta sincronizada.** El repo vivía en OneDrive. Al pasar a dos computadoras se clonó fuera de la sincronización, porque `.git`, `.venv` y `node_modules` sincronizados entre dos máquinas corrompen el repositorio. Desde entonces el trabajo pasa de una máquina a la otra solo con `push` y `pull`, una rama por *change*.

---

### 3. Modelo de Datos

> Prompts de la sesión de Claude Code (CLI) sobre el repo. Se transcriben tal cual se escribieron.

**Prompt 1: Diseño del modelo completo, marcando qué entra en la Entrega 1**

*Contexto:* el backlog, las 3 historias con criterios y las aclaraciones ya estaban cerrados. Pedí el modelo de todo el sistema, no solo del MVP, y señalé las partes con más reglas de negocio.

```
Escribí docs/3-modelo-de-datos.md.

Diseñá el modelo de datos completo del sistema a partir de
docs/prd/aclaraciones-cliente.md (prevalece), el PRD y docs/product/historias-backlog.md.
No lo limites al MVP: el modelo tiene que cubrir todo el sistema, pero marcá qué tablas
entran en el lote de la Entrega 1 y cuáles quedan para después.

Incluí:
- Un diagrama entidad-relación en Mermaid, con claves primarias y foráneas, tipos de
  dato y cardinalidades.
- Debajo, una descripción de cada entidad: para qué existe, sus campos relevantes y las
  reglas que la afectan.

Prestá atención a estas partes, que son las que tienen enjundia:
- Temporada como entidad: la tarifa base, la tabla de descuentos, el % de canon, los
  tipos de cargo y los documentos obligatorios cuelgan de ella. Las inscripciones y las
  cuentas son por temporada; alumnos, familias, tutores y usuarios no.
- La tabla de descuentos tiene dos partes: un % por categoría para Día, Semana y
  Quincena, y un % por categoría y tramo de hijos para el Mes.
- El cargo guarda el resultado del cálculo (base, % aplicado, total), no solo la
  referencia al tarifario, porque el tarifario puede cambiar después y lo ya cobrado no
  se recalcula.
- Anulación de cobros: motivo, usuario y fecha.
- Cierre de canon: rango, cobros incluidos, monto, usuario y fecha. Un cierre abonado
  no se modifica.
- Trazabilidad de documentos: quién subió o modificó cada uno y cuándo.

Usá el stack de docs/architecture/documento-tecnico.md (PostgreSQL) para los tipos.
```

*Respuesta clave:* la IA armó un modelo de 24 tablas (17 en la Entrega 1). Algunas decisiones de diseño:
- la tabla de descuentos se partió en dos (`descuento_modalidad` sin el Mes y `descuento_mes` con el tramo), para que ningún cargo pueda encontrar dos porcentajes;
- el cargo copia la categoría y la cantidad de hijos que usó, y tiene un `CHECK` que verifica la cuenta;
- el cierre de canon se guarda recién al abonarlo y es inmutable, y cada cobro entra en un solo cierre.

Siguiendo la regla de `CLAUDE.md`, marcó 4 supuestos y los registró como preguntas abiertas: grupos por temporada, contactos de emergencia por familia, teléfono y DNI de las personas, y el efecto de una anulación en la tesorería. También detectó dos huecos en el alcance de la Entrega 1: nadie creaba la primera temporada, y los pagos se registraban sin su ingreso en tesorería.

*Ajuste humano / impacto:* ver el prompt 2.

---

**Prompt 2: Corrección de los supuestos y de los huecos del alcance**

*Contexto:* los cuatro supuestos del prompt 1 no eran preguntas para el cliente. Tres eran decisiones que yo podía tomar, y uno era de diseño puro.

```
Los cuatro supuestos no son preguntas para el cliente. Resolvelos así y sacalos de
preguntas abiertas:

1. Grupos por temporada: confirmado, el rango de fechas de nacimiento se corre cada año.
   Agregá que al abrir una temporada nueva se pueden copiar los grupos de la anterior.
   Va como decisión en aclaraciones-cliente.md.
2. Contactos de emergencia por familia: confirmado, los hermanos los comparten.
   Va como decisión en aclaraciones-cliente.md.
3. Teléfono obligatorio y DNI opcional: es una decisión de nullabilidad, no de negocio.
   Documentala en 3-modelo-de-datos.md con su justificación y NO la pongas en
   aclaraciones-cliente.md.
4. Egreso de anulación conservando el ingreso original: confirmado. Es el criterio
   contable correcto, un asiento registrado se contraasienta en vez de borrarse, y el
   neto queda en cero conservando la trazabilidad. Va como decisión en la sección 7 de
   aclaraciones-cliente.md (tesorería).

Los dos huecos del alcance:

a) Primera temporada: se crea en la puesta en marcha, junto con el primer Admin. Ya hay
   precedente: las aclaraciones dicen que el primer Admin se crea al instalar, y el
   backlog lo trata como tarea de puesta en marcha y no como historia. Configurarla
   (tarifas, descuentos, documentos obligatorios) ya está en el lote vía HU-TAR-01.
   "Abrir una temporada nueva", con la copia y los reseteos, sigue en Backlog.

b) Tesorería: creá la tabla tesoreria_movimiento en la migración de la Entrega 1 y que
   registrar un pago escriba su ingreso desde el primer día. La pantalla de tesorería
   sigue fuera del lote. Escribir la fila cuesta dos líneas; backfillear después con una
   migración es más riesgoso y más feo. Separá "el dato se registra" de "hay pantalla
   para verlo", y dejalo aclarado en el backlog.

Actualizá también el backlog y CLAUDE.md si algo de esto los contradice.
```

*Respuesta clave:* la IA hizo cuatro cambios:
- registró las tres decisiones de negocio en las aclaraciones (secciones 3, 4 y 7), y la nulabilidad la documentó solo en el modelo, con su justificación;
- pasó `tesoreria_movimiento` a la Entrega 1 (18 tablas) y movió HU-TES-01 al lote, separando el dato de la pantalla;
- dejó la primera temporada como tarea de puesta en marcha, en el modelo, en el backlog y en las aclaraciones;
- detectó que la regla 5 de `CLAUDE.md` contradecía el punto 3 y la ajustó.

*Ajuste humano / impacto:* la distinción entre "pregunta para el cliente" y "decisión de diseño" quedó como regla del proyecto en `CLAUDE.md`. Las reglas de negocio que faltan van como [SUPUESTO] a las aclaraciones. Las decisiones de diseño (nulabilidad, tipos, índices) se documentan con su justificación donde se toman. Esto evita llevarle al cliente preguntas que no le corresponden.

---

### 4. Especificación de la API

> Prompt de la sesión de Claude Code (CLI) sobre el repo. Se transcribe tal cual se escribió.

**Prompt 1: Tres endpoints en OpenAPI, uno por historia documentada**

*Contexto:* con el modelo de datos cerrado, pedí los endpoints de las 3 historias de `5-historias-de-usuario.md`, atados a los nombres del modelo y a los criterios de aceptación.

```
Escribí 4-especificaciones-de-la-api.md, en la raíz.

Documentá exactamente 3 endpoints en formato OpenAPI 3, uno por cada historia
documentada en 5-historias-de-usuario.md:
- Alta de alumno con familia, grupo y turno (HU-AF-01)
- Tomar asistencia de un grupo para un día y turno (HU-GA-04)
- Registrar un cargo con cálculo de tarifa y descuento (HU-CC-01)

Para cada uno: método y ruta, descripción, parámetros, esquema del request y del
response con ejemplos reales, y los códigos de error relevantes con su significado
(incluí los de permisos por rol y los de validación que salgan de los criterios de
aceptación).

Usá los nombres de entidades y campos de 3-modelo-de-datos.md, sin inventar otros.
El stack es FastAPI, así que seguí las convenciones REST que usaría FastAPI + Pydantic.
```

*Respuesta clave:* la IA documentó tres endpoints:
- `POST /api/v1/alumnos`: alta en una transacción, que exige categoría y tutor cuando la familia es nueva;
- `PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}`: idempotente, para que corregir no duplique registros;
- `POST /api/v1/cargos`: la API calcula y guarda el resultado.

Los ejemplos usan los datos de los escenarios. Hay una tabla que relaciona cada código de error con su escenario. La especificación se validó con Redocly CLI y es válida.

La IA marcó lo que no sale tal cual del modelo: el parámetro `simular=true`, para mostrar el cálculo antes de confirmar, y el campo `etiqueta` de la vista de familia. También señaló dos escenarios que no se pueden mostrar con solo estos 3 endpoints: el grupo sin alumnos (es un `GET`) y el saldo de la familia (está en la cuenta corriente).

*Ajuste humano / impacto:* revisé la especificación generada e hice tres ajustes sobre el contrato:
- **`simular=true`: se mantuvo, pero documentado explícitamente como concesión** al límite de 3 endpoints de la entrega. Sin ese límite sería `GET /cargos/simulacion`. La previsualización no se puede resolver en el frontend, porque el precio no puede venir del cliente: la tarifa, el descuento y la cantidad de hijos se resuelven siempre en el servidor.
- **Se agregó el saldo de la familia a la respuesta de `POST /cargos`** (`saldo_pendiente`). Así el escenario 1 de HU-CC-01 ("el saldo de la familia aumenta") se verifica en la misma respuesta, sin gastar un cuarto endpoint en la cuenta corriente. Para que el modelo y la API digan lo mismo, se nombraron las columnas de las vistas en `3-modelo-de-datos.md` (`v_cuenta_corriente.saldo_pendiente`, `v_familia_etiqueta.etiqueta`).
- **Se quitó `contacto_emergencia` de la respuesta del alta.** En esta versión nunca puede ser true, así que ensuciaba el contrato. Vuelve cuando llegue HU-AF-08.

Además, **no forcé el escenario 4 de la asistencia** (abrir la lista de un grupo sin alumnos) contra estos endpoints. El `422` por lista vacía del `PUT` queda como validación propia del cuerpo. En la especificación quedó aclarado que ese escenario se verifica contra un `GET` de la lista, que no está entre los 3 documentados.

---

### 5. Historias de Usuario

> Prompts de la sesión de Claude Code (CLI) sobre el repo. Se transcriben tal cual se escribieron (extractos marcados con [...]).

**Prompt 1: La IA como Product Owner, con preguntas antes de generar**

*Contexto:* el PRD y las aclaraciones del cliente ya estaban cerrados. Pedí el backlog completo, prohibiendo inventar funcionalidad y obligando a la IA a preguntar antes de asumir.

```
Actuá como Product Owner. Antes de generar nada, preguntame lo que necesites para
no asumir de más.

Con estas fuentes —y solo estas, no inventes funcionalidad que no esté ahí—:
- docs/prd/prd-escuelita-de-verano.md
- docs/prd/aclaraciones-cliente.md
- docs/architecture/documento-tecnico.md (para saber qué es técnicamente viable con
  el stack elegido, no para sacar historias de ahí)

Generá una lista de historias de usuario candidatas que cubran el sistema, en formato
"Como [rol] quiero [acción] para [beneficio]". Agrupalas por módulo del PRD (alumnos
y familias, documentación, grupos y asistencia, tarifario, cuenta corriente, tesorería,
canon). No prioricés ni redactes criterios de aceptación todavía — eso lo hacemos
después con las 3 que elijamos. Para cada historia, una línea indicando qué módulo del
PRD la sustenta.
```

*Respuesta clave:* antes de generar, la IA leyó el documento técnico y marcó tres diferencias con las aclaraciones: el tamaño máximo de archivo (10 MB contra 5 MB), el borrado de documentos al cerrar la temporada, y la anulación de cobros, que no estaba en las fuentes. Después hizo 4 preguntas:
- qué hacer con Usuarios y Temporadas, que faltaban en mi lista de módulos;
- con qué nivel de detalle armar las historias;
- cómo redactar las historias que comparten varios roles;
- dónde guardar la lista.

*Ajuste humano / impacto:* sumé el grupo "Usuarios y temporadas" y cambié el pedido. En lugar de candidatas sin prioridad, pedí el backlog completo con prioridad MVP-Entrega1 / Should-have / Backlog. Además lo mandé a `docs/product/historias-backlog.md`, no a `docs/prd/`, porque las historias son un artefacto derivado y no parte del PRD. Resultado: 42 historias, cada una con su sustento.

---

**Prompt 2: Recorte del MVP sin datos semilla**

*Contexto:* la IA había propuesto 3 bloques para el MVP (alta de alumno, asistencia y cobro), cargando usuarios y grupos como datos semilla.

```
no quiero cargar datos semilla. Hagamos la US de usuarios, ya que convive con el login y hagamos el abm de grupos y profesores, así con eso ya podemos registrar los alumnos. la categoria de la familia se carga al momento de cargar el 1er hijo de la flia. y el de asistencia tmb sera mvp 1
```

*Respuesta clave:* la IA rearmó el MVP como una cadena de bloques, donde cada uno habilita al siguiente: usuarios y login, grupos y profesores, alta de alumno y asistencia. Avisó dos cosas: que la consigna pide 3 historias y quedaban 4 bloques, y que la baja de grupos no figuraba en las fuentes.

*Ajuste humano / impacto:*
- Edité el backlog por fuera de la IA. Volví a meter el cobro en el lote y separé dos conceptos: el **lote de desarrollo** (lo que se construye) y las **3 historias documentadas** (lo que pide la consigna). Dejé la baja de grupos como propuesta pendiente.
- Cuando la IA releyó el archivo, detectó que el cobro sin datos semilla necesitaba el tarifario configurado. Entonces subí HU-TAR-01 a HU-TAR-04 al lote como un bloque propio.
- El lote terminó en 18 historias de un backlog de 46.

---

**Prompt 3: Criterios de aceptación de las 3 historias documentadas**

*Contexto:* con el lote cerrado, pedí los criterios solo para las 3 historias elegidas, con las dependencias como precondiciones.

```
[...] Escribí los criterios de aceptación de las 3 historias seleccionadas para
5-historias-de-usuario.md:

1. HU-AF-01 — registrar un alumno con familia, grupo y turno
2. HU-GA-04 — tomar asistencia por grupo, día y turno
3. HU-CC-01 — registrar un cargo con cálculo de tarifa y descuento

Para cada una:
- Escenarios en formato Dado / Cuando / Entonces.
- Cubrí el camino feliz, al menos un caso límite y al menos uno de permisos o error.
- Las precondiciones que dependen de otras historias van en el "Dado" (por ejemplo:
  "Dado que el administrador cargó la tarifa base del turno mañana y la tabla de
  descuentos"). Esas historias no hace falta documentarlas.

Fuentes: docs/prd/aclaraciones-cliente.md (prevalece) y el PRD. Para HU-CC-01 mirá
especialmente la sección 5 de las aclaraciones: la tarifa base sale del turno y la
modalidad, se aplica un único porcentaje que nunca se acumula, y la cantidad de hijos
solo interviene cuando la modalidad es Mes.

Escribilas en docs/product/historias-backlog.md junto a cada historia, y copiá las tres
completas a 5-historias-de-usuario.md con el formato del template del repo. En ese
archivo agregá una línea aclarando que son el recorte de MVP de un backlog de 42
historias, con el link al backlog.
```

*Respuesta clave:* la IA escribió 7, 7 y 11 escenarios. HU-CC-01 tiene un contexto común con la tarifa base y la tabla de descuentos de ejemplo, y los montos de cada escenario están verificados (por ejemplo, 15 % sobre $ 100.000 da $ 85.000). Las aclaraciones cambiaron en disco mientras trabajaba; las releyó e incorporó el checklist de documentos, la regla del hijo que se suma a mitad de temporada y la temporada anterior solo para consulta. Marcó 2 supuestos: los datos mínimos del alta y qué hijos cuentan para el tramo del Mes.

*Ajuste humano / impacto:* rechacé los dos supuestos.
- El conteo de hijos ya lo define el PRD: "contando solo a los hermanos anotados en ese turno".
- El alta **exige al menos un tutor**. Sin tutor no hay categoría, sin categoría no se puede calcular ningún cargo, y un chico no puede quedar inscripto sin nadie autorizado a retirarlo. Lo registré como decisión en la sección 3 de las aclaraciones, y la IA ajustó los escenarios 1 y 7 de HU-AF-01.

---

### 6. Tickets de Trabajo

> Prompt de la sesión de Claude Code (CLI) sobre el repo. Se transcribe tal cual se escribió.

**Prompt 1: Corte vertical de HU-CC-01 en tres tickets**

*Contexto:* el template pide un ticket de base de datos, uno de backend y uno de frontend. En lugar de tres tickets sueltos, pedí que fueran las tres capas de una misma historia: la que concentra las reglas de negocio. Dejé fijados los constraints de la base y los casos de test mínimos.

```
Escribí 6-tickets-de-trabajo.md, en la raíz.

Son exactamente 3 tickets —uno de base de datos, uno de backend y uno de frontend— y
los tres son el corte vertical de HU-CC-01 (registrar un cargo con cálculo de tarifa y
descuento). Elegimos esa historia porque es la que concentra las reglas de negocio, así
que es la que mejor se ve partida en capas.

Ticket de base de datos: las tablas que hacen falta para el cargo (tarifa_base,
descuento_modalidad, descuento_mes, periodo_cobro, tipo_cargo, cargo), la migración de
Alembic, y los constraints que sostienen las reglas: el CHECK que verifica que el total
coincida con base y porcentaje, y la foránea compuesta que impide asociar un período de
otra modalidad.

Ticket de backend: POST /api/v1/cargos con el motor de cálculo, incluido simular=true.
Listá los casos de test en pytest que tiene que cubrir, como mínimo: socio con 1 hijo al
mes, no socio con 3 hijos al mes, empleado por día (donde la cantidad de hijos no
interviene), el tramo de 4 o más aplicado a todos los hijos, y los rechazos por rol y
por familia o inscripción inexistente.

Ticket de frontend: la pantalla de registrar cobro en React, con el desglose del cálculo
usando la simulación antes de confirmar.

Cada ticket con: título, descripción, criterios de aceptación técnicos, dependencias
entre ellos, estimación, y las referencias concretas a la historia, a las tablas de
3-modelo-de-datos.md y al endpoint de 4-especificaciones-de-la-api.md.
```

*Respuesta clave:* la IA armó tres tickets encadenados (base de datos → backend → frontend), con un diagrama de dependencias y una estimación total de 22 horas:
- **TK-01, base de datos (4 h):** la migración de Alembic con ida y vuelta; el `CHECK` del total; la FK compuesta con `MATCH SIMPLE`, explicando por qué la Preinscripción y el Día no la violan; los `CHECK` de forma del cargo; y tests de constraints contra PostgreSQL.
- **TK-02, backend (10 h):** el motor de cálculo como función pura, con redondeo `Decimal` igual al de PostgreSQL para que el `CHECK` nunca rechace un cargo calculado por la API; `simular=true` sin escribir nada; y 16 casos de test, los 7 pedidos más 9 que salen de los escenarios de HU-CC-01.
- **TK-03, frontend (8 h):** el formulario según el tipo de cargo y la modalidad, el desglose con la simulación, la confirmación con el saldo y el manejo de errores. El frontend nunca calcula ni envía montos.

*Ajuste humano / impacto:* la revisión dejó tres cosas, y las tres se aceptaron:
- **Se incorporaron la tabla `pago` y la vista `v_cuenta_corriente` al ticket de base de datos,** aunque no estaban en la lista pedida. El `saldo_pendiente` que devuelve `POST /cargos` depende de ellas. `pago` se crea solo con su estructura; su endpoint sigue siendo de HU-CC-02.
- **El caso "familia inexistente" se prueba con un `alumno_id` inexistente.** La API no recibe `familia_id`: la familia se deriva del alumno, así que a nivel API ese es el caso real.
- **Quedó anotada como dependencia del ticket de frontend la falta de endpoints de lectura** para llenar los selectores (alumnos con sus inscripciones, tipos de cargo y períodos). No entran entre los 3 endpoints documentados por el límite de la entrega, así que hay que acordarlos con el backend o con el ticket de lectura que corresponda del lote.

---

### 7. Pull Requests

> Prompts de las sesiones de Claude Code (CLI) sobre el repo, durante la construcción del lote 1. Se transcriben tal cual se escribieron.
>
> El lote se construyó en ocho *changes* de OpenSpec, uno por rama y por pull request. Cada uno siguió el mismo ciclo: `openspec-propose` → revisión humana de la propuesta y la spec → `openspec-apply-change` → `openspec-verify` → `openspec-archive`, que funde el delta en la spec vigente. Dentro del *apply*, dos subagentes con permisos distintos: **`test-writer`**, que escribe los tests desde la spec y tiene prohibido leer la implementación, y **`implementer`**, que escribe el código hasta ponerlos en verde y tiene prohibido tocar los tests. Entre uno y otro, los tests se congelan por hash (`git ls-files -s`) y al final se comprueba que el hash no cambió. Antes de cerrar cada change corre un **`adversarial-reviewer`** que busca lo que está mal, no lo que está bien.
>
> Sobre eso, dos capas automáticas en cada pull request: el *workflow* de integración continua (`ruff`, `mypy`, `pytest`, tests y build del frontend, y el ida y vuelta de las migraciones) y una revisión con `claude-code-action` configurada en `.github/workflows/revisor.yml`.
>
> Los tres prompts que siguen son los que más cambiaron el resultado: uno arregla la base sobre la que corren todos los tests, otro arregla cómo se verifica que un test puede fallar, y el tercero corrige a la IA sobre un riesgo de seguridad que una regla del cliente no había visto.

**Prompt 1: Un conftest que dejaba la suite en verde con el bloqueo roto**

*Contexto:* en el primer change, `auth-ingreso` (HU-UT-01), el agente verificó el rojo de los tests del login y señaló dos huecos. Uno era un *Scenario* que se aprobaba con una constante. El otro llevó a descubrir que el `conftest.py` le daba a la API la misma sesión de base de datos que al test: un servicio que confirmaba la transacción y uno que no eran indistinguibles. Lo corregí a mano en la rama y se lo pasé al agente con este prompt.

```
Los dos huecos son reales y el 2 es un bug mío en el conftest, no tuyo.
Ya actualicé backend/tests/conftest.py en tu rama, sin commitear. Hacé
git diff backend/tests/conftest.py para verlo.

Qué cambió y por qué: la API ahora recibe su PROPIA sesión, abierta y
cerrada en cada petición sobre la misma conexión, en lugar de compartir la
del test. Verificado contra Postgres en los dos sentidos: con el conftest
viejo, un endpoint que incrementa un contador y lanza 401 sin commitear
dejaba el test en verde (el test leía 3 en lugar de 2); con el nuevo, ese
test falla. En producción el incremento se habría perdido y el bloqueo por
intentos nunca se habría activado, con la suite en verde.

Además el cliente de pruebas expira los objetos del test después de cada
petición: un objeto del ORM cargado antes devolvía el valor viejo, así que
un test que afirma que un contador NO cambió pasaba aunque la API lo
hubiera incrementado.

Ahora, en este orden:

1. Corregí el hueco 1 en la spec con /openspec-update-change: en el Scenario
   «Ingresa con el cambio pendiente», el GIVEN tiene que incluir
   intentos_fallidos en 2, para que el AND de que quede en 0 pruebe algo.
   Como está, se aprueba con una constante. Y revisá si algún otro Scenario
   tiene el mismo problema de arrancar en el valor que después afirma.

2. Volvé a invocar al test-writer SOLO para reescribir ese test según el
   GIVEN nuevo. No le des acceso a nada más de lo que ya tenía.

3. Volvé a verificar el rojo con el conftest nuevo y el test corregido:
   pegame la última línea del pytest y confirmame que siguen fallando los
   16 por 404 y que el control positivo está entre ellos. Si alguno falla
   por otra razón, el conftest nuevo rompió algo y quiero saberlo.

4. Recién ahí congelá los tests y seguí con el implementer.

Y una advertencia para cuando implementes: el test del contador ahora SÍ
exige el commit antes del 401 que dice el design. Si el servicio no
commitea, ese test falla. Eso es correcto, no lo trabajes alrededor.
```

*Respuesta clave:* el *Scenario* se corrigió en la spec, el test-writer reescribió solo ese test, y con el conftest nuevo los 15 *Scenarios* fallaron por 404, como correspondía. Se congelaron los tests junto con `conftest.py`, y el implementer los puso en verde con el `commit()` antes del 401 (31 tests en verde, huella intacta).

*Ajuste humano / impacto:* fue el peor defecto del proyecto, y estaba en la base de las pruebas, no en el código. Con el conftest viejo, la suite quedaba en verde aunque el contador de intentos fallidos nunca se guardara: en producción, el bloqueo tras 5 intentos no se habría activado nunca. Salió de **leer los tests, no solo mirar que estuvieran en rojo**. Desde ahí la skill `backend-feature` congela `conftest.py` junto con los tests de la capability y exige leer los tests buscando aserciones que se aprueben con una constante.

---

**Prompt 2: Un test en rojo que no podía fallar**

*Contexto:* el `adversarial-reviewer` del change de asistencia encontró que la función que calcula «hoy» en el navegador estaba bien escrita, pero que ningún test la protegía: los tests fijaban la hora a las 10:00, cuando la fecha local y la UTC coinciden. Si alguien cambiaba `hoyLocal()` por `toISOString()`, todo seguía en verde. En producción, un profesor abriendo la pantalla a las 21:30 habría guardado la asistencia en el día siguiente, sin aviso.

```
Avanzá con los dos arreglos, reabriendo el change. Y las preguntas están
decididas, no las dejes como supuesto.

1) HUSO HORARIO
Fijá TZ=America/Argentina/Buenos_Aires para los tests del frontend, en
vite.config.ts, en tasks.py y en el workflow del CI: si queda en un solo
lugar, local y CI se separan. Pasá fijarHoy a las 21:30.

Pero antes de darlo por bueno, vas a verlo fallar a propósito: cambiá
hoyLocal() por toISOString(), corré los tests, confirmá que se ponen en
rojo, y revertí. Si siguen en verde, TZ no quedó puesto donde hace falta
y hay que buscar otro lugar. Pegame la salida del rojo.

[…]
```

*(Fragmento: el mensaje seguía con cuatro puntos más sobre el mismo change —el guardado que pisaba otra fecha, no permitir desmarcar una asistencia ya guardada, registrar el autor solo en las marcas que cambiaron y un test de permisos para el profesor—. Se transcribe solo el punto del huso horario, que es el que se comenta acá.)*

*Respuesta clave:* la zona horaria quedó fijada en los tres lugares, la hora de prueba pasó a las 21:30 —cuando en Argentina es el día 5 y en UTC ya es el 6— y el agente devolvió la salida en rojo de la rotura deliberada antes de revertirla.

*Ajuste humano / impacto:* **un guardarraíl que nunca se vio frenar nada no está probado.** No alcanzaba con poner la variable: había que romper el código a propósito y comprobar que el test lo notaba. En este mismo proyecto ya había pasado lo contrario tres veces —un hook de formato que llamaba a un ejecutable inexistente y nunca corrió, una integración continua que no habría pasado nunca y todavía no había corrido, y un revisor automático que se salteaba en silencio—, y las tres se descubrieron usándolas, no leyéndolas. El mismo criterio dejó dos reglas más en el repo: el rojo se verifica leyendo *el motivo* de cada fallo, porque un `TypeError` dentro del test no es rojo sino un test roto; y los plazos de los tests llevan anotado el número medido y la fecha, para que un valor mágico no quede sin explicación.

---

**Prompt 3: Un riesgo de seguridad que la regla del cliente no había visto**

*Contexto:* en el mismo change `auth-ingreso`, el agente presentó la propuesta, la spec y el design del login. Antes de aplicarlos los revisé y devolví seis ajustes. El primero es el que importa acá: un riesgo que ni la IA ni la aclaración del cliente sobre el bloqueo (Acl. 9) habían evaluado.

```
Seis ajustes antes de aplicar. Ninguno toca el proposal salvo el 1.

1. RIESGO que no estaba evaluado: el bloqueo se puede disparar desde
   afuera. Los usernames son predecibles (inicial + apellido), el 403
   confirma que el usuario existe, y solo un Admin desbloquea. Cualquiera
   con internet puede dejar afuera a quien quiera, y enumerar usernames
   bloqueándolos.
   - En design.md, sección "Riesgos": escribilo, con la mitigación
     deferida a HU-UT-08 (límite por IP y/o desbloqueo automático).
   - En docs/prd/aclaraciones-cliente.md, pregunta abierta: ¿una cuenta
     bloqueada se desbloquea sola después de un rato, o sigue dependiendo
     del Admin sabiendo que cualquiera puede bloquearla desde internet?
     Acl. 9 dice lo segundo, pero se decidió sin esto a la vista.
   - En proposal.md, fuera de alcance: la mitigación del bloqueo remoto.

2. Mové el Scenario "El token del ingreso sirve para identificarse" del
   requirement "Ingreso con usuario y contraseña" al de "Identificación
   del usuario actual por token". Como está, la tarea 1 tiene que hacerlo
   pasar pero llama a /auth/yo, que se construye en la tarea 2: la tarea 1
   no puede cerrar en verde.

3. GET /api/v1/auth/yo queda exento del 403 por cambio pendiente, igual
   que el cambio de contraseña: el frontend lo necesita para saber quién
   está logueado al recargar, y no expone nada sensible. El Scenario "Con
   el cambio pendiente no puede hacer nada más" se reescribe contra el
   router de sonda de la tarea 3. Agregá un Scenario: con el cambio
   pendiente, /yo responde 200 con debe_cambiar_password en true.

4. En design.md, invariante explícito: el username se guarda siempre en
   minúsculas y el login busca por igualdad exacta contra la entrada ya
   normalizada. El CHECK (username = lower(username)) lo agrega HU-UT-02;
   mientras tanto la semilla lo respeta. Si la base tuviera JPerez, el
   login fallaría en silencio.

5. En el requirement "Identificación del usuario actual por token",
   reemplazá "si el usuario no existe" por "si el sub del token no
   corresponde a ningún usuario" y agregale su Scenario. Como está, es una
   cláusula inalcanzable sin test.

6. Renombrá require_rol a exigir_rol, en el change y en
   docs/architecture/documento-tecnico.md. La regla 8 de CLAUDE.md pide
   todo en castellano y require_rol es mitad inglés.

Mostrame el diff de la spec y del design, y pará.
```

*Respuesta clave:* el riesgo quedó escrito en el design del change, con la mitigación diferida a HU-UT-08, y como pregunta abierta en `aclaraciones-cliente.md` («Desbloqueo de una cuenta bloqueada»). La spec se reordenó para que cada tarea pudiera cerrar en verde por sí sola, y `require_rol` pasó a `exigir_rol` en todo el repo.

*Ajuste humano / impacto:* tres cosas que la IA no iba a resolver sola.

- **Una regla del cliente puede haberse decidido sin ver un riesgo.** Acl. 9 dice que una cuenta bloqueada queda así hasta que un Admin le blanquee la contraseña. Con usernames predecibles y el ingreso abierto a internet, eso deja a cualquiera bloquear al staff entero, incluidos todos los Admin. No se cambió la regla por cuenta propia: se dejó la pregunta registrada para el cliente y, mientras no conteste, rige la Acl. 9.
- **Un Scenario que una tarea no puede hacer pasar sola rompe el ciclo.** Si el test de la tarea 1 depende de un endpoint de la tarea 2, la tarea 1 nunca cierra en verde, y la tentación es aflojar el test.
- **Un «queda para otro change» sin historia que lo reciba se pierde.** En la ronda siguiente apareció que HU-UT-08 describía el bloqueo que ya estaba construyendo HU-UT-01, así que nadie era dueño de la mitigación. Se reescribió HU-UT-08 como la mitigación y se marcó que no bloquea las entregas académicas, pero sí la salida a producción con datos reales.
