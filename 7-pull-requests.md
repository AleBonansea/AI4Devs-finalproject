# 7. Pull Requests

> Documenta 3 de las Pull Requests realizadas durante la ejecución del proyecto

El lote 1 se construyó en ocho *changes* de OpenSpec, uno por rama, cada uno con su propia pull request hacia la rama de la entrega. Contando la de la Entrega 1 y las de cierre (documentación y configuración del repositorio), son las de la tabla del final. Después de la Entrega 2 se sumaron tres *changes* más: el menú lateral, los tests de punta a punta y la semilla del entorno demo en Render (#14, #16 y #17). Las de código pasaron por integración continua (`ruff`, `mypy`, `pytest`, tests y build del frontend, y el ida y vuelta de las migraciones). Desde la #3, todas tienen además el informe de una revisión automática con `claude-code-action`, configurada en [`.github/workflows/revisor.yml`](.github/workflows/revisor.yml) y gobernada por [`REVIEW.md`](REVIEW.md); en la #2 el revisor todavía no publicaba. Cómo encaja esa revisión en el mantenimiento del sistema está en [`2-arquitectura-del-sistema.md`](2-arquitectura-del-sistema.md), 2.4.

Las tres que siguen se eligieron porque muestran tres cosas distintas: el ciclo completo estrenándose, la lógica de negocio más delicada, y el cierre de punta a punta del flujo principal.

---

**Pull Request 1**

## [#2 — `feat/auth-ingreso`](https://github.com/AleBonansea/AI4Devs-finalproject/pull/2) · Ingreso al sistema (HU-UT-01)

18 commits · 36 archivos · +2.749 / −134

La primera funcionalidad con código, y la que estrenó el método. Implementa el ingreso con usuario y contraseña, la identificación del usuario por token, el rol exigido en cada endpoint y el cambio de contraseña pendiente.

**Por qué es interesante:** es la PR donde el andamiaje se probó por primera vez, y donde se vio que no funcionaba. Tres commits no son de la funcionalidad sino del propio método:

- `fix: tres agujeros del arnés que aparecieron al estrenarlo con HU-UT-01` — el hook de formato llamaba a `ruff` a secas y nunca lo encontraba, y el error quedaba tragado por un `except`. Llevaba semanas sin correr.
- `fix: reemplazar el Makefile por tasks.py, que sí corre en Windows` — un comando documentado que no se puede ejecutar es una regla que no se cumple.
- `fix: el CI nunca habría pasado, y todavía no corrió ni una vez` — faltaban `SECRET_KEY` y la base de pruebas en el workflow.

El pase del revisor adversarial encontró además un 500 en el login público ante un carácter mal formado, corregido en `fix: el 422 no repite lo recibido y un surrogate suelto da 422`.

**Lo que dejó para el resto del proyecto:** el plan de los siete *changes* del lote, escrito en el backlog para no tener que decidir el orden cada vez; y la reescritura de HU-UT-08, que pasó a ser la mitigación del bloqueo de cuentas disparado desde internet, un riesgo que apareció al diseñar esta misma historia y que no tenía dueño.

---

**Pull Request 2**

## [#8 — `feat/cobro`](https://github.com/AleBonansea/AI4Devs-finalproject/pull/8) · Registrar un cargo con su cálculo (HU-TAR-04, HU-CC-01)

14 commits · 58 archivos · +8.864 / −313

El corazón del sistema: el cálculo del importe que paga una familia, con la tarifa base por turno y modalidad y el descuento por categoría y cantidad de hijos.

**Por qué es interesante:** es donde las reglas del proyecto se vuelven visibles.

- **El cálculo vive en una sola función pura** (`app/services/calculo_cargo.py`) y en ningún otro lado.
- **El precio nunca viene del cliente.** La pantalla manda qué se cobra, no cuánto; el importe lo calcula la API y lo devuelve con su desglose.
- **Cada cargo guarda su cálculo y no se recalcula nunca.** Si mañana cambia el tarifario, los cargos ya emitidos siguen diciendo lo que dijeron.
- **Un solo porcentaje, nunca acumulado**, según la aclaración del cliente: el descuento de categoría y el de tramo de hijos no se suman.

Los montos viajan como texto (`"4462.50"`) y no como número JSON, para que un centavo no pase nunca por un decimal de punto flotante.

El pase adversarial encontró una carrera en el rechazo de cargos repetidos, cerrada en `fix: probar la carrera del repetido, el 100 % y mostrar el total registrado`.

---

**Pull Request 3**

## [#9 — `feat/cuenta-corriente`](https://github.com/AleBonansea/AI4Devs-finalproject/pull/9) · Pagos, saldo y tesorería (HU-CC-02, HU-CC-03, HU-TES-01)

19 commits · 72 archivos · +6.965 / −40

El último *change* del lote, que cierra el flujo principal operativo: alumno inscripto → cargo calculado → pagos parciales → saldo → ingreso en tesorería.

**Por qué es interesante:** tres decisiones de diseño que la revisión puso a prueba.

- **Una sola definición del saldo.** La vista `v_cuenta_corriente` es el único lugar donde se resta pagos a cargos, y la usan el registro de cargos, el de pagos y la consulta. Los pagos se agregan por cargo *antes* del `JOIN`: un `JOIN` directo contaría doble el importe de un cargo con dos pagos.
- **Dos pagos simultáneos del mismo cargo no pueden superar el total.** Se bloquea la fila del cargo con `SELECT … FOR UPDATE` antes de comprobar el saldo. Los tests no pueden reproducirlo, porque cada test corre dentro de una sola transacción; se comprobó a mano con dos pedidos en paralelo, y se agregó un test que protege el bloqueo (`test: proteger el bloqueo del cargo al registrar un pago`).
- **El pago y su ingreso en tesorería, o los dos o ninguno**: una sola transacción con un solo *commit*.

El monto del pago sí lo manda el cliente, y la revisión lo señaló como una posible contradicción con la regla anterior. No lo es —lo que la regla protege es el precio de un cargo, mientras que un pago es un hecho que el Admin informa— pero la redacción se prestaba a confusión y se acotó en `docs: acotar en REVIEW.md la regla del monto al precio de un cargo`.

---

### Todas las pull requests

| # | Rama | Qué incorpora |
|---|---|---|
| [#1](https://github.com/AleBonansea/AI4Devs-finalproject/pull/1) | `feature/entrega-1-AlexisBonansea` | Documentación de la Entrega 1 |
| [#2](https://github.com/AleBonansea/AI4Devs-finalproject/pull/2) | `feat/auth-ingreso` | Ingreso, token, roles (HU-UT-01) |
| [#3](https://github.com/AleBonansea/AI4Devs-finalproject/pull/3) | `feat/tarifario-y-semilla` | Tarifario, temporada, grupos y datos de ejemplo |
| [#4](https://github.com/AleBonansea/AI4Devs-finalproject/pull/4) | `feat/pantalla-de-ingreso` | Pantalla de ingreso y zona protegida |
| [#5](https://github.com/AleBonansea/AI4Devs-finalproject/pull/5) | `feat/familias-y-alumnos` | Alta de alumno con familia y personas autorizadas (HU-AF-01…04) |
| [#6](https://github.com/AleBonansea/AI4Devs-finalproject/pull/6) | `feat/paleta-y-encuadre` | Paleta y encuadre visual del prototipo |
| [#7](https://github.com/AleBonansea/AI4Devs-finalproject/pull/7) | `feat/asistencia` | Tomar asistencia por grupo y fecha (HU-GA-04) |
| [#8](https://github.com/AleBonansea/AI4Devs-finalproject/pull/8) | `feat/cobro` | Cargo con cálculo de tarifa y descuento (HU-TAR-04, HU-CC-01) |
| [#9](https://github.com/AleBonansea/AI4Devs-finalproject/pull/9) | `feat/cuenta-corriente` | Pagos, saldo y tesorería (HU-CC-02, HU-CC-03, HU-TES-01) |
| [#10](https://github.com/AleBonansea/AI4Devs-finalproject/pull/10) | `docs/arranque-y-pull-requests` | Instrucciones de arranque en el readme, este documento y los prompts de la sección 7 |
| [#11](https://github.com/AleBonansea/AI4Devs-finalproject/pull/11) | `feat/fin-de-linea` | Fin de línea LF en todo el repositorio, con `.gitattributes` |
| [#12](https://github.com/AleBonansea/AI4Devs-finalproject/pull/12) | `docs/actualizar-documentacion-entrega-2` | Documentación numerada alineada con lo construido en la Entrega 2 |
| [#13](https://github.com/AleBonansea/AI4Devs-finalproject/pull/13) | `feature/entrega-2-AlexisBonansea` | Entrega 2 hacia `main` |
| [#14](https://github.com/AleBonansea/AI4Devs-finalproject/pull/14) | `feat/menu-lateral-y-edad-de-grupos` | Menú lateral y edad de cada grupo en los selectores |
| [#15](https://github.com/AleBonansea/AI4Devs-finalproject/pull/15) | `feature/entrega-2-AlexisBonansea` | El menú lateral (#14) hacia `main` |
| [#16](https://github.com/AleBonansea/AI4Devs-finalproject/pull/16) | `feat/pruebas-e2e` | Tres recorridos de punta a punta con Playwright, con su job en el CI |
| [#17](https://github.com/AleBonansea/AI4Devs-finalproject/pull/17) | `feat/semilla-fuera-de-local` | Permiso explícito para sembrar la base del entorno demo en Render |
