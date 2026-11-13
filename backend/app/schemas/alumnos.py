"""Esquemas de entrada y salida del alta de un alumno.

La entrada dice QUE se registra; ningun campo de monto. Aca solo se valida
la forma de cada campo: las reglas que cruzan campos o miran la base
(familia xor categoria, tutores, DNI repetido) viven en
app/services/alumnos.py, porque un `model_validator` las pegaria a la raiz
del cuerpo en lugar de al campo.
"""

from datetime import date
from typing import Annotated, Any, get_args

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Discriminator,
    StringConstraints,
    Tag,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError
from pydantic_core.core_schema import ErrorType

from app.models.enums import CategoriaFamilia, Turno
from app.services.personas import normalizar_dni

# Se recorta antes de medir: "  Juan  " mide 4. 80 es el ancho de las columnas.
Texto80 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Telefono = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]


def _dni_o_nada(valor: object) -> object:
    # Corre antes del largo: el tope de 15 (ancho de persona.dni) se mide ya
    # normalizado. Vacio despues de normalizar es "sin DNI". Lo que no es
    # texto pasa sin tocar y lo rechaza la validacion de tipo.
    if isinstance(valor, str):
        return normalizar_dni(valor) or None
    return valor


Dni = Annotated[
    Annotated[str, StringConstraints(max_length=15)] | None, BeforeValidator(_dni_o_nada)
]


def _no_posterior_a_hoy(valor: date) -> date:
    # PydanticCustomError con type `regla_de_negocio`: el mensaje pasa intacto
    # por el manejador del 422.
    if valor > date.today():
        raise PydanticCustomError(
            "regla_de_negocio", "La fecha de nacimiento no puede ser posterior a hoy."
        )
    return valor


class PersonaReutilizada(BaseModel):
    """Una persona ya cargada, elegida por su id (de la busqueda por DNI)."""

    model_config = ConfigDict(extra="forbid")

    persona_id: int
    es_tutor: bool


class PersonaNueva(BaseModel):
    """Una persona que se carga en el alta."""

    model_config = ConfigDict(extra="forbid")

    nombre: Texto80
    apellido: Texto80
    telefono: Telefono
    dni: Dni = None
    es_tutor: bool


def _tipo_de_persona(valor: Any) -> str:
    # Con `persona_id` es una reutilizada; si no, una nueva.
    if isinstance(valor, dict):
        return "reutilizada" if "persona_id" in valor else "nueva"
    return "reutilizada" if isinstance(valor, PersonaReutilizada) else "nueva"


_TIPOS_DE_PYDANTIC = frozenset(get_args(ErrorType))


def _sin_etiqueta(valor: Any, siguiente: ValidatorFunctionWrapHandler) -> Any:
    """Quita la etiqueta de la union del `loc` de cada error.

    La union discriminada agrega su etiqueta al camino ("personas", 0,
    "nueva", "telefono"); la pantalla espera el campo tal como lo mando,
    `personas.0.telefono`.
    """
    try:
        return siguiente(valor)
    except ValidationError as exc:
        detalles = [
            InitErrorDetails(
                type=(
                    e["type"]
                    if e["type"] in _TIPOS_DE_PYDANTIC
                    else PydanticCustomError(e["type"], e["msg"])
                ),
                loc=tuple(e["loc"][1:]),
                input=e["input"],
                ctx=e.get("ctx", {}),
            )
            for e in exc.errors()
        ]
        raise ValidationError.from_exception_data(exc.title, detalles) from None


PersonaDelAlta = Annotated[
    Annotated[PersonaReutilizada, Tag("reutilizada")] | Annotated[PersonaNueva, Tag("nueva")],
    Discriminator(_tipo_de_persona),
    WrapValidator(_sin_etiqueta),
]


class AltaAlumnoEntrada(BaseModel):
    """El alta: datos del alumno, grupo, familia (existente o nueva) y
    personas autorizadas a retirar."""

    model_config = ConfigDict(extra="forbid")

    nombre: Texto80
    apellido: Texto80
    fecha_nacimiento: Annotated[date, AfterValidator(_no_posterior_a_hoy)]
    grupo_id: int
    # Uno de los dos: familia existente o categoria de la familia nueva. La
    # regla la aplica el servicio, atada a su campo.
    familia_id: int | None = None
    categoria: CategoriaFamilia | None = None
    personas: list[PersonaDelAlta] = []


class FamiliaDelAlumno(BaseModel):
    id: int
    etiqueta: str
    categoria: CategoriaFamilia


class InscripcionDelAlumno(BaseModel):
    grupo_id: int
    grupo_nombre: str
    turno: Turno
    temporada_id: int


class AlumnoRegistrado(BaseModel):
    """El alumno recien dado de alta, con su familia y su inscripcion."""

    id: int
    nombre: str
    apellido: str
    fecha_nacimiento: date
    familia: FamiliaDelAlumno
    inscripcion: InscripcionDelAlumno
