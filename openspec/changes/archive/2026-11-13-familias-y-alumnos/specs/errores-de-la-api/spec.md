# Spec Delta

## Purpose

Fija la forma y el idioma de los rechazos por validación que emite la API, para que cualquier pantalla pueda pegar cada mensaje junto a su campo y mostrárselo tal cual a una persona.

## ADDED Requirements

### Requirement: Mensajes de validación en castellano
Todo 422 de validación SHALL traer el `msg` de cada error en castellano, con la misma forma de lista de `loc`, `msg` y `type`. Los casos comunes tienen el mensaje fijo de cada Scenario; cualquier otro caso lleva `El valor no es válido.`

#### Scenario: Dato que falta
- **WHEN** se llama a `POST /api/v1/alumnos` con un Coordinador y sin `fecha_nacimiento`
- **THEN** la respuesta es 422 con un error con `loc` terminado en `fecha_nacimiento` y `msg` `Este dato es obligatorio.`

#### Scenario: Texto más largo que el máximo
- **WHEN** se llama a `POST /api/v1/alumnos` con un Coordinador y un `nombre` de 81 caracteres
- **THEN** el error de `nombre` tiene `msg` `Puede tener hasta 80 caracteres.`

#### Scenario: Texto que queda vacío
- **WHEN** se llama a `POST /api/v1/alumnos` con un Coordinador y un `apellido` de solo espacios
- **THEN** el error de `apellido` tiene `msg` `No puede quedar vacío.`

#### Scenario: Texto más corto que un mínimo mayor que uno
- **WHEN** un Coordinador llama a `GET /api/v1/familias?apellido=%20P%20`
- **THEN** la respuesta es 422 y el error de `apellido` tiene `msg` `Tiene que tener al menos 2 caracteres.`

#### Scenario: Número mal escrito
- **WHEN** se llama a `POST /api/v1/alumnos` con un Coordinador y `grupo_id` `"uno"`
- **THEN** el error de `grupo_id` tiene `msg` `Tiene que ser un número entero.`

#### Scenario: Fecha mal escrita
- **WHEN** se llama a `POST /api/v1/alumnos` con un Coordinador y `fecha_nacimiento` `10/03/2020`
- **THEN** el error de `fecha_nacimiento` tiene `msg` `La fecha no es válida.`

#### Scenario: Categoría que no existe
- **WHEN** se llama a `POST /api/v1/alumnos` con un Coordinador y `categoria` `vip`
- **THEN** el error de `categoria` tiene `msg` `El valor no es una de las opciones válidas.`

#### Scenario: Usuario del login demasiado largo
- **WHEN** se llama a `POST /api/v1/auth/login` con un `username` de 61 caracteres y `Verano2026`
- **THEN** la respuesta es 422 y el error de `username` tiene `msg` `Puede tener hasta 60 caracteres.`
- **AND** el cuerpo no tiene ningún campo `input`

### Requirement: Caracteres de control en los textos
Un texto del pedido (en el cuerpo o en un parámetro de búsqueda) que contiene un carácter de control SHALL rechazarse con 422 y `msg` `No puede tener caracteres de control.` en ese campo, nunca con 500.

#### Scenario: Carácter NUL en el nombre del alumno
- **WHEN** un Coordinador llama a `POST /api/v1/alumnos` con un alta válida salvo `nombre` `"Ju\u0000an"`
- **THEN** la respuesta es 422 y el error de `nombre` tiene `msg` `No puede tener caracteres de control.`
- **AND** no se crea nada

#### Scenario: Carácter NUL en el teléfono de una persona
- **WHEN** un Coordinador llama a `POST /api/v1/alumnos` con un alta válida salvo una persona nueva con `telefono` `"351\u00001234"`
- **THEN** la respuesta es 422 y el error de `personas.0.telefono` tiene `msg` `No puede tener caracteres de control.`

#### Scenario: Carácter NUL en la búsqueda de familias
- **WHEN** un Coordinador llama a `GET /api/v1/familias?apellido=P%00e`
- **THEN** la respuesta es 422 y el error de `apellido` tiene `msg` `No puede tener caracteres de control.`

#### Scenario: Carácter NUL en la búsqueda por DNI
- **WHEN** un Coordinador llama a `GET /api/v1/personas?dni=301%0011222`
- **THEN** la respuesta es 422 y el error de `dni` tiene `msg` `No puede tener caracteres de control.`

### Requirement: Rechazos de reglas del negocio con la forma de validación
Un rechazo por una regla del negocio que se puede atribuir a un campo del pedido (una familia que no existe, un DNI ya cargado, un grupo inactivo) SHALL responder 422 con la misma forma que un error de validación: `detail` como lista, con `loc` apuntando a ese campo (`["body", "personas", 0, "dni"]`), el mensaje en `msg` y `type` `regla_de_negocio`.

#### Scenario: Grupo inactivo
- **GIVEN** un grupo inactivo de la temporada vigente
- **WHEN** un Coordinador da de alta a un alumno en ese grupo
- **THEN** la respuesta es 422 con `detail` igual a una lista con un elemento, con `loc` `["body", "grupo_id"]`, `msg` `El grupo no está activo.` y `type` `regla_de_negocio`
