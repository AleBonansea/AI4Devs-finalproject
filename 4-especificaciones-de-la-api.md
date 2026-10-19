# 4. Especificación de la API

> Son 3 endpoints, uno por cada historia documentada en [`5-historias-de-usuario.md`](5-historias-de-usuario.md). Los nombres de entidades y campos son los de [`3-modelo-de-datos.md`](3-modelo-de-datos.md). El stack es FastAPI + Pydantic v2 ([`docs/architecture/documento-tecnico.md`](docs/architecture/documento-tecnico.md)).

## Convenciones

- **Autenticación:** todos los endpoints exigen el token de acceso JWT en `Authorization: Bearer <token>` (documento técnico, «Contraseñas y sesión»). El control de permisos se hace en la API, nunca solo en el frontend.
- **Rutas:** el prefijo es `/api/v1`, los recursos van en plural y los identificadores de la base viajan en la ruta o en el cuerpo con el mismo nombre que la columna (`grupo_id`, `familia_id`, …).
- **Tipos en JSON:**
  - Las fechas son ISO 8601: `date` como `"2027-01-05"` y `timestamptz` con zona horaria.
  - Los montos y porcentajes son `Decimal` en Pydantic, y viajan como **string** (`"85000.00"`) para no perder precisión. Es lo que hace Pydantic v2 en modo JSON.
- **Errores:**
  - `401`: no hay token, el token venció o el usuario está desactivado.
  - `403`: el rol no puede usar el endpoint, o el Profesor actúa sobre un grupo que no tiene asignado.
  - `404`: no existe un recurso referenciado (`grupo_id`, `familia_id`, …).
  - `409`: el pedido es válido, pero choca con el estado actual. Por ejemplo, una temporada `cerrada` (solo consulta) o una configuración que falta.
  - `422`: los datos no cumplen las reglas. Hay dos formatos:
    - Si la regla se puede validar con el cuerpo solo (un campo que falta, una combinación inválida), FastAPI devuelve su formato estándar: `{"detail": [{"loc", "msg", "type"}]}`.
    - Si la regla necesita consultar la base (por ejemplo, una inscripción que no es de ese grupo), devuelve `{"detail": "mensaje"}`.

## Resumen

| Historia | Método y ruta | Quién puede usarlo | Éxito |
|---|---|---|---|
| HU-AF-01 | `POST /api/v1/alumnos` | Admin y Coordinador en cualquier grupo; Profesor solo en sus grupos | `201` alumno creado e inscripto |
| HU-GA-04 | `PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}` | Admin y Coordinador en cualquier grupo; Profesor solo en sus grupos | `200` asistencia registrada |
| HU-CC-01 | `POST /api/v1/cargos` | Solo Admin | `201` cargo registrado (`200` si se usa `simular=true`) |

### Errores por endpoint y escenario

En cada fila, el escenario indica de qué criterio de aceptación de `5-historias-de-usuario.md` sale el error. "Regla" indica que sale de una regla del modelo de datos.

**`POST /api/v1/alumnos` (HU-AF-01)**

| Código | Cuándo | Origen |
|---|---|---|
| 403 | Un Profesor inscribe en un grupo que no tiene asignado | Escenario 5 |
| 404 | No existe el `grupo_id`, el `familia_id` o un `persona_id` | — |
| 409 | El grupo es de una temporada `cerrada` | Acl. 10 |
| 409 | El grupo está inactivo | Modelo, `grupo.activo` |
| 409 | Ya existe una persona con ese `dni` | Modelo, `persona.dni` UNIQUE |
| 422 | Falta nombre, apellido, fecha de nacimiento o `grupo_id` | Escenario 7 |
| 422 | Familia nueva sin `categoria` o sin ningún tutor | Escenario 7; Acl. 3 |
| 422 | Se envía `categoria` junto con una familia existente | Escenario 6; solo un Admin la modifica |

**`PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}` (HU-GA-04)**

| Código | Cuándo | Origen |
|---|---|---|
| 403 | Un Profesor toma asistencia de un grupo que no tiene asignado | Escenario 6 |
| 404 | No existe el `grupo_id` | — |
| 409 | El grupo es de una temporada `cerrada` | Acl. 10 |
| 422 | La `fecha` está fuera de la temporada | Regla de `asistencia` |
| 422 | Una `inscripcion_id` no es de ese grupo, o está repetida en el cuerpo | Escenarios 1 y 2 |
| 422 | La lista llega vacía | Escenario 4 |

**`POST /api/v1/cargos` (HU-CC-01)**

| Código | Cuándo | Origen |
|---|---|---|
| 403 | Quien lo usa es Coordinador o Profesor | Escenario 11 |
| 404 | No existe el alumno, el tipo de cargo, la inscripción o el período | — |
| 409 | El tipo de cargo es de una temporada `cerrada` | Escenario 10 |
| 409 | Falta la tarifa base para ese turno y modalidad | Escenario 9 |
| 409 | Falta el % de descuento que corresponde | Escenario 9, por extensión |
| 422 | Los campos no cumplen la forma que corresponde a la Preinscripción o al Abono | Reglas de `cargo` |
| 422 | El período es de otra modalidad | Regla de `cargo` |
| 422 | La inscripción no es del alumno | Regla de `cargo` |

## Especificación OpenAPI

```yaml
openapi: 3.1.0
info:
  title: API Escuelita de Verano
  version: 0.1.0
  description: >
    Recorte de 3 endpoints, uno por cada historia documentada en
    5-historias-de-usuario.md (HU-AF-01, HU-GA-04 y HU-CC-01).
servers:
  - url: /
    description: Mismo dominio que el servicio web FastAPI (Render).
tags:
  - name: Alumnos
    description: Alta de alumnos, familias e inscripciones.
  - name: Asistencia
    description: Presencia por grupo, día y turno.
  - name: Cargos
    description: Cuenta corriente familiar, cargos con cálculo de tarifa y descuento.
security:
  - bearerAuth: []

paths:
  /api/v1/alumnos:
    post:
      tags: [Alumnos]
      operationId: crear_alumno
      summary: Alta de alumno con familia, grupo y turno (HU-AF-01)
      description: |
        Crea el alumno y su inscripción en el grupo, en una sola transacción.
        El turno y la temporada salen del grupo.

        - Familia nueva: `familia_id` es null. Hay que mandar `categoria` y al
          menos una persona con `es_tutor = true` (Acl. 3). La familia se crea
          con el alumno.
        - Familia existente: se manda `familia_id` y no se manda `categoria`,
          porque solo un Admin la modifica (Acl. 2, 9). El alumno queda
          cubierto por los tutores que la familia ya tiene. `personas` es
          opcional y sirve para sumar vínculos a la familia.
        - Cada elemento de `personas` puede ser una persona nueva (`nombre`,
          `apellido`, `telefono`) o una ya cargada en otra familia
          (`persona_id`, Acl. 3).
        - Si `es_tutor` es true, `autorizado_retiro` se guarda como true
          (CHECK de `familia_persona`).
        - El rango de nacimiento del grupo solo orienta: se acepta un grupo
          fuera de rango (escenario 4).
        - La documentación no forma parte del alta.

        Permisos: Admin y Coordinador en cualquier grupo; Profesor solo en
        grupos que tiene asignados en `grupo_profesor`.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AlumnoCreate'
            examples:
              primer_hijo:
                summary: Primer hijo, se crea la familia (escenario 1)
                value:
                  nombre: Juan
                  apellido: Pérez
                  fecha_nacimiento: '2018-03-10'
                  familia_id: null
                  categoria: empleado
                  personas:
                    - nombre: María
                      apellido: Pérez
                      telefono: '351 555-1234'
                      dni: null
                      es_tutor: true
                      autorizado_retiro: true
                  grupo_id: 3
              segundo_hijo:
                summary: Segundo hijo, familia existente (escenario 2)
                value:
                  nombre: Ana
                  apellido: Pérez
                  fecha_nacimiento: '2016-07-05'
                  familia_id: 12
                  grupo_id: 4
      responses:
        '201':
          description: Alumno creado e inscripto.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AlumnoCreado'
              examples:
                primer_hijo:
                  summary: Se creó la familia «Pérez – Juan»
                  value:
                    id: 41
                    familia_id: 12
                    nombre: Juan
                    apellido: Pérez
                    fecha_nacimiento: '2018-03-10'
                    familia:
                      id: 12
                      categoria: empleado
                      etiqueta: 'Pérez – Juan'
                    inscripcion:
                      id: 88
                      grupo_id: 3
                      temporada_id: 1
                      turno: manana
                    personas:
                      - persona_id: 20
                        es_tutor: true
                        autorizado_retiro: true
                        contacto_emergencia: false
                segundo_hijo:
                  summary: La etiqueta pasa a «Pérez – Ana»
                  value:
                    id: 42
                    familia_id: 12
                    nombre: Ana
                    apellido: Pérez
                    fecha_nacimiento: '2016-07-05'
                    familia:
                      id: 12
                      categoria: empleado
                      etiqueta: 'Pérez – Ana'
                    inscripcion:
                      id: 91
                      grupo_id: 4
                      temporada_id: 1
                      turno: manana
                    personas:
                      - persona_id: 20
                        es_tutor: true
                        autorizado_retiro: true
                        contacto_emergencia: false
        '401':
          $ref: '#/components/responses/NoAutenticado'
        '403':
          description: El Profesor intenta inscribir en un grupo que no tiene asignado (escenario 5). No se crea el alumno ni la familia.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                detail: No tenés asignado el grupo 4.
        '404':
          description: No existe el grupo, la familia o alguna de las personas indicadas.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                detail: No existe la familia 99.
        '409':
          description: El pedido choca con el estado actual.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              examples:
                temporada_cerrada:
                  summary: El grupo es de una temporada cerrada (Acl. 10)
                  value:
                    detail: La temporada 2025-26 está cerrada y queda solo para consulta.
                grupo_inactivo:
                  summary: El grupo fue dado de baja
                  value:
                    detail: El grupo 3 está inactivo y no admite inscripciones.
                dni_duplicado:
                  summary: Ya existe una persona con ese DNI
                  value:
                    detail: Ya existe una persona con DNI 28123456 (persona_id 20). Usá persona_id para vincularla.
        '422':
          description: Faltan datos mínimos o no cumplen las reglas del alta (escenario 7).
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
              examples:
                falta_fecha:
                  summary: Falta la fecha de nacimiento
                  value:
                    detail:
                      - type: missing
                        loc: [body, fecha_nacimiento]
                        msg: Field required
                familia_nueva_sin_tutor:
                  summary: Familia nueva sin ningún tutor (Acl. 3)
                  value:
                    detail:
                      - type: value_error
                        loc: [body]
                        msg: 'Value error, Una familia nueva necesita al menos una persona con es_tutor = true.'
                familia_nueva_sin_categoria:
                  summary: Familia nueva sin categoría
                  value:
                    detail:
                      - type: value_error
                        loc: [body]
                        msg: 'Value error, Una familia nueva necesita la categoria.'
                categoria_con_familia_existente:
                  summary: Se envía categoría para una familia existente (escenario 6)
                  value:
                    detail:
                      - type: value_error
                        loc: [body]
                        msg: 'Value error, La categoria solo se asigna al crear la familia. Para cambiarla, la tiene que modificar un Admin.'

  /api/v1/grupos/{grupo_id}/asistencias/{fecha}:
    put:
      tags: [Asistencia]
      operationId: registrar_asistencia
      summary: Tomar asistencia de un grupo para un día y turno (HU-GA-04)
      description: |
        Registra o corrige la asistencia de un grupo en una fecha. El turno es
        el del grupo, porque cada grupo tiene un solo turno.

        - Es idempotente: crea o actualiza un registro por inscripción y fecha
          (`UNIQUE (inscripcion_id, fecha)`). Corregir no duplica registros
          (escenario 2).
        - Las inscripciones que no vienen en el cuerpo no se modifican.
        - Un alumno inscripto en los dos turnos tiene una inscripción en cada
          grupo, así que su asistencia de cada turno se registra por separado
          (escenario 3).
        - No genera ni modifica cargos, y no envía avisos (escenario 5,
          Acl. 5).

        Permisos: Admin y Coordinador en cualquier grupo, aunque no tengan
        grupos asignados (escenario 7); Profesor solo en sus grupos.
      parameters:
        - name: grupo_id
          in: path
          required: true
          schema:
            type: integer
          example: 3
        - name: fecha
          in: path
          required: true
          description: Día de la asistencia. Tiene que estar dentro de la temporada del grupo.
          schema:
            type: string
            format: date
          example: '2027-01-05'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AsistenciaLoteIn'
            examples:
              toma:
                summary: Juan y Sofía presentes, Martín ausente (escenario 1)
                value:
                  asistencias:
                    - inscripcion_id: 88
                      presente: true
                    - inscripcion_id: 89
                      presente: true
                    - inscripcion_id: 90
                      presente: false
              correccion:
                summary: Martín pasa a presente (escenario 2)
                value:
                  asistencias:
                    - inscripcion_id: 90
                      presente: true
      responses:
        '200':
          description: Asistencia registrada. Devuelve los registros de esa fecha para las inscripciones enviadas.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AsistenciaLoteOut'
              example:
                grupo_id: 3
                fecha: '2027-01-05'
                turno: manana
                asistencias:
                  - id: 501
                    inscripcion_id: 88
                    fecha: '2027-01-05'
                    presente: true
                    registrado_por: 7
                    registrado_en: '2027-01-05T09:12:40-03:00'
                  - id: 502
                    inscripcion_id: 89
                    fecha: '2027-01-05'
                    presente: true
                    registrado_por: 7
                    registrado_en: '2027-01-05T09:12:40-03:00'
                  - id: 503
                    inscripcion_id: 90
                    fecha: '2027-01-05'
                    presente: false
                    registrado_por: 7
                    registrado_en: '2027-01-05T09:12:40-03:00'
        '401':
          $ref: '#/components/responses/NoAutenticado'
        '403':
          description: El Profesor intenta tomar asistencia de un grupo que no tiene asignado (escenario 6). No se registra nada.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                detail: No tenés asignado el grupo 5.
        '404':
          description: No existe el grupo.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                detail: No existe el grupo 99.
        '409':
          description: El grupo es de una temporada cerrada, que queda solo para consulta (Acl. 10).
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                detail: La temporada 2025-26 está cerrada y queda solo para consulta.
        '422':
          description: Los datos no cumplen las reglas de la asistencia.
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: '#/components/schemas/HTTPValidationError'
                  - $ref: '#/components/schemas/Error'
              examples:
                lista_vacia:
                  summary: No hay alumnos para registrar (escenario 4)
                  value:
                    detail:
                      - type: too_short
                        loc: [body, asistencias]
                        msg: List should have at least 1 item after validation, not 0
                inscripcion_repetida:
                  summary: La misma inscripción viene dos veces en el cuerpo
                  value:
                    detail:
                      - type: value_error
                        loc: [body, asistencias]
                        msg: 'Value error, La inscripcion_id 88 está repetida.'
                inscripcion_ajena:
                  summary: Una inscripción no es de ese grupo
                  value:
                    detail: La inscripcion_id 120 no pertenece al grupo 3.
                fecha_fuera_de_temporada:
                  summary: La fecha está fuera de la temporada del grupo
                  value:
                    detail: La fecha 2027-04-01 está fuera de la temporada 2026-27.

  /api/v1/cargos:
    post:
      tags: [Cargos]
      operationId: registrar_cargo
      summary: Registrar un cargo con cálculo de tarifa y descuento (HU-CC-01)
      description: |
        Registra un cargo a la familia del alumno. El cliente indica qué se
        cobra, y la API calcula y guarda el resultado. El cálculo queda
        congelado en el cargo y no se recalcula nunca (Acl. 5). Datos que
        calcula la API:

        - `familia_id`: sale del alumno.
        - `temporada_id`: sale del tipo de cargo.
        - `categoria_aplicada`: la categoría actual de la familia.
        - `cantidad_hijos_aplicada`: solo en el Mes. Cuenta las inscripciones
          de la familia en ese turno y temporada al momento del cargo. Se
          cuenta por turno, "contando solo a los hermanos anotados en ese
          turno" (PRD).
        - `monto_base`, `porcentaje_aplicado` y `monto_total`.

        Cómo se calcula según el tipo de cargo:

        - Preinscripción (`tipo_cargo.calculo = monto_fijo`):
          - `monto_base` es `tipo_cargo.monto_fijo` y `porcentaje_aplicado` es 0.
          - No lleva inscripción, modalidad ni período.
        - Abono (`tipo_cargo.calculo = tarifario`):
          - Exige `inscripcion_id`, que da el turno, y `modalidad`.
          - Además exige `periodo_cobro_id` (Mes, Quincena, Semana) o
            `fecha_dia` (Día).
          - `monto_base` sale de `tarifa_base` (turno, modalidad).
          - Se aplica un único porcentaje: el de `descuento_mes` (categoría y
            `least(hijos, 4)`) si la modalidad es Mes, o el de
            `descuento_modalidad` en los demás casos. Nunca se acumulan.

        Con `simular=true` devuelve el cálculo sin guardar nada. Es lo que usa
        la pantalla para mostrar base, porcentaje y total antes de confirmar
        (escenario 1).

        Que la ficha esté incompleta no impide el cargo (escenario 8).

        Permisos: solo Admin (Acl. 9).
      parameters:
        - name: simular
          in: query
          required: false
          description: Si es true, calcula y devuelve el cargo sin guardarlo (200).
          schema:
            type: boolean
            default: false
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CargoCreate'
            examples:
              abono_mes:
                summary: Abono · Mes, empleado, 2 hijos en la mañana (escenario 1)
                value:
                  alumno_id: 41
                  tipo_cargo_id: 2
                  inscripcion_id: 88
                  modalidad: mes
                  periodo_cobro_id: 5
              abono_semana:
                summary: Abono · Semana, la cantidad de hijos no cuenta (escenario 2)
                value:
                  alumno_id: 41
                  tipo_cargo_id: 2
                  inscripcion_id: 88
                  modalidad: semana
                  periodo_cobro_id: 9
              preinscripcion:
                summary: Preinscripción, monto fijo sin descuento (escenario 7)
                value:
                  alumno_id: 41
                  tipo_cargo_id: 1
      responses:
        '201':
          description: Cargo registrado en la cuenta corriente de la familia.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Cargo'
              examples:
                abono_mes:
                  summary: 15 % sobre $ 100.000 = $ 85.000
                  value:
                    id: 301
                    temporada_id: 1
                    familia_id: 12
                    alumno_id: 41
                    tipo_cargo_id: 2
                    inscripcion_id: 88
                    modalidad: mes
                    periodo_cobro_id: 5
                    fecha_dia: null
                    categoria_aplicada: empleado
                    cantidad_hijos_aplicada: 2
                    monto_base: '100000.00'
                    porcentaje_aplicado: '15.00'
                    monto_total: '85000.00'
                    creado_por: 2
                    creado_en: '2026-12-20T10:31:05-03:00'
                abono_semana:
                  summary: 10 % sobre $ 30.000 = $ 27.000
                  value:
                    id: 302
                    temporada_id: 1
                    familia_id: 12
                    alumno_id: 41
                    tipo_cargo_id: 2
                    inscripcion_id: 88
                    modalidad: semana
                    periodo_cobro_id: 9
                    fecha_dia: null
                    categoria_aplicada: empleado
                    cantidad_hijos_aplicada: null
                    monto_base: '30000.00'
                    porcentaje_aplicado: '10.00'
                    monto_total: '27000.00'
                    creado_por: 2
                    creado_en: '2026-12-20T10:33:47-03:00'
                preinscripcion:
                  summary: Monto fijo de $ 20.000, sin descuento
                  value:
                    id: 303
                    temporada_id: 1
                    familia_id: 12
                    alumno_id: 41
                    tipo_cargo_id: 1
                    inscripcion_id: null
                    modalidad: null
                    periodo_cobro_id: null
                    fecha_dia: null
                    categoria_aplicada: empleado
                    cantidad_hijos_aplicada: null
                    monto_base: '20000.00'
                    porcentaje_aplicado: '0.00'
                    monto_total: '20000.00'
                    creado_por: 2
                    creado_en: '2026-12-20T10:35:12-03:00'
        '200':
          description: Solo con `simular=true`. Devuelve el cálculo sin guardarlo.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CargoCalculo'
              example:
                temporada_id: 1
                familia_id: 12
                alumno_id: 41
                tipo_cargo_id: 2
                inscripcion_id: 88
                modalidad: mes
                periodo_cobro_id: 5
                fecha_dia: null
                categoria_aplicada: empleado
                cantidad_hijos_aplicada: 2
                monto_base: '100000.00'
                porcentaje_aplicado: '15.00'
                monto_total: '85000.00'
        '401':
          $ref: '#/components/responses/NoAutenticado'
        '403':
          description: Quien lo usa no es Admin (escenario 11). No se registra nada.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                detail: Solo un Admin puede registrar cargos.
        '404':
          description: No existe el alumno, el tipo de cargo, la inscripción o el período de cobro.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                detail: No existe el periodo_cobro 77.
        '409':
          description: El pedido choca con el estado de la temporada o con su configuración.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              examples:
                temporada_cerrada:
                  summary: Cargo en una temporada cerrada (escenario 10)
                  value:
                    detail: La temporada 2025-26 está cerrada y queda solo para consulta.
                falta_tarifa_base:
                  summary: Falta la tarifa base de ese turno y modalidad (escenario 9)
                  value:
                    detail: 'Falta la tarifa_base de la temporada 2026-27 para turno tarde y modalidad quincena.'
                falta_descuento:
                  summary: Falta el porcentaje que corresponde
                  value:
                    detail: 'Falta el descuento_mes de la temporada 2026-27 para categoría empleado y tramo 3.'
        '422':
          description: Los campos no cumplen la forma que corresponde al tipo de cargo y la modalidad.
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: '#/components/schemas/HTTPValidationError'
                  - $ref: '#/components/schemas/Error'
              examples:
                abono_sin_periodo:
                  summary: Abono · Mes sin periodo_cobro_id
                  value:
                    detail:
                      - type: value_error
                        loc: [body]
                        msg: 'Value error, Con modalidad mes, quincena o semana hace falta periodo_cobro_id.'
                dia_sin_fecha:
                  summary: Abono · Día sin fecha_dia
                  value:
                    detail:
                      - type: value_error
                        loc: [body]
                        msg: 'Value error, Con modalidad dia hace falta fecha_dia.'
                abono_sin_inscripcion:
                  summary: El tipo de cargo es Abono y falta la inscripción
                  value:
                    detail: 'El tipo_cargo 2 (Abono) exige inscripcion_id y modalidad.'
                preinscripcion_con_modalidad:
                  summary: La Preinscripción no lleva inscripción, modalidad ni período
                  value:
                    detail: 'El tipo_cargo 1 (Preinscripción) es de monto fijo: no lleva inscripcion_id, modalidad, periodo_cobro_id ni fecha_dia.'
                periodo_de_otra_modalidad:
                  summary: El período no corresponde a la modalidad
                  value:
                    detail: 'El periodo_cobro 9 es de modalidad semana, no mes.'
                inscripcion_de_otro_alumno:
                  summary: La inscripción no es del alumno
                  value:
                    detail: 'La inscripcion_id 91 no pertenece al alumno 41.'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  responses:
    NoAutenticado:
      description: Falta el token de acceso, el token venció o el usuario está desactivado.
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            detail: Not authenticated

  schemas:
    Turno:
      type: string
      enum: [manana, tarde]
    Modalidad:
      type: string
      enum: [mes, quincena, semana, dia]
    CategoriaFamilia:
      type: string
      enum: [socio, empleado, no_socio]
    Decimal:
      type: string
      pattern: '^\d+\.\d{2}$'
      description: numeric serializado como string (Pydantic Decimal).

    PersonaVinculo:
      type: object
      description: |
        Vínculo de una persona con la familia (`familia_persona`). Tiene que
        traer `persona_id` (persona ya cargada) o `nombre`, `apellido` y
        `telefono` (persona nueva). Al menos uno de `es_tutor` o
        `autorizado_retiro` tiene que ser true. `contacto_emergencia` llega
        con HU-AF-08 y no se acepta en este endpoint.
      properties:
        persona_id:
          type: [integer, 'null']
        nombre:
          type: [string, 'null']
          maxLength: 80
        apellido:
          type: [string, 'null']
          maxLength: 80
        telefono:
          type: [string, 'null']
          maxLength: 30
        dni:
          type: [string, 'null']
          maxLength: 15
        es_tutor:
          type: boolean
          default: false
        autorizado_retiro:
          type: boolean
          default: false

    AlumnoCreate:
      type: object
      required: [nombre, apellido, fecha_nacimiento, grupo_id]
      properties:
        nombre:
          type: string
          minLength: 1
          maxLength: 80
        apellido:
          type: string
          minLength: 1
          maxLength: 80
        fecha_nacimiento:
          type: string
          format: date
        familia_id:
          type: [integer, 'null']
          description: Null para crear una familia nueva.
        categoria:
          description: Obligatoria si la familia es nueva. No se acepta si la familia ya existe.
          oneOf:
            - $ref: '#/components/schemas/CategoriaFamilia'
            - type: 'null'
        personas:
          type: array
          items:
            $ref: '#/components/schemas/PersonaVinculo'
          default: []
          description: Con familia nueva, al menos una con es_tutor = true.
        grupo_id:
          type: integer
          description: Grupo de la temporada vigente. Define el turno.

    FamiliaResumen:
      type: object
      required: [id, categoria, etiqueta]
      properties:
        id:
          type: integer
        categoria:
          $ref: '#/components/schemas/CategoriaFamilia'
        etiqueta:
          type: string
          description: '"Apellido – Hijo mayor", calculada por la vista v_familia_etiqueta (Acl. 1).'

    InscripcionResumen:
      type: object
      required: [id, grupo_id, temporada_id, turno]
      properties:
        id:
          type: integer
        grupo_id:
          type: integer
        temporada_id:
          type: integer
        turno:
          $ref: '#/components/schemas/Turno'

    FamiliaPersona:
      type: object
      required: [persona_id, es_tutor, autorizado_retiro, contacto_emergencia]
      properties:
        persona_id:
          type: integer
        es_tutor:
          type: boolean
        autorizado_retiro:
          type: boolean
        contacto_emergencia:
          type: boolean

    AlumnoCreado:
      type: object
      required: [id, familia_id, nombre, apellido, fecha_nacimiento, familia, inscripcion, personas]
      properties:
        id:
          type: integer
        familia_id:
          type: integer
        nombre:
          type: string
        apellido:
          type: string
        fecha_nacimiento:
          type: string
          format: date
        familia:
          $ref: '#/components/schemas/FamiliaResumen'
        inscripcion:
          $ref: '#/components/schemas/InscripcionResumen'
        personas:
          type: array
          description: Personas vinculadas a la familia después del alta.
          items:
            $ref: '#/components/schemas/FamiliaPersona'

    AsistenciaItemIn:
      type: object
      required: [inscripcion_id, presente]
      properties:
        inscripcion_id:
          type: integer
        presente:
          type: boolean

    AsistenciaLoteIn:
      type: object
      required: [asistencias]
      properties:
        asistencias:
          type: array
          minItems: 1
          description: Una entrada por inscripción del grupo, sin repetir.
          items:
            $ref: '#/components/schemas/AsistenciaItemIn'

    Asistencia:
      type: object
      required: [id, inscripcion_id, fecha, presente, registrado_por, registrado_en]
      properties:
        id:
          type: integer
        inscripcion_id:
          type: integer
        fecha:
          type: string
          format: date
        presente:
          type: boolean
        registrado_por:
          type: integer
        registrado_en:
          type: string
          format: date-time

    AsistenciaLoteOut:
      type: object
      required: [grupo_id, fecha, turno, asistencias]
      properties:
        grupo_id:
          type: integer
        fecha:
          type: string
          format: date
        turno:
          $ref: '#/components/schemas/Turno'
        asistencias:
          type: array
          items:
            $ref: '#/components/schemas/Asistencia'

    CargoCreate:
      type: object
      required: [alumno_id, tipo_cargo_id]
      description: |
        Preinscripción: solo alumno_id y tipo_cargo_id.
        Abono: además inscripcion_id y modalidad, y periodo_cobro_id
        (mes, quincena, semana) o fecha_dia (dia).
      properties:
        alumno_id:
          type: integer
        tipo_cargo_id:
          type: integer
        inscripcion_id:
          type: [integer, 'null']
        modalidad:
          oneOf:
            - $ref: '#/components/schemas/Modalidad'
            - type: 'null'
        periodo_cobro_id:
          type: [integer, 'null']
        fecha_dia:
          type: [string, 'null']
          format: date

    CargoCalculo:
      type: object
      description: Resultado del cálculo, tal como queda guardado en `cargo`.
      required: [temporada_id, familia_id, alumno_id, tipo_cargo_id, categoria_aplicada, monto_base, porcentaje_aplicado, monto_total]
      properties:
        temporada_id:
          type: integer
        familia_id:
          type: integer
        alumno_id:
          type: integer
        tipo_cargo_id:
          type: integer
        inscripcion_id:
          type: [integer, 'null']
        modalidad:
          oneOf:
            - $ref: '#/components/schemas/Modalidad'
            - type: 'null'
        periodo_cobro_id:
          type: [integer, 'null']
        fecha_dia:
          type: [string, 'null']
          format: date
        categoria_aplicada:
          $ref: '#/components/schemas/CategoriaFamilia'
        cantidad_hijos_aplicada:
          type: [integer, 'null']
          minimum: 1
          description: Solo en el Mes.
        monto_base:
          $ref: '#/components/schemas/Decimal'
        porcentaje_aplicado:
          $ref: '#/components/schemas/Decimal'
        monto_total:
          $ref: '#/components/schemas/Decimal'

    Cargo:
      allOf:
        - $ref: '#/components/schemas/CargoCalculo'
        - type: object
          required: [id, creado_por, creado_en]
          properties:
            id:
              type: integer
            creado_por:
              type: integer
            creado_en:
              type: string
              format: date-time

    Error:
      type: object
      required: [detail]
      properties:
        detail:
          type: string

    ValidationError:
      type: object
      required: [loc, msg, type]
      properties:
        loc:
          type: array
          items:
            oneOf:
              - type: string
              - type: integer
        msg:
          type: string
        type:
          type: string

    HTTPValidationError:
      type: object
      properties:
        detail:
          type: array
          items:
            $ref: '#/components/schemas/ValidationError'
```
