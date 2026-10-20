> Detalla en esta sección los prompts principales utilizados durante la creación del proyecto, que justifiquen el uso de asistentes de código en todas las fases del ciclo de vida del desarrollo. Esperamos un máximo de 3 por sección, principalmente los de creación inicial o  los de corrección o adición de funcionalidades que consideres más relevantes.
Puedes añadir adicionalmente la conversación completa como link o archivo adjunto si así lo consideras


## Índice

1. [Descripción general del producto](1-descripcion-general-del-producto.md)
2. [Arquitectura del sistema](2-arquitectura-del-sistema.md)
3. [Modelo de datos](3-modelo-de-datos.md)
4. [Especificación de la API](4-especificaciones-de-la-api.md)
5. [Historias de usuario](5-historias-de-usuario.md)
6. [Tickets de trabajo](6-tickets-de-trabajo.md)
7. [Pull requests](7-pull-requests.md)

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

### **2.1. Diagrama de arquitectura:**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

### **2.2. Descripción de componentes principales:**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

### **2.3. Descripción de alto nivel del proyecto y estructura de ficheros**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

### **2.4. Infraestructura y despliegue**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

### **2.5. Seguridad**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

### **2.6. Tests**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

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

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

---

### 7. Pull Requests

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**
