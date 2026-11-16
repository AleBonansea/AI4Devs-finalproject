# Spec Delta

## MODIFIED Requirements

### Requirement: La semilla solo corre sobre una base vacía
La semilla SHALL cargar sus datos solo si la base no tiene ninguna temporada, ningún usuario, ninguna familia ni ninguna persona. Si tiene alguna, MUST terminar con error, con el mensaje `La base no está vacía: la semilla solo corre sobre una base vacía.`, sin escribir nada.

#### Scenario: Base vacía
- **GIVEN** una base migrada sin temporadas ni usuarios
- **WHEN** se corre la semilla
- **THEN** la semilla termina bien y la base tiene la temporada 2026-27

#### Scenario: Base con un usuario
- **GIVEN** una base migrada con un único usuario y ninguna temporada
- **WHEN** se corre la semilla
- **THEN** la semilla termina con error y el mensaje `La base no está vacía: la semilla solo corre sobre una base vacía.`
- **AND** la base sigue con ese único usuario, sin temporadas, grupos ni filas de tarifario

#### Scenario: Base con una temporada
- **GIVEN** una base migrada con una única temporada y ningún usuario
- **WHEN** se corre la semilla
- **THEN** la semilla termina con error y la base sigue con esa única temporada, sin usuarios, grupos ni filas de tarifario

#### Scenario: Base con una persona
- **GIVEN** una base migrada con una única persona, sin temporadas, usuarios ni familias
- **WHEN** se corre la semilla
- **THEN** la semilla termina con error y el mensaje `La base no está vacía: la semilla solo corre sobre una base vacía.`
- **AND** la base sigue con esa única persona y sin temporadas ni usuarios

#### Scenario: Correr la semilla dos veces
- **GIVEN** una base en la que ya se corrió la semilla
- **WHEN** se corre la semilla otra vez
- **THEN** la semilla termina con error y la base tiene una sola temporada y los mismos cuatro usuarios

## ADDED Requirements

### Requirement: Familias y alumnos de ejemplo
La semilla SHALL crear tres familias con sus personas, sus alumnos y una inscripción por alumno en la temporada 2026-27, con datos inventados, de modo que cada grupo tenga al menos un alumno y una familia tenga dos hijos en el mismo turno.

#### Scenario: Las familias de la semilla
- **WHEN** se corre la semilla sobre una base vacía
- **THEN** hay exactamente estas familias:
  - `Pérez – Ana`, `empleado`: Ana Pérez, nacida el 2018-07-05, en «Tiburones» mañana, y Juan Pérez, nacido el 2020-03-10, en «Delfines» mañana; tutora María Pérez (teléfono `3511234567`, DNI `30111222`) y autorizado a retirar Raúl Pérez (teléfono `3517654321`, sin DNI)
  - `Gómez – Lucía`, `socio`: Lucía Gómez, nacida el 2021-05-20, en «Delfines» tarde; tutor Pablo Gómez (teléfono `3519998877`, DNI `28999888`) y autorizada a retirar María Pérez
  - `Ruiz – Sofía`, `no_socio`: Sofía Ruiz, nacida el 2017-09-01, en «Tiburones» tarde; tutora Laura Ruiz (teléfono `3515556666`, sin DNI)
- **AND** hay exactamente cuatro personas, y María Pérez es una sola fila vinculada a dos familias
- **AND** hay exactamente cuatro inscripciones, todas de la temporada 2026-27
