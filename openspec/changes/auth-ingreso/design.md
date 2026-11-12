# Design

## Context

Ver `proposal.md` para el porqué. Lo que ya existe y condiciona el enfoque:

- `app/models/usuario.py`: `username` único, `password_hash` (argon2), `debe_cambiar_password`, `intentos_fallidos` (SmallInteger con check `>= 0`), `activo`, `rol` (enum `admin | coordinador | profesor`) y la propiedad `bloqueado` (`intentos_fallidos >= 5`). El bloqueo no tiene columna: es estado derivado.
- `app/core/security.py`: `hashear`, `verificar`, `crear_token(asunto, extra)` y `leer_token(token)` con PyJWT, HS256 y `exp` según `access_token_expire_minutes` (480 por defecto en `config.py`).
- `app/core/db.py`: `obtener_sesion`, que los tests reemplazan por una sesión atada a una transacción que se revierte.
- No hay ningún router de capability todavía; `app/api/v1/router.py` está vacío.

El change no toca el esquema, así que no lleva sección de Reversibilidad.

## Goals / Non-Goals

**Goals:**
- Dejar `obtener_usuario_actual`, `usuario_habilitado` y `exigir_rol` listos para que cada historia siguiente declare sus roles en una línea.
- Que el estado del usuario (activo, bloqueado, cambio pendiente, rol) se lea de la base en cada petición, nunca del token.

**Non-Goals:**
- Token de renovación, cookie y vencimiento por inactividad (ver proposal, «Fuera de alcance»).
- La dependencia de pertenencia del Profesor a un grupo o alumno.
- Cualquier escritura sobre `usuario` que no sea el contador de intentos.

## Decisions

### Ubicación

| Pieza | Archivo |
|---|---|
| Rutas `POST /auth/login` y `GET /auth/yo` | `app/api/v1/auth.py`, incluido en `app/api/v1/router.py` |
| Esquemas de entrada y salida | `app/schemas/auth.py` |
| Regla del ingreso (buscar, verificar, contador) | `app/services/auth.py` |
| Dependencias `obtener_usuario_actual`, `usuario_habilitado`, `exigir_rol` | `app/core/deps.py` |

CLAUDE.md pone las dependencias de permisos en `core/` y las reglas de negocio en `services/`. El router solo traduce el resultado del servicio a HTTP.

### Roles de cada endpoint

- `POST /api/v1/auth/login`: público, sin token. Es la puerta.
- `GET /api/v1/auth/yo`: los tres roles, vía `obtener_usuario_actual`, **exento del cambio pendiente**. El frontend lo necesita al recargar para saber quién está logueado y si tiene que mandarlo al cambio de contraseña, y no devuelve nada que el usuario no sepa de sí mismo. Responde `UsuarioActual`. No hay filtro por grupo: devuelve solo al propio usuario.

Ninguno de los dos devuelve datos de alumnos, así que no aplica el filtro de consulta del Profesor.

### Cuerpo del login: JSON, no formulario OAuth2

`LoginEntrada` es un esquema Pydantic con `username` y `password`. Un pedido malformado da 422 (requirement «Pedido de ingreso malformado»). Alternativa: `OAuth2PasswordRequestForm`, que habilita el botón «Authorize» de Swagger. Se descarta porque obliga a `application/x-www-form-urlencoded` y `src/lib/api.ts` habla JSON en todo lo demás; un único formato de error y de cuerpo pesa más que la comodidad de Swagger. Para leer el token se usa `HTTPBearer(auto_error=False)`, que igual aparece en el contrato como esquema de seguridad.

`username` se normaliza con `strip().lower()` en el propio esquema, antes de validarlo: los usuarios se generan en minúsculas (documento técnico) y el teclado del celular capitaliza la primera letra. La contraseña no se toca. Las validaciones corren sobre el valor ya normalizado, así username y contraseña se comportan igual: vacío da 422, también un username hecho solo de espacios.

- `username`: largo 1 a 60, el ancho de la columna `usuario.username`. Sin caracteres de control: un NUL llegaba a Postgres, que lo rechaza, y el login público respondía 500. Es entrada malformada, como la contraseña vacía, y no un usuario inexistente: por eso 422 y no el 401 genérico.
- **El largo se mide después de normalizar.** El tipo `Username` de `app/schemas/auth.py` aplica `strip().lower()` en un `BeforeValidator` y recién después el `max_length`. El orden importa porque `lower()` puede alargar el texto: «İ» en minúsculas son dos caracteres, así que 31 «İ» son 62 normalizados y dan 422, mientras que medido sobre la entrada cruda pasarían. En este change es benigno, porque el login solo hace un `SELECT` y un username de 62 caracteres da 401. **HU-UT-02, que inserta usuarios, tiene que usar este mismo tipo `Username`:** si midiera antes de normalizar, el `INSERT` de 62 caracteres en una columna de 60 rompería con 500.
- `password`: largo 1 a 128. argon2 no tiene el tope de 72 bytes de bcrypt y procesa cualquier tamaño, así que sin tope una contraseña de megabytes cuesta CPU en un endpoint público. 128 deja margen de sobra para cualquier frase de paso. **Este tope protege a argon2, no al servidor:** cuando Pydantic lo comprueba, el cuerpo ya se leyó entero y ya está en memoria.
- **El límite del cuerpo de la petición es de despliegue, no de la aplicación.** FastAPI lee el cuerpo entero antes de validar, así que el `max_length` corta el costo de argon2 pero no el de recibir un cuerpo enorme. Ese tope va en la configuración de Render (o del proxy que tenga delante). Queda como pendiente en «Pendientes técnicos» del documento técnico.
- **Surrogates sueltos.** Un `\ud800` escrito como escape en el JSON no se puede codificar en UTF-8. Pydantic ya lo rechaza (`string_unicode`), pero el 422 de FastAPI repetía el valor recibido en `input` y la respuesta rompía al codificarse: el login público respondía 500. Lo resuelve el manejador de «El 422 no repite lo recibido», más abajo.

**Invariante: `usuario.username` se guarda siempre en minúsculas.** El login busca por igualdad exacta (`Usuario.username == entrada_normalizada`), no con `lower()` sobre la columna, para usar el índice único tal cual. Eso solo es correcto si el invariante se cumple: si la base tuviera `JPerez`, ese usuario no podría ingresar nunca y el login respondería el 401 genérico, sin ninguna pista de por qué. Hoy nada en la base lo impide. El `CHECK (username = lower(username))` lo agrega HU-UT-02, que es la que escribe usuarios; hasta entonces la semilla lo respeta, y los tests crean usuarios en minúsculas.

### El token lleva solo el id

`crear_token(str(usuario.id))`, sin rol ni indicadores en `extra`. La dependencia relee el usuario por id en cada petición. Alternativa: poner el rol en el token y evitar la consulta. Se descarta porque un usuario desactivado, bloqueado o con el rol cambiado seguiría operando hasta que el token venza (hasta 8 horas). Una consulta por clave primaria por petición es despreciable para este volumen.

### Tres dependencias encadenadas

1. `obtener_usuario_actual`: lee el bearer, `leer_token`, busca por `sub`. 401 si falta, no valida (`jwt.PyJWTError`, incluido el vencido), `sub` no es un entero dentro del rango de BIGINT (un valor más grande hacía fallar a Postgres y respondía 500), el `sub` no corresponde a ningún usuario, `activo` es false o `bloqueado`. Todas con `WWW-Authenticate: Bearer` y `detail` `Sesión inválida o vencida.` No rechaza el cambio pendiente: la usan los dos exentos, `GET /auth/yo` y el endpoint de HU-UT-06. Ningún otro endpoint la usa directamente.
2. `usuario_habilitado`: depende de la anterior; 403 `Tenés que cambiar tu contraseña antes de continuar.` si `debe_cambiar_password`.
3. `exigir_rol(*roles: RolUsuario)`: fábrica que devuelve una dependencia sobre `usuario_habilitado`; 403 `No tenés permiso para esta operación.` si el rol no está. Se usa como `usuario: Usuario = Depends(exigir_rol(RolUsuario.ADMIN))` o en `dependencies=[...]` del decorador. Es la que usa todo endpoint de negocio, así que el cambio pendiente se hace cumplir sin que cada endpoint tenga que acordarse.

El orden hace que el 401 gane al 403 de cambio pendiente, y este al 403 de rol: un usuario con el cambio pendiente no se entera de qué roles usa un endpoint.

Las dependencias devuelven el modelo `Usuario` al endpoint; eso no viola «toda respuesta pasa por un esquema» porque lo que sale por HTTP pasa por esquemas con `model_config = ConfigDict(from_attributes=True)`:

- `UsuarioActual` (`id`, `username`, `nombre`, `apellido`, `rol`, `debe_cambiar_password`): respuesta de `/yo` y campo `usuario` del login.
- `LoginRespuesta` (`access_token`, `token_type`, `usuario: UsuarioActual`): respuesta del login.
- `UsuarioPublico` (lo mismo sin `debe_cambiar_password`): para anidar un usuario en otra respuesta (quién cobró, quién anuló). No lo usa ningún endpoint de este change, así que no se crea todavía.

`debe_cambiar_password` es un dato del usuario, no de la sesión, así que sale en un único lugar: dentro del usuario. El frontend lo lee igual después del login y al recargar con `/yo`.

### Orden de las comprobaciones en el login

1. Buscar por `username` normalizado, con bloqueo de fila (ver «Concurrencia»).
2. Inexistente → verificar la contraseña contra un hash ficticio fijo (calculado una vez al importar) y responder 401 genérico. Sin esto, «usuario inexistente» responde mucho más rápido que «contraseña incorrecta» y el tiempo revela qué usuarios existen.
3. Desactivado → verificar igual (por la misma razón), 401 genérico, contador intacto.
4. Bloqueado → 403 de bloqueo, **sin verificar la contraseña** y sin tocar el contador. Si el 403 dependiera de que la contraseña fuera correcta, la cuenta bloqueada serviría para adivinarla.
5. Contraseña incorrecta → incremento y 401 genérico.
6. Correcta → contador a 0, token y 200 (con `debe_cambiar_password` tal cual esté).

El 403 de bloqueo sí revela que el usuario existe. Es deliberado: quien quedó bloqueado necesita saber que tiene que ir al Admin, no seguir probando. El costo está en «Risks / Trade-offs», bloqueo disparado desde afuera. El desactivado, en cambio, no se distingue: no hay nada que pueda hacer.

### Concurrencia: incremento atómico y bloqueo de fila

Son dos mecanismos y cada uno garantiza una cosa distinta:

- **El `UPDATE` atómico hace exacta la cuenta.** El incremento es `UPDATE usuario SET intentos_fallidos = intentos_fallidos + 1 WHERE id = :id` con `update()` de SQLAlchemy, no leer-sumar-escribir en Python: dos fallos simultáneos suman 2, no 1. Por sí solo no hace valer el límite: el chequeo de bloqueo se hace antes de verificar la contraseña, y entre ese chequeo y el incremento está argon2. Cincuenta pedidos simultáneos contra una cuenta con 4 fallos leían todos 4, verificaban todos su contraseña y probaban cincuenta claves en vez de una; si una acertaba, la puesta en 0 pisaba los incrementos de las demás y desbloqueaba la cuenta.
- **El bloqueo de fila hace valer el límite entre pedidos simultáneos de la misma cuenta.** El login lee el usuario con `with_for_update()`, que serializa los logins concurrentes de esa cuenta hasta el `commit`: a partir del quinto fallo, los pedidos que esperaban ven el contador en 5 y responden 403 sin verificar la contraseña. No cambia la respuesta de ningún pedido individual. El costo es que los logins de una misma cuenta se atienden de a uno, lo que para personas reales no se nota.
- **La defensa contra la fuerza bruta distribuida es el límite por origen de HU-UT-08.** Ninguno de los dos mecanismos frena a quien prueba pocas claves contra muchas cuentas.

La puesta en 0 sí puede ser una asignación: con la fila bloqueada nadie más la modifica en el medio. El servicio hace `commit` del contador también cuando responde 401: el intento fallido tiene que quedar aunque la petición termine en error, así que el commit va antes de lanzar la excepción HTTP, y es el commit el que libera el bloqueo de fila.

**Excepción deliberada: el bloqueo de fila es código de producción sin test.** Un test de concurrencia acá necesitaría varias conexiones reales fuera de la transacción que se revierte, hilos y tiempos, y saldría lento y frágil. Ningún Scenario lo cubre y no se agrega uno. Queda escrito para que nadie lo saque creyendo que sobra: sin él, el límite de 5 intentos no vale bajo pedidos simultáneos.

### Errores en castellano y con forma de FastAPI

Todos los rechazos son `HTTPException` con `detail` string, que es lo que `src/lib/api.ts` ya sabe traducir. El 422 de validación conserva la forma de FastAPI (`detail` como lista con `loc`, `msg` y `type`), salvo el campo `input`.

### El 422 no repite lo recibido

Un manejador de `RequestValidationError` registrado en `app/main.py` arma el mismo 422 que FastAPI pero sin el campo `input` de cada error. Por dos motivos: el 422 del login repetía la contraseña rechazada, que así queda escrita en cualquier proxy o log que guarde respuestas, y repetir un surrogate suelto hacía romper la respuesta con 500. Es global, no solo del login: ningún endpoint necesita que le devuelvan lo que mandó, y los que reciban datos sensibles (contraseñas nuevas, datos médicos) quedan cubiertos sin acordarse. `loc` alcanza para que `src/lib/api.ts` pegue el error al lado de su campo.

### Cómo se prueba `exigir_rol` sin endpoints de negocio

Todavía no hay endpoints restringidos por rol. Los tests de la spec «Declaración de roles por endpoint», y los dos Scenarios de «Cambio obligatorio de contraseña pendiente» que llaman a un endpoint protegido, montan en el test un `APIRouter` de sonda con rutas declaradas con `exigir_rol(...)` sobre una instancia de FastAPI propia del test (con el mismo override de `obtener_sesion`), y llaman a esas rutas por HTTP. No se agregan rutas de prueba a la aplicación real ni al contrato.

## Risks / Trade-offs

- [Vida del token de 8 horas sin renovación ni revocación] → Se mitiga releyendo el usuario en cada petición: desactivar o bloquear corta la sesión al instante. La renovación y la inactividad llegan con el dominio propio (pendiente del documento técnico).
- [**Bloqueo disparado desde afuera.** Los usernames son predecibles (inicial + apellido), el login es público en internet y solo un Admin desbloquea. Cualquiera puede dejar afuera a quien quiera con 5 intentos, y eso además le corta la sesión abierta. Sumado a que el 403 de bloqueo confirma que el usuario existe, sirve también para enumerar usernames: probar 5 veces cada candidato y ver cuáles terminan en 403. Un ataque contra todos los Admin deja al sistema sin nadie que desbloquee] → **Sin mitigación en este change.** Se difiere a HU-UT-08: límite de intentos por IP, desbloqueo automático pasado un tiempo, o ambos. Acl. 9 pide que el bloqueo dure hasta el blanqueo, pero se decidió sin este riesgo a la vista; quedó como pregunta abierta en `aclaraciones-cliente.md` («Desbloqueo de una cuenta bloqueada»). Mientras tanto, el Admin blanquea a mano.
- [`intentos_fallidos` es SmallInteger] → No puede desbordar: a partir de 5 el login ya no incrementa.
- [El hash ficticio no iguala el tiempo exacto de un hash real con otros parámetros] → Se calcula con el mismo `hashear` al importar el módulo, así que usa los mismos parámetros de argon2.

## Migration Plan

Sin migración. Desplegar es publicar el código; volver atrás es revertir el commit. Requiere `SECRET_KEY` en el entorno, que `config.py` ya exige para arrancar.
