# Aclaraciones del cliente sobre el PRD

Fuente complementaria de `prd-escuelita-de-verano.md`. Recoge las respuestas a la revisión adversarial del PRD (octubre 2026).

**Precedencia:** cuando una aclaración contradice al PRD, vale la aclaración. El PRD se mantiene como transcripción fiel del documento original y no se modifica.

---

## 1. Familia

- La familia agrupa a los hijos que asisten a la escuelita. La cuenta corriente es única por familia, sin importar qué adulto pague (los padres separados también pagan en una sola cuenta).
- La arma a mano quien carga al alumno. Al cargar el primer hijo se crea la familia; a partir del segundo se elige la familia existente a la que pertenece.
- Puede incluir medio hermanos con otro apellido.
- **Identificación:**
  - ID interno autogenerado al crear la familia, que nunca cambia.
  - Etiqueta visible "Apellido – Hijo mayor", que se recalcula automáticamente cuando cambia la composición de la familia. No es un campo editable.
  - A futuro, y fuera del MVP: un alias manual opcional para distinguir dos familias con el mismo apellido e igual hijo mayor.
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

## 4. Grupos

- Cada grupo tiene un nombre y un rango de fechas de nacimiento (desde/hasta).
- Al cargar un alumno, el sistema sugiere el grupo que corresponde por su fecha de nacimiento, y el usuario puede elegir otro.

## 5. Modalidades y tarifario

- Modalidades: **Mes, Quincena, Semana, Día**. "Mes" reemplaza a lo que el PRD llamaba "Período".
- El "Mes" son 4 semanas que definen los administradores con una fecha desde y una fecha hasta. Puede incluir días de otro mes calendario.
- La **Quincena** y la **Semana** también tienen fechas fijas (desde/hasta) definidas por los administradores.
- Se cobra la modalidad contratada, asista o no el chico. La asistencia no interviene en el cobro.
- **Se elimina** la regla "si asistió más de 3 días sueltos se cobra la semana". La tarifa por día va a quedar más cara que la semana.
- La pantalla de registrar cobro **no** muestra la asistencia.
- **Descuentos:**
  - Se aplican **solo a la modalidad Mes**.
  - Quincena, Semana y Día pagan la tarifa base sin descuento, incluso para socios.
  - Los porcentajes los configuran los administradores, por categoría y por cantidad de hijos.
- **Tarifa base:** se define por turno (mañana/tarde) y por modalidad. Sobre esa tarifa, el descuento del Mes se aplica según la cantidad de hijos de la familia.

## 6. Cargos y pagos

- Se mantienen los pagos parciales por cargo (por ejemplo, un % en la inscripción y el resto el primer día) y el reporte de deudas.
- Se espera que la familia haya pagado todo al ingresar a la modalidad contratada, así que no debería quedar deuda al terminar la temporada.

## 7. Tesorería y canon

- Cada pago registrado genera automáticamente un ingreso en la tesorería.
- **Canon:**
  - El porcentaje es configurable.
  - El cierre se hace por un rango desde/hasta, normalmente mensual, sobre todo lo cobrado en ese rango.
  - Abonar el canon genera automáticamente un **egreso** en la tesorería.

## 8. Ficha del alumno y documentación

- La ficha se considera **completa** cuando tiene el **certificado médico**. Es el **único documento obligatorio**; el resto de la documentación es adicional.
- El certificado médico **vale por una temporada**: en cada temporada nueva hay que presentar uno nuevo.
- Se puede cobrar aunque la ficha esté incompleta.

## 9. Roles y permisos

- Puede haber varios administradores.
- **Alta de usuarios:** los usuarios los da de alta un Admin. El primer Admin se crea al instalar el sistema.
- El **Coordinador también administra profesores**. Se mantiene lo del PRD ("Registrar profesores": Admin y Coordinador).
- "Administrar profesores" incluye que el Coordinador dé de alta el usuario de acceso con rol Profesor, y le asigne grupos. Los usuarios con rol Admin o Coordinador los da de alta solo un Admin.
- Solo los Admin registran cobros.
- Solo los Admin modifican la categoría de una familia.
- El profesor puede crear familias y ve los datos de los hijos que componen la familia. Esto queda limitado por la sección 11: no ve datos médicos ni documentos de hijos de otros grupos.

## 10. Temporadas y persistencia

- **Nueva definición:** se conservan todos los datos entre temporadas, y la base queda en stand-by cuando no se usa. No se borra nada, ni siquiera los datos médicos y documentos. Esto reemplaza lo que dice el PRD ("cada temporada arranca de cero"; "Historial o datos que persistan entre temporadas" estaba fuera de alcance).
- En la temporada siguiente se reemplazan los documentos vencidos, como el certificado médico (sección 8).
- Un alumno que vuelve en otra temporada reutiliza su ficha y su familia. Solo se renueva el certificado médico y se lo inscribe en los grupos y turnos de la nueva temporada.

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
- **MVP para la presentación (3 historias):**
  1. Alta de alumno con familia, persona autorizada y grupo-turno, con permisos por rol.
  2. Asistencia por grupo, día y turno.
  3. Registrar cargo y pago (con pagos parciales) y ver el saldo de la familia.

---

## Cambios respecto del PRD

| Tema | PRD | Aclaración |
|---|---|---|
| Modalidad de 4 semanas | "Período de 4 semanas" | "Mes", con fechas desde/hasta definidas por los Admin |
| Regla de 3 días | Más de 3 días sueltos se cobra como semana | Eliminada |
| Asistencia y cobro | La asistencia sirve de referencia; la pantalla de cobro debería mostrarla | Sin relación; no se muestra |
| Descuentos | Se aplican sobre la tarifa base de cada modalidad | Solo en la modalidad Mes |
| Categoría | Se determina por los tutores (socio si alguno es socio) | La asigna quien registra; prioridad socio > empleado > no socio; solo los Admin la modifican |
| Tutores | Tutores más personas autorizadas y de emergencia | Los tutores son personas autorizadas a retirar; los contactos de emergencia son una lista aparte |
| Quincena / Semana | Sin definición de fechas | Fechas fijas definidas por los Admin |
| Usuarios | No especificado | Los da de alta un Admin; el primer Admin se crea al instalar; el Coordinador también administra profesores |
| Documentación obligatoria | Ficha médica, DNI y otros certificados | Solo el certificado médico es obligatorio y vale por temporada |
| Grupos | Por franja de edad | Por rango de fechas de nacimiento, con sugerencia automática |
| Temporadas | Cada temporada arranca de cero | Se conservan todos los datos, sin borrar nada; los documentos vencidos se reemplazan en la temporada siguiente |
| Canon | Cuenta aparte de la tesorería | Abonar el canon genera un egreso en tesorería |
| Terminología | Hermanos | Hijos |

## Preguntas abiertas

No hay preguntas abiertas.

Resueltas: conservar todo vs. retención (sección 10), fechas de Quincena y Semana (sección 5), tarifa por turno (sección 5), alta de usuarios y Coordinador, incluido el alta de usuarios Profesor (sección 9), contactos de emergencia (sección 3), cambio de categoría (secciones 2 y 9), vigencia del certificado médico (sección 8) y alumno que vuelve en otra temporada (sección 10).
