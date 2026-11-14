import Box from "@mui/material/Box";

import { colores } from "../tema";

/**
 * El logo de la escuela dentro de su salvavidas.
 *
 * En el prototipo el aro no es parte de la imagen: es un conic-gradient de
 * ocho gajos que alterna el naranja del dinero con blanco. Se usa grande en
 * el encuadre de las pantallas sin sesion y chico en la barra superior.
 */
// El grande es mas que los 108 px del prototipo: a 140 el logo se lee mejor
// en el ingreso (decidido con el usuario, probado en el navegador).
const MEDIDAS = {
  grande: { lado: 140, aro: 9 },
  chico: { lado: 46, aro: 4 },
} as const;

// Lado de la imagen respecto del circulo blanco. El dibujo de `logo.png` no
// es un circulo inscripto en el cuadrado: las letras de «CENTRO MÉDICO»
// llegan hasta las esquinas, a unos 270 px del centro en una imagen de 512.
// Por eso la imagen NO se recorta en circulo (eso le comia las letras): va
// entera, centrada y al 94 % del circulo, que es lo maximo con el que el
// dibujo completo entra (512 / 540 = 0,95, menos un pelo de margen). Las
// esquinas del cuadrado que sobresalen son transparentes.
const LADO_DE_LA_IMAGEN = "94%";

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
      {/* El circulo blanco con su contorno, separado de la imagen para no recortarla. */}
      <Box
        sx={{
          width: "100%",
          height: "100%",
          borderRadius: "50%",
          bgcolor: colores.superficie,
          boxShadow: `0 0 0 1.5px ${colores.texto}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Box
          component="img"
          src="/logo.png"
          alt="Logo de la Escuela de Verano"
          sx={{
            display: "block",
            width: LADO_DE_LA_IMAGEN,
            height: LADO_DE_LA_IMAGEN,
            objectFit: "contain",
          }}
        />
      </Box>
    </Box>
  );
}
