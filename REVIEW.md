# Como se revisa en este repo

Esto es vinculante para el subagente `adversarial-reviewer` y para el
revisor automatico de los pull requests. Si no entra en esta pagina, no
es regla.

## Que es grave

Solo estas cuatro cosas abren un hallazgo grave. Fuera de aca, nada es
grave.

1. **El dinero sale mal.** Un importe que se recalcula en vez de usar el
   que se guardo con el cargo. **El % de la categoria aplicado a la tarifa
   base en lugar de al valor del no socio** (es el error del modelo viejo,
   vigente hasta el 10/11/2026, y el mas facil de cometer). Los dos
   porcentajes sumados en lugar de multiplicados. Un redondeo intermedio
   entre los dos factores en vez de uno solo al final. La escala de hijos
   aplicada en Dia, Semana o Quincena, donde no corre. Una dimension de
   tramos en el % de la categoria, que escalaria dos veces. Un tramo
   aplicado a un solo hijo. Un monto que llega del cuerpo de la peticion.
   Hermanos contados sin separar por turno. Una comparacion de dinero con
   tolerancia.

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
**[GRAVE] El % de la categoria se aplica a la tarifa base, no al valor del no socio**
`backend/app/services/calculo_cargo.py:48`
    total = base * (1 - pct_categoria / 100)

Familia socia, 3 hijos en el turno mañana, modalidad Mes. Tarifa base
100000, tramo de 3 hijos 15%, socio 50%. El total correcto es 42500
(100000 x 0,85 x 0,50). Esta linea devuelve 50000, porque descarta la
escala de hijos: 7500 de mas por hijo y por mes, 22500 por familia.
```

Que esta mal, donde, y **que pasa concretamente si sale asi**: entrada,
estado y resultado equivocado. Si no podes escribir ese caso concreto,
el hallazgo no esta listo para reportarse.

## Lo que el revisor no hace

No felicita. No resume lo que el codigo hace. No arregla: señala, y
arregla otro. No propone refactors de gusto.
