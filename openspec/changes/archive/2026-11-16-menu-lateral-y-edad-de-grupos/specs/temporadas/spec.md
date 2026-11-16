# Spec Delta

## Purpose

La temporada como eje del modelo: su identificación, sus fechas y las reglas que rigen sus datos. Esta capability nace con el formato del nombre y la va a ampliar la apertura de temporadas (HU-UT-04).

## ADDED Requirements

### Requirement: Formato del nombre de la temporada
El nombre de una temporada SHALL tener la forma `AAAA-AA`: cuatro dígitos, un guion y dos dígitos (por ejemplo, `2026-27`). La base MUST rechazar cualquier otro nombre. Es lo que permite leer el año de referencia de la edad de los grupos.

#### Scenario: Nombre con el formato
- **WHEN** se inserta una temporada con nombre `2026-27`
- **THEN** la fila queda guardada

#### Scenario: Nombre con el año corto
- **WHEN** se inserta una temporada con nombre `26-27`
- **THEN** la base rechaza la fila

#### Scenario: Nombre con texto
- **WHEN** se inserta una temporada con nombre `Verano 2026`
- **THEN** la base rechaza la fila

#### Scenario: Nombre con el segundo año completo
- **WHEN** se inserta una temporada con nombre `2026-2027`
- **THEN** la base rechaza la fila
