# Backlog de historias de usuario — Escuelita de Verano

Artefacto de trabajo derivado de las fuentes. **No** es parte del PRD.

**Fuentes:**
- `docs/prd/prd-escuelita-de-verano.md` (en el campo *Sustento*, "PRD" seguido de la sección).
- `docs/prd/aclaraciones-cliente.md` ("Acl." seguido del número de sección). Prevalece sobre el PRD.
- `docs/architecture/documento-tecnico.md`: se usó solo para verificar que cada historia sea viable técnicamente. No se sacó ninguna historia de ahí.

**Criterios de aceptación:** se escriben lote por lote, justo antes de programar cada lote — no para todo el backlog de una. Así ninguna historia queda con criterios escritos sobre definiciones que todavía pueden cambiar.

**Roles:** cuando varios roles hacen lo mismo, se nombran juntos en una sola historia. Los matices de permisos se definen en los criterios de aceptación. "Staff" significa Admin, Coordinador o Profesor; el Profesor siempre solo sobre sus grupos.

**Prioridades:**
- **MVP-Entrega1**: forma parte del primer lote de desarrollo (18 historias, ver «Alcance de la Entrega 1»). Tres de ellas, además, se documentan con criterios en `5-historias-de-usuario.md` para cumplir con la consigna del curso.
- **Should-have**: valiosa, pero no imprescindible para demostrar el sistema en esta entrega.
- **Backlog**: necesaria para el sistema en producción, pero fuera de esta entrega académica.

---

## 1. Alumnos y familias

**HU-AF-01** · `MVP-Entrega1`
Como staff, quiero registrar un alumno con sus datos mínimos (incluido al menos un tutor) y asignarlo a un grupo y turno, para tenerlo inscripto desde el primer contacto y completar la documentación más adelante.
*Sustento:* PRD «Alumnos, tutores y documentación» (ficha progresiva; la inscripción la hace el staff); PRD «Roles y permisos»; Acl. 3, 4, 8.

*Criterios de aceptación* (incluyen la creación o elección de familia, la categoría y el tutor obligatorio, que se apoyan en HU-AF-02, HU-AF-03 y HU-AF-04):

Datos mínimos del alta (Acl. 3): nombre, apellido y fecha de nacimiento del alumno; familia (nueva, con su categoría, o existente); al menos un tutor; y grupo y turno. La documentación no forma parte del mínimo.

**Escenario 1 — Primer hijo: se crea la familia** (camino feliz)
- **Dado** que existe el grupo «Delfines», turno mañana, para nacidos entre el 01/01/2018 y el 31/12/2019 en la temporada vigente
- **Y** que un Coordinador inició sesión
- **Cuando** registra a Juan Pérez, nacido el 10/03/2018, elige "crear familia nueva" con categoría empleado, carga como tutora a María Pérez y lo inscribe en «Delfines», turno mañana
- **Entonces** Juan queda inscripto en «Delfines», turno mañana, en la temporada vigente
- **Y** se crea la familia «Pérez – Juan», con categoría empleado y una cuenta corriente única
- **Y** María Pérez queda como tutora de la familia y autorizada a retirar a Juan
- **Y** el alta no exige documentación: la ficha se completa después

**Escenario 2 — Segundo hijo: se elige la familia existente** (camino feliz)
- **Dado** que existe la familia «Pérez – Juan», categoría empleado, con Juan nacido el 10/03/2018 y María Pérez como tutora
- **Y** que existe el grupo «Tiburones», turno mañana, para nacidos entre el 01/01/2015 y el 31/12/2017
- **Cuando** un Admin registra a Ana Pérez, nacida el 05/07/2016, elige la familia «Pérez – Juan» y la inscribe en «Tiburones», turno mañana
- **Entonces** Ana queda en la misma familia y comparte su cuenta corriente
- **Y** no se le pide categoría: la familia sigue siendo empleado
- **Y** Ana queda cubierta por la tutora de la familia, María Pérez
- **Y** la etiqueta de la familia pasa a «Pérez – Ana», porque Ana es la hija mayor, sin que cambie el ID interno de la familia

**Escenario 3 — Medio hermano con otro apellido** (caso límite)
- **Dado** que existe la familia «Pérez – Ana»
- **Cuando** se registra a Tomás Gómez, nacido el 20/11/2019, eligiendo esa familia
- **Entonces** Tomás queda en la familia «Pérez – Ana»
- **Y** la etiqueta no cambia, porque Tomás no es el hijo mayor

**Escenario 4 — Grupo fuera del rango de nacimiento** (caso límite)
- **Dado** que Lucía nació el 02/02/2018 y que el grupo «Tiburones» es para nacidos entre 2015 y 2017
- **Cuando** un Coordinador la inscribe en «Tiburones», turno mañana
- **Entonces** la inscripción se registra: el rango de nacimiento orienta la sugerencia de grupo, pero no impide elegir otro

**Escenario 5 — Profesor fuera de sus grupos** (permisos)
- **Dado** que un Profesor tiene asignado solo «Delfines», turno mañana
- **Cuando** registra un alumno
- **Entonces** solo puede elegir «Delfines», turno mañana
- **Y** si la solicitud llega con otro grupo (por ejemplo, llamando a la API directamente), se rechaza y no se crean ni el alumno ni la familia

**Escenario 6 — Profesor con una familia existente** (permisos)
- **Dado** que un Profesor inició sesión y que la familia «Pérez – Ana» es categoría empleado
- **Cuando** registra un nuevo hijo de esa familia en uno de sus grupos
- **Entonces** el alumno se registra en la familia
- **Y** el Profesor no puede cambiar la categoría de la familia, porque eso lo hace solo un Admin

**Escenario 7 — Faltan datos mínimos** (error)
- **Dado** que un Coordinador está registrando un alumno
- **Cuando** intenta guardar sin fecha de nacimiento, sin grupo y turno, sin familia, sin categoría (si la familia es nueva) o sin ningún tutor
- **Entonces** el alumno no se registra
- **Y** el sistema indica qué dato falta

**HU-AF-02** · `MVP-Entrega1`
Como staff, quiero que al cargar el primer hijo se cree su familia, y que al cargar los siguientes pueda elegir la familia existente (identificada como "Apellido – Hijo mayor"), para que todos los hijos compartan una sola cuenta corriente.
*Sustento:* PRD «Tarifario y cuenta corriente familiar»; Acl. 1.

**HU-AF-03** · `MVP-Entrega1`
Como staff, quiero cargar las personas autorizadas a retirar al alumno (incluidos los tutores, de los que hace falta al menos uno), y reutilizar una persona ya cargada en otra familia, para saber quién puede llevarse a cada chico.
*Sustento:* PRD «Alumnos, tutores y documentación» (Tutores); Acl. 3.

**HU-AF-04** · `MVP-Entrega1`
Como staff, quiero asignar la categoría de la familia (socio, empleado o no socio) al cargar el primer hijo, cuando se crea la familia, siguiendo la prioridad socio > empleado > no socio, para que después se apliquen los descuentos que corresponden.
*Sustento:* PRD «Alumnos, tutores y documentación» (Categoría); Acl. 2.

**HU-AF-05** · `Backlog`
Como Admin, quiero modificar la categoría de una familia ya asignada, para corregir errores de carga.
*Sustento:* Acl. 2, 9.

**HU-AF-06** · `Should-have`
Como staff, quiero completar y editar la ficha del alumno (datos personales y datos sensibles como alergias y condiciones médicas) a medida que la familia entrega la información, para tener la ficha al día.
*Sustento:* PRD «Alumnos, tutores y documentación» (Ficha del alumno).

**HU-AF-07** · `Should-have`
Como staff, quiero registrar que el tutor dio su consentimiento para cargar datos médicos, para cumplir con la Ley 25.326 sobre datos sensibles.
*Sustento:* Acl. 11 (Consentimiento).

**HU-AF-08** · `Should-have`
Como staff, quiero cargar los contactos de emergencia del alumno en una lista separada de las personas autorizadas, para saber a quién llamar ante una urgencia.
*Sustento:* PRD «Alumnos, tutores y documentación» (Tutores); Acl. 3.

**HU-AF-09** · `Should-have`
Como staff, quiero inscribir a un alumno en los dos turnos como inscripciones independientes, para que la asistencia y el cobro se manejen por separado en cada turno.
*Sustento:* PRD «Grupos, turnos y asistencia».

**HU-AF-10** · `Should-have`
Como Profesor, quiero ver las alergias y condiciones médicas de los alumnos de mis grupos (y no las de los hijos de la misma familia que estén en otros grupos), para actuar rápido ante una emergencia.
*Sustento:* Acl. 9, 11 (Acceso por necesidad).

**HU-AF-11** · `Backlog`
Como staff, quiero inscribir en los grupos de la nueva temporada a un alumno que vuelve, reutilizando su ficha, su familia y sus tutores, para no cargar todo de nuevo. Las inscripciones a grupos se hacen de nuevo en cada temporada.
*Sustento:* Acl. 10.

## 2. Documentación

**HU-DOC-01** · `Should-have`
Como staff, quiero adjuntar documentos a la ficha del alumno como archivos privados (los obligatorios de la temporada y otros certificados no obligatorios), para tener toda la documentación en un solo lugar.
*Sustento:* PRD «Alumnos, tutores y documentación» (Documentación); Acl. 8, 11.

**HU-DOC-02** · `Should-have`
Como staff, quiero ver en cada ficha qué documentos obligatorios de la temporada le faltan, y un listado de los alumnos con documentación pendiente, para saber a qué familias reclamárselos.
*Sustento:* Acl. 8 (Checklist configurable).

**HU-DOC-03** · `Should-have`
Como staff, quiero ver y descargar los documentos de los alumnos que tengo permitidos, para consultarlos cuando los necesito.
*Sustento:* PRD «Roles y permisos» (Cargar documentación); Acl. 11 (Archivos privados).

**HU-DOC-04** · `Backlog`
Como staff, quiero cargar en la nueva temporada los documentos que volvieron a quedar pendientes (incluido el carnet de socio), para que la ficha vuelva a estar completa.
*Sustento:* Acl. 8, 10.

**HU-DOC-05** · `Backlog`
Como Admin, quiero ver quién subió o modificó cada documento médico y cuándo, para tener trazabilidad sobre los datos sensibles.
*Sustento:* Acl. 11 (Trazabilidad mínima).

**HU-DOC-06** · `Should-have`
Como Admin, quiero definir por temporada qué documentos son obligatorios (por ejemplo, ficha médica, DNI o autorización de salidas), para que cada ficha muestre qué le falta y se sepa cuándo está completa.
*Sustento:* Acl. 8 (Checklist configurable), 10.

## 3. Grupos y asistencia

**HU-GA-01** · `MVP-Entrega1`
Como Admin o Coordinador, quiero dar de alta, modificar y dar de baja grupos con nombre, turno y rango de fechas de nacimiento, para organizar a los chicos por edad y turno.
*Sustento:* PRD «Grupos, turnos y asistencia»; PRD «Roles y permisos»; Acl. 4. La baja de grupos no está en las fuentes. Cómo funciona (desactivar, no borrar) es una propuesta pendiente de confirmar: ver «Baja de grupos — propuesta, pendiente de confirmar».

**HU-GA-02** · `MVP-Entrega1`
Como Admin o Coordinador, quiero asignar uno o más profesores a cada grupo (y un profesor a más de un grupo), para que cada profesor trabaje solo sobre sus grupos.
*Sustento:* PRD «Roles y permisos».

**HU-GA-03** · `Should-have`
Como staff, quiero que al cargar un alumno el sistema me sugiera el grupo según su fecha de nacimiento, y poder elegir otro, para inscribirlo más rápido y sin errores.
*Sustento:* Acl. 4.

**HU-GA-04** · `MVP-Entrega1`
Como staff, quiero tomar asistencia por grupo, día y turno desde el celular o la PC, para registrar quién estuvo presente.
*Sustento:* PRD «Grupos, turnos y asistencia»; Acl. 12.

*Criterios de aceptación:*

**Escenario 1 — Tomar asistencia desde el celular** (camino feliz)
- **Dado** que un Profesor tiene asignado «Delfines», turno mañana
- **Y** que Juan, Sofía y Martín están inscriptos en «Delfines», turno mañana, en la temporada vigente
- **Cuando** desde el celular abre la asistencia de hoy de «Delfines», turno mañana, marca a Juan y a Sofía como presentes y a Martín como ausente, y guarda
- **Entonces** queda registrada la asistencia de esa fecha y turno: Juan presente, Sofía presente, Martín ausente
- **Y** la lista muestra solo a los alumnos inscriptos en ese grupo y turno

**Escenario 2 — Corregir una asistencia ya tomada** (caso límite)
- **Dado** que la asistencia de hoy de «Delfines», turno mañana, ya está registrada con Martín ausente
- **Cuando** el Profesor la vuelve a abrir, marca a Martín como presente y guarda
- **Entonces** Martín queda presente para esa fecha y turno
- **Y** hay un solo registro por alumno, fecha y turno, sin duplicados

**Escenario 3 — Alumno inscripto en los dos turnos** (caso límite)
- **Dado** que Juan está inscripto en «Delfines», turno mañana, y en «Pulpos», turno tarde
- **Cuando** se lo marca presente en el turno mañana
- **Entonces** su asistencia del turno tarde no se modifica: se registra aparte, en la asistencia de «Pulpos»

**Escenario 4 — Grupo sin alumnos inscriptos** (caso límite)
- **Dado** que el grupo «Caballitos», turno tarde, no tiene alumnos inscriptos en la temporada vigente
- **Cuando** se abre su asistencia del día
- **Entonces** el sistema informa que no hay alumnos inscriptos y no hay nada para guardar

**Escenario 5 — La asistencia no genera cobros ni avisos** (regla de negocio)
- **Dado** que Martín está inscripto en «Delfines», turno mañana
- **Cuando** se guarda la asistencia del día con Martín ausente
- **Entonces** no se genera ni se modifica ningún cargo, y el saldo de su familia no cambia
- **Y** no se envía ningún aviso a los padres

**Escenario 6 — Profesor sobre un grupo ajeno** (permisos)
- **Dado** que un Profesor tiene asignado solo «Delfines», turno mañana
- **Cuando** busca tomar asistencia de «Pulpos», turno tarde
- **Entonces** «Pulpos» no aparece entre sus grupos
- **Y** si la solicitud llega igual (por ejemplo, por la API), se rechaza y no se registra nada

**Escenario 7 — Coordinador o Admin en cualquier grupo** (permisos)
- **Dado** que un Coordinador inició sesión y no tiene grupos asignados
- **Cuando** toma asistencia de cualquier grupo y turno
- **Entonces** la asistencia se registra

**HU-GA-05** · `Should-have`
Como staff, quiero consultar la asistencia registrada de un grupo o de un alumno, para controlar quién vino cada día.
*Sustento:* PRD «Grupos, turnos y asistencia»; Acl. 5 (la asistencia es solo control).

## 4. Tarifario

**HU-TAR-01** · `MVP-Entrega1`
Como Admin, quiero definir la tarifa base de la temporada por turno y modalidad (Mes, Quincena, Semana, Día), y los dos tipos de cargo de la temporada (Preinscripción, con monto fijo y sin descuento, y Abono, que se calcula con el tarifario), para que todos cobren con los mismos precios.
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (Tarifario; Tipos de cargo); Acl. 5. El ABM libre de tipos de cargo es HU-TAR-05 (Backlog).

**HU-TAR-02** · `MVP-Entrega1`
Como Admin, quiero definir las fechas desde/hasta de cada Mes, Quincena y Semana de la temporada, para que cada cargo quede asociado a un período concreto.
*Sustento:* Acl. 5.

**HU-TAR-03** · `MVP-Entrega1`
Como Admin, quiero configurar la tabla de descuentos de la temporada —un % por categoría para Día, Semana y Quincena, y un % por categoría y tramo de cantidad de hijos (1, 2, 3, 4 o más) para el Mes— para reflejar la política de descuentos sin tocar código.
*Sustento:* PRD «Tarifario y cuenta corriente familiar»; Acl. 2, 5.

**HU-TAR-04** · `MVP-Entrega1`
Como Admin, quiero que al cargar un cargo el sistema calcule el monto solo: tarifa base del turno y la modalidad, menos el único porcentaje que corresponda según la categoría de la familia (y, en el Mes, la cantidad de hijos anotados en ese turno), para no calcularlo a mano.
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (facturación por turno); Acl. 5.

**HU-TAR-05** · `Backlog`
Como Admin, quiero administrar el catálogo de tipos de cargo de la temporada (por ejemplo, Preinscripción o Abono), para no depender de un esquema fijo.
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (Tipos de cargo).

## 5. Cuenta corriente familiar

**HU-CC-01** · `MVP-Entrega1`
Como Admin, quiero registrar un cargo a una familia (tipo, alumno, turno, modalidad y período), para dejar asentado lo que tiene que pagar.
*Sustento:* PRD «Tarifario y cuenta corriente familiar»; Acl. 5, 6.

*Criterios de aceptación* (incluyen el cálculo de HU-TAR-04):

**Contexto común.** Son las precondiciones que dependen del bloque Tarifario (HU-TAR-01 a HU-TAR-03). Los montos y porcentajes son de ejemplo: los porcentajes del Mes siguen el ejemplo del PRD, y el resto se eligió para los escenarios.
- **Dado** que la temporada vigente es 2026-27
- **Y** que el Admin cargó esta tarifa base:

  | Turno | Mes | Quincena | Semana | Día |
  |---|---|---|---|---|
  | Mañana | $ 100.000 | $ 55.000 | $ 30.000 | $ 8.000 |
  | Tarde | $ 80.000 | $ 45.000 | $ 25.000 | $ 7.000 |

- **Y** que cargó esta tabla de descuentos:

  | Categoría | Día | Semana | Quincena | Mes · 1 hijo | Mes · 2 | Mes · 3 | Mes · 4 o más |
  |---|---|---|---|---|---|---|---|
  | Socio | 50 % | 50 % | 50 % | 50 % | 50 % | 50 % | 50 % |
  | Empleado | 10 % | 10 % | 10 % | 10 % | 15 % | 20 % | 25 % |
  | No socio | 0 % | 0 % | 0 % | 0 % | 10 % | 15 % | 20 % |

- **Y** que definió los tipos de cargo Preinscripción (monto fijo de $ 20.000) y Abono
- **Y** que definió las fechas del «Mes 1» (04/01/2027 al 29/01/2027), del «Mes 2» (01/02/2027 al 26/02/2027) y de la «Semana 1» (04/01/2027 al 08/01/2027)
- **Y** que un Admin inició sesión

Qué hijos cuentan para el tramo del Mes: lo define el PRD («Tarifario y cuenta corriente familiar»). Cada turno se factura por separado, "contando solo a los hermanos anotados en ese turno", y el porcentaje "se aplica a cada hermano sobre el valor base de su modalidad".

**Escenario 1 — Abono · Mes con descuento por cantidad de hijos** (camino feliz)
- **Dado** que la familia «Pérez – Ana» es categoría empleado y tiene 2 hijos inscriptos en el turno mañana: Ana y Juan
- **Cuando** el Admin registra un cargo de tipo Abono para Juan, turno mañana, modalidad Mes, período «Mes 1»
- **Entonces** el sistema muestra la tarifa base ($ 100.000), el porcentaje aplicado (15 %: empleado, 2 hijos) y el monto final ($ 85.000)
- **Y** al confirmar, el cargo queda en la cuenta corriente de la familia con su tipo, alumno, turno, modalidad, período y monto
- **Y** el saldo pendiente de la familia aumenta en $ 85.000

**Escenario 2 — En Día, Semana y Quincena no cuenta la cantidad de hijos** (regla de negocio)
- **Dado** que una familia es categoría empleado y tiene 3 hijos inscriptos en el turno mañana
- **Cuando** el Admin registra un Abono para uno de ellos, turno mañana, modalidad Semana, período «Semana 1»
- **Entonces** se aplica el 10 % de empleado para Semana, sin importar la cantidad de hijos
- **Y** el monto es $ 27.000

**Escenario 3 — Se aplica un único porcentaje, nunca acumulado** (caso límite)
- **Dado** que una familia es categoría socio y tiene 4 hijos inscriptos en el turno mañana
- **Cuando** el Admin registra un Abono · Mes, turno mañana, para uno de ellos
- **Entonces** se aplica solo el 50 % de la celda «socio · Mes · 4 o más»
- **Y** el monto es $ 50.000: no se suman porcentajes de otras celdas ni se aplican descuentos en cascada

**Escenario 4 — El tramo alcanza a todos los hijos** (caso límite)
- **Dado** que una familia es categoría no socio y tiene 4 hijos inscriptos en el turno mañana
- **Cuando** el Admin registra un Abono · Mes, turno mañana, «Mes 1», para cada uno de los 4 hijos
- **Entonces** los 4 cargos son de $ 80.000 (20 %), incluido el del primer hijo

**Escenario 5 — Los hijos se cuentan por turno** (caso límite)
- **Dado** que la familia «Pérez – Ana» es categoría empleado, que Ana está inscripta solo en el turno mañana y que Juan está inscripto en los turnos mañana y tarde
- **Cuando** el Admin registra para Juan un Abono · Mes en el turno mañana y otro en el turno tarde, ambos del «Mes 1»
- **Entonces** el de la mañana cuenta 2 hijos: 15 % sobre $ 100.000, es decir $ 85.000
- **Y** el de la tarde cuenta 1 hijo: 10 % sobre $ 80.000, es decir $ 72.000

**Escenario 6 — Hijo que se suma a mitad de temporada** (caso límite)
- **Dado** que la familia «Pérez – Ana», categoría empleado, ya tiene registrado un Abono · Mes de Juan, turno mañana, «Mes 1», por $ 85.000 (2 hijos)
- **Y** que después se inscribe a Tomás en el turno mañana, y la familia pasa a tener 3 hijos en ese turno
- **Cuando** el Admin registra un Abono · Mes para Juan, turno mañana, «Mes 2»
- **Entonces** el cargo nuevo usa el tramo de 3 hijos: 20 %, es decir $ 80.000
- **Y** el cargo del «Mes 1», ya registrado, sigue siendo de $ 85.000: no se recalcula

**Escenario 7 — Preinscripción: monto fijo, sin descuento** (regla de negocio)
- **Dado** que una familia es categoría socio
- **Cuando** el Admin registra un cargo de tipo Preinscripción para uno de sus hijos
- **Entonces** el monto es $ 20.000, sin descuento y sin pasar por el tarifario
- **Y** el monto sería el mismo si la familia fuera empleado o no socio

**Escenario 8 — La ficha incompleta no impide registrar el cargo** (caso límite)
- **Dado** que la ficha de Juan tiene documentación obligatoria pendiente
- **Cuando** el Admin le registra un Abono · Mes
- **Entonces** el cargo se registra igual

**Escenario 9 — Falta la tarifa base** (error)
- **Dado** que, a diferencia del contexto común, el Admin no cargó la tarifa base del turno tarde para la modalidad Quincena
- **Cuando** intenta registrar un Abono · Quincena en el turno tarde
- **Entonces** el sistema no calcula ni registra el cargo
- **Y** indica que falta la tarifa base de esa combinación de turno y modalidad

**Escenario 10 — Temporada anterior, solo consulta** (error)
- **Dado** que la temporada 2025-26 ya cerró
- **Cuando** el Admin intenta registrar un cargo en esa temporada
- **Entonces** el sistema lo rechaza, porque la temporada anterior queda solo para consulta

**Escenario 11 — Solo el Admin registra cargos** (permisos)
- **Dado** que un Coordinador o un Profesor inició sesión
- **Cuando** intenta registrar un cargo o ver la cuenta corriente de una familia
- **Entonces** no tiene esa opción en pantalla
- **Y** si la solicitud llega igual (por ejemplo, por la API), se rechaza y no se registra nada

**HU-CC-02** · `MVP-Entrega1`
Como Admin, quiero registrar uno o varios pagos parciales sobre un cargo hasta saldarlo, para reflejar cómo paga cada familia (por ejemplo, una parte en la inscripción y el resto el primer día).
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (Pagos); Acl. 6, 9.

**HU-CC-03** · `MVP-Entrega1`
Como Admin, quiero ver la cuenta corriente de una familia con sus cargos, pagos y saldo pendiente, para saber en todo momento cuánto debe.
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (Pagos).

**HU-CC-04** · `Should-have`
Como Admin, quiero un reporte de deudas con las familias que tienen saldo pendiente, para hacer el seguimiento de cobro sin recordatorios automáticos.
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (Pagos); Acl. 6.

**HU-CC-05** · `Backlog`
Como staff, quiero indicar una modalidad sugerida al inscribir a un alumno, para que el Admin la tenga como referencia al registrar el cargo.
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (Modalidad).

**HU-CC-06** · `Should-have`
Como Admin, quiero anular un cobro mal cargado indicando el motivo, sin borrarlo y dejando registrado quién lo anuló, para corregir errores sin perder el rastro de lo que pasó.
*Sustento:* Acl. 6 (Anulaciones).

## 6. Tesorería general

**HU-TES-01** · `MVP-Entrega1`
Como Admin, quiero que cada pago registrado genere automáticamente un ingreso en la tesorería, para no cargar los cobros dos veces.
*Sustento:* PRD «Tesorería general»; Acl. 7. Entra en el lote como **dato**: desde la Entrega 1, registrar un pago escribe su ingreso en la tesorería, aunque no haya pantalla para verlo (eso es HU-TES-03).

**HU-TES-02** · `Should-have`
Como Admin, quiero registrar egresos con descripción y monto (sueldos, festejos, insumos u otros), para que la tesorería refleje los gastos.
*Sustento:* PRD «Tesorería general».

**HU-TES-03** · `Should-have`
Como Admin, quiero ver los ingresos, los egresos y el saldo disponible de la tesorería, para conocer la situación financiera de la escuelita.
*Sustento:* PRD «Tesorería general».

## 7. Canon al club

**HU-CAN-01** · `Backlog`
Como Admin, quiero configurar el % de canon que se le paga al club, para que el cálculo se ajuste a lo acordado.
*Sustento:* Acl. 7.

**HU-CAN-02** · `Backlog`
Como Admin, quiero iniciar un cierre de canon por un rango de fechas y ver el total cobrado, el detalle de los cobros que lo componen y el monto a abonar, para saber cuánto pagarle al club.
*Sustento:* PRD «Cuenta corriente del canon al club»; Acl. 7.

**HU-CAN-03** · `Backlog`
Como Admin, quiero abonar el canon de un cierre, dejando registrado qué Admin lo hizo y generando el egreso en tesorería, para que quede constancia del pago y el saldo de tesorería sea correcto.
*Sustento:* PRD «Cuenta corriente del canon al club»; Acl. 7.

**HU-CAN-04** · `Backlog`
Como Admin, quiero ver la cuenta corriente del canon con los cierres realizados y su detalle, para controlar qué se le pagó al club y cómo se compone cada monto.
*Sustento:* PRD «Cuenta corriente del canon al club».

**HU-CAN-05** · `Backlog`
Como Admin, quiero que, si se anula un cobro que ya estaba incluido en un cierre de canon abonado, la diferencia se ajuste en el próximo cierre sin modificar el cierre abonado, para que lo pagado al club quede correcto.
*Sustento:* Acl. 6 (Anulaciones), 7.

## 8. Usuarios y temporadas

**HU-UT-01** · `MVP-Entrega1`
Como staff, quiero ingresar con mi usuario y contraseña personales, para acceder solo a lo que permite mi rol.
*Sustento:* PRD «Roles y permisos»; Acl. 11 (Autenticación: usuarios individuales).

**HU-UT-02** · `MVP-Entrega1`
Como Admin (cualquier rol) o Coordinador (solo usuarios Profesor), quiero dar de alta usuarios y modificar sus datos, para que cada persona del staff tenga su propio acceso.
*Sustento:* PRD «Roles y permisos» (Registrar profesores); Acl. 9.

**HU-UT-03** · `MVP-Entrega1`
Como Admin, quiero desactivar usuarios, para que quien deja de trabajar en la escuelita no pueda ingresar y se conserve igual lo que registró.
*Sustento:* Acl. 11 (Autenticación).

**HU-UT-04** · `Backlog`
Como Admin, quiero abrir una nueva temporada con su fecha de inicio y de cierre y su propia configuración (tarifa base, tabla de descuentos, % de canon, tipos de cargo y documentos obligatorios), para arrancar cada verano sin recargar datos ni mezclar cuentas. Al abrirla:
- se pueden copiar los grupos de la temporada anterior, para después ajustar sus rangos de nacimiento;
- se conservan los alumnos, los tutores y los profesores, con sus usuarios;
- las inscripciones a grupos se hacen de nuevo;
- toda la documentación vuelve a quedar pendiente;
- las cuentas corrientes y la tesorería arrancan en cero.

*Sustento:* PRD «Resumen y objetivo» (uso por temporada); Acl. 4, 10. La **primera** temporada no se abre con esta historia: se crea en la puesta en marcha (ver «Excluido por no estar en las fuentes»).

**HU-UT-05** · `Backlog`
Como staff, quiero consultar los datos de una temporada anterior, según los permisos de mi rol y sin poder modificarlos, para revisar lo que pasó sin alterar el historial.
*Sustento:* Acl. 10 (la temporada anterior queda solo para consulta).

---

## Resumen

| Módulo | Historias | MVP-Entrega1 | Should-have | Backlog |
|---|---|---|---|---|
| Alumnos y familias | 11 | 4 | 5 | 2 |
| Documentación | 6 | 0 | 4 | 2 |
| Grupos y asistencia | 5 | 3 | 2 | 0 |
| Tarifario | 5 | 4 | 0 | 1 |
| Cuenta corriente familiar | 6 | 3 | 2 | 1 |
| Tesorería general | 3 | 1 | 2 | 0 |
| Canon al club | 5 | 0 | 0 | 5 |
| Usuarios y temporadas | 5 | 3 | 0 | 2 |
| **Total** | **46** | **18** | **15** | **13** |

## Alcance de la Entrega 1 (decisión del 19/10/2026)

No se usan datos semilla: todo lo que hace falta para demostrar el sistema se carga desde la propia aplicación. Por eso el MVP se arma en cadena, y cada bloque habilita al siguiente:

1. **Usuarios y login:**
   - HU-UT-01: ingresar con usuario y contraseña.
   - HU-UT-02: alta y modificación de usuarios.
   - HU-UT-03: baja, es decir, desactivar un usuario.

   El ABM de profesores es el ABM de usuarios con rol Profesor.
2. **Grupos y profesores:**
   - HU-GA-01: ABM de grupos.
   - HU-GA-02: asignar profesores a grupos.
3. **Alta de alumno:**
   - HU-AF-01: registrar alumno con grupo y turno.
   - HU-AF-02: crear o elegir familia.
   - HU-AF-03: personas autorizadas, con al menos un tutor.
   - HU-AF-04: categoría, que se carga junto con el primer hijo.
4. **Asistencia:**
   - HU-GA-04: tomar asistencia por grupo, día y turno.
5. **Tarifario:**
   - HU-TAR-01: tarifa base por turno y modalidad, y los tipos de cargo Preinscripción y Abono.
   - HU-TAR-02: fechas desde/hasta de cada Mes, Quincena y Semana.
   - HU-TAR-03: tabla de descuentos por categoría (y por tramo de hijos en el Mes).
   - HU-TAR-04: cálculo automático del monto del cargo.
6. **Cobro:**
   - HU-CC-01: registrar un cargo (tipo, alumno, turno, modalidad y período), con el cálculo de tarifa base y descuento.
   - HU-CC-02: registrar pagos parciales sobre un cargo hasta saldarlo.
   - HU-CC-03: ver la cuenta corriente de la familia con cargos, pagos y saldo.
   - HU-TES-01: cada pago escribe su ingreso en la tesorería.

**El dato no es lo mismo que la pantalla.** La tabla de tesorería se crea en la Entrega 1 y cada pago registra su ingreso desde el primer día (HU-TES-01). Lo que queda afuera son las pantallas: ver movimientos y saldo (HU-TES-03) y cargar egresos manuales (HU-TES-02). Escribir el ingreso al registrar el pago cuesta dos líneas; generar esos ingresos después con una migración sería más riesgoso.

**Puesta en marcha.** El lote arranca con el primer Admin y la primera temporada vigente, que se crean al instalar el sistema (Acl. 9, 10). Configurar esa temporada (tarifa base, descuentos, tipos de cargo y fechas) ya está en el lote con el bloque Tarifario. Abrir una temporada **nueva**, con la copia de grupos y los reseteos, sigue en Backlog (HU-UT-04).

### Lote de desarrollo vs. historias documentadas

Son dos cosas distintas y no tienen por qué coincidir:

- **Lote de desarrollo (18 historias, los 6 bloques de arriba):** es lo que se construye primero, en cadena. Sin usuarios, grupos y alta de alumno no hay nada que demostrar de punta a punta.
- **Historias documentadas con criterios en [`5-historias-de-usuario.md`](../../5-historias-de-usuario.md) (3):** es lo que pide la consigna del curso. Se documentan en profundidad, con criterios Dado / Cuando / Entonces, las tres que mejor muestran el sistema. Los criterios son los mismos que figuran en este archivo, debajo de cada historia:
  1. **HU-AF-01** — registrar un alumno con familia, grupo y turno.
  2. **HU-GA-04** — tomar asistencia por grupo, día y turno.
  3. **HU-CC-01** — registrar un cargo con cálculo de tarifa y descuento (es la que concentra las reglas de negocio). Sus dependencias del bloque Tarifario (tarifa base, tipos de cargo, fechas del período y tabla de descuentos) van como precondiciones en el "Dado" de los escenarios. Las historias HU-TAR no se documentan aparte.

Las otras 15 del lote se construyen igual, pero quedan listadas acá sin criterios. Esto resuelve el "4 bloques contra 3 historias" sin recortar el sistema real ni inflar la entrega.

**Cambios respecto de las versiones anteriores:**
- El bloque de cobro (HU-CC-01 a HU-CC-03) vuelve a MVP-Entrega1.
- HU-TAR-01 a HU-TAR-04 suben a MVP-Entrega1 como un bloque nuevo de Tarifario, antes del Cobro, porque sin datos semilla el cálculo del cargo los necesita. HU-TAR-01 incorpora los dos tipos de cargo de la temporada (Preinscripción y Abono). El ABM libre de tipos de cargo (HU-TAR-05) sigue en Backlog.
- HU-UT-03 pasa de Backlog a MVP, como la baja del ABM.
- HU-GA-01 incorpora la baja de grupos, que no figura en el PRD ni en las aclaraciones.
- HU-AF-01 exige al menos un tutor en el alta (Acl. 3).
- La anulación de cobros sale de «Excluido» porque ya la define Acl. 6. Se agregan HU-CC-06 (anular un cobro) y HU-CAN-05 (ajuste del canon).
- Checklist de documentación configurable (Acl. 8): se reescribe HU-DOC-02 y se agrega HU-DOC-06.
- HU-AF-11, HU-DOC-04 y HU-UT-04 se reescriben según la nueva sección 10 de las aclaraciones, y se agrega HU-UT-05 (consulta de temporadas anteriores).
- HU-TES-01 pasa a MVP-Entrega1 como dato: cada pago escribe su ingreso desde la Entrega 1. Las pantallas de tesorería (HU-TES-02, HU-TES-03) siguen como Should-have.
- HU-UT-04 incorpora la copia de grupos de la temporada anterior (Acl. 4). La primera temporada se crea en la puesta en marcha.

**Baja de grupos — propuesta, pendiente de confirmar:** un grupo con alumnos o asistencia registrada no se borra, se **desactiva**: deja de aparecer para inscribir, pero conserva su historia. Es el mismo criterio que ya rige para los usuarios (los desactivados se conservan para no romper las referencias de quién cobró). Si se confirma, pasa a `aclaraciones-cliente.md`.

## Excluido por no estar en las fuentes

Estos temas aparecen solo en el documento técnico, así que no se convirtieron en historias. Si se quieren, primero hay que confirmarlos con el cliente y sumarlos a `aclaraciones-cliente.md`:
- Cambio y blanqueo de contraseña, y bloqueo tras 5 intentos fallidos.

El primer Admin (Acl. 9) y la primera temporada (Acl. 10), que se crean al instalar el sistema, son tareas de puesta en marcha, no historias de usuario.

## Diferencias con el documento técnico

1. **Tamaño máximo de archivo:** el documento técnico dice 10 MB y Acl. 11 dice 5 MB. Por precedencia vale 5 MB, pero hay que alinear el documento técnico.
2. **Borrado de documentos al cerrar la temporada:** el documento técnico lo recomienda, pero Acl. 10 dice que no se borra nada: los documentos se conservan y vuelven a quedar pendientes en la temporada nueva. No se creó ninguna historia de borrado.
3. **Retención de backups:** el documento técnico dice "el PRD pide al menos 30 días", pero el PRD no dice eso.
