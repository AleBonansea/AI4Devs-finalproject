import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

export default function App() {
  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Stack spacing={2}>
        <Typography variant="h4" component="h1">
          Escuelita de Verano
        </Typography>
        <Typography color="text.secondary">
          Andamiaje listo. Las pantallas se construyen con la skill frontend-feature, una por
          historia.
        </Typography>
      </Stack>
    </Container>
  );
}
