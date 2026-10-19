# 5. Historias de Usuario

> **Recorte de MVP.** Estas 3 historias son el recorte de MVP de un backlog completo de **46 historias**. Son las que se documentan con criterios de aceptación; el resto del primer lote de desarrollo (18 historias en total) y el backlog completo, con prioridades y sustento, están en [`docs/product/historias-backlog.md`](docs/product/historias-backlog.md).

> **Convenciones.** "Staff" significa Admin, Coordinador o Profesor; el Profesor siempre actúa solo sobre sus grupos asignados. En el campo *Sustento*, "PRD" remite a [`docs/prd/prd-escuelita-de-verano.md`](docs/prd/prd-escuelita-de-verano.md) y "Acl." a [`docs/prd/aclaraciones-cliente.md`](docs/prd/aclaraciones-cliente.md), que prevalece sobre el PRD. Las precondiciones que dependen de otras historias del lote van en el "Dado".

**Historia de Usuario 1**

**HU-AF-01 — Registrar un alumno con familia, grupo y turno** · `MVP-Entrega1`

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

---

**Historia de Usuario 2**

**HU-GA-04 — Tomar asistencia por grupo, día y turno** · `MVP-Entrega1`

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

---

**Historia de Usuario 3**

**HU-CC-01 — Registrar un cargo con cálculo de tarifa y descuento** · `MVP-Entrega1`

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
