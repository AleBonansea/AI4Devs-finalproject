# CLAUDE.md

## Producto

Sistema de administración para la escuelita de verano del club sede: gestiona fichas de alumnos, documentación, asistencia por grupo y turno, cuenta corriente por familia, tesorería general y canon al club, por temporada. Fuentes de verdad: `docs/prd/prd-escuelita-de-verano.md` (transcripción fiel del PRD, no se modifica) y lo confirmado en `docs/prd/aclaraciones-cliente.md`, que prevalece sobre el PRD cuando se contradicen.

## Roles

- **Admin** (puede haber varios; el primero se crea al instalar el sistema):
  - Da de alta usuarios de cualquier rol, y puede desactivarlos.
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
- **Temporada**: agrupa la configuración, las inscripciones y los movimientos de cada verano.
- **Usuario**:
  - Tiene un rol: Admin, Coordinador o Profesor.
  - Se puede activar y desactivar.
  - Un Profesor se asigna a uno o más grupos, y un grupo puede tener varios profesores.
- **Grupo**: nombre, turno (mañana o tarde) y rango de fechas de nacimiento (desde/hasta). Se usa para sugerir el grupo al cargar un alumno.

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
  - Si vuelve en otra temporada, reutiliza su ficha.
- **Inscripción**: alumno × grupo/turno × temporada. Cada turno es una inscripción independiente.
- **Persona autorizada a retirar**: incluye a los tutores. Puede estar autorizada en más de una familia.
- **Contacto de emergencia**: lista aparte de las personas autorizadas.
- **Documento**:
  - Archivo privado (PDF, JPG o PNG, hasta 5 MB) adjunto a la ficha.
  - El certificado médico es el único obligatorio y vale por temporada.
  - Se guarda quién lo subió o modificó, y cuándo.
- **Asistencia**: presencia por alumno, día y turno. No interviene en el cobro.

**Tarifario y cobros**
- **Período de cobro**: fechas desde/hasta de cada Mes (4 semanas), Quincena y Semana, definidas por los Admin. La modalidad Día no tiene rango.
- **Tarifa base**: por temporada, turno y modalidad (Mes, Quincena, Semana, Día).
- **Descuento**:
  - Porcentaje por categoría y cantidad de hijos (1, 2, 3, 4 o más).
  - Se aplica solo a la modalidad Mes.
  - Los hijos se cuentan por turno.
- **Tipo de cargo**: catálogo configurable por temporada (por ejemplo, Preinscripción o Mes).
- **Cargo**: lo que se le cobra a la familia, según tipo, modalidad y monto.
- **Pago**:
  - Se permiten pagos parciales por cargo.
  - Lo registra solo un Admin.
  - Cada pago genera un ingreso en tesorería.
- **Cuenta corriente familiar**: cargos y pagos de la familia, con su saldo pendiente. Es la fuente del reporte de deudas.

**Tesorería y canon**
- **Movimiento de tesorería**:
  - Ingreso (automático por cada pago) o egreso (descripción y monto, sin categorías).
  - El saldo disponible sale de los movimientos.
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
   - Lo que no aparece en ninguno de los dos archivos se marca como **[SUPUESTO]** y se registra como pregunta abierta en `aclaraciones-cliente.md`.
