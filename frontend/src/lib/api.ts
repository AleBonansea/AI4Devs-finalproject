/**
 * El unico punto de contacto con el backend.
 *
 * Todo lo que el frontend le pide a la API pasa por aca. Ningun componente
 * llama a `fetch` por su cuenta: hay una regla de eslint que lo corta. Asi
 * el token, el manejo de errores y la traduccion de los mensajes se escriben
 * una vez en lugar de catorce.
 */

const BASE = import.meta.env.VITE_API_URL ?? "";
const CLAVE_TOKEN = "escuelita.token";

/** Error de la API, con el detalle por campo que devuelve FastAPI. */
export class ErrorDeApi extends Error {
  constructor(
    readonly estado: number,
    mensaje: string,
    readonly porCampo: Record<string, string> = {},
  ) {
    super(mensaje);
    this.name = "ErrorDeApi";
  }
}

export function guardarToken(token: string): void {
  try {
    localStorage.setItem(CLAVE_TOKEN, token);
  } catch {
    // Navegacion privada o almacenamiento bloqueado: la sesion dura lo que
    // dure la pestana. No es motivo para romper la pantalla.
  }
}

export function leerToken(): string | null {
  try {
    return localStorage.getItem(CLAVE_TOKEN);
  } catch {
    return null;
  }
}

export function borrarToken(): void {
  try {
    localStorage.removeItem(CLAVE_TOKEN);
  } catch {
    /* ver guardarToken */
  }
}

// --- Aviso de sesion perdida ---------------------------------------------------
// Un 401 en una llamada que salio con token quiere decir que el token ya no
// sirve. En lugar de que cada pantalla lo atrape (y alguna se olvide), api.ts
// avisa a quien se haya suscripto; hoy, ProveedorSesion.

const oyentesSesionPerdida = new Set<() => void>();

/**
 * Suscribe `fn` al aviso de sesion perdida. Devuelve la funcion para
 * desuscribirse, pensada para la limpieza de un efecto.
 */
export function alPerderSesion(fn: () => void): () => void {
  oyentesSesionPerdida.add(fn);
  return () => {
    oyentesSesionPerdida.delete(fn);
  };
}

function avisarSesionPerdida(): void {
  // Se copia el conjunto: un oyente podria desuscribirse mientras se recorre.
  for (const fn of [...oyentesSesionPerdida]) fn();
}

/**
 * Traduce el cuerpo de error de FastAPI a algo que una pantalla pueda mostrar.
 *
 * FastAPI devuelve `{detail: "texto"}` para los errores que levantamos y
 * `{detail: [{loc, msg, type}, ...]}` para los de validacion de Pydantic.
 * Las pantallas necesitan el error pegado a su campo, no un parrafo.
 */
function traducirError(estado: number, cuerpo: unknown): ErrorDeApi {
  const detalle = (cuerpo as { detail?: unknown } | null)?.detail;

  if (typeof detalle === "string") {
    return new ErrorDeApi(estado, detalle);
  }

  if (Array.isArray(detalle)) {
    const porCampo: Record<string, string> = {};
    for (const item of detalle) {
      const loc = (item as { loc?: unknown[] }).loc ?? [];
      const campo = loc.filter((p) => p !== "body").join(".");
      const msg = String((item as { msg?: unknown }).msg ?? "Valor inválido");
      if (campo) porCampo[campo] = msg;
    }
    const primero = Object.values(porCampo)[0] ?? "Revisá los datos ingresados.";
    return new ErrorDeApi(estado, primero, porCampo);
  }

  if (estado === 401) return new ErrorDeApi(estado, "Tu sesión venció. Volvé a ingresar.");
  if (estado === 403) return new ErrorDeApi(estado, "No tenés permiso para hacer esto.");
  if (estado >= 500)
    return new ErrorDeApi(estado, "El servidor tuvo un problema. Intentá de nuevo.");
  return new ErrorDeApi(estado, "No se pudo completar la operación.");
}

async function pedir<T>(metodo: string, ruta: string, cuerpo?: unknown): Promise<T> {
  const cabeceras: Record<string, string> = {};
  const token = leerToken();
  if (token) cabeceras.Authorization = `Bearer ${token}`;
  if (cuerpo !== undefined) cabeceras["Content-Type"] = "application/json";

  let respuesta: Response;
  try {
    respuesta = await fetch(`${BASE}/api/v1${ruta}`, {
      method: metodo,
      headers: cabeceras,
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    });
  } catch {
    // Sin red, o el backend caido. El Profesor toma asistencia desde el
    // telefono en el club, asi que este caso pasa de verdad.
    throw new ErrorDeApi(0, "No se pudo conectar con el servidor. Revisá tu conexión.");
  }

  if (respuesta.status === 401) {
    borrarToken();
    // Solo avisa si la llamada salio con token: el 401 del login (usuario o
    // contrasena incorrectos) sale sin token y no es una sesion que se pierde.
    if (token) avisarSesionPerdida();
  }

  if (!respuesta.ok) {
    let cuerpoError: unknown = null;
    try {
      cuerpoError = await respuesta.json();
    } catch {
      /* el servidor no devolvio JSON */
    }
    throw traducirError(respuesta.status, cuerpoError);
  }

  if (respuesta.status === 204) return undefined as T;
  return (await respuesta.json()) as T;
}

export const api = {
  get: <T>(ruta: string) => pedir<T>("GET", ruta),
  post: <T>(ruta: string, cuerpo?: unknown) => pedir<T>("POST", ruta, cuerpo),
  put: <T>(ruta: string, cuerpo?: unknown) => pedir<T>("PUT", ruta, cuerpo),
  patch: <T>(ruta: string, cuerpo?: unknown) => pedir<T>("PATCH", ruta, cuerpo),
};

// --- Sesion -----------------------------------------------------------------
// Los tipos copian los campos del contrato (docs/api/openapi.json).

export type RolUsuario = "admin" | "coordinador" | "profesor";

/** El usuario que ingreso, tal como lo devuelve la API: sin hash ni intentos. */
export interface UsuarioActual {
  id: number;
  username: string;
  nombre: string;
  apellido: string;
  rol: RolUsuario;
  debe_cambiar_password: boolean;
}

/** Respuesta de `POST /auth/login`. */
export interface LoginRespuesta {
  access_token: string;
  token_type?: "bearer";
  usuario: UsuarioActual;
}

/**
 * El usuario del token guardado. Responde aunque el cambio de contrasena
 * este pendiente, que es lo que se necesita al recargar la pagina.
 */
export function usuarioActual(): Promise<UsuarioActual> {
  return api.get<UsuarioActual>("/auth/yo");
}

/**
 * Ingreso con usuario y contrasena. Se mandan tal como se escribieron: la API
 * no normaliza la contrasena y el usuario lo compara ella.
 */
export function ingresar(username: string, password: string): Promise<LoginRespuesta> {
  return api.post<LoginRespuesta>("/auth/login", { username, password });
}

// --- Alta de alumnos ----------------------------------------------------------
// Los tipos copian los esquemas del contrato (docs/api/openapi.json). Ninguno
// lleva un monto: la pantalla manda que se registra, nunca un precio.

export type Turno = "manana" | "tarde";

export type CategoriaFamilia = "socio" | "empleado" | "no_socio";

/** `GrupoParaInscribir`: un grupo donde se puede inscribir, con su sugerencia. */
export interface GrupoParaInscribir {
  id: number;
  nombre: string;
  turno: Turno;
  nacimiento_desde: string;
  nacimiento_hasta: string;
  sugerido: boolean;
}

/** `FamiliaEncontrada`: lo unico que trae la busqueda por apellido. */
export interface FamiliaEncontrada {
  id: number;
  etiqueta: string;
  categoria: CategoriaFamilia;
}

/** `PersonaEncontrada`: lo unico que trae la busqueda por DNI. */
export interface PersonaEncontrada {
  id: number;
  nombre: string;
  apellido: string;
}

/** `PersonaNueva`: una persona que se carga en el alta. */
export interface PersonaNueva {
  nombre: string;
  apellido: string;
  telefono: string;
  dni?: string | null;
  es_tutor: boolean;
}

/** `PersonaReutilizada`: una persona ya cargada, elegida por su id. */
export interface PersonaReutilizada {
  persona_id: number;
  es_tutor: boolean;
}

/** `AltaAlumnoEntrada`: `familia_id` para una familia existente, `categoria` para una nueva. */
export interface AltaAlumnoEntrada {
  nombre: string;
  apellido: string;
  fecha_nacimiento: string;
  grupo_id: number;
  familia_id?: number | null;
  categoria?: CategoriaFamilia | null;
  personas: (PersonaReutilizada | PersonaNueva)[];
}

/** `AlumnoRegistrado`: la respuesta 201 del alta. */
export interface AlumnoRegistrado {
  id: number;
  nombre: string;
  apellido: string;
  fecha_nacimiento: string;
  familia: FamiliaEncontrada;
  inscripcion: {
    grupo_id: number;
    grupo_nombre: string;
    turno: Turno;
    temporada_id: number;
  };
}

/**
 * Los grupos donde el usuario puede inscribir. Con la fecha de nacimiento,
 * la API marca los que corresponden como sugeridos.
 */
export function listarGrupos(fechaNacimiento?: string): Promise<GrupoParaInscribir[]> {
  const consulta = fechaNacimiento
    ? `?${new URLSearchParams({ fecha_nacimiento: fechaNacimiento })}`
    : "";
  return api.get<GrupoParaInscribir[]>(`/grupos${consulta}`);
}

/** Familias cuyo apellido empieza por `apellido`. La API exige 2 caracteres o mas. */
export function buscarFamilias(apellido: string): Promise<FamiliaEncontrada[]> {
  return api.get<FamiliaEncontrada[]>(`/familias?${new URLSearchParams({ apellido })}`);
}

/** La persona con ese DNI exacto. Si no hay ninguna, la API responde 404. */
export function buscarPersonaPorDni(dni: string): Promise<PersonaEncontrada> {
  return api.get<PersonaEncontrada>(`/personas?${new URLSearchParams({ dni })}`);
}

/** Da de alta un alumno con su familia, sus personas y su inscripcion. */
export function registrarAlumno(entrada: AltaAlumnoEntrada): Promise<AlumnoRegistrado> {
  return api.post<AlumnoRegistrado>("/alumnos", entrada);
}

// --- Asistencia -----------------------------------------------------------------
// Los tipos copian los esquemas del contrato (docs/api/openapi.json).

/** `AlumnoEnAsistencia`: un inscripto del grupo; `presente` es null si no se tomo. */
export interface AlumnoEnAsistencia {
  inscripcion_id: number;
  nombre: string;
  apellido: string;
  presente: boolean | null;
}

/** `AsistenciaDelGrupo`: la lista entera del grupo en una fecha. */
export interface AsistenciaDelGrupo {
  grupo_id: number;
  grupo: string;
  turno: Turno;
  fecha: string;
  alumnos: AlumnoEnAsistencia[];
}

/** Un elemento de `asistencias` en el cuerpo del guardado: lo marcado de una inscripcion. */
export interface AsistenciaMarcada {
  inscripcion_id: number;
  presente: boolean;
}

/** La asistencia del grupo en `fecha` (`AAAA-MM-DD`), con lo ya tomado. */
export function abrirAsistencia(grupoId: number, fecha: string): Promise<AsistenciaDelGrupo> {
  return api.get<AsistenciaDelGrupo>(`/grupos/${grupoId}/asistencias/${fecha}`);
}

/** Guarda o corrige las marcas enviadas; la API devuelve la lista entera del grupo. */
export function guardarAsistencia(
  grupoId: number,
  fecha: string,
  asistencias: AsistenciaMarcada[],
): Promise<AsistenciaDelGrupo> {
  return api.put<AsistenciaDelGrupo>(`/grupos/${grupoId}/asistencias/${fecha}`, { asistencias });
}
