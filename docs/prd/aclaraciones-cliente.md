# Aclaraciones del cliente sobre el PRD

Fuente complementaria de `prd-escuelita-de-verano.md`. Recoge las respuestas a la revisión adversarial del PRD (octubre 2026).

**Precedencia:** cuando una aclaración contradice al PRD, vale la aclaración. El PRD se mantiene como transcripción fiel del documento original y no se modifica.

**Nota (19/10/2026):** el cliente mantiene además una versión evolucionada del PRD fuera del repo (`PRD Escuelita de Verano.pdf`, 6 páginas). Este archivo ya está reconciliado contra ella: donde esa versión trae material nuevo, se incorporó acá; donde contradice una decisión tomada en esta ronda (descuentos por modalidad, regla de los 3 días, asistencia en la pantalla de cobro, "Mes" en lugar de "Período"), prevalece lo que dice este archivo.

---

## 1. Familia

- La familia agrupa a los hijos que asisten a la escuelita. La cuenta corriente es única por familia, sin importar qué adulto pague (los padres separados también pagan en una sola cuenta).
- La arma a mano quien carga al alumno. Al cargar el primer hijo se crea la familia; a partir del segundo se elige la familia existente a la que pertenece.
- Puede incluir medio hermanos con otro apellido.
- **Identificación:**
  - ID interno autogenerado al crear la familia, que nunca cambia.
  - Etiqueta visible "Apellido – Hijo mayor", que se recalcula automáticamente cuando cambia la composición de la familia. No es un campo editable.
  - A futuro: un alias manual opcional para distinguir dos familias con el mismo apellido e igual hijo mayor.
- Terminología: se usa **"hijo"** en lugar de "hermano". Una familia con un solo chico cuenta como "1 hijo".

## 2. Categoría de la familia

- Valores: socio, empleado, no socio.
- Empleado significa empleado del centro médico o de la escuelita.
- La asigna quien registra al alumno (puede ser un profesor). Si aplican varias, el orden de prioridad es: **socio > empleado > no socio**.
- No hay paso de verificación por parte del Admin. Los precios y descuentos los definen los administradores, que les informan a los profesores.
- Una vez asignada, **solo los Admin** pueden modificar la categoría.

## 3. Tutores, personas autorizadas y contactos de emergencia

- Los tutores son personas autorizadas a retirar al chico. Un primo, por ejemplo, también es una persona autorizada.
- Una misma persona puede estar autorizada en más de una familia.
- Los **contactos de emergencia** son una lista aparte de las personas autorizadas a retirar.
- Los contactos de emergencia son **de la familia**, no de cada alumno: los hermanos los comparten, igual que comparten las personas autorizadas.
- **El alta de un alumno exige al menos un tutor.** No es opcional, por dos motivos:
  - La categoría de la familia se determina por los tutores: sin ninguno no hay categoría, y sin categoría no se puede calcular ningún cargo.
  - Un chico inscripto sin nadie autorizado a retirarlo no debería existir en el sistema.

  Cuando el PRD dice que la ficha "se crea con lo mínimo", se refiere a la documentación, no a los tutores. Lo mínimo para el alta es: nombre, apellido y fecha de nacimiento del alumno; familia (nueva, con su categoría, o existente); al menos un tutor; y grupo y turno.

## 4. Grupos

- Cada grupo tiene un nombre y un rango de fechas de nacimiento (desde/hasta).
- Los grupos son **por temporada**: el rango de fechas de nacimiento se corre cada año. Al abrir una temporada nueva se pueden **copiar los grupos de la anterior** y ajustar sus rangos.
- Al cargar un alumno, el sistema sugiere el grupo que corresponde por su fecha de nacimiento, y el usuario puede elegir otro.

## 5. Modalidades y tarifario

- Modalidades: **Mes, Quincena, Semana, Día**. "Mes" reemplaza a lo que el PRD llamaba "Período".
- El "Mes" son 4 semanas que definen los administradores con una fecha desde y una fecha hasta. Puede incluir días de otro mes calendario.
- La **Quincena** y la **Semana** también tienen fechas fijas (desde/hasta) definidas por los administradores.
- Se cobra la modalidad contratada, asista o no el chico. La asistencia no interviene en el cobro.
- **Se elimina** la regla "si asistió más de 3 días sueltos se cobra la semana". La tarifa por día va a quedar más cara que la semana.
- La pantalla de registrar cobro **no** muestra la asistencia.
- **Tarifa base:** un monto por **turno** (mañana/tarde) y por **modalidad** (Mes, Quincena, Semana, Día). El turno mañana y el turno tarde tienen precios distintos. Los montos los carga el administrador y cambian cada temporada.
- **Descuentos:** una tabla paramétrica que carga el administrador, con una fila por categoría (socio, empleado, no socio) y estas columnas:
  - Un porcentaje para **Día**, uno para **Semana** y uno para **Quincena**. Dependen solo de la categoría: **la cantidad de hijos no los afecta**.
  - Un porcentaje para **Mes** por cada tramo de cantidad de hijos: 1 hijo, 2 hijos, 3 hijos, 4 o más.
  - Los porcentajes son libres. El administrador decide cuánto da en cada celda y hasta dónde escala: puede cortar el beneficio en el tramo de 3 hijos, o seguir subiéndolo en el de 4 o más.
- **Cómo se aplica:** se toma la tarifa base del turno y la modalidad contratada y se le descuenta **un solo porcentaje**, el de la celda que corresponde a la categoría de la familia (y, si la modalidad es Mes, también a su cantidad de hijos). Los porcentajes no se acumulan entre sí.
- **Alcance del descuento por hijos:** el porcentaje del tramo se aplica a **todos los hijos** de la familia, no solo a partir del que supera el tramo. Una familia de 4 hijos cuyo tramo "4 o más" tenga 20% paga los cuatro meses con 20%.
- **Hijo que se suma a mitad de temporada:** los cargos que se generen desde ese momento usan el tramo nuevo. **Lo ya cobrado no se recalcula.**
- **Tipos de cargo:** hay dos.
  - **Preinscripción:** monto fijo, **sin descuento**, igual para las tres categorías. No pasa por el tarifario.
  - **Abono:** se calcula con el tarifario según turno, modalidad, categoría de la familia y cantidad de hijos (esta última solo en el Mes).
  - El tipo de cargo y la modalidad son campos distintos. Un cargo es, por ejemplo, "Abono · Mes", "Abono · Semana" o "Abono · Día".
  - El cliente al Abono lo llama "período". Se renombró para no volver a usar esa palabra, que ya se había sacado de circulación al renombrar la modalidad a "Mes".
- La planilla de aranceles 2025-26 sirve como referencia de la **estructura**, no de los valores: los montos y porcentajes de cada temporada los carga el administrador desde el sistema.

## 6. Cargos y pagos

- El pago se hace **por adelantado**, antes de que el chico empiece lo que se está pagando.
- Se mantienen los pagos parciales por cargo (por ejemplo, un % en la inscripción y el resto el primer día) y el reporte de deudas.
- Se espera que la familia haya pagado todo al ingresar a la modalidad contratada, así que no debería quedar deuda al terminar la temporada.
- **No hay saldos a favor ni devoluciones:** si una familia paga y el chico no va, lo pierde.
- **No se registra el medio de pago ni se emiten recibos.**
- **Anulaciones:** un cobro mal cargado **no se borra**, se anula indicando el motivo, y queda registrado quién lo anuló. Si ese cobro ya estaba incluido en un cierre de canon abonado, la diferencia se ajusta en el próximo cierre. Un cierre abonado no se modifica.

## 7. Tesorería y canon

- Cada pago registrado genera automáticamente un ingreso en la tesorería.
- **Anulación de un cobro en la tesorería:** el ingreso original **se conserva** y se registra automáticamente un **egreso por el mismo monto**, que referencia al cobro anulado. Es el criterio contable correcto: un asiento registrado se contraasienta en vez de borrarse. El neto queda en cero y se conserva la trazabilidad.
- **Canon:**
  - El porcentaje es configurable.
  - El cierre se hace por un rango desde/hasta, normalmente mensual, sobre todo lo cobrado en ese rango.
  - Abonar el canon genera automáticamente un **egreso** en la tesorería.

## 8. Ficha del alumno y documentación

- **Checklist configurable:** el Admin define **por temporada** qué documentos son obligatorios (por ejemplo: ficha médica, DNI, autorización de salidas). Cada ficha muestra qué le falta, y hay un listado de alumnos con documentación pendiente.
- Se pueden adjuntar otros certificados no obligatorios.
- Al abrir una temporada nueva, **todos los documentos vuelven a quedar pendientes**, incluido el carnet de socio.
- La ficha se considera **completa** cuando tiene todos los documentos marcados como obligatorios en esa temporada.
- **Se puede cobrar aunque la ficha esté incompleta.** Son temas independientes.

## 9. Roles y permisos

- Puede haber varios administradores.
- **Alta de usuarios:** los usuarios los da de alta un Admin. El primer Admin se crea al instalar el sistema.
- El **Coordinador también administra profesores**. Se mantiene lo del PRD ("Registrar profesores": Admin y Coordinador).
- "Administrar profesores" incluye que el Coordinador dé de alta el usuario de acceso con rol Profesor, y le asigne grupos. Los usuarios con rol Admin o Coordinador los da de alta solo un Admin.
- Solo los Admin registran cobros.
- Solo los Admin modifican la categoría de una familia.
- El profesor puede crear familias y ve los datos de los hijos que componen la familia. Esto queda limitado por la sección 11: no ve datos médicos ni documentos de hijos de otros grupos.

## 10. Temporadas y persistencia

- La **primera temporada se crea en la puesta en marcha**, junto con el primer Admin (sección 9). Su configuración (tarifas, descuentos, documentos obligatorios) la carga después el Admin desde el sistema.
- **Nueva definición:** no se borra nada entre temporadas. Esto reemplaza lo que decía el PRD original ("cada temporada arranca de cero"; "historial o datos que persistan entre temporadas" estaba fuera de alcance).
- Cada temporada tiene **fecha de inicio y de cierre** y su propia configuración: tarifa base, tabla de descuentos, % de canon, tipos de cargo y documentos obligatorios.
- Al abrir una temporada nueva:
  - Se **conservan** los alumnos, tutores y profesores, con sus usuarios.
  - Las **inscripciones a grupos se hacen de nuevo**.
  - Toda la **documentación vuelve a quedar pendiente** (sección 8).
  - Las **cuentas corrientes y la tesorería arrancan en cero**. Si quedó algo pendiente de la temporada anterior, lo gestiona el Admin por fuera del sistema.
- La temporada anterior queda disponible **solo para consulta**.
- Un alumno que vuelve reutiliza su ficha y su familia.

## 11. Seguridad y datos sensibles (aprobado)

- **Acceso por necesidad:**
  - El profesor ve alergias y condiciones médicas de los alumnos de sus grupos.
  - De los hijos de la misma familia que estén en otros grupos ve los datos de familia y las personas autorizadas, pero no los datos médicos ni los documentos.
- **Archivos privados:**
  - Nunca URLs públicas, solo enlaces temporales con vencimiento.
  - Formatos permitidos: PDF, JPG y PNG.
  - Límite de tamaño de 5 MB por archivo.
- **Cifrado:** HTTPS obligatorio, y cifrado en reposo de la base y del almacenamiento (a verificar contra el documento técnico).
- **Autenticación:**
  - Contraseñas con hash (bcrypt o argon2) y sesiones con vencimiento.
  - Usuarios individuales, sin cuentas compartidas.
  - El Admin puede desactivar usuarios.
- **Consentimiento:** una casilla registra que el tutor autorizó la carga de datos médicos (Ley 25.326, datos sensibles).
- **Retención:** ~~borrar los datos médicos y los documentos al cerrar la temporada~~. Reemplazado por la sección 10: no se borra nada. Así, los datos sensibles de menores quedan guardados de forma indefinida, y el resto de los controles de esta sección pasan a ser más importantes.
- **Trazabilidad mínima:** guardar quién subió o modificó cada documento médico y cuándo.
- **Antes de producción:** pedir una consulta legal para confirmar si la base debe inscribirse ante la AAIP.

## 12. Requisitos no funcionales

- Sistema web, usable desde **celular y PC**.
- Hosting y backups: definidos en el documento técnico.

## 13. Alcance

- Se construye el sistema completo, incluidos los módulos que la revisión marcó como scope creep oculto: reporte de deudas, subida de archivos, ABM del tarifario y de tipos de cargo, cierre de canon, temporadas, gestión de usuarios y roles, personas autorizadas.
- El recorte de alcance de cada entrega del curso **no es una definición del cliente**, así que no se registra acá: se define en `docs/product/historias-backlog.md`. Este archivo contiene solo decisiones de negocio.

---

## Cambios respecto del PRD

| Tema | PRD | Aclaración |
|---|---|---|
| Modalidad de 4 semanas | "Período de 4 semanas" | "Mes", con fechas desde/hasta definidas por los Admin |
| Regla de 3 días | Más de 3 días sueltos se cobra como semana | Eliminada |
| Asistencia y cobro | La asistencia sirve de referencia; la pantalla de cobro debería mostrarla | Sin relación; no se muestra |
| Descuentos | Se aplican sobre la tarifa base de cada modalidad | Igual, en todas las modalidades, con una tabla paramétrica por categoría; la cantidad de hijos solo afecta a la modalidad Mes |
| Tipos de cargo | Catálogo configurable por temporada (por ejemplo, Preinscripción, Período) | Dos tipos: Preinscripción (monto fijo, sin tarifario) y Abono (calculado con el tarifario). "Período" se renombró a "Abono"; tipo y modalidad son campos distintos |
| Categoría | Se determina por los tutores (socio si alguno es socio) | La asigna quien registra; prioridad socio > empleado > no socio; solo los Admin la modifican |
| Tutores | Tutores más personas autorizadas y de emergencia | Los tutores son personas autorizadas a retirar; los contactos de emergencia son una lista aparte |
| Quincena / Semana | Sin definición de fechas | Fechas fijas definidas por los Admin |
| Usuarios | No especificado | Los da de alta un Admin; el primer Admin se crea al instalar; el Coordinador también administra profesores |
| Documentación obligatoria | Ficha médica, DNI y otros certificados | Checklist configurable por temporada: el Admin define cuáles son obligatorios. Al abrir una temporada vuelven a quedar pendientes |
| Grupos | Por franja de edad | Por rango de fechas de nacimiento, con sugerencia automática. Son por temporada y se pueden copiar de la anterior |
| Temporadas | Cada temporada arranca de cero | Se conservan todos los datos, sin borrar nada; los documentos vencidos se reemplazan en la temporada siguiente |
| Canon | Cuenta aparte de la tesorería | Abonar el canon genera un egreso en tesorería |
| Anulaciones | No contempladas | Un cobro mal cargado se anula con motivo y queda registrado quién lo anuló; si estaba en un canon abonado, se ajusta en el próximo cierre. En tesorería se contraasienta con un egreso, sin borrar el ingreso |
| Devoluciones | No contempladas | No hay saldos a favor ni devoluciones. No se registra medio de pago ni se emiten recibos |
| Terminología | Hermanos | Hijos |

## Preguntas abiertas

No hay preguntas abiertas.

Resueltas:
- **Grupos por temporada y copia de grupos:** sección 4.
- **Contactos de emergencia por familia:** sección 3.
- **Anulación de un cobro en la tesorería:** sección 7.
- **Primera temporada:** sección 10.
- **Conservar todo vs. retención:** sección 10.
- **Fechas de Quincena y Semana:** sección 5.
- **Tarifa por turno:** sección 5.
- **Alta de usuarios y Coordinador**, incluido el alta de usuarios Profesor: sección 9.
- **Contactos de emergencia:** sección 3.
- **Cambio de categoría:** secciones 2 y 9.
- **Documentación obligatoria por temporada:** sección 8.
- **Alumno que vuelve en otra temporada:** sección 10.
- **Datos mínimos del alta y tutor obligatorio:** sección 3.
- **Qué hijos cuentan para el tramo del Mes:** lo define el PRD («Tarifario y cuenta corriente familiar»). Se cuenta por turno, "contando solo a los hermanos anotados en ese turno", y el porcentaje "se aplica a cada hermano sobre el valor base de su modalidad". Ver también "Hijo que se suma a mitad de temporada" en la sección 5.
