# Backlog de historias de usuario — Escuelita de Verano

Artefacto de trabajo derivado de las fuentes. **No** es parte del PRD.

**Fuentes:**
- `docs/prd/prd-escuelita-de-verano.md` (en el campo *Sustento*, "PRD" seguido de la sección).
- `docs/prd/aclaraciones-cliente.md` ("Acl." seguido del número de sección). Prevalece sobre el PRD.
- `docs/architecture/documento-tecnico.md`: se usó solo para verificar que cada historia sea viable técnicamente. No se sacó ninguna historia de ahí.

**Criterios de aceptación:** se escriben lote por lote, justo antes de programar cada lote — no para todo el backlog de una. Así ninguna historia queda con criterios escritos sobre definiciones que todavía pueden cambiar.

**Roles:** cuando varios roles hacen lo mismo, se nombran juntos en una sola historia. Los matices de permisos se definen en los criterios de aceptación. "Staff" significa Admin, Coordinador o Profesor; el Profesor siempre solo sobre sus grupos.

**Prioridades:**
- **Lote 1**: se construye en la Entrega 2 (11 historias, ver «Alcance de la implementación»). Tres de ellas, además, se documentan con criterios en `5-historias-de-usuario.md` para cumplir con la consigna del curso.
- **Lote 2**: se construye después del lote 1 (9 historias). Son las que `make seed` sustituye durante el lote 1 y que el sistema necesita antes de ser productivo.
- **Should-have**: valiosa, pero no imprescindible para demostrar el sistema en esta entrega.
- **Backlog**: necesaria para el sistema en producción, pero fuera de esta entrega académica.

---

## 1. Alumnos y familias

**HU-AF-01** · `Lote 1`
Como staff, quiero registrar un alumno con sus datos mínimos (incluido al menos un tutor) y asignarlo a un grupo y turno, para tenerlo inscripto desde el primer contacto y completar la documentación más adelante.
*Sustento:* PRD «Alumnos, tutores y documentación» (ficha progresiva; la inscripción la hace el staff); PRD «Roles y permisos»; Acl. 3, 4, 8.

*Criterios de aceptación:* están en [`5-historias-de-usuario.md`](../../5-historias-de-usuario.md), que es el documento que los entrega. **No se copian acá**: hasta el 11/11/2026 estaban en los dos archivos y ya habían empezado a divergir.

**HU-AF-02** · `Lote 1`
Como staff, quiero que al cargar el primer hijo se cree su familia, y que al cargar los siguientes pueda elegir la familia existente (identificada como "Apellido – Hijo mayor"), para que todos los hijos compartan una sola cuenta corriente.
*Sustento:* PRD «Tarifario y cuenta corriente familiar»; Acl. 1.

**HU-AF-03** · `Lote 1`
Como staff, quiero cargar las personas autorizadas a retirar al alumno (incluidos los tutores, de los que hace falta al menos uno), y reutilizar una persona ya cargada en otra familia, para saber quién puede llevarse a cada chico.
*Sustento:* PRD «Alumnos, tutores y documentación» (Tutores); Acl. 3.

**HU-AF-04** · `Lote 1`
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

**HU-GA-01** · `Lote 2`
Como Admin o Coordinador, quiero dar de alta, modificar y dar de baja grupos con nombre, turno y rango de fechas de nacimiento, para organizar a los chicos por edad y turno.
*Sustento:* PRD «Grupos, turnos y asistencia»; PRD «Roles y permisos»; Acl. 4. La baja de grupos no está en las fuentes. Cómo funciona (desactivar, no borrar) es una propuesta pendiente de confirmar: ver «Baja de grupos — propuesta, pendiente de confirmar».

**HU-GA-02** · `Lote 2`
Como Admin o Coordinador, quiero asignar uno o más profesores a cada grupo (y un profesor a más de un grupo), para que cada profesor trabaje solo sobre sus grupos.
*Sustento:* PRD «Roles y permisos».

**HU-GA-03** · `Should-have`
Como staff, quiero que al cargar un alumno el sistema me sugiera el grupo según su fecha de nacimiento, y poder elegir otro, para inscribirlo más rápido y sin errores.
*Sustento:* Acl. 4.

**HU-GA-04** · `Lote 1`
Como staff, quiero tomar asistencia por grupo, día y turno desde el celular o la PC, para registrar quién estuvo presente.
*Sustento:* PRD «Grupos, turnos y asistencia»; Acl. 12.

*Criterios de aceptación:* están en [`5-historias-de-usuario.md`](../../5-historias-de-usuario.md), que es el documento que los entrega. **No se copian acá**: hasta el 11/11/2026 estaban en los dos archivos y ya habían empezado a divergir.

**HU-GA-05** · `Should-have`
Como staff, quiero consultar la asistencia registrada de un grupo o de un alumno, para controlar quién vino cada día.
*Sustento:* PRD «Grupos, turnos y asistencia»; Acl. 5 (la asistencia es solo control).

## 4. Tarifario

**HU-TAR-01** · `Lote 2`
Como Admin, quiero definir la tarifa base de la temporada por turno y modalidad (Mes, Quincena, Semana, Día), y los dos tipos de cargo de la temporada (Preinscripción, con monto fijo y sin descuento, y Abono, que se calcula con el tarifario), para que todos cobren con los mismos precios.
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (Tarifario; Tipos de cargo); Acl. 5. El ABM libre de tipos de cargo es HU-TAR-05 (Backlog).

**HU-TAR-02** · `Lote 2`
Como Admin, quiero definir las fechas desde/hasta de cada Mes, Quincena y Semana de la temporada, para que cada cargo quede asociado a un período concreto.
*Sustento:* Acl. 5.

**HU-TAR-03** · `Lote 2`
Como Admin, quiero configurar las dos tablas de descuentos de la temporada —la escala por cantidad de hijos (1, 2, 3, 4 o más, solo para el Mes, con 0% en el tramo de 1 hijo) y el % de cada categoría por modalidad, que se aplica sobre el valor del no socio— para reflejar la política de descuentos sin tocar código.
*Sustento:* PRD «Tarifario y cuenta corriente familiar»; Acl. 2, 5.

**HU-TAR-04** · `Lote 1`
Como Admin, quiero que al cargar un cargo el sistema calcule el monto solo: tarifa base del turno y la modalidad, por el porcentaje del tramo de hijos (solo en el Mes, según los hijos anotados en ese turno) y por el porcentaje de la categoría de la familia, con un solo redondeo al final, para no calcularlo a mano.
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (facturación por turno); Acl. 5.

**HU-TAR-05** · `Backlog`
Como Admin, quiero administrar el catálogo de tipos de cargo de la temporada (por ejemplo, Preinscripción o Abono), para no depender de un esquema fijo.
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (Tipos de cargo).

## 5. Cuenta corriente familiar

**HU-CC-01** · `Lote 1`
Como Admin, quiero registrar un cargo a una familia (tipo, alumno, turno, modalidad y período), para dejar asentado lo que tiene que pagar.
*Sustento:* PRD «Tarifario y cuenta corriente familiar»; Acl. 5, 6.

*Criterios de aceptación:* están en [`5-historias-de-usuario.md`](../../5-historias-de-usuario.md), que es el documento que los entrega. **No se copian acá**: hasta el 11/11/2026 estaban en los dos archivos y ya habían empezado a divergir.

**HU-CC-02** · `Lote 1`
Como Admin, quiero registrar uno o varios pagos parciales sobre un cargo hasta saldarlo, para reflejar cómo paga cada familia (por ejemplo, una parte en la inscripción y el resto el primer día).
*Sustento:* PRD «Tarifario y cuenta corriente familiar» (Pagos); Acl. 6, 9.

**HU-CC-03** · `Lote 1`
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

**HU-TES-01** · `Lote 1`
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

**HU-UT-01** · `Lote 1`
Como staff, quiero ingresar con mi usuario y contraseña personales, para acceder solo a lo que permite mi rol.
*Sustento:* PRD «Roles y permisos»; Acl. 9 (Acceso al sistema), 11 (Autenticación: usuarios individuales). Si el usuario tiene pendiente el cambio obligatorio de contraseña, el ingreso lo lleva directo a HU-UT-06, y la API rechaza cualquier otra operación hasta que la cambie.

**HU-UT-02** · `Lote 2`
Como Admin (cualquier rol) o Coordinador (solo usuarios Profesor), quiero dar de alta usuarios y modificar sus datos, para que cada persona del staff tenga su propio acceso.
*Sustento:* PRD «Roles y permisos» (Registrar profesores); Acl. 9.

**HU-UT-03** · `Lote 2`
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

**HU-UT-06** · `Lote 2`
Como staff, quiero que el sistema me obligue a cambiar la contraseña en el primer ingreso y después de un blanqueo, para que solo yo conozca la contraseña con la que entro.
*Sustento:* Acl. 9 (Acceso al sistema: cambio obligatorio). Las reglas de la contraseña nueva están en el documento técnico, «Contraseñas y sesión»: mínimo 8 caracteres, al menos una letra y un número, distinta del nombre de usuario y de la anterior.

**HU-UT-07** · `Lote 2`
Como Admin, quiero blanquear la contraseña de un usuario, para que pueda volver a ingresar si la olvidó o si quedó bloqueado. Al blanquearla se activa el cambio obligatorio (HU-UT-06) y se desbloquea el usuario.
*Sustento:* Acl. 9 (Acceso al sistema: blanqueo).

**HU-UT-08** · `Should-have`
Como Admin, quiero que un usuario quede bloqueado después de 5 intentos de ingreso fallidos seguidos, hasta que yo le blanquee la contraseña (HU-UT-07), para que nadie pueda adivinar una contraseña probando.
*Sustento:* Acl. 9 (Acceso al sistema: bloqueo).

---

## Resumen

| Módulo | Historias | Lote 1 | Lote 2 | Should-have | Backlog |
|---|---|---|---|---|---|
| Alumnos y familias | 11 | 4 | 0 | 5 | 2 |
| Documentación | 6 | 0 | 0 | 4 | 2 |
| Grupos y asistencia | 5 | 1 | 2 | 2 | 0 |
| Tarifario | 5 | 1 | 3 | 0 | 1 |
| Cuenta corriente familiar | 6 | 3 | 0 | 2 | 1 |
| Tesorería general | 3 | 1 | 0 | 2 | 0 |
| Canon al club | 5 | 0 | 0 | 0 | 5 |
| Usuarios y temporadas | 8 | 1 | 4 | 1 | 2 |
| **Total** | **49** | **11** | **9** | **16** | **13** |

## Alcance de la implementación (decisión del 11/11/2026)

**Hay script de datos.** `make seed` deja la temporada vigente, los usuarios de los tres roles, los grupos de los dos turnos con sus profesores y el tarifario completo. Eso cambia el tamaño del primer lote: la decisión anterior (19/10/2026) era no usar semilla, y por eso el lote tenía que armarse en cadena —sin ABM de usuarios no había con qué entrar, sin ABM de grupos no había dónde inscribir, sin ABM de tarifario no había con qué calcular—. Con semilla la cadena se corta y el primer lote puede ser la espina del producto en lugar de su andamiaje.

El motivo del cambio es el feedback de la Entrega 1: el lote de 20 historias era demasiado para el plazo, y el ABM de usuarios, grupos y tarifario son formularios que no ejercitan ninguna regla de negocio.

### Lote 1 — la espina del dinero (Entrega 2)

Once historias. Es el flujo que se demuestra de punta a punta: entrar, cargar una familia con un hijo, inscribirlo, tomarle asistencia, cobrarle y ver el saldo.

1. **Entrar:**
   - HU-UT-01: ingresar con usuario y contraseña.
2. **Alta de alumno:**
   - HU-AF-02: crear o elegir familia.
   - HU-AF-04: categoría, que se carga junto con el primer hijo.
   - HU-AF-03: personas autorizadas, con al menos un tutor.
   - HU-AF-01: registrar alumno con grupo y turno.
3. **Asistencia:**
   - HU-GA-04: tomar asistencia por grupo, día y turno.
4. **Cobro:**
   - HU-TAR-04: cálculo automático del monto del cargo.
   - HU-CC-01: registrar un cargo (tipo, alumno, turno, modalidad y período), con tarifa base y descuento.
   - HU-CC-02: registrar pagos parciales sobre un cargo hasta saldarlo.
   - HU-CC-03: ver la cuenta corriente de la familia con cargos, pagos y saldo.
   - HU-TES-01: cada pago escribe su ingreso en la tesorería.

**Por qué asistencia entra en una espina que es del dinero.** No toca dinero y es la historia más barata del lote. Entra por otra razón: las tres historias documentadas con criterios Dado / Cuando / Entonces en [`5-historias-de-usuario.md`](../../5-historias-de-usuario.md) son HU-AF-01, HU-GA-04 y HU-CC-01, y con asistencia dentro el lote 1 implementa exactamente las tres que la Entrega 1 documentó. Sin ella, una de las tres queda documentada y sin construir.

**Dónde está el riesgo.** De las once, dos concentran casi todo: HU-TAR-04, el cálculo, y HU-CC-01, el cargo. Ahí viven el porcentaje único no acumulado, el tramo que alcanza a todos los hijos, el conteo de hermanos por turno y la persistencia del cálculo en el cargo. El resto son altas y consultas. El tiempo de revisión se reparte en consecuencia.

### Lote 2 — el ABM que la semilla sustituye

Nueve historias. Son las que `make seed` cubre durante el lote 1 y que el sistema necesita antes de ser productivo, porque en producción no hay semilla: alguien tiene que poder crear un usuario y configurar la temporada desde la aplicación.

- HU-UT-02: alta y modificación de usuarios. El ABM de profesores es este mismo, con rol Profesor.
- HU-UT-03: baja, es decir, desactivar un usuario.
- HU-UT-06: cambio obligatorio de contraseña en el primer ingreso y después de un blanqueo.
- HU-UT-07: blanqueo de contraseña por un Admin.
- HU-GA-01: ABM de grupos.
- HU-GA-02: asignar profesores a grupos.
- HU-TAR-01: tarifa base por turno y modalidad, y los tipos de cargo Preinscripción y Abono.
- HU-TAR-02: fechas desde/hasta de cada Mes, Quincena y Semana.
- HU-TAR-03: tabla de descuentos por categoría y por tramo de hijos.

**Las contraseñas bajaron de lote por indicación del revisor de la Entrega 1.** HU-UT-06 y HU-UT-07 estaban en el lote original; el revisor pidió sacarlas, y el motivo se sostiene: con un usuario de semilla ya logueable, el cambio obligatorio y el blanqueo no hacen falta para demostrar nada. Pero **no son opcionales para producción**: un sistema con datos de menores donde el Admin no puede blanquear una contraseña no se pone en marcha. Van en el lote 2, no en el Backlog.

**El dato no es lo mismo que la pantalla.** La tabla de tesorería se crea en el lote 1 y cada pago registra su ingreso desde el primer día (HU-TES-01). Lo que queda afuera son las pantallas: ver movimientos y saldo (HU-TES-03) y cargar egresos manuales (HU-TES-02). Escribir el ingreso al registrar el pago cuesta dos líneas; generar esos ingresos después con una migración sería más riesgoso.

**Puesta en marcha.** El primer Admin y la primera temporada vigente se crean al instalar el sistema (Acl. 9, 10) y no son historias de usuario. Abrir una temporada **nueva**, con la copia de grupos y los reseteos, sigue en Backlog (HU-UT-04).

**Qué es y qué no es la semilla.** `make seed` es una herramienta de desarrollo y de demostración. Carga datos inventados, nunca datos reales de familias ni de alumnos, y no se ejecuta en producción. La puesta en marcha real de la temporada es el lote 2.

### Lote de desarrollo vs. historias documentadas

Son dos cosas distintas y no tienen por qué coincidir:

- **Lote de desarrollo (11 historias en el lote 1):** es lo que se construye primero.
- **Historias documentadas con criterios (3):** es lo que pide la consigna del curso. Se documentan en profundidad, con criterios Dado / Cuando / Entonces, las tres que mejor muestran el sistema:
  1. **HU-AF-01** — registrar un alumno con familia, grupo y turno.
  2. **HU-GA-04** — tomar asistencia por grupo, día y turno.
  3. **HU-CC-01** — registrar un cargo con cálculo de tarifa y descuento (es la que concentra las reglas de negocio). Sus dependencias del bloque Tarifario (tarifa base, tipos de cargo, fechas del período y tabla de descuentos) van como precondiciones en el "Dado" de los escenarios, y en el lote 1 las aporta la semilla. Las historias HU-TAR no se documentan aparte.

Las otras ocho del lote 1 se construyen igual, pero quedan listadas acá sin criterios.

**Cambios respecto de las versiones anteriores:**
- **11/11/2026.** Se incorpora el script de datos (`make seed`) y el lote de 20 se parte en dos: lote 1, la espina del dinero más asistencia (11 historias); lote 2, el ABM que la semilla sustituye (9 historias). Ninguna historia cambia de contenido y ninguna sale del alcance: solo cambia el orden. Motivo: el feedback de la Entrega 1 sobre el tamaño del lote.
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
- El cambio y el blanqueo de contraseña y el bloqueo por intentos salen de «Excluido», porque los define la sección «Acceso al sistema y usuarios» del PRD vigente (registrada en Acl. 9). Se agregan tres historias:
  - HU-UT-06, cambio obligatorio, al lote;
  - HU-UT-07, blanqueo, al lote, junto a HU-UT-02;
  - HU-UT-08, bloqueo tras 5 intentos, como Should-have porque es endurecimiento y no hace falta para demostrar el sistema.

  Ninguna se resolvió como criterio de una historia existente, por estos motivos:
  - el cambio obligatorio tiene su propia pantalla, su endpoint y sus reglas de validación, y HU-UT-01 solo lo hace cumplir;
  - el blanqueo lo hace solo el Admin, mientras que HU-UT-02 también la usa el Coordinador, y tiene efectos propios (activa el cambio obligatorio y desbloquea);
  - el bloqueo tiene otra prioridad que HU-UT-01, y un criterio no puede tener una prioridad distinta de la de su historia.

**Baja de grupos — propuesta, pendiente de confirmar:** un grupo con alumnos o asistencia registrada no se borra, se **desactiva**: deja de aparecer para inscribir, pero conserva su historia. Es el mismo criterio que ya rige para los usuarios (los desactivados se conservan para no romper las referencias de quién cobró). Si se confirma, pasa a `aclaraciones-cliente.md`.

## Excluido por no estar en las fuentes

Hoy no queda ningún tema del documento técnico fuera de las fuentes. El cambio y el blanqueo de contraseña y el bloqueo por intentos ya tienen historias (HU-UT-06 a HU-UT-08). Si aparece otro tema, va acá hasta que se confirme y se sume a `aclaraciones-cliente.md`.

El primer Admin (Acl. 9) y la primera temporada (Acl. 10), que se crean al instalar el sistema, son tareas de puesta en marcha, no historias de usuario.

## Diferencias con el documento técnico

1. **Tamaño máximo de archivo:** el documento técnico dice 10 MB y Acl. 11 dice 5 MB. Por precedencia vale 5 MB, pero hay que alinear el documento técnico.
2. **Borrado de documentos al cerrar la temporada:** el documento técnico lo recomienda, pero Acl. 10 dice que no se borra nada: los documentos se conservan y vuelven a quedar pendientes en la temporada nueva. No se creó ninguna historia de borrado.
3. **Retención de backups:** el documento técnico dice "el PRD pide al menos 30 días", pero el PRD no dice eso.
