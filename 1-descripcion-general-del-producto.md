# 1. Descripción general del producto

> ⏳ **Pendiente:** 1.3 y 1.4. Se completan en los próximos pasos de la Entrega 1 (ver `prompts.md`).

> Fuentes: `docs/prd/prd-escuelita-de-verano.md` y `docs/prd/aclaraciones-cliente.md`. Cuando se contradicen, vale la aclaración.

### **1.1. Objetivo:**

**Qué es.** Un sistema web de administración para una escuelita de verano, que se usa desde celular y PC. Reemplaza la gestión manual de inscripciones, documentación, asistencia y cobros.

**Qué problema resuelve.** Hoy la información está repartida en planillas sueltas. El sistema resuelve tres problemas concretos:

1. **Ficha del alumno en un solo lugar:** datos personales, datos sensibles (alergias, condiciones médicas), documentación, personas autorizadas a retirarlo y contactos de emergencia.
2. **Cuentas claras:** la cuenta corriente de cada familia, con su saldo pendiente siempre visible; la tesorería general; y el canon que se le paga al club sede.
3. **Asistencia** por grupo, día y turno.

**Para quién.** Para el staff de la escuelita. Los padres no usan el sistema: la inscripción la hace siempre el staff. Hay tres roles:

- **Admin:** gestiona todo, y es el único que maneja cobros, tesorería, canon, tarifario y alta de usuarios en general. Puede haber varios.
- **Coordinador:** administra profesores y grupos, y registra alumnos de cualquier grupo. No ve nada contable.
- **Profesor:** registra alumnos, carga documentación y toma asistencia solo en los grupos que tiene asignados. No ve nada contable.

**Alcance a nivel producto.**

- El sistema se organiza por **temporada** (cada verano), con su propia configuración. No se borra nada entre temporadas:
  - Un alumno que vuelve reutiliza su ficha, su familia y sus tutores, y se lo inscribe de nuevo en los grupos.
  - La documentación obligatoria vuelve a quedar pendiente.
  - Las cuentas corrientes y la tesorería arrancan en cero.
  - La temporada anterior queda solo para consulta.
- La unidad de facturación es la **familia**: los hijos que asisten a la escuelita, con una sola cuenta corriente y una categoría (socio, empleado o no socio) que define los descuentos.
- Se cobra la **modalidad contratada** (Mes, Quincena, Semana o Día), asista o no el chico. La asistencia es solo control y no interviene en el cobro.
- Se protegen los datos sensibles de menores: acceso por rol y por grupo, archivos privados, consentimiento del tutor para cargar datos médicos, y registro de quién sube o modifica cada documento médico.

**Fuera de alcance:**

- Novedades o incidentes del día cargados por los profesores (candidato a mejora futura).
- Notificaciones automáticas a los padres: se sigue haciendo por WhatsApp.
- Recordatorios de pago automáticos.
- Auditoría general de cambios (salvo la trazabilidad de documentos médicos).
- Formulario público de inscripción para los padres.
- Emisión de comprobantes ARCA.
- Cupos máximos por grupo y lista de espera.
- Alias manual para distinguir familias con igual etiqueta (a futuro).

**Entrega.** Se construye el sistema completo. El backlog y el recorte de MVP de esta entrega están en [`docs/product/historias-backlog.md`](docs/product/historias-backlog.md). Las 3 historias documentadas con criterios de aceptación están en [`5-historias-de-usuario.md`](5-historias-de-usuario.md).

### **1.2. Características y funcionalidades principales:**

| Módulo | Qué hace |
|---|---|
| **Usuarios y roles** | El Admin da de alta y desactiva usuarios (el primer Admin se crea al instalar). El Coordinador da de alta a los profesores. Cada usuario ve y hace solo lo que permite su rol. |
| **Temporadas** | Cada verano tiene fecha de inicio y de cierre y su propia configuración. Al abrir una nueva se conservan alumnos, tutores y profesores; las inscripciones, la documentación obligatoria, las cuentas corrientes y la tesorería arrancan de nuevo; la anterior queda solo para consulta. |
| **Grupos y profesores** | Alta de grupos con nombre, turno (mañana o tarde) y rango de fechas de nacimiento. Asignación de uno o más profesores por grupo, y de uno o más grupos por profesor. |
| **Familias** | Agrupa a los hijos con una etiqueta automática "Apellido – Hijo mayor", una categoría (socio, empleado o no socio, que solo modifican los Admin) y una cuenta corriente única. |
| **Alumnos e inscripciones** | Alta con los datos mínimos (incluido al menos un tutor), y una ficha que se completa de a poco. El sistema sugiere el grupo según la fecha de nacimiento. Un alumno puede inscribirse en uno o en los dos turnos, y cada turno es una inscripción independiente. |
| **Personas autorizadas y contactos de emergencia** | Dos listas separadas: quién puede retirar al chico (incluye a los tutores, y una persona puede estar en varias familias) y a quién llamar en una emergencia. |
| **Documentación** | Adjuntos privados a la ficha (PDF, JPG o PNG, hasta 5 MB). El Admin define por temporada qué documentos son obligatorios. Cada ficha muestra qué le falta, y hay un listado de alumnos con documentación pendiente. |
| **Asistencia** | Registro de presencia por alumno, día y turno, para los grupos de cada profesor. |
| **Tarifario** | Configuración por temporada de: tarifa base por turno y modalidad, fechas de cada Mes, Quincena y Semana, descuentos por categoría (un % para Día, Semana y Quincena, y para el Mes un % por tramo de cantidad de hijos; siempre un único % sin acumular), y catálogo de tipos de cargo. |
| **Cuenta corriente familiar** | Registro de cargos (Preinscripción o Abono) y pagos (con pagos parciales) por parte del Admin, saldo pendiente de cada familia, y reporte de deudas. Un cobro mal cargado no se borra: se anula con motivo, y queda registrado quién lo anuló. |
| **Tesorería general** | Ingresos generados automáticamente por cada pago, y egresos cargados con descripción y monto, con el saldo disponible. |
| **Canon al club** | Cierre por rango de fechas sobre lo cobrado, con el detalle de los cobros y un % configurable. Al abonarlo se registra qué Admin lo pagó y se genera un egreso en tesorería. |

### **1.3. Diseño y experiencia de usuario:**

> Proporciona imágenes y/o videotutorial mostrando la experiencia del usuario desde que aterriza en la aplicación, pasando por todas las funcionalidades principales.

### **1.4. Instrucciones de instalación:**
> Documenta de manera precisa las instrucciones para instalar y poner en marcha el proyecto en local (librerías, backend, frontend, servidor, base de datos, migraciones y semillas de datos, etc.)
