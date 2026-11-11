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
      const msg = String((item as { msg?: unknown }).msg ?? "Valor invalido");
      if (campo) porCampo[campo] = msg;
    }
    const primero = Object.values(porCampo)[0] ?? "Revisa los datos ingresados.";
    return new ErrorDeApi(estado, primero, porCampo);
  }

  if (estado === 401) return new ErrorDeApi(estado, "Tu sesion vencio. Volve a ingresar.");
  if (estado === 403) return new ErrorDeApi(estado, "No tenes permiso para hacer esto.");
  if (estado >= 500)
    return new ErrorDeApi(estado, "El servidor tuvo un problema. Intenta de nuevo.");
  return new ErrorDeApi(estado, "No se pudo completar la operacion.");
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
    throw new ErrorDeApi(0, "No se pudo conectar con el servidor. Revisa tu conexion.");
  }

  if (respuesta.status === 401) {
    borrarToken();
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
