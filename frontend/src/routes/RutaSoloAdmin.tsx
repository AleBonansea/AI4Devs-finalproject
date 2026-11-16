/**
 * La puerta de las pantallas que solo usa el Admin.
 *
 * Va dentro de RutaProtegida, que ya garantiza el usuario. Si el rol no es
 * Admin se redirige antes de montar la pagina, asi no se dispara ningun
 * pedido a la API.
 */
import { Navigate, Outlet } from "react-router-dom";

import { useSesion } from "../lib/sesion";

export default function RutaSoloAdmin() {
  const { usuario } = useSesion();

  if (usuario?.rol !== "admin") return <Navigate to="/" replace />;

  return <Outlet />;
}
