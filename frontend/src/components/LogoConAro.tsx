import Box from "@mui/material/Box";

import { colores } from "../tema";

/**
 * El logo de la escuela dentro de su salvavidas.
 *
 * En el prototipo el aro no es parte de la imagen: es un conic-gradient de
 * ocho gajos que alterna el naranja del dinero con blanco. Se usa grande en
 * el encuadre de las pantallas sin sesion y chico en la barra superior.
 */
const MEDIDAS = {
  grande: { lado: 108, aro: 9 },
  chico: { lado: 46, aro: 4 },
} as const;

// Ocho gajos de 45 grados, empezando por el naranja.
const GAJOS = Array.from({ length: 8 }, (_, i) => {
  const color = i % 2 === 0 ? colores.dinero : colores.superficie;
  return `${color} ${i * 45}deg ${(i + 1) * 45}deg`;
}).join(", ");

interface Props {
  tamano?: keyof typeof MEDIDAS;
}

export default function LogoConAro({ tamano = "grande" }: Props) {
  const { lado, aro } = MEDIDAS[tamano];
  return (
    <Box
      sx={{
        width: lado,
        height: lado,
        p: `${aro}px`,
        borderRadius: "50%",
        background: `conic-gradient(${GAJOS})`,
        boxShadow: `inset 0 0 0 1.5px ${colores.texto}`,
        flexShrink: 0,
      }}
    >
      <Box
        component="img"
        src="/logo.png"
        alt="Logo de la Escuela de Verano"
        sx={{
          display: "block",
          width: "100%",
          height: "100%",
          borderRadius: "50%",
          objectFit: "cover",
          bgcolor: colores.superficie,
          boxShadow: `0 0 0 1.5px ${colores.texto}`,
        }}
      />
    </Box>
  );
}
