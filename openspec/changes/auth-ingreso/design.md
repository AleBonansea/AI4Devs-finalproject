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

`LoginEntrada` es un esquema Pydantic con `username` y `password` (`min_length=1` ambos, para el 422). Alternativa: `OAuth2PasswordRequestForm`, que habilita el botón «Authorize» de Swagger. Se descarta porque obliga a `application/x-www-form-urlencoded` y `src/lib/api.ts` habla JSON en todo lo demás; un único formato de error y de cuerpo pesa más que la comodidad de Swagger. Para leer el token se usa `HTTPBearer(auto_error=False)`, que igual aparece en el contrato como esquema de seguridad.

`username` se normaliza con `strip().lower()` antes de buscar: los usuarios se generan en minúsculas (documento técnico) y el teclado del celular capitaliza la primera letra. La contraseña no se toca.

**Asimetría deliberada entre username y contraseña vacíos.** `min_length=1` se valida sobre el valor crudo. Una contraseña vacía da 422. Un username hecho solo de espacios, en cambio, pasa la validación, queda vacío al normalizarse, no encuentra a nadie y termina en el 401 genérico. Es una decisión, no un descuido: el 401 no revela nada que el 422 no revelara, y validar después de normalizar obligaría a un validador propio para un caso que solo produce un pedido inválido. Se puede revisar cuando HU-UT-02 agregue la normalización del username al darlo de alta, y validar los dos con la misma regla.

**Invariante: `usuario.username` se guarda siempre en minúsculas.** El login busca por igualdad exacta (`Usuario.username == entrada_normalizada`), no con `lower()` sobre la columna, para usar el índice único tal cual. Eso solo es correcto si el invariante se cumple: si la base tuviera `JPerez`, ese usuario no podría ingresar nunca y el login respondería el 401 genérico, sin ninguna pista de por qué. Hoy nada en la base lo impide. El `CHECK (username = lower(username))` lo agrega HU-UT-02, que es la que escribe usuarios; hasta entonces la semilla lo respeta, y los tests crean usuarios en minúsculas.

### El token lleva solo el id

`crear_token(str(usuario.id))`, sin rol ni indicadores en `extra`. La dependencia relee el usuario por id en cada petición. Alternativa: poner el rol en el token y evitar la consulta. Se descarta porque un usuario desactivado, bloqueado o con el rol cambiado seguiría operando hasta que el token venza (hasta 8 horas). Una consulta por clave primaria por petición es despreciable para este volumen.

### Tres dependencias encadenadas

1. `obtener_usuario_actual`: lee el bearer, `leer_token`, busca por `sub`. 401 si falta, no valida (`jwt.PyJWTError`, incluido el vencido), `sub` no es un entero, el `sub` no corresponde a ningún usuario, `activo` es false o `bloqueado`. Todas con `WWW-Authenticate: Bearer` y `detail` `Sesión inválida o vencida.` No rechaza el cambio pendiente: la usan los dos exentos, `GET /auth/yo` y el endpoint de HU-UT-06. Ningún otro endpoint la usa directamente.
2. `usuario_habilitado`: depende de la anterior; 403 `Tenés que cambiar tu contraseña antes de continuar.` si `debe_cambiar_password`.
3. `exigir_rol(*roles: RolUsuario)`: fábrica que devuelve una dependencia sobre `usuario_habilitado`; 403 `No tenés permiso para esta operación.` si el rol no está. Se usa como `usuario: Usuario = Depends(exigir_rol(RolUsuario.ADMIN))` o en `dependencies=[...]` del decorador. Es la que usa todo endpoint de negocio, así que el cambio pendiente se hace cumplir sin que cada endpoint tenga que acordarse.

El orden hace que el 401 gane al 403 de cambio pendiente, y este al 403 de rol: un usuario con el cambio pendiente no se entera de qué roles usa un endpoint.

Las dependencias devuelven el modelo `Usuario` al endpoint; eso no viola «toda respuesta pasa por un esquema» porque lo que sale por HTTP pasa por esquemas con `model_config = ConfigDict(from_attributes=True)`:

- `UsuarioActual` (`id`, `username`, `nombre`, `apellido`, `rol`, `debe_cambiar_password`): respuesta de `/yo` y campo `usuario` del login.
- `LoginRespuesta` (`access_token`, `token_type`, `usuario: UsuarioActual`): respuesta del login.
- `UsuarioPublico` (lo mismo sin `debe_cambiar_password`): para anidar un usuario en otra respuesta (quién cobró, quién anuló). No lo usa ningún endpoint de este change, así que no se crea todavía.

`debe_cambiar_password` es un dato del usuario, no de la sesión, así que sale en un único lugar: dentro del usuario. El frontend lo lee igual después del login y al recargar con `/yo`.

### Orden de las comprobaciones en el login

1. Buscar por `username` normalizado.
2. Inexistente → verificar la contraseña contra un hash ficticio fijo (calculado una vez al importar) y responder 401 genérico. Sin esto, «usuario inexistente» responde mucho más rápido que «contraseña incorrecta» y el tiempo revela qué usuarios existen.
3. Desactivado → verificar igual (por la misma razón), 401 genérico, contador intacto.
4. Bloqueado → 403 de bloqueo, **sin verificar la contraseña** y sin tocar el contador. Si el 403 dependiera de que la contraseña fuera correcta, la cuenta bloqueada serviría para adivinarla.
5. Contraseña incorrecta → incremento y 401 genérico.
6. Correcta → contador a 0, token y 200 (con `debe_cambiar_password` tal cual esté).

El 403 de bloqueo sí revela que el usuario existe. Es deliberado: quien quedó bloqueado necesita saber que tiene que ir al Admin, no seguir probando. El costo está en «Risks / Trade-offs», bloqueo disparado desde afuera. El desactivado, en cambio, no se distingue: no hay nada que pueda hacer.

### Incremento atómico

El incremento es `UPDATE usuario SET intentos_fallidos = intentos_fallidos + 1 WHERE id = :id` con `update()` de SQLAlchemy, no leer-sumar-escribir en Python. Dos intentos simultáneos con la lectura en memoria dejarían el contador en 1 en vez de 2, y con eso un atacante en paralelo esquiva el bloqueo. La puesta en 0 sí puede ser una asignación. El servicio hace `commit` del contador también cuando responde 401: el intento fallido tiene que quedar aunque la petición termine en error, así que el commit va antes de lanzar la excepción HTTP.

### Errores en castellano y con forma de FastAPI

Todos los rechazos son `HTTPException` con `detail` string, que es lo que `src/lib/api.ts` ya sabe traducir. El 422 de validación queda como lo emite FastAPI.

### Cómo se prueba `exigir_rol` sin endpoints de negocio

Todavía no hay endpoints restringidos por rol. Los tests de la spec «Declaración de roles por endpoint», y los dos Scenarios de «Cambio obligatorio de contraseña pendiente» que llaman a un endpoint protegido, montan en el test un `APIRouter` de sonda con rutas declaradas con `exigir_rol(...)` sobre una instancia de FastAPI propia del test (con el mismo override de `obtener_sesion`), y llaman a esas rutas por HTTP. No se agregan rutas de prueba a la aplicación real ni al contrato.

## Risks / Trade-offs

- [Vida del token de 8 horas sin renovación ni revocación] → Se mitiga releyendo el usuario en cada petición: desactivar o bloquear corta la sesión al instante. La renovación y la inactividad llegan con el dominio propio (pendiente del documento técnico).
- [**Bloqueo disparado desde afuera.** Los usernames son predecibles (inicial + apellido), el login es público en internet y solo un Admin desbloquea. Cualquiera puede dejar afuera a quien quiera con 5 intentos, y eso además le corta la sesión abierta. Sumado a que el 403 de bloqueo confirma que el usuario existe, sirve también para enumerar usernames: probar 5 veces cada candidato y ver cuáles terminan en 403. Un ataque contra todos los Admin deja al sistema sin nadie que desbloquee] → **Sin mitigación en este change.** Se difiere a HU-UT-08: límite de intentos por IP, desbloqueo automático pasado un tiempo, o ambos. Acl. 9 pide que el bloqueo dure hasta el blanqueo, pero se decidió sin este riesgo a la vista; quedó como pregunta abierta en `aclaraciones-cliente.md` («Desbloqueo de una cuenta bloqueada»). Mientras tanto, el Admin blanquea a mano.
- [`intentos_fallidos` es SmallInteger] → No puede desbordar: a partir de 5 el login ya no incrementa.
- [El hash ficticio no iguala el tiempo exacto de un hash real con otros parámetros] → Se calcula con el mismo `hashear` al importar el módulo, así que usa los mismos parámetros de argon2.

## Migration Plan

Sin migración. Desplegar es publicar el código; volver atrás es revertir el commit. Requiere `SECRET_KEY` en el entorno, que `config.py` ya exige para arrancar.
