/**
 * La pantalla «Registrar cargo» (`/cargos/nuevo`), solo para el Admin: se
 * elige la familia, el alumno y turno y que se cobra; la API calcula el
 * desglose y, al registrar, lo guarda.
 *
 * Manda QUE se cobra (alumno, tipo, modalidad, periodo o fecha); ningun
 * monto. Con el cargo completo pide la simulacion y la muestra tal como
 * llega. Cada pedido de simulacion lleva un numero: solo vale la respuesta del
 * ultimo, porque dos respuestas pueden llegar en otro orden. Cambiar un campo
 * borra el desglose y el error. Los errores de la API vuelven con la clave del
 * campo y se muestran junto a el; lo que no tiene campo va a un aviso general.
 */
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import BuscadorFamilia from "../components/BuscadorFamilia";
import DesgloseCargo from "../components/DesgloseCargo";
import {
  ErrorDeApi,
  inscripcionesDeFamilia,
  opcionesDeCargo,
  registrarCargo,
  simularCargo,
  type CargoEntrada,
  type CargoSimulado,
  type FamiliaEncontrada,
  type InscripcionDeFamilia,
  type Modalidad,
  type OpcionesDeCargo,
} from "../lib/api";
import { formatearFecha } from "../lib/fechas";
import { formatearMonto } from "../lib/montos";
import { NOMBRE_DE_LA_MODALIDAD, NOMBRE_DEL_TURNO } from "../lib/nombres";

const MENSAJE_INESPERADO = "No se pudo completar la operación.";
const SIN_HIJOS = "La familia no tiene hijos inscriptos en la temporada.";

const MODALIDADES = Object.keys(NOMBRE_DE_LA_MODALIDAD) as Modalidad[];

/** Los campos que se eligen, como los entrega cada lista: texto. */
interface Campos {
  inscripcionId: string;
  tipoId: string;
  modalidad: Modalidad | "";
  periodoId: string;
  fecha: string;
}

const CAMPOS_VACIOS: Campos = {
  inscripcionId: "",
  tipoId: "",
  modalidad: "",
  periodoId: "",
  fecha: "",
};

/** El campo de la pantalla donde se muestra cada clave de error de la API. */
const CAMPO_DE_LA_CLAVE: Record<string, keyof Campos> = {
  alumno_id: "inscripcionId",
  inscripcion_id: "inscripcionId",
  tipo_cargo_id: "tipoId",
  modalidad: "modalidad",
  periodo_cobro_id: "periodoId",
  fecha_dia: "fecha",
};

type Errores = Partial<Record<keyof Campos, string>>;

/** Una simulacion y el cargo exacto (la misma referencia) que la pidio. */
interface Simulacion {
  entrada: CargoEntrada;
  datos: CargoSimulado;
}

function textoDeLaInscripcion(inscripcion: InscripcionDeFamilia): string {
  return `${inscripcion.nombre} ${inscripcion.apellido} · ${NOMBRE_DEL_TURNO[inscripcion.turno]}`;
}

/** Una lista nativa: en el telefono abre el selector del sistema. */
function Lista(props: {
  etiqueta: string;
  valor: string;
  alElegir: (valor: string) => void;
  placeholder: string;
  error?: string;
  ayuda?: string;
  children: ReactNode;
}) {
  const { etiqueta, valor, alElegir, placeholder, error, ayuda, children } = props;
  return (
    <TextField
      select
      required
      label={etiqueta}
      value={valor}
      onChange={(evento) => alElegir(evento.target.value)}
      error={Boolean(error)}
      helperText={error ?? ayuda}
      slotProps={{ select: { native: true }, inputLabel: { shrink: true } }}
    >
      <option value="" disabled>
        {placeholder}
      </option>
      {children}
    </TextField>
  );
}

export default function RegistrarCargo() {
  const [opciones, setOpciones] = useState<OpcionesDeCargo | null>(null);
  const [errorOpciones, setErrorOpciones] = useState<string | null>(null);

  const [familia, setFamilia] = useState<FamiliaEncontrada | null>(null);
  // null mientras se piden las inscripciones de la familia elegida.
  const [inscripciones, setInscripciones] = useState<InscripcionDeFamilia[] | null>(null);
  const [errorInscripciones, setErrorInscripciones] = useState<string | null>(null);

  const [campos, setCampos] = useState<Campos>(CAMPOS_VACIOS);
  const [simulacion, setSimulacion] = useState<Simulacion | null>(null);
  const [errores, setErrores] = useState<Errores>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [exito, setExito] = useState<string | null>(null);
  const [registrando, setRegistrando] = useState(false);

  // El numero del ultimo pedido de simulacion, y si hay un registro en curso
  // (el estado llega un render tarde: un segundo clic seguido lo atravesaria).
  const ultimoPedido = useRef(0);
  const registroEnCurso = useRef(false);

  // Las opciones se piden una vez, al montar.
  useEffect(() => {
    let vigente = true;
    opcionesDeCargo()
      .then((leidas) => {
        if (vigente) setOpciones(leidas);
      })
      .catch((causa: unknown) => {
        if (!vigente) return;
        setErrorOpciones(
          causa instanceof ErrorDeApi ? causa.message : "No se pudieron cargar los tipos de cargo.",
        );
      });
    return () => {
      vigente = false;
    };
  }, []);

  // Las inscripciones se piden al elegir la familia; solo vale la de la ultima.
  const familiaId = familia?.id ?? null;
  useEffect(() => {
    setInscripciones(null);
    setErrorInscripciones(null);
    if (familiaId === null) return;
    let vigente = true;
    inscripcionesDeFamilia(familiaId)
      .then((leidas) => {
        if (vigente) setInscripciones(leidas);
      })
      .catch((causa: unknown) => {
        if (!vigente) return;
        setErrorInscripciones(
          causa instanceof ErrorDeApi ? causa.message : "No se pudieron cargar los hijos.",
        );
      });
    return () => {
      vigente = false;
    };
  }, [familiaId]);

  const inscripcion = inscripciones?.find((i) => String(i.inscripcion_id) === campos.inscripcionId);
  const tipo = opciones?.tipos_cargo.find((t) => String(t.id) === campos.tipoId);
  const esTarifario = tipo?.calculo === "tarifario";
  const modalidad = esTarifario && campos.modalidad !== "" ? campos.modalidad : null;
  const conPeriodo = modalidad !== null && modalidad !== "dia";

  // El cargo, solo con las claves que corresponden, o null si falta algo. Es
  // la misma referencia mientras no cambie ningun dato: la simulacion y el
  // registro hablan del mismo cargo.
  const entrada = useMemo((): CargoEntrada | null => {
    if (!inscripcion || !tipo) return null;
    if (tipo.calculo === "monto_fijo") {
      return { alumno_id: inscripcion.alumno_id, tipo_cargo_id: tipo.id };
    }
    if (campos.modalidad === "") return null;
    const base: CargoEntrada = {
      alumno_id: inscripcion.alumno_id,
      tipo_cargo_id: tipo.id,
      inscripcion_id: inscripcion.inscripcion_id,
      modalidad: campos.modalidad,
    };
    if (campos.modalidad === "dia") {
      return campos.fecha ? { ...base, fecha_dia: campos.fecha } : null;
    }
    return campos.periodoId ? { ...base, periodo_cobro_id: Number(campos.periodoId) } : null;
  }, [inscripcion, tipo, campos.modalidad, campos.periodoId, campos.fecha]);

  // Con el cargo completo, pide la simulacion. Cambiar el cargo borra el
  // desglose y el error anteriores; solo vale la respuesta del ultimo pedido.
  useEffect(() => {
    const pedido = ++ultimoPedido.current;
    setSimulacion(null);
    setErrorGeneral(null);
    setErrores({});
    if (!entrada) return;
    simularCargo(entrada)
      .then((datos) => {
        if (pedido === ultimoPedido.current) setSimulacion({ entrada, datos });
      })
      .catch((causa: unknown) => {
        if (pedido === ultimoPedido.current) mostrarErrorActual.current(causa);
      });
  }, [entrada]);

  // La respuesta llega despues del render que la pidio: el error se reparte
  // segun los campos a la vista de ese momento.
  const mostrarErrorActual = useRef(mostrarError);
  useEffect(() => {
    mostrarErrorActual.current = mostrarError;
  });

  /** El mensaje de la API en su campo, o en un aviso general si no tiene campo a la vista. */
  function mostrarError(causa: unknown) {
    if (!(causa instanceof ErrorDeApi)) {
      setErrorGeneral(MENSAJE_INESPERADO);
      return;
    }
    const aVista: Record<keyof Campos, boolean> = {
      inscripcionId: true,
      tipoId: true,
      modalidad: esTarifario,
      periodoId: conPeriodo,
      fecha: modalidad === "dia",
    };
    const conCampo: Errores = {};
    const sinCampo: string[] = [];
    for (const [clave, mensaje] of Object.entries(causa.porCampo)) {
      const campo = CAMPO_DE_LA_CLAVE[clave];
      if (campo && aVista[campo]) conCampo[campo] = mensaje;
      else sinCampo.push(mensaje);
    }
    setErrores(conCampo);
    if (Object.keys(causa.porCampo).length === 0) setErrorGeneral(causa.message);
    else if (sinCampo.length > 0) setErrorGeneral(sinCampo.join(" "));
  }

  function elegirFamilia(elegida: FamiliaEncontrada | null) {
    setFamilia(elegida);
    setCampos(CAMPOS_VACIOS);
    setExito(null);
  }

  function cambiar(cambios: Partial<Campos>) {
    setCampos((anteriores) => ({ ...anteriores, ...cambios }));
    setExito(null);
  }

  function elegirTipo(tipoId: string) {
    // Un tipo de monto fijo no lleva modalidad, periodo ni fecha: no se
    // arrastran los de un Abono anterior.
    cambiar({ tipoId, modalidad: "", periodoId: "", fecha: "" });
  }

  function elegirModalidad(nueva: string) {
    cambiar({ modalidad: nueva as Modalidad, periodoId: "", fecha: "" });
  }

  // El desglose vale solo si es del cargo que se ve ahora.
  const desglose = simulacion !== null && simulacion.entrada === entrada ? simulacion : null;

  async function alEnviar(evento: FormEvent) {
    evento.preventDefault();
    if (!desglose || registroEnCurso.current) return;
    registroEnCurso.current = true;
    setRegistrando(true);
    setExito(null);
    setErrorGeneral(null);
    setErrores({});
    try {
      const registrado = await registrarCargo(desglose.entrada);
      setCampos(CAMPOS_VACIOS);
      setExito(
        `Cargo registrado. Saldo pendiente de la familia: ${formatearMonto(registrado.saldo_pendiente)}.`,
      );
    } catch (causa) {
      mostrarError(causa);
    } finally {
      registroEnCurso.current = false;
      setRegistrando(false);
    }
  }

  const periodos = opciones?.periodos.filter((p) => p.modalidad === campos.modalidad) ?? [];
  const sinHijos = familia !== null && inscripciones !== null && inscripciones.length === 0;

  return (
    <Container maxWidth="md" sx={{ py: { xs: 3, sm: 6 } }}>
      <Paper variant="outlined" sx={{ p: { xs: 2, sm: 4 } }}>
        <Stack component="form" noValidate onSubmit={alEnviar} spacing={4}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
            <Typography variant="h4" component="h1">
              Registrar cargo
            </Typography>
            <Button component={Link} to="/" variant="text">
              Volver al inicio
            </Button>
          </Stack>

          <Stack spacing={2}>
            {errorOpciones ? <Alert severity="error">{errorOpciones}</Alert> : null}

            <BuscadorFamilia familia={familia} onElegir={elegirFamilia} etiqueta="Familia" />

            {familia && inscripciones === null && !errorInscripciones ? (
              <Typography color="text.secondary">Cargando los hijos de la familia…</Typography>
            ) : null}
            {errorInscripciones ? <Alert severity="error">{errorInscripciones}</Alert> : null}
            {sinHijos ? <Alert severity="info">{SIN_HIJOS}</Alert> : null}

            {inscripciones !== null && inscripciones.length > 0 ? (
              <>
                <Lista
                  etiqueta="Alumno y turno"
                  placeholder="Elegí un alumno y turno"
                  valor={campos.inscripcionId}
                  alElegir={(inscripcionId) => cambiar({ inscripcionId })}
                  error={errores.inscripcionId}
                >
                  {inscripciones.map((i) => (
                    <option key={i.inscripcion_id} value={i.inscripcion_id}>
                      {textoDeLaInscripcion(i)}
                    </option>
                  ))}
                </Lista>

                <Lista
                  etiqueta="Tipo de cargo"
                  placeholder="Elegí un tipo de cargo"
                  valor={campos.tipoId}
                  alElegir={elegirTipo}
                  error={errores.tipoId}
                  ayuda={
                    opciones === null && !errorOpciones ? "Cargando tipos de cargo…" : undefined
                  }
                >
                  {opciones?.tipos_cargo.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nombre}
                    </option>
                  ))}
                </Lista>

                {esTarifario ? (
                  <Lista
                    etiqueta="Modalidad"
                    placeholder="Elegí una modalidad"
                    valor={campos.modalidad}
                    alElegir={elegirModalidad}
                    error={errores.modalidad}
                  >
                    {MODALIDADES.map((m) => (
                      <option key={m} value={m}>
                        {NOMBRE_DE_LA_MODALIDAD[m]}
                      </option>
                    ))}
                  </Lista>
                ) : null}

                {conPeriodo ? (
                  <Lista
                    etiqueta="Período"
                    placeholder="Elegí un período"
                    valor={campos.periodoId}
                    alElegir={(periodoId) => cambiar({ periodoId })}
                    error={errores.periodoId}
                    ayuda={
                      periodos.length === 0
                        ? "No hay períodos cargados para esta modalidad."
                        : undefined
                    }
                  >
                    {periodos.map((p) => (
                      <option key={p.id} value={p.id}>
                        {`${p.nombre} · ${formatearFecha(p.fecha_desde)} al ${formatearFecha(p.fecha_hasta)}`}
                      </option>
                    ))}
                  </Lista>
                ) : null}

                {modalidad === "dia" ? (
                  <TextField
                    label="Fecha"
                    type="date"
                    required
                    value={campos.fecha}
                    onChange={(evento) => cambiar({ fecha: evento.target.value })}
                    error={Boolean(errores.fecha)}
                    helperText={errores.fecha}
                    // El campo de fecha siempre muestra su mascara: la etiqueta va arriba.
                    slotProps={{ inputLabel: { shrink: true } }}
                  />
                ) : null}

                {desglose && inscripcion ? (
                  <DesgloseCargo
                    desglose={desglose.datos}
                    turno={inscripcion.turno}
                    modalidad={modalidad}
                  />
                ) : null}

                {errorGeneral ? <Alert severity="error">{errorGeneral}</Alert> : null}
              </>
            ) : null}

            {exito ? <Alert severity="success">{exito}</Alert> : null}

            {inscripciones !== null && inscripciones.length > 0 ? (
              <Stack alignItems="flex-start">
                <Button type="submit" disabled={!desglose || registrando}>
                  Registrar cargo
                </Button>
              </Stack>
            ) : null}
          </Stack>
        </Stack>
      </Paper>
    </Container>
  );
}
