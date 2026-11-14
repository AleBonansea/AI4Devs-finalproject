# Tasks

> Antes de la primera tarea: rama `feat/cobro` salida de la rama de entrega actualizada (regla 1 de CLAUDE.md); ya creada el 14/11/2026 desde `feature/entrega-2-AlexisBonansea` con `asistencia` mergeado. Cada tarea que toca rutas, esquemas o modelos cierra su commit con `python tasks.py openapi-generate` (regla 5). La tarea 4.1 lo comprueba al final.

## 1. Esquema del cargo y supuestos

- [x] 1.1 Con la skill `backend-feature`, crear el modelo `Cargo` y la migración `crear_cargo`, según los Requirements de `cargos` «El cargo guarda su cálculo» (3 Scenarios), «La forma del cargo según el tipo y la modalidad» (8) y «Un cargo no se repite» (5): 16 Scenarios.
  - Columnas según `3-modelo-de-datos.md`, «`cargo`»; restricciones, nombres e índices según design, «Esquema». Con `MarcaDeCreacion`; reusa `TIPO_MODALIDAD` y `TIPO_CATEGORIA_FAMILIA` de `enums.py`.
  - Los tests insertan directo en la base: los endpoints todavía no existen. Tests en `backend/tests/functional/cargos/`.
  - Sumar a la regla de `cargo` en `3-modelo-de-datos.md` los tres índices únicos parciales, con la nota de que sumarán `AND anulado_en IS NULL` cuando llegue la anulación de cargos.
  - **Se verifica con** los 16 tests en rojo por el motivo correcto (no existe la tabla) y después en verde; la skill `revisar-migracion` sobre la migración (sin `CREATE TYPE`, con los `postgresql_where` de los índices parciales), con `upgrade head` → `downgrade -1` → `upgrade head` contra la base de pruebas; `python tasks.py test`, `lint` y `typecheck` en verde.
- [x] 1.2 Registrar en `docs/prd/aclaraciones-cliente.md`, «Preguntas abiertas», las tres entradas de design, «Supuestos registrados»: «Cargos repetidos» (decidido con el usuario el 14/11/2026), «Cargo de un alumno sin inscripción» y «Fecha del cargo del Día», cada una con su **[SUPUESTO]** vigente y la referencia al change `cobro`. **Se verifica con** las tres entradas escritas con esos títulos, que son los que citan los Requirements de `cargos`.

## 2. El cálculo

- [x] 2.1 Con la skill `backend-feature`, crear `app/services/calculo_cargo.py` con `calcular_abono`, `calcular_monto_fijo`, `TablaDescuentos`, `Desglose` y `FaltaDescuento`, según design, «El cálculo, en `app/services/calculo_cargo.py`, como función pura».
  - Función pura: no importa nada de `app.core.db` ni de los modelos de SQLAlchemy, solo los enumerados.
  - Tests en `backend/tests/functional/cargos/test_calculo_cargo.py`, con los casos de la lista del design, sin base ni cliente.
  - **Se verifica con** los tests en rojo por el motivo correcto (no existe el módulo) y después en verde; el caso 1000.05 al 50 % en rojo a propósito si se cambia `ROUND_HALF_UP` por el redondeo por defecto, y revertido; `python tasks.py test`, `lint` y `typecheck` en verde.

## 3. Endpoints

- [x] 3.1 Con la skill `backend-feature`, construir `POST /api/v1/cargos` y `POST /api/v1/cargos/simulacion` en un router `cargos.py`, con el servicio `app/services/cargos.py` y los esquemas de `app/schemas/cargos.py`, según estos Requirements de `cargos`: «Registrar un cargo» (6 Scenarios), «Un único porcentaje sobre la tarifa base» (5), «El tramo de hijos del Mes» (6), «Un cargo registrado no se recalcula» (2), «Saldo pendiente al registrar» (2), «Simular un cargo» (2), y de «Solo el Admin registra cargos» todos menos «Coordinador pide las opciones» (5): 28 Scenarios.
  - `preparar_cargo` compartida por simulación y registro, y el orden de los pasos según design, «El servicio». En esta tarea alcanza con los pasos que piden estos Scenarios; los rechazos de la 3.2 pueden quedar sin implementar.
  - Los tests arman su propio tarifario con los valores de cada Scenario, no el de la semilla (los porcentajes de `empleado` difieren). El de «Medio centavo» pasa por la base: el `CHECK` es parte de lo que prueba.
  - Los tests de «no se guarda nada» cuentan los cargos antes y después.
  - **Se verifica con** los 28 tests en rojo por el motivo correcto y después en verde, `docs/api/openapi.json` regenerado, y `python tasks.py test`, `lint` y `typecheck` en verde.
- [x] 3.2 Con la skill `backend-feature`, los rechazos del registro y la simulación, según estos Requirements de `cargos`: «Qué pide cada tipo de cargo» (12 Scenarios), «El alumno está inscripto en la temporada» (2), «La fecha del Día está dentro de la temporada» (4), «La temporada cerrada queda para consulta» (1), «Falta configuración del tarifario» (3) y «Un cargo repetido se rechaza» (4): 26 Scenarios.
  - Errores juntados en un `ReglaIncumplida`, 409 con `detail` de texto, y el `IntegrityError` de los índices únicos traducido al mismo 409, según design, «El servicio».
  - Además de los Scenarios, un test de la carrera: con el cargo insertado directo en la base entre la comprobación y el `INSERT` (o, más simple, saltando la comprobación con el índice ya ocupado), la respuesta es 409 y no 500.
  - **Se verifica con** los 26 tests en rojo por el motivo correcto y después en verde (los 28 de la 3.1 siguen en verde sin tocarlos), `docs/api/openapi.json` regenerado, y `python tasks.py test`, `lint` y `typecheck` en verde.
- [x] 3.3 Con la skill `backend-feature`, construir `GET /api/v1/cargos/opciones` en el mismo router, según el Requirement de `cargos` «Opciones para registrar un cargo» (1 Scenario) y el Scenario «Coordinador pide las opciones» de «Solo el Admin registra cargos»: 2 Scenarios. **Se verifica con** los 2 tests en rojo por el motivo correcto y después en verde, `docs/api/openapi.json` regenerado, y `python tasks.py test`, `lint` y `typecheck` en verde.
- [x] 3.4 Con la skill `backend-feature`, construir `GET /api/v1/familias/{familia_id}/inscripciones` en `familias.py`, según los Requirements de `familias` «Inscripciones de una familia» (7 Scenarios) y «Quién puede ver las inscripciones de una familia» (5): 12 Scenarios.
  - `exigir_rol(ADMIN)` antes de buscar la familia; `id_posible` para el id fuera de `bigint`; el esquema `InscripcionDeFamilia` con solo seis campos (design, «Esquemas»).
  - **Se verifica con** los 12 tests en rojo por el motivo correcto y después en verde, incluido el que comprueba exactamente seis campos; los tests de `familias` que ya existen siguen en verde sin tocarlos; `docs/api/openapi.json` regenerado; `python tasks.py test`, `lint` y `typecheck` en verde.

## 4. Contrato

- [x] 4.1 Comprobar que `docs/api/openapi.json` tiene los cuatro endpoints nuevos con sus esquemas, que `CargoEntrada` no tiene ningún campo de monto ni de porcentaje y no admite campos extra, que `InscripcionDeFamilia` tiene solo sus seis campos, y que ningún endpoint existente cambió. **Se verifica con** `python tasks.py openapi-check` en verde y el diff de `openapi.json` limitado a lo nuevo.

## 5. Pantalla «Registrar cargo»

- [x] 5.1 Con la skill `frontend-feature`, crear `src/lib/montos.ts` con `formatearMonto` y `formatearPorcentaje`, según design, «Frontend», y sumar la regla a CLAUDE.md, sección Frontend, junto a la de `fechas.ts`.
  - Test de las funciones puras en `frontend/tests/lib/montos.test.ts`, con los casos del design.
  - **Se verifica con** el test en rojo por el motivo correcto (no existe el módulo) y después en verde, la huella de `frontend/tests/` intacta, y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.
- [x] 5.2 Con la skill `frontend-feature`, el acceso solo para el Admin: `src/routes/RutaSoloAdmin.tsx`, la ruta `/cargos/nuevo` en `App.tsx` (con una página mínima que la 5.3 completa) y el botón en `Inicio.tsx`, según los Scenarios de `auth` «Ir a registrar un cargo», «El Coordinador no ve el acceso a cobrar» y «El Profesor no ve el acceso a cobrar», y el de `cargos` «Coordinador abre la pantalla»: 4 Scenarios.
  - Tests en `frontend/tests/auth/` y `frontend/tests/cargos/`. Los tests de `auth` que ya existen no se tocan.
  - **Se verifica con** los 4 tests en rojo por el motivo correcto y después en verde, la huella de `frontend/tests/` intacta después de implementar, y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.
- [x] 5.3 Con la skill `frontend-feature`, construir la pantalla `/cargos/nuevo`, según los Requirements de `cargos` «Pantalla «Registrar cargo»» (los 3 Scenarios que no son del Coordinador), «El desglose en la pantalla» (4) y «Registrar desde la pantalla» (4): 11 Scenarios.
  - Las llamadas y sus tipos en `src/lib/api.ts`; `NOMBRE_DE_LA_MODALIDAD` en `src/lib/nombres.ts`; `BuscadorFamilia` sacado de `SelectorFamilia` y `DesgloseCargo`, en `src/components/`; la página en `src/pages/RegistrarCargo.tsx` (design, «Frontend»). Ningún color nuevo: el total usa `dinero`.
  - Tests en `frontend/tests/cargos/` con `fetch` fingido. Los tests de `frontend/tests/alumnos/` no se tocan: son el control de que la extracción de `BuscadorFamilia` no cambió el alta.
  - El test del cuerpo enviado comprueba la lista exacta de claves, no solo la ausencia de `monto_total`.
  - **Se verifica con** los 11 tests en rojo por el motivo correcto, la huella de `frontend/tests/` intacta después de implementar, los tests de alumnos en verde, y `python tasks.py front-test` y `cd frontend && npm run lint && npm run build` en verde.

## 6. Comprobación de punta a punta

- [ ] 6.1 Con la base de desarrollo migrada y la semilla cargada, la API y el frontend levantados, comprobar a mano en el navegador:
  - como `lrodriguez` (coordinador) y como `jperez` (profesor), el inicio no muestra `Registrar cargo` y `/cargos/nuevo` vuelve a `/`;
  - como `mgarcia` (admin), en `/cargos/nuevo`, la familia «Pérez – Ana» (empleado, Ana y Juan a la mañana) muestra `Empleado` y ofrece `Ana Pérez · Mañana` y `Juan Pérez · Mañana`;
  - un «Abono» del Mes para Juan, «Mes 1»: con la semilla (empleado, 2 hijos, 32,50 %) el desglose dice `$ 100.000`, `32,5 %` y `$ 67.500`; registrarlo y ver el saldo `$ 67.500`;
  - repetir el mismo cargo y ver el rechazo por repetido antes de poder registrar;
  - una «Preinscripción» para Ana: `$ 20.000`, `Sin descuento`; al registrarla, saldo `$ 87.500`;
  - en la base, los dos cargos con su desglose y `mgarcia` como autor;
  - la pantalla a 360 px de ancho, sin scroll horizontal, y recorrible con el teclado.
  - **Se verifica con** cada punto anotado como hecho en el informe de la tarea, con lo que haya fallado.
- [ ] 6.2 `python tasks.py test`, `lint`, `typecheck`, `openapi-check`, `front-test` y `front-lint` en verde. **Se verifica con** la salida de cada uno anotada en el informe.

## 7. Revisión adversarial

- [ ] 7.1 Un pase del subagente `adversarial-reviewer` sobre el change terminado, antes del pull request. Rige `REVIEW.md`, «Cuándo se deja de revisar». **Se verifica con** sus hallazgos resueltos o justificados por escrito en esta tarea.

## Workflow follow-up

- Comprobar el change con `/openspec-verify-change` y archivarlo con `/openspec-archive-change`, que crea `openspec/specs/cargos` y funde los deltas de `familias` y `auth`.
- Al archivar, reemplazar los criterios de HU-CC-01 en `5-historias-de-usuario.md` por un puntero a la spec de `cargos`.
- Pull request de `feat/cobro` hacia la rama de entrega.
