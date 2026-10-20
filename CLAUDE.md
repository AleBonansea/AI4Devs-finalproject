# CLAUDE.md

## Producto

Sistema de administración para la escuelita de verano del club sede: gestiona fichas de alumnos, documentación, asistencia por grupo y turno, cuenta corriente por familia, tesorería general y canon al club, por temporada. Fuentes de verdad: `docs/prd/prd-escuelita-de-verano.md` (transcripción fiel del PRD, no se modifica) y lo confirmado en `docs/prd/aclaraciones-cliente.md`, que prevalece sobre el PRD cuando se contradicen.

## Roles

- **Admin** (puede haber varios; el primero se crea al instalar el sistema):
  - Da de alta usuarios de cualquier rol, puede desactivarlos y les blanquea la contraseña.
  - Administra profesores y grupos.
  - Registra alumnos en cualquier grupo, carga documentación y gestiona asistencia.
  - Es el único rol que registra cobros y ve la cuenta corriente familiar y la tesorería.
  - Es el único que modifica la categoría de una familia ya asignada.
  - Configura el tarifario, los descuentos, las fechas de Mes, Quincena y Semana, y el % del canon.
  - Hace el cierre del canon y lo abona, lo que genera un egreso en tesorería.
- **Coordinador**:
  - Administra profesores (incluye dar de alta su usuario con rol Profesor y asignarles grupos) y grupos.
  - Registra alumnos en cualquier grupo, crea familias, carga documentación y gestiona asistencia.
  - **No** ve la cuenta corriente familiar, la tesorería ni los cobros.
- **Profesor**:
  - Registra alumnos, carga documentación y gestiona asistencia solo en los grupos que tiene asignados.
  - Puede crear familias y asignar la categoría al registrar.
  - Ve alergias y condiciones médicas solo de los alumnos de sus grupos. De los hijos de la misma familia en otros grupos ve los datos de familia y las personas autorizadas, pero no los datos médicos ni los documentos.
  - No administra profesores ni grupos, y no ve nada contable.

## Entidades principales

Los datos se conservan entre temporadas: no se borra nada.

**Personas y estructura**
- **Temporada**:
  - La primera se crea en la puesta en marcha, junto con el primer Admin.
  - Tiene fecha de inicio y de cierre.
  - Tiene su propia configuración: tarifa base, tabla de descuentos, % de canon, tipos de cargo y documentos obligatorios.
  - Al abrir una nueva: se pueden copiar los grupos de la anterior; se conservan alumnos, tutores y profesores con sus usuarios; las inscripciones a grupos se hacen de nuevo; toda la documentación vuelve a quedar pendiente; y las cuentas corrientes y la tesorería arrancan en cero.
  - La temporada anterior queda solo para consulta.
- **Usuario**:
  - Tiene un rol: Admin, Coordinador o Profesor.
  - Se puede activar y desactivar.
  - Acceso: cambio obligatorio de contraseña en el primer ingreso y después de un blanqueo. Solo un Admin blanquea contraseñas. El usuario queda bloqueado tras 5 intentos fallidos seguidos, hasta que se le blanquee la contraseña.
  - Un Profesor se asigna a uno o más grupos, y un grupo puede tener varios profesores.
- **Grupo**:
  - Nombre, turno (mañana o tarde) y rango de fechas de nacimiento (desde/hasta). El rango se usa para sugerir el grupo al cargar un alumno.
  - Es por temporada, porque el rango se corre cada año. Al abrir una temporada nueva se pueden copiar los grupos de la anterior.

**Familia y alumnos**
- **Familia**:
  - ID interno que nunca cambia.
  - Etiqueta visible "Apellido – Hijo mayor", que se recalcula sola y no se edita.
  - Categoría: socio, empleado o no socio.
  - Tiene una única cuenta corriente.
  - Se crea al cargar el primer hijo.
- **Alumno (hijo)**:
  - Pertenece a una familia.
  - Datos personales, fecha de nacimiento y datos sensibles (alergias, condiciones médicas).
  - Registro del consentimiento del tutor para cargar datos médicos.
  - Datos mínimos del alta: nombre, apellido, fecha de nacimiento, familia, **al menos un tutor**, y grupo y turno. La documentación no forma parte del mínimo.
  - Si vuelve en otra temporada, reutiliza su ficha, su familia y sus tutores, pero se lo inscribe de nuevo en los grupos.
- **Inscripción**: alumno × grupo/turno × temporada. Cada turno es una inscripción independiente.
- **Persona autorizada a retirar**: incluye a los tutores. Puede estar autorizada en más de una familia.
- **Contacto de emergencia**: lista aparte de las personas autorizadas. Es de la familia: los hermanos lo comparten.
- **Documento**:
  - Archivo privado (PDF, JPG o PNG, hasta 5 MB) adjunto a la ficha.
  - Checklist configurable: el Admin define por temporada qué documentos son obligatorios (por ejemplo, ficha médica, DNI o autorización de salidas). También se pueden adjuntar otros no obligatorios.
  - La ficha está completa cuando tiene todos los obligatorios de la temporada. Al abrir una temporada nueva todos vuelven a quedar pendientes, incluido el carnet de socio.
  - Se puede cobrar aunque la ficha esté incompleta.
  - Se guarda quién lo subió o modificó, y cuándo.
- **Asistencia**: presencia por alumno, día y turno. No interviene en el cobro.

**Tarifario y cobros**
- **Período de cobro**: fechas desde/hasta de cada Mes (4 semanas), Quincena y Semana, definidas por los Admin. La modalidad Día no tiene rango.
- **Tarifa base**: por temporada, turno y modalidad (Mes, Quincena, Semana, Día).
- **Descuento**: tabla paramétrica por temporada, con una fila por categoría (socio, empleado, no socio).
  - Un % por categoría para Día, Semana y Quincena. La cantidad de hijos no interviene.
  - Un % por categoría y tramo de hijos (1, 2, 3, 4 o más), solo para el Mes.
  - Se aplica un único porcentaje a la tarifa base, nunca acumulado.
  - El % del tramo alcanza a todos los hijos de la familia, no solo al que supera el tramo.
  - Los hijos se cuentan por turno.
- **Tipo de cargo**: catálogo configurable por temporada (por ejemplo, Preinscripción o Abono).
- **Cargo**: lo que se le cobra a la familia, según tipo, modalidad y monto.
- **Pago**:
  - Se permiten pagos parciales por cargo.
  - Lo registra solo un Admin.
  - Cada pago genera un ingreso en tesorería.
- **Cuenta corriente familiar**: cargos y pagos de la familia, con su saldo pendiente. Es la fuente del reporte de deudas.

**Tesorería y canon**
- **Movimiento de tesorería**:
  - Ingreso (automático por cada pago, desde la Entrega 1) o egreso (descripción y monto, sin categorías).
  - Anular un cobro no borra su ingreso: se contraasienta con un egreso automático por el mismo monto, y el neto queda en cero.
  - Ningún movimiento se modifica ni se borra. El saldo disponible sale de los movimientos.
- **Cierre de canon**:
  - Rango desde/hasta, total cobrado en ese rango, % configurable y monto a abonar.
  - Se guarda qué Admin lo abonó.
  - Al abonarlo se genera un egreso en tesorería.

## Reglas de proceso

1. La Entrega 1 es solo documentación: nada de código.
2. La documentación vive en los archivos numerados `0-ficha-del-proyecto.md` a `7-pull-requests.md` de la raíz; `readme.md` es solo el índice.
3. Los prompts reales que usemos se registran en `prompts.md` (máximo 3 por sección).
4. Todo en español.
5. Lo que no esté en las fuentes de verdad se marca como **[SUPUESTO]**:
   - Lo **confirmado** en `aclaraciones-cliente.md` es fuente de verdad y no lleva la marca.
   - Lo que en `aclaraciones-cliente.md` figura como **[SUPUESTO]** o como pregunta abierta **no** es fuente de verdad: está pensado y pendiente de confirmar con el cliente. Al usarlo se sigue marcando como **[SUPUESTO]**, pero se referencia esa entrada en lugar de tratarlo como algo no documentado.
   - Lo que no aparece en ninguno de los dos archivos y es una **regla de negocio** (qué hace el sistema, qué pasa en un caso) se marca como **[SUPUESTO]** y se registra como pregunta abierta en `aclaraciones-cliente.md`.
   - Las **decisiones de diseño** (nulabilidad, tipos, índices, cómo se modela algo) no son preguntas para el cliente: se documentan con su justificación en el archivo donde se toman (por ejemplo, `3-modelo-de-datos.md`), sin marca y sin pasar por `aclaraciones-cliente.md`.
