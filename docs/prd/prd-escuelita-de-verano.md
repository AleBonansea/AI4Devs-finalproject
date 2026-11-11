# PRD — Sistema de Administración, Escuelita de Verano

Sep 30, 2026 · preparado por @ Ale

## Resumen y objetivo

Sistema de administración para la escuelita de verano que organiza el cuñado de Ale, para reemplazar la gestión manual de inscripciones, documentación, asistencia y cobros.

Resuelve tres problemas concretos: tener la ficha completa de cada alumno (datos, documentación, tutores autorizados) en un solo lugar; llevar la cuenta corriente de cada familia y la tesorería general sin depender de planillas sueltas; y registrar la asistencia por grupo y turno.

El sistema se usa por temporada: cada verano arranca sin datos de la temporada anterior (alumnos, documentación y cuentas se cargan de nuevo).

## Roles y permisos

Tres roles, con acceso creciente salvo en lo contable, donde el Coordinador queda al mismo nivel que el Profesor.

| Acción | Admin | Coordinador | Profesor |
|---|---|---|---|
| Registrar profesores | Sí | Sí | No |
| Registrar grupos | Sí | Sí | No |
| Registrar alumnos | Sí (cualquier grupo) | Sí (cualquier grupo) | Solo en los grupos que tiene asignados |
| Cargar documentación del alumno | Sí | Sí | Sí, de sus grupos |
| Gestionar asistencia | Sí | Sí | Sí, de sus grupos |
| Ver cuenta corriente familiar y tesorería | Sí | No | No |

Un grupo puede tener más de un profesor asignado, y un profesor puede tener asignado más de un grupo (incluso uno a la mañana y otro a la tarde).

## Alumnos, tutores y documentación

La inscripción la hace siempre el staff (Admin, Coordinador o Profesor según el grupo) — no hay formulario público para que los padres se anoten solos.

Ficha del alumno: datos personales, grupo(s) y turno(s) asignados, datos sensibles (alergias, condiciones médicas) y contactos. Se completa de forma progresiva: se crea con lo mínimo al anotarse y se va editando a medida que entregan documentación.

Tutores: al menos uno por alumno, más las personas autorizadas a retirarlo o a ser llamadas en caso de emergencia.

Documentación: ficha médica, DNI y otros certificados que se suban (por ejemplo, un certificado médico específico), adjuntos a la ficha del alumno.

Categoría de la familia (socio / empleado / no socio, ver Tarifario): se define a nivel familia por los tutores, no por alumno: los chicos no tienen carnet propio. Si al menos uno de los tutores de la familia es socio (típicamente quien trabaja en el centro médico y se afilia), toda la familia — incluidos todos los hermanos — entra en la categoría socio. La verificación es manual, contra el carnet del tutor, sin integración con el sistema de socios del club.

## Grupos, turnos y asistencia

Los grupos se arman por franja de edad, y cada grupo tiene turno mañana o tarde. Un alumno puede estar anotado en ambos turnos; a efectos de asistencia y facturación cada turno se trata como una inscripción independiente. No hay cupo máximo ni lista de espera.

La asistencia registra presencia por día y por turno. No dispara automáticamente cobros ni avisos a los padres; sirve como referencia para quien registra el cobro del período (ver Tarifario y cuenta corriente).

## Tarifario y cuenta corriente familiar

Los alumnos se agrupan por familia (hermanos) a los efectos de facturación; la cuenta corriente es única por familia.

Categoría de familia: socio, empleado o no socio. Es un dato único por familia, no por alumno: los chicos no tienen carnet propio. Se determina por los tutores — si al menos uno de los tutores de la familia es socio, toda la familia entra en la categoría socio, incluidos todos los hermanos.

Tarifario configurable por temporada: dos tablas separadas, ambas editables por el administrador. Una tarifa base por turno (mañana/tarde) y modalidad (día / semana / quincena / período de 4 semanas), igual para todas las categorías. Y una tabla de descuentos por categoría y cantidad de hermanos (1, 2, 3, 4 o más) que define el % a aplicar sobre esa tarifa base — el % no sigue una fórmula fija (ejemplo ilustrativo dado por el cliente: socio 50% fijo sin importar la cantidad de hijos; empleado 10% / 15% / 20% / 25% según tenga 1, 2, 3 o 4+ hijos; no socio 0% / 10% / 15% / 20%). El % que corresponda a la familia se aplica a cada hermano sobre el valor base de su modalidad.

Cada turno se factura de forma independiente, contando solo a los hermanos anotados en ese turno: por ejemplo, si un hermano va a los dos turnos y el otro solo a la mañana, el turno mañana calcula la tarifa como 2 hermanos y el turno tarde como 1 hermano.

Modalidad: se puede sugerir al anotar al alumno, pero se confirma recién al momento de registrar el cobro — no hay cálculo automático en base a la asistencia. Si un alumno asistió más de 3 días sueltos, ya se cobra como semana completa; entre semana, quincena y período no hay conversión automática, se elige directamente. La pantalla de registrar el cobro debería mostrar los días de asistencia del período, como ayuda para decidir la modalidad.

Tipos de cargo: catálogo configurable por temporada (por ejemplo: Preinscripción, Período) — no hay un esquema fijo de "seña".

Pagos: se permiten varios pagos parciales por cargo hasta saldar el total (la mayoría paga todo junto, pero el sistema debe soportarlo). En todo momento se debe poder ver el saldo pendiente de cada familia. No hay recordatorios automáticos de pago; el seguimiento se hace desde el reporte de deudas.

## Tesorería general

Módulo separado de la cuenta corriente familiar: registra los ingresos (cobros) y los egresos (sueldos, gastos de festejos, insumos u otros) con un saldo general disponible. Cada egreso se carga con descripción y monto, sin categorías.

## Cuenta corriente del canon al club

Se le paga al club sede un canon equivalente a un porcentaje sobre lo efectivamente cobrado a cada alumno que pagó. Se lleva como una cuenta corriente aparte de la tesorería general, visible para los administradores, con el detalle de cómo se compone el monto.

El cierre del canon lo inicia el administrador cuando quiere, con la periodicidad que elija (quincenal o mensual, a su criterio). Al iniciar el cierre de un período, el sistema muestra el total cobrado en ese rango de fechas, permite ver el detalle de los cobros que lo componen, y calcula el monto de canon a abonar al club. Un botón de "abonar" registra el pago, dejando constancia de qué usuario lo realizó.

## Fuera de alcance de esta versión

- Novedades/incidentes del día cargados por los profesores (candidato a mejora futura).
- Notificaciones automáticas a los padres (circulares, avisos) — se sigue haciendo por WhatsApp.
- Recordatorios de pago automáticos.
- Auditoría de cambios (quién modificó qué dato y cuándo).
- Formulario público de inscripción para que los padres se anoten solos.
- Historial o datos que persistan entre temporadas: cada temporada arranca de cero.
- Emisión de comprobantes ARCA desde el sistema.
- Cupos máximos por grupo o lista de espera.

## Supuestos y puntos a validar con el cliente

- La verificación de la categoría socio es manual, mirando el carnet que presenta la familia, sin integración con el sistema de socios del club.
- La categoría no se mezcla entre hermanos: es un dato de la familia (ver Alumnos, tutores y documentación), determinado por si algún tutor es socio.
- Los tipos de cargo (preinscripción, período, u otros) se definen libremente por temporada; no se asume que siempre exista una "seña" fija como la del arancel 2025-26 adjuntado como referencia.
