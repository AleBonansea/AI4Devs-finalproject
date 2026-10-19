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

> Prompts extraídos de la sesión de relevamiento en Claude (chat) donde se armó el PRD. Se transcriben tal cual se escribieron (extractos marcados con [...]).

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

**Prompt 2: Decisiones después de que la IA cuestionara el alcance**

*Contexto:* la IA objetó tres puntos de mis respuestas: que todos los roles pudieran inscribir, que la "cuenta corriente" mezclara cobros a familias con sueldos y gastos, y el criterio de cálculo del canon.

*Respuesta clave (la objeción de la IA):*
> "Sospecho que en realidad querés decir 'admin y coordinador pueden inscribir', y el profe no."
> "Eso ya no es una cuenta corriente [...] es una tesorería completa: ingresos (cobros) y egresos (sueldos, gastos varios) con un saldo general."

```
El Admin y coordinador registra profes, grupos y alumnos.
Profe, solo puede registrar alumnos y cargarles la documentacion, mas todo lo
relacionado a la actividad, faltas etc.
si el modulo de tesoreria que quede separado como propones... y la cuenta corriente
familiar.
el canon es por cada alumno que haya pagado.
turnos.. quizas puede tener mas de un profe, le demos esa posibilidad, seria solo darle
acceso al profe para que gestione x grupo... quizas tmb pueda tener un grupo a la mañana
y otro a la tarde... aunque la logica seria q sea siempre el mismo grupo, pero no lo
limitemos.
por ahora la temporada arranca 100% de cero.
si, ya lo mencione mas arriba la diferencia de carga de profes y grupos... solo no puede
ver la parte contable.
```

*Ajuste humano / impacto:* acepté separar cuenta corriente familiar y tesorería general, pero no acepté sacarle al profesor la inscripción: sigue pudiendo inscribir (después lo limité a sus propios grupos). Quedaron definidos la relación muchos-a-muchos entre profesores y grupos, el coordinador como admin sin la parte contable y la temporada que arranca de cero. En la vuelta siguiente la IA recomendó categorizar los egresos y sumar auditoría de cambios a la v1, y descarté las dos para mantener la v1 simple (solo se registra quién abona el canon).

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

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

---

### 4. Especificación de la API

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

---

### 5. Historias de Usuario

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

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
