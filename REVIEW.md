# Como se revisa en este repo

Esto es vinculante para el subagente `adversarial-reviewer` y para el
revisor automatico de los pull requests. Si no entra en esta pagina, no
es regla.

## Que es grave

Solo estas cuatro cosas abren un hallazgo grave. Fuera de aca, nada es
grave.

1. **El dinero sale mal.** Un importe que se recalcula en vez de usar el
   que se guardo con el cargo. Un porcentaje acumulado. Un tramo
   aplicado a un solo hijo. Un monto que llega del cuerpo de la
   peticion. Hermanos contados sin separar por turno. Un redondeo
   distinto en dos lugares. Una comparacion de dinero con tolerancia.

2. **Alguien ve lo que no le toca.** Un listado que trae todo y filtra
   en memoria. Un endpoint sin dependencia de rol. Un Profesor que llega
   a datos medicos o documentos de un alumno fuera de sus grupos. Un
   esquema de respuesta que arrastra un campo que no deberia salir
   (hash de contraseña, dato medico, documento). Un enlace a un archivo
   adjunto que no caduca.

3. **Se destruye algo.** Un `DELETE` sobre datos del negocio. Una
   anulacion sin contraasiento en tesoreria. Un movimiento de tesoreria
   o un cierre de canon modificable. Una migracion que tira una columna
   o una tabla con datos. Un `downgrade()` vacio.

4. **El verde no significa nada.** Un test que pasaria igual con la
   funcion comentada. Un caso de limite con un solo lado. Un test que
   depende del orden o del estado que dejo otro. Una base de pruebas que
   no es Postgres.

## Cuanto se puede sugerir

Los hallazgos graves, todos. Ademas, **hasta cinco** sugerencias
menores, las cinco que mas valen. No seis.

El tope no es por ahorrar. Un informe de cuarenta puntos no se lee: se
cierra. Cinco se arreglan.

## Donde no se reporta

- **Lo que ya cubre otra comprobacion.** El formato lo arregla `ruff
  format`. Los tipos los agarra `mypy`. El estilo lo agarra `ruff
  check`. Si el CI ya lo dice, el revisor callado.
- **Codigo generado.** Las migraciones de Alembic ya pasaron por la
  skill `revisar-migracion`; `docs/api/openapi.json` lo genera FastAPI.
- **Archivos que este cambio no toco.** La deuda vieja no es hallazgo de
  este pull request.
- **El estilo del proyecto.** Castellano en los nombres de dominio,
  servicios como funciones puras, esquemas de Pydantic en toda
  respuesta: asi se hace aca. No se propone cambiarlo en una revision.
- **La version del stack.** SQLAlchemy 2, Pydantic v2 y FastAPI con
  `lifespan` son deliberados. Una firma que no reconoces no es un error:
  comprobala en el paquete instalado antes de reportarla.

## Cita o calla

Cada hallazgo lleva `fichero:linea` y la linea citada textual.

Deducir del nombre de la funcion no cuenta. Si no abriste el archivo, no
lo reportes.

## Forma del hallazgo

```
**[GRAVE] El descuento del tramo se aplica a un solo hijo**
`backend/app/services/calculo_cargo.py:48`
    pct = tabla[cat].mes[tramo - 1] if alumno.es_el_mayor else 0

Familia de 3 hijos en el turno mañana, categoria empleado, modalidad
Mes. Tarifa base 85000, tramo 3 = 30%. Deberia cobrarse 59500 por cada
uno de los tres. Se cobra 59500 por el mayor y 85000 por los otros dos:
51000 de mas por mes y por familia.
```

Que esta mal, donde, y **que pasa concretamente si sale asi**: entrada,
estado y resultado equivocado. Si no podes escribir ese caso concreto,
el hallazgo no esta listo para reportarse.

## Lo que el revisor no hace

No felicita. No resume lo que el codigo hace. No arregla: señala, y
arregla otro. No propone refactors de gusto.
