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
- Dejar `obtener_usuario_actual`, `usuario_habilitado` y `require_rol` listos para que cada historia siguiente declare sus roles en una línea.
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
| Dependencias `obtener_usuario_actual`, `usuario_habilitado`, `require_rol` | `app/core/deps.py` |

CLAUDE.md pone las dependencias de permisos en `core/` y las reglas de negocio en `services/`. El router solo traduce el resultado del servicio a HTTP.

### Roles de cada endpoint

- `POST /api/v1/auth/login`: público, sin token. Es la puerta.
- `GET /api/v1/auth/yo`: los tres roles, vía `usuario_habilitado` (rechaza el cambio pendiente). No hay filtro por grupo: devuelve solo al propio usuario.

Ninguno de los dos devuelve datos de alumnos, así que no aplica el filtro de consulta del Profesor.

### Cuerpo del login: JSON, no formulario OAuth2

`LoginEntrada` es un esquema Pydantic con `username` y `password` (`min_length=1` ambos, para el 422). Alternativa: `OAuth2PasswordRequestForm`, que habilita el botón «Authorize» de Swagger. Se descarta porque obliga a `application/x-www-form-urlencoded` y `src/lib/api.ts` habla JSON en todo lo demás; un único formato de error y de cuerpo pesa más que la comodidad de Swagger. Para leer el token se usa `HTTPBearer(auto_error=False)`, que igual aparece en el contrato como esquema de seguridad.

`username` se normaliza con `strip().lower()` antes de buscar: los usuarios se generan en minúsculas (documento técnico) y el teclado del celular capitaliza la primera letra. La contraseña no se toca.

### El token lleva solo el id

`crear_token(str(usuario.id))`, sin rol ni indicadores en `extra`. La dependencia relee el usuario por id en cada petición. Alternativa: poner el rol en el token y evitar la consulta. Se descarta porque un usuario desactivado, bloqueado o con el rol cambiado seguiría operando hasta que el token venza (hasta 8 horas). Una consulta por clave primaria por petición es despreciable para este volumen.

### Tres dependencias encadenadas

1. `obtener_usuario_actual`: lee el bearer, `leer_token`, busca por `sub`. 401 si falta, no valida (`jwt.PyJWTError`, incluido el vencido), `sub` no es un entero, el usuario no existe, `activo` es false o `bloqueado`. Todas con `WWW-Authenticate: Bearer` y `detail` `Sesión inválida o vencida.` No rechaza el cambio pendiente: es la que va a usar el endpoint de HU-UT-06.
2. `usuario_habilitado`: depende de la anterior; 403 `Tenés que cambiar tu contraseña antes de continuar.` si `debe_cambiar_password`.
3. `require_rol(*roles: RolUsuario)`: fábrica que devuelve una dependencia sobre `usuario_habilitado`; 403 `No tenés permiso para esta operación.` si el rol no está. Se usa como `usuario: Usuario = Depends(require_rol(RolUsuario.ADMIN))` o en `dependencies=[...]` del decorador.

El orden hace que el 401 gane al 403 de cambio pendiente, y este al 403 de rol: un usuario con el cambio pendiente no se entera de qué roles usa un endpoint.

Las dependencias devuelven el modelo `Usuario` al endpoint; eso no viola «toda respuesta pasa por un esquema» porque lo que sale por HTTP pasa por `UsuarioPublico` (`id`, `username`, `nombre`, `apellido`, `rol`), con `model_config = ConfigDict(from_attributes=True)`.

### Orden de las comprobaciones en el login

1. Buscar por `username` normalizado.
2. Inexistente → verificar la contraseña contra un hash ficticio fijo (calculado una vez al importar) y responder 401 genérico. Sin esto, «usuario inexistente» responde mucho más rápido que «contraseña incorrecta» y el tiempo revela qué usuarios existen.
3. Desactivado → verificar igual (por la misma razón), 401 genérico, contador intacto.
4. Bloqueado → 403 de bloqueo, **sin verificar la contraseña** y sin tocar el contador. Si el 403 dependiera de que la contraseña fuera correcta, la cuenta bloqueada serviría para adivinarla.
5. Contraseña incorrecta → incremento y 401 genérico.
6. Correcta → contador a 0, token y 200 (con `debe_cambiar_password` tal cual esté).

El 403 de bloqueo sí revela que el usuario existe. Es deliberado: el staff es chico, los usuarios son predecibles (inicial + apellido) y quien quedó bloqueado necesita saber que tiene que ir al Admin, no seguir probando. El desactivado, en cambio, no se distingue: no hay nada que pueda hacer.

### Incremento atómico

El incremento es `UPDATE usuario SET intentos_fallidos = intentos_fallidos + 1 WHERE id = :id` con `update()` de SQLAlchemy, no leer-sumar-escribir en Python. Dos intentos simultáneos con la lectura en memoria dejarían el contador en 1 en vez de 2, y con eso un atacante en paralelo esquiva el bloqueo. La puesta en 0 sí puede ser una asignación. El servicio hace `commit` del contador también cuando responde 401: el intento fallido tiene que quedar aunque la petición termine en error, así que el commit va antes de lanzar la excepción HTTP.

### Errores en castellano y con forma de FastAPI

Todos los rechazos son `HTTPException` con `detail` string, que es lo que `src/lib/api.ts` ya sabe traducir. El 422 de validación queda como lo emite FastAPI.

### Cómo se prueba `require_rol` sin endpoints de negocio

Todavía no hay endpoints restringidos por rol. Los tests de la spec «Declaración de roles por endpoint» montan en el test un `APIRouter` de sonda con rutas declaradas con `require_rol(...)` sobre una instancia de FastAPI propia del test (con el mismo override de `obtener_sesion`), y llaman a esas rutas por HTTP. No se agregan rutas de prueba a la aplicación real ni al contrato.

## Risks / Trade-offs

- [Vida del token de 8 horas sin renovación ni revocación] → Se mitiga releyendo el usuario en cada petición: desactivar o bloquear corta la sesión al instante. La renovación y la inactividad llegan con el dominio propio (pendiente del documento técnico).
- [Bloqueo provocado por un tercero: cualquiera que conozca un usuario puede bloquearlo con 5 intentos, y eso además corta su sesión abierta] → Es el comportamiento que piden Acl. 9 y el documento técnico; el blanqueo lo resuelve. HU-UT-08 puede revisar si hace falta algo más.
- [El 403 de bloqueo confirma que el usuario existe] → Aceptado, ver «Orden de las comprobaciones».
- [`intentos_fallidos` es SmallInteger] → No puede desbordar: a partir de 5 el login ya no incrementa.
- [El hash ficticio no iguala el tiempo exacto de un hash real con otros parámetros] → Se calcula con el mismo `hashear` al importar el módulo, así que usa los mismos parámetros de argon2.

## Migration Plan

Sin migración. Desplegar es publicar el código; volver atrás es revertir el commit. Requiere `SECRET_KEY` en el entorno, que `config.py` ya exige para arrancar.
