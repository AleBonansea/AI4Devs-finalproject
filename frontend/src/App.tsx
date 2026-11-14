import { Navigate, Route, Routes } from "react-router-dom";

import { ProveedorSesion } from "./lib/sesion";
import Ingreso from "./pages/Ingreso";
import Inicio from "./pages/Inicio";
import RegistrarAlumno from "./pages/RegistrarAlumno";
import TomarAsistencia from "./pages/TomarAsistencia";
import RutaProtegida from "./routes/RutaProtegida";

/**
 * Las rutas de la aplicacion. No crea el router: main.tsx la monta en un
 * BrowserRouter y los tests en un MemoryRouter con la direccion del caso.
 */
export default function App() {
  return (
    <ProveedorSesion>
      <Routes>
        <Route path="/ingresar" element={<Ingreso />} />
        <Route element={<RutaProtegida />}>
          <Route path="/" element={<Inicio />} />
          <Route path="/alumnos/nuevo" element={<RegistrarAlumno />} />
          <Route path="/asistencia" element={<TomarAsistencia />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </ProveedorSesion>
  );
}
