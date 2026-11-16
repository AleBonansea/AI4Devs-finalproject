# 4. Especificación de la API

> Son 3 endpoints, uno por cada historia documentada en [`5-historias-de-usuario.md`](5-historias-de-usuario.md). Los nombres de entidades y campos son los de [`3-modelo-de-datos.md`](3-modelo-de-datos.md). El stack es FastAPI + Pydantic v2 ([`docs/architecture/documento-tecnico.md`](docs/architecture/documento-tecnico.md)).
>
> **De dónde sale.** Los tres endpoints están construidos. El OpenAPI de abajo **no está escrito a mano**: es un extracto del contrato completo, [`docs/api/openapi.json`](docs/api/openapi.json), que se genera desde el código con `python tasks.py openapi-generate`. El CI lo regenera en cada pull request y la PR no pasa si no coincide con el versionado ([`.github/workflows/openapi.yml`](.github/workflows/openapi.yml)). Con la API levantada, el mismo contrato se navega en `http://localhost:8000/docs`.
>
> El comportamiento de cada endpoint, con un Scenario por caso, está en [`openspec/specs/`](openspec/specs/): `alumnos`, `asistencia` y `cargos`. Si este documento y una spec difieren, manda la spec.

## Convenciones

- **Autenticación:** todos los endpoints de negocio exigen el token de acceso JWT en `Authorization: Bearer <token>`, que devuelve `POST /api/v1/auth/login`. El control de permisos se hace en la API, nunca solo en el frontend.
- **Rutas:** el prefijo es `/api/v1`, los recursos van en plural y los identificadores de la base viajan en la ruta o en el cuerpo con el mismo nombre que la columna (`grupo_id`, `familia_id`, …).
- **Tipos en JSON:**
  - Las fechas son ISO 8601: `date` como `"2027-01-05"` y `timestamptz` con zona horaria.
  - Los montos y porcentajes son `Decimal` en Pydantic y viajan como **string** con dos decimales (`"85000.00"`), para que un centavo no pase nunca por un número de punto flotante.
  - Ningún cuerpo de entrada acepta el precio de un cargo: el cliente dice **qué** se cobra y la API calcula **cuánto**.
- **Errores** (spec [`errores-de-la-api`](openspec/specs/errores-de-la-api/spec.md)):
  - `401`: no hay token, no es válido, venció, o el usuario está desactivado o bloqueado.
  - `403`: el rol no puede usar el endpoint, o el Profesor actúa sobre un grupo que no tiene asignado.
  - `404`: el recurso **de la ruta** no existe (por ejemplo, el `grupo_id` de la asistencia).
  - `409`: el pedido es válido, pero choca con el estado actual: un grupo inactivo o de una temporada cerrada, una configuración del tarifario que falta, un cargo repetido.
  - `422`: los datos no cumplen las reglas. **Siempre** con la misma forma, `{"detail": [{"loc", "msg", "type"}]}`, y el `msg` en castellano, tanto si lo detecta Pydantic como si sale de una regla que consulta la base (`type` `regla_de_negocio`). Así cada pantalla pega cada mensaje junto a su campo.
  - `401`, `403`, `404` y `409` llevan `{"detail": "mensaje"}`.

## Resumen

| Historia | Método y ruta | Quién puede usarlo | Éxito |
|---|---|---|---|
| HU-AF-01 | `POST /api/v1/alumnos` | Admin y Coordinador en cualquier grupo; Profesor solo en sus grupos | `201` alumno creado e inscripto, con su familia |
| HU-GA-04 | `PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}` | Admin y Coordinador en cualquier grupo; Profesor solo en sus grupos | `200` con la asistencia del grupo en esa fecha |
| HU-CC-01 | `POST /api/v1/cargos` | Solo Admin | `201` cargo registrado con su desglose y el saldo de la familia |

**El resto del contrato.** La API expone 15 rutas. Las que acompañan a estas tres, y que no se detallan acá por el límite de la consigna, son:

| Ruta | Para qué |
|---|---|
| `POST /api/v1/auth/login`, `GET /api/v1/auth/yo` | Ingresar, y saber quién es el usuario del token |
| `GET /api/v1/grupos`, `GET /api/v1/familias`, `GET /api/v1/personas` | Llenar los selectores del alta: grupos sugeridos por fecha de nacimiento, familia por apellido, persona por DNI |
| `GET /api/v1/grupos/{grupo_id}/asistencias/{fecha}` | Abrir la lista de asistencia antes de guardarla |
| `POST /api/v1/cargos/simulacion`, `GET /api/v1/cargos/opciones`, `GET /api/v1/familias/{familia_id}/inscripciones` | Mostrar el desglose antes de confirmar y llenar los selectores del cargo |
| `POST /api/v1/cargos/{cargo_id}/pagos`, `GET /api/v1/familias/{familia_id}/cuenta-corriente` | Pagos parciales y cuenta corriente de la familia (HU-CC-02, HU-CC-03) |
| `GET /salud` | Comprobar que la API responde |

### Qué cambió respecto de la Entrega 1

En la Entrega 1 este documento era el diseño previo al código. Al construirlo cambiaron tres cosas, y cada una quedó justificada en el design del change que la tomó:

- **La simulación es un endpoint propio, `POST /api/v1/cargos/simulacion`**, y no `POST /api/v1/cargos?simular=true`. Aquel parámetro era una concesión al límite de 3 endpoints de la consigna, no una decisión de diseño. Con un endpoint aparte, cada uno tiene su propio esquema de respuesta y su propio código (`200` y `201`), en lugar de uno solo con dos formas de respuesta. Es `POST` y no `GET` porque lleva el mismo cuerpo que el registro (design del change `cobro`).
- **Una referencia del cuerpo que no existe es `422` en su campo, no `404`.** Un `grupo_id`, `familia_id`, `alumno_id` o `periodo_cobro_id` inexistente vuelve como error de ese campo, igual que el tipo de cargo de una temporada cerrada. Es lo que permite que la pantalla muestre el mensaje al lado del campo que hay que corregir (spec `errores-de-la-api`). El `404` queda para el recurso de la ruta.
- **El escenario 4 de HU-GA-04 (grupo sin alumnos) ya está cubierto** por `GET /api/v1/grupos/{grupo_id}/asistencias/{fecha}`, que devuelve `alumnos` vacío. En la Entrega 1 quedaba sin cubrir porque ese `GET` no entraba entre los 3 endpoints documentados.

Además, el registro rechaza con `409` un **cargo repetido** (el mismo Abono para la misma inscripción y período, o el mismo monto fijo para el alumno en la temporada), una regla que la Entrega 1 no tenía. Es **[SUPUESTO]**: `aclaraciones-cliente.md`, «Preguntas abiertas», «Cargos repetidos».

### Errores por endpoint

Cada fila remite al requirement de la spec que la define.

**`POST /api/v1/alumnos` (HU-AF-01)** — spec [`alumnos`](openspec/specs/alumnos/spec.md)

| Código | Cuándo | Requirement |
|---|---|---|
| 403 | Un Profesor inscribe en un grupo que no tiene asignado, exista o no | «Quién puede dar de alta un alumno» |
| 422 | Falta nombre, apellido, fecha de nacimiento o `grupo_id`, o la fecha es posterior a hoy | «Datos del alumno en el alta» |
| 422 | El grupo no existe, está inactivo o no es de la temporada vigente | «El grupo del alta» |
| 422 | Familia nueva sin `categoria` o sin ningún tutor | «Alta de un alumno con familia nueva» |
| 422 | Se envía `categoria` con una familia existente, o la familia no existe | «Alta de un alumno en una familia existente» |
| 422 | Una persona repetida, incompleta, inexistente o con un DNI ya cargado | «Personas en el alta» |

**`PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}` (HU-GA-04)** — spec [`asistencia`](openspec/specs/asistencia/spec.md)

| Código | Cuándo | Requirement |
|---|---|---|
| 403 | Un Profesor toma asistencia de un grupo que no tiene asignado | «Quién puede abrir y guardar la asistencia» |
| 404 | No existe el `grupo_id` | «Grupos donde no se guarda asistencia» |
| 409 | El grupo es de una temporada cerrada o está inactivo | «Grupos donde no se guarda asistencia» |
| 422 | La `fecha` está fuera de la temporada del grupo | «La fecha está dentro de la temporada del grupo» |
| 422 | La lista llega vacía, un elemento no trae `presente`, o una `inscripcion_id` no es de ese grupo o está repetida | «El cuerpo del guardado» |

**`POST /api/v1/cargos` (HU-CC-01)** — spec [`cargos`](openspec/specs/cargos/spec.md). La simulación rechaza con los mismos códigos y mensajes.

| Código | Cuándo | Requirement |
|---|---|---|
| 403 | Quien lo usa es Coordinador o Profesor | «Solo el Admin registra cargos» |
| 409 | Falta la tarifa base del turno y la modalidad, o el % que corresponde | «Falta configuración del tarifario» |
| 409 | Ya existe el mismo cargo | «Un cargo repetido se rechaza» |
| 422 | El alumno o el tipo de cargo no existen; los campos no tienen la forma del monto fijo o del Abono; el período no existe o es de otra modalidad; la inscripción no es del alumno | «Qué pide cada tipo de cargo» |
| 422 | El tipo de cargo es de una temporada cerrada | «La temporada cerrada queda para consulta» |
| 422 | El alumno no tiene inscripción en la temporada, o la fecha del Día está fuera de ella | «El alumno está inscripto en la temporada» y «La fecha del Día está dentro de la temporada» |

## Ejemplos

Los datos son los de los Scenarios de las specs.

**Alta de un alumno con familia nueva** (`POST /api/v1/alumnos`, como Coordinador):

```json
{
  "nombre": "Juan",
  "apellido": "Pérez",
  "fecha_nacimiento": "2018-03-10",
  "grupo_id": 1,
  "categoria": "empleado",
  "personas": [
    { "nombre": "María", "apellido": "Pérez", "telefono": "3415550101", "es_tutor": true }
  ]
}
```

Respuesta `201`:

```json
{
  "id": 1,
  "nombre": "Juan",
  "apellido": "Pérez",
  "fecha_nacimiento": "2018-03-10",
  "familia": { "id": 1, "etiqueta": "Pérez – Juan", "categoria": "empleado" },
  "inscripcion": { "grupo_id": 1, "grupo_nombre": "Delfines", "turno": "manana", "temporada_id": 1 }
}
```

**Guardar la asistencia** (`PUT /api/v1/grupos/1/asistencias/2027-01-05`, como Profesor del grupo):

```json
{ "asistencias": [ { "inscripcion_id": 1, "presente": true }, { "inscripcion_id": 2, "presente": false } ] }
```

Respuesta `200`, con la misma forma que abrir esa asistencia (los alumnos, por apellido y nombre):

```json
{
  "grupo_id": 1,
  "grupo": "Delfines",
  "turno": "manana",
  "fecha": "2027-01-05",
  "alumnos": [
    { "inscripcion_id": 2, "nombre": "Martín", "apellido": "Gómez", "presente": false },
    { "inscripcion_id": 1, "nombre": "Juan", "apellido": "Pérez", "presente": true }
  ]
}
```

**Registrar un Abono del Mes** (`POST /api/v1/cargos`, como Admin). Familia «Pérez – Ana», categoría empleado, con dos hijos en el turno mañana: tramo 2 del Mes, 15 %. El cuerpo no lleva ningún monto:

```json
{ "alumno_id": 1, "tipo_cargo_id": 2, "inscripcion_id": 1, "modalidad": "mes", "periodo_cobro_id": 1 }
```

Respuesta `201`, con el cálculo que queda guardado en el cargo y el saldo de la familia:

```json
{
  "id": 1,
  "temporada_id": 1,
  "familia_id": 1,
  "alumno_id": 1,
  "tipo_cargo_id": 2,
  "inscripcion_id": 1,
  "modalidad": "mes",
  "periodo_cobro_id": 1,
  "fecha_dia": null,
  "categoria_aplicada": "empleado",
  "cantidad_hijos_aplicada": 2,
  "monto_base": "100000.00",
  "porcentaje_aplicado": "15.00",
  "monto_total": "85000.00",
  "creado_por": 1,
  "creado_en": "2027-01-05T10:15:00-03:00",
  "saldo_pendiente": "85000.00"
}
```

Un rechazo `422`, por ejemplo un Abono sin inscripción ni modalidad:

```json
{
  "detail": [
    { "loc": ["body", "inscripcion_id"], "msg": "Este dato es obligatorio.", "type": "regla_de_negocio" },
    { "loc": ["body", "modalidad"], "msg": "Este dato es obligatorio.", "type": "regla_de_negocio" }
  ]
}
```

## Especificación OpenAPI

Extracto de [`docs/api/openapi.json`](docs/api/openapi.json) con los tres endpoints y los esquemas que usan, convertido a YAML sin cambios.

```yaml
openapi: 3.1.0
info:
  title: Escuelita de Verano
  version: 0.1.0
  description: Extracto de docs/api/openapi.json con los 3 endpoints de las historias documentadas. Generado
    desde el código, no escrito a mano.
paths:
  /api/v1/alumnos:
    post:
      tags:
      - alumnos
      summary: Registrar
      operationId: registrar_api_v1_alumnos_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AltaAlumnoEntrada'
        required: true
      responses:
        '201':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AlumnoRegistrado'
        '401':
          description: Sesión inválida o vencida.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MensajeError'
              example:
                detail: Sesión inválida o vencida.
        '403':
          description: Solo podés inscribir alumnos en tus grupos.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MensajeError'
              example:
                detail: Solo podés inscribir alumnos en tus grupos.
        '422':
          description: Datos invalidos o una regla del alta incumplida (grupo, familia, personas). Cada
            error trae su campo en `loc`.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErroresDeCampo'
      security:
      - HTTPBearer: []
  /api/v1/grupos/{grupo_id}/asistencias/{fecha}:
    put:
      tags:
      - asistencias
      summary: Guardar
      operationId: guardar_api_v1_grupos__grupo_id__asistencias__fecha__put
      security:
      - HTTPBearer: []
      parameters:
      - name: grupo_id
        in: path
        required: true
        schema:
          type: integer
          title: Grupo Id
      - name: fecha
        in: path
        required: true
        schema:
          type: string
          format: date
          title: Fecha
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AsistenciaEntrada'
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AsistenciaDelGrupo'
        '401':
          description: Sesión inválida o vencida.
          content:
            application/json:
              example:
                detail: Sesión inválida o vencida.
              schema:
                $ref: '#/components/schemas/MensajeError'
        '403':
          description: Solo podés tomar asistencia de tus grupos.
          content:
            application/json:
              example:
                detail: Solo podés tomar asistencia de tus grupos.
              schema:
                $ref: '#/components/schemas/MensajeError'
        '404':
          description: El grupo no existe.
          content:
            application/json:
              example:
                detail: El grupo no existe.
              schema:
                $ref: '#/components/schemas/MensajeError'
        '409':
          description: El grupo no está activo.
          content:
            application/json:
              example:
                detail: El grupo no está activo.
              schema:
                $ref: '#/components/schemas/MensajeError'
        '422':
          description: La fecha está fuera de la temporada del grupo, del 04/01/2027 al 26/02/2027.
          content:
            application/json:
              example:
                detail: La fecha está fuera de la temporada del grupo, del 04/01/2027 al 26/02/2027.
              schema:
                $ref: '#/components/schemas/MensajeError'
  /api/v1/cargos:
    post:
      tags:
      - cargos
      summary: Registrar
      operationId: registrar_api_v1_cargos_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CargoEntrada'
        required: true
      responses:
        '201':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CargoRegistrado'
        '401':
          description: Sesión inválida o vencida.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MensajeError'
              example:
                detail: Sesión inválida o vencida.
        '403':
          description: No tenés permiso para esta operación.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MensajeError'
              example:
                detail: No tenés permiso para esta operación.
        '409':
          description: El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MensajeError'
              example:
                detail: El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana.
        '422':
          description: Datos inválidos o una regla del cargo incumplida. Cada error trae su campo en `loc`.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErroresDeCampo'
      security:
      - HTTPBearer: []
components:
  schemas:
    AltaAlumnoEntrada:
      properties:
        nombre:
          type: string
          maxLength: 80
          minLength: 1
          title: Nombre
        apellido:
          type: string
          maxLength: 80
          minLength: 1
          title: Apellido
        fecha_nacimiento:
          type: string
          format: date
          title: Fecha Nacimiento
        grupo_id:
          type: integer
          title: Grupo Id
        familia_id:
          anyOf:
          - type: integer
          - type: 'null'
          title: Familia Id
        categoria:
          anyOf:
          - $ref: '#/components/schemas/CategoriaFamilia'
          - type: 'null'
        personas:
          items:
            oneOf:
            - $ref: '#/components/schemas/PersonaReutilizada'
            - $ref: '#/components/schemas/PersonaNueva'
          type: array
          title: Personas
          default: []
      additionalProperties: false
      type: object
      required:
      - nombre
      - apellido
      - fecha_nacimiento
      - grupo_id
      title: AltaAlumnoEntrada
      description: |-
        El alta: datos del alumno, grupo, familia (existente o nueva) y
        personas autorizadas a retirar.
    AlumnoEnAsistencia:
      properties:
        inscripcion_id:
          type: integer
          title: Inscripcion Id
        nombre:
          type: string
          title: Nombre
        apellido:
          type: string
          title: Apellido
        presente:
          anyOf:
          - type: boolean
          - type: 'null'
          title: Presente
      type: object
      required:
      - inscripcion_id
      - nombre
      - apellido
      - presente
      title: AlumnoEnAsistencia
    AlumnoRegistrado:
      properties:
        id:
          type: integer
          title: Id
        nombre:
          type: string
          title: Nombre
        apellido:
          type: string
          title: Apellido
        fecha_nacimiento:
          type: string
          format: date
          title: Fecha Nacimiento
        familia:
          $ref: '#/components/schemas/FamiliaDelAlumno'
        inscripcion:
          $ref: '#/components/schemas/InscripcionDelAlumno'
      type: object
      required:
      - id
      - nombre
      - apellido
      - fecha_nacimiento
      - familia
      - inscripcion
      title: AlumnoRegistrado
      description: El alumno recien dado de alta, con su familia y su inscripcion.
    AsistenciaDelGrupo:
      properties:
        grupo_id:
          type: integer
          title: Grupo Id
        grupo:
          type: string
          title: Grupo
        turno:
          $ref: '#/components/schemas/Turno'
        fecha:
          type: string
          format: date
          title: Fecha
        alumnos:
          items:
            $ref: '#/components/schemas/AlumnoEnAsistencia'
          type: array
          title: Alumnos
      type: object
      required:
      - grupo_id
      - grupo
      - turno
      - fecha
      - alumnos
      title: AsistenciaDelGrupo
    AsistenciaEntrada:
      properties:
        asistencias:
          items:
            $ref: '#/components/schemas/AsistenciaMarcada'
          type: array
          title: Asistencias
      type: object
      required:
      - asistencias
      title: AsistenciaEntrada
      description: |-
        Lo que se guarda: solo quien y si estuvo. Fecha y grupo vienen del path
        y el autor de la sesion; nada de eso se acepta del cuerpo.

        Sin tope de largo: el limite natural es el tamano del grupo, y los ids de
        otro grupo ya se rechazan por elemento.
    AsistenciaMarcada:
      properties:
        inscripcion_id:
          type: integer
          title: Inscripcion Id
        presente:
          type: boolean
          title: Presente
      type: object
      required:
      - inscripcion_id
      - presente
      title: AsistenciaMarcada
    CargoEntrada:
      properties:
        alumno_id:
          type: integer
          title: Alumno Id
        tipo_cargo_id:
          type: integer
          title: Tipo Cargo Id
        inscripcion_id:
          anyOf:
          - type: integer
          - type: 'null'
          title: Inscripcion Id
        modalidad:
          anyOf:
          - $ref: '#/components/schemas/Modalidad'
          - type: 'null'
        periodo_cobro_id:
          anyOf:
          - type: integer
          - type: 'null'
          title: Periodo Cobro Id
        fecha_dia:
          anyOf:
          - type: string
            format: date
          - type: 'null'
          title: Fecha Dia
      additionalProperties: false
      type: object
      required:
      - alumno_id
      - tipo_cargo_id
      title: CargoEntrada
    CargoRegistrado:
      properties:
        familia_id:
          type: integer
          title: Familia Id
        categoria_aplicada:
          $ref: '#/components/schemas/CategoriaFamilia'
        cantidad_hijos_aplicada:
          anyOf:
          - type: integer
          - type: 'null'
          title: Cantidad Hijos Aplicada
        monto_base:
          type: string
          pattern: ^(?!^[-+.]*$)[+-]?0*\d*\.?\d*$
          title: Monto Base
        porcentaje_aplicado:
          type: string
          pattern: ^(?!^[-+.]*$)[+-]?0*\d*\.?\d*$
          title: Porcentaje Aplicado
        monto_total:
          type: string
          pattern: ^(?!^[-+.]*$)[+-]?0*\d*\.?\d*$
          title: Monto Total
        id:
          type: integer
          title: Id
        temporada_id:
          type: integer
          title: Temporada Id
        alumno_id:
          type: integer
          title: Alumno Id
        tipo_cargo_id:
          type: integer
          title: Tipo Cargo Id
        inscripcion_id:
          anyOf:
          - type: integer
          - type: 'null'
          title: Inscripcion Id
        modalidad:
          anyOf:
          - $ref: '#/components/schemas/Modalidad'
          - type: 'null'
        periodo_cobro_id:
          anyOf:
          - type: integer
          - type: 'null'
          title: Periodo Cobro Id
        fecha_dia:
          anyOf:
          - type: string
            format: date
          - type: 'null'
          title: Fecha Dia
        creado_por:
          type: integer
          title: Creado Por
        creado_en:
          type: string
          format: date-time
          title: Creado En
        saldo_pendiente:
          type: string
          pattern: ^(?!^[-+.]*$)[+-]?0*\d*\.?\d*$
          title: Saldo Pendiente
      type: object
      required:
      - familia_id
      - categoria_aplicada
      - cantidad_hijos_aplicada
      - monto_base
      - porcentaje_aplicado
      - monto_total
      - id
      - temporada_id
      - alumno_id
      - tipo_cargo_id
      - inscripcion_id
      - modalidad
      - periodo_cobro_id
      - fecha_dia
      - creado_por
      - creado_en
      - saldo_pendiente
      title: CargoRegistrado
    CategoriaFamilia:
      type: string
      enum:
      - socio
      - empleado
      - no_socio
      title: CategoriaFamilia
    ErrorDeCampo:
      properties:
        loc:
          items:
            anyOf:
            - type: string
            - type: integer
          type: array
          title: Loc
        msg:
          type: string
          title: Msg
        type:
          type: string
          title: Type
      type: object
      required:
      - loc
      - msg
      - type
      title: ErrorDeCampo
      description: |-
        Un error atado a un campo del pedido, de validacion o de una regla del
        negocio (`type` `regla_de_negocio`).
    ErroresDeCampo:
      properties:
        detail:
          items:
            $ref: '#/components/schemas/ErrorDeCampo'
          type: array
          title: Detail
      type: object
      required:
      - detail
      title: ErroresDeCampo
      description: 'El 422: la lista de errores, cada uno con su campo en `loc`.'
    FamiliaDelAlumno:
      properties:
        id:
          type: integer
          title: Id
        etiqueta:
          type: string
          title: Etiqueta
        categoria:
          $ref: '#/components/schemas/CategoriaFamilia'
      type: object
      required:
      - id
      - etiqueta
      - categoria
      title: FamiliaDelAlumno
    InscripcionDelAlumno:
      properties:
        grupo_id:
          type: integer
          title: Grupo Id
        grupo_nombre:
          type: string
          title: Grupo Nombre
        turno:
          $ref: '#/components/schemas/Turno'
        temporada_id:
          type: integer
          title: Temporada Id
      type: object
      required:
      - grupo_id
      - grupo_nombre
      - turno
      - temporada_id
      title: InscripcionDelAlumno
    MensajeError:
      properties:
        detail:
          type: string
          title: Detail
      type: object
      required:
      - detail
      title: MensajeError
      description: |-
        Un rechazo con `detail` en castellano, que src/lib/api.ts muestra tal
        cual.
    Modalidad:
      type: string
      enum:
      - mes
      - quincena
      - semana
      - dia
      title: Modalidad
    PersonaNueva:
      properties:
        nombre:
          type: string
          maxLength: 80
          minLength: 1
          title: Nombre
        apellido:
          type: string
          maxLength: 80
          minLength: 1
          title: Apellido
        telefono:
          type: string
          maxLength: 30
          minLength: 1
          title: Telefono
        dni:
          anyOf:
          - type: string
            maxLength: 15
          - type: 'null'
          title: Dni
        es_tutor:
          type: boolean
          title: Es Tutor
      additionalProperties: false
      type: object
      required:
      - nombre
      - apellido
      - telefono
      - es_tutor
      title: PersonaNueva
      description: Una persona que se carga en el alta.
    PersonaReutilizada:
      properties:
        persona_id:
          type: integer
          title: Persona Id
        es_tutor:
          type: boolean
          title: Es Tutor
      additionalProperties: false
      type: object
      required:
      - persona_id
      - es_tutor
      title: PersonaReutilizada
      description: Una persona ya cargada, elegida por su id (de la busqueda por DNI).
    Turno:
      type: string
      enum:
      - manana
      - tarde
      title: Turno
  securitySchemes:
    HTTPBearer:
      type: http
      scheme: bearer
```
