/**
 * La sesion del navegador, resuelta en un solo lugar.
 *
 * Guarda si hay token y quien es el usuario actual. Las pantallas la leen
 * con `useSesion()` y no vuelven a mirar el token por su cuenta. No es una
 * pieza de interfaz: es estado compartido, igual que el token en api.ts.
 */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import {
  borrarToken,
  guardarToken,
  leerToken,
  type LoginRespuesta,
  type UsuarioActual,
} from "./api";

interface Sesion {
  /** Si hay un token guardado. No dice si sigue vigente: eso lo dice `/yo`. */
  hayToken: boolean;
  /** El usuario actual, o null si todavia no se sabe o no hay sesion. */
  usuario: UsuarioActual | null;
  /** Guarda el token del login y fija su usuario, sin volver a pedirlo. */
  ingresar: (respuesta: LoginRespuesta) => void;
  /** Fija el usuario leido de `GET /auth/yo` para el token ya guardado. */
  fijarUsuario: (usuario: UsuarioActual) => void;
  /** Borra el token y el usuario. No llama a la API: no hay logout. */
  salir: () => void;
}

const ContextoSesion = createContext<Sesion | null>(null);

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [hayToken, setHayToken] = useState(() => leerToken() !== null);
  const [usuario, setUsuario] = useState<UsuarioActual | null>(null);

  const ingresar = useCallback((respuesta: LoginRespuesta) => {
    guardarToken(respuesta.access_token);
    setHayToken(true);
    setUsuario(respuesta.usuario);
  }, []);

  const fijarUsuario = useCallback((nuevo: UsuarioActual) => {
    setUsuario(nuevo);
  }, []);

  const salir = useCallback(() => {
    borrarToken();
    setHayToken(false);
    setUsuario(null);
  }, []);

  const valor = useMemo(
    () => ({ hayToken, usuario, ingresar, fijarUsuario, salir }),
    [hayToken, usuario, ingresar, fijarUsuario, salir],
  );

  return <ContextoSesion.Provider value={valor}>{children}</ContextoSesion.Provider>;
}

export function useSesion(): Sesion {
  const sesion = useContext(ContextoSesion);
  if (!sesion) throw new Error("useSesion se usa dentro de ProveedorSesion");
  return sesion;
}
