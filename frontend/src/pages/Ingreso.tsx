import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import EncuadreSinSesion from "../components/EncuadreSinSesion";
import { ErrorDeApi, ingresar as pedirIngreso } from "../lib/api";
import { useSesion } from "../lib/sesion";

interface ErroresPorCampo {
  username?: string;
  password?: string;
}

/**
 * Pantalla de ingreso. Valida los vacios antes de llamar a la API, frena el
 * doble envio y muestra el error por campo al lado del campo o el error
 * general arriba del formulario.
 */
export default function Ingreso() {
  const { ingresar } = useSesion();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errores, setErrores] = useState<ErroresPorCampo>({});
  const [aviso, setAviso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  // El estado de React se ve en el proximo render: dos clics en el mismo tick
  // pasarian los dos con solo el `disabled`. La ref corta el segundo.
  const enCurso = useRef(false);

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (enCurso.current) return;

    setAviso(null);
    const faltan: ErroresPorCampo = {};
    if (username.trim() === "") faltan.username = "Ingresá tu usuario.";
    // La contrasena no se recorta: la API tampoco la normaliza.
    if (password === "") faltan.password = "Ingresá tu contraseña.";
    setErrores(faltan);
    if (faltan.username || faltan.password) return;

    enCurso.current = true;
    setEnviando(true);
    try {
      const respuesta = await pedirIngreso(username, password);
      ingresar(respuesta);
      navigate("/", { replace: true });
    } catch (error) {
      const porCampo = error instanceof ErrorDeApi ? error.porCampo : {};
      if (porCampo.username || porCampo.password) {
        setErrores({ username: porCampo.username, password: porCampo.password });
      } else {
        setAviso(
          error instanceof ErrorDeApi ? error.message : "No se pudo completar la operación.",
        );
        setPassword("");
      }
    } finally {
      enCurso.current = false;
      setEnviando(false);
    }
  }

  return (
    <EncuadreSinSesion>
      <Stack component="form" spacing={2} noValidate onSubmit={enviar}>
        {aviso && <Alert severity="error">{aviso}</Alert>}
        <TextField
          id="ingreso-usuario"
          label="Usuario"
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          error={Boolean(errores.username)}
          helperText={errores.username}
        />
        <TextField
          id="ingreso-contrasena"
          label="Contraseña"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={Boolean(errores.password)}
          helperText={errores.password}
        />
        <Button
          type="submit"
          variant="contained"
          disabled={enviando}
          startIcon={enviando ? <CircularProgress size={16} color="inherit" /> : undefined}
        >
          Ingresar
        </Button>
      </Stack>
    </EncuadreSinSesion>
  );
}
