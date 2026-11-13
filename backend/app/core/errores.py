"""Rechazos de reglas del negocio atribuibles a un campo del pedido.

Se responden con la misma forma que el 422 de validacion (ver el manejador
en app/main.py), asi src/lib/api.ts los reparte por campo sin distinguirlos.
Las reglas sin campo (el permiso del Profesor) siguen siendo HTTPException.
"""

# Ruta del campo dentro del cuerpo, sin el "body" inicial: ("personas", 0, "dni").
Ubicacion = tuple[str | int, ...]


class ReglaIncumplida(Exception):
    """Una o mas reglas incumplidas, cada una con su campo y su mensaje."""

    def __init__(self, errores: list[tuple[Ubicacion, str]]) -> None:
        super().__init__(errores)
        self.errores = errores
