/**
 * Tests de la pantalla «Registrar alumno» (`/alumnos/nuevo`): el formulario,
 * los grupos y su sugerencia, la familia nueva o existente, las personas
 * autorizadas a retirar, la validacion antes de enviar y el envio del alta.
 *
 * Spec: openspec/changes/familias-y-alumnos/specs/alumnos/spec.md
 * Un `describe` por Requirement y un `it` por Scenario.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { respuestaJson, sinRespuesta } from "../auth/montar";
import {
  DELFINES_MANANA,
  DELFINES_TARDE,
  FAMILIA_PEREZ_JUAN,
  OBLIGATORIO,
  PERSONA_MARIA,
  SIN_TUTOR,
  TIBURONES_MANANA,
  abrirRegistrar,
  alertasCon,
  altasEnviadas,
  alumnoRegistradoJuan,
  buscadorFamilia,
  botonRegistrar,
  campoAlumno,
  campoCategoria,
  campoCategoriaSiHay,
  campoDniABuscar,
  campoGrupo,
  cargarPersonaNueva,
  casillasTutor,
  completarAltaJuan,
  completarAlumnoJuan,
  contiene,
  elegir,
  elegirFamiliaExistente,
  escribirFecha,
  esperar,
  fingirApi,
  llamadasA,
  opcionesDe,
  porTexto,
  profesor,
  sugeridos,
  textoElegido,
} from "./pantalla";

const TODOS = [DELFINES_MANANA, DELFINES_TARDE, TIBURONES_MANANA];
const EXITO = "Juan Pérez quedó inscripto en Delfines (Mañana). Familia: Pérez – Juan.";
const DNI_YA_CARGADO = "Ya hay una persona con ese DNI. Buscala por DNI para reutilizarla.";
const DNI_NO_CARGADO = "No hay ninguna persona con ese DNI.";
const GRUPO_AJENO = "Solo podés inscribir alumnos en tus grupos.";

/** Las claves que el contrato admite en el cuerpo del alta. */
const CLAVES_ALTA = [
  "nombre",
  "apellido",
  "fecha_nacimiento",
  "grupo_id",
  "familia_id",
  "categoria",
  "personas",
];
const CLAVES_PERSONA_NUEVA = ["nombre", "apellido", "telefono", "dni", "es_tutor"];

describe("Pantalla «Registrar alumno»", () => {
  it("con el formulario vacío se ven Nombre, Apellido, Fecha de nacimiento, Grupo, Familia nueva elegida, Categoría y Registrar", async () => {
    fingirApi();

    await abrirRegistrar();

    expect(campoAlumno("Nombre")).toBeInTheDocument();
    expect(campoAlumno("Apellido")).toBeInTheDocument();
    expect(campoAlumno("Fecha de nacimiento")).toBeInTheDocument();
    expect(campoGrupo()).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Familia nueva" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Familia existente" })).not.toBeChecked();
    expect(campoCategoria()).toBeInTheDocument();
    expect(botonRegistrar()).toBeInTheDocument();
  });
});

describe("Grupos en la pantalla", () => {
  it("un Profesor ve como única opción de Grupo Delfines · Mañana", async () => {
    fingirApi({ usuario: profesor(), grupos: () => [DELFINES_MANANA] });
    const usuario = userEvent.setup();

    await abrirRegistrar();

    await waitFor(async () => {
      expect(await opcionesDe(usuario, campoGrupo())).toEqual(["Delfines · Mañana"]);
    });
  });

  it("al escribir la fecha sin haber elegido grupo, Grupo queda en Delfines · Mañana (sugerido)", async () => {
    const api = fingirApi({
      grupos: (fecha) => (fecha === "2020-03-10" ? sugeridos(TODOS, [DELFINES_MANANA.id]) : TODOS),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await escribirFecha(usuario, "2020-03-10");

    await waitFor(() =>
      expect(
        llamadasA(api, "GET", "/api/v1/grupos").some(
          (llamada) =>
            new URL(llamada.url, "http://localhost").searchParams.get("fecha_nacimiento") ===
            "2020-03-10",
        ),
      ).toBe(true),
    );
    await waitFor(() => expect(textoElegido(campoGrupo())).toBe("Delfines · Mañana (sugerido)"));
  });

  it("con dos grupos sugeridos Grupo sigue sin elegir y al desplegarlo se ven los dos con (sugerido)", async () => {
    fingirApi({
      grupos: (fecha) =>
        fecha === "2020-03-10" ? sugeridos(TODOS, [DELFINES_MANANA.id, DELFINES_TARDE.id]) : TODOS,
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await escribirFecha(usuario, "2020-03-10");

    let opciones: string[] = [];
    await waitFor(async () => {
      opciones = await opcionesDe(usuario, campoGrupo());
      expect(opciones).toContain("Delfines · Mañana (sugerido)");
    });
    expect(opciones).toContain("Delfines · Tarde (sugerido)");
    expect(textoElegido(campoGrupo())).toBe("");
  });

  it("la sugerencia no pisa una elección: Grupo sigue en Tiburones · Mañana", async () => {
    fingirApi({
      grupos: (fecha) => (fecha === "2020-03-10" ? sugeridos(TODOS, [DELFINES_MANANA.id]) : TODOS),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await waitFor(async () => {
      expect(await opcionesDe(usuario, campoGrupo())).toContain("Tiburones · Mañana");
    });
    await elegir(usuario, campoGrupo(), "Tiburones · Mañana");
    await waitFor(() => expect(textoElegido(campoGrupo())).toBe("Tiburones · Mañana"));
    await escribirFecha(usuario, "2020-03-10");

    // La respuesta con la sugerencia ya llego a la pantalla...
    await waitFor(async () => {
      expect(await opcionesDe(usuario, campoGrupo())).toContain("Delfines · Mañana (sugerido)");
    });
    // ...y la eleccion se mantiene.
    expect(textoElegido(campoGrupo())).toBe("Tiburones · Mañana");
  });
});

describe("Familia en la pantalla", () => {
  it("al elegir una familia existente se ve Categoría: Empleado como texto, sin campo para cambiarla", async () => {
    fingirApi({
      familias: (apellido) => respuestaJson(200, apellido === "Pé" ? [FAMILIA_PEREZ_JUAN] : []),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await elegirFamiliaExistente(usuario, "Pé", "Pérez – Juan");

    expect(await screen.findByText(porTexto("Categoría: Empleado"))).toBeInTheDocument();
    expect(campoCategoriaSiHay()).toBeNull();
    expect(screen.queryByRole("radio", { name: "Socio" })).not.toBeInTheDocument();
    expect(screen.queryByRole("radio", { name: "No socio" })).not.toBeInTheDocument();
  });

  it("un carácter en el buscador no llama a GET /api/v1/familias", async () => {
    const api = fingirApi({
      familias: () => respuestaJson(200, [FAMILIA_PEREZ_JUAN]),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await usuario.click(screen.getByRole("radio", { name: "Familia existente" }));
    const buscador = await buscadorFamilia();
    await usuario.type(buscador, "P");
    // Mas que la espera de 300 ms entre teclas.
    await esperar(800);

    expect(buscador).toHaveValue("P");
    expect(llamadasA(api, "GET", "/api/v1/familias")).toHaveLength(0);
  });
});

describe("Personas en la pantalla", () => {
  it("al buscar por DNI una persona cargada se ve María Pérez en la lista con la casilla Tutor", async () => {
    const api = fingirApi({
      personas: (dni) =>
        dni === "30111222"
          ? respuestaJson(200, PERSONA_MARIA)
          : respuestaJson(404, { detail: DNI_NO_CARGADO }),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    expect(casillasTutor()).toHaveLength(0);
    await usuario.type(campoDniABuscar(), "30111222");
    await usuario.click(screen.getByRole("button", { name: "Buscar por DNI" }));

    expect(await screen.findByText(porTexto("María Pérez"))).toBeInTheDocument();
    await waitFor(() => expect(casillasTutor()).toHaveLength(1));
    expect(
      llamadasA(api, "GET", "/api/v1/personas").map((llamada) =>
        new URL(llamada.url, "http://localhost").searchParams.get("dni"),
      ),
    ).toEqual(["30111222"]);
  });

  it("con un DNI que no está cargado se ve No hay ninguna persona con ese DNI. y la lista de personas no cambia", async () => {
    fingirApi({
      personas: () => respuestaJson(404, { detail: DNI_NO_CARGADO }),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    const tutoresAntes = casillasTutor().length;
    await usuario.type(campoDniABuscar(), "30111222");
    await usuario.click(screen.getByRole("button", { name: "Buscar por DNI" }));

    expect(await screen.findByText(DNI_NO_CARGADO)).toBeInTheDocument();
    expect(casillasTutor()).toHaveLength(tutoresAntes);
    expect(screen.queryByText(porTexto("María Pérez"))).not.toBeInTheDocument();
  });
});

describe("Validación antes de enviar el alta", () => {
  it("al registrar con el formulario vacío Nombre, Apellido, Fecha de nacimiento, Grupo y Categoría muestran Este dato es obligatorio. y no se llama al alta", async () => {
    const api = fingirApi({ alta: () => sinRespuesta() });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await usuario.click(botonRegistrar());

    await waitFor(() => expect(screen.getAllByText(OBLIGATORIO).length).toBeGreaterThanOrEqual(5));
    expect(campoAlumno("Nombre")).toHaveAccessibleDescription(contiene(OBLIGATORIO));
    expect(campoAlumno("Apellido")).toHaveAccessibleDescription(contiene(OBLIGATORIO));
    expect(campoAlumno("Fecha de nacimiento")).toHaveAccessibleDescription(contiene(OBLIGATORIO));
    expect(campoGrupo()).toHaveAccessibleDescription(contiene(OBLIGATORIO));
    expect(campoCategoria()).toHaveAccessibleDescription(contiene(OBLIGATORIO));
    expect(llamadasA(api, "POST", "/api/v1/alumnos")).toHaveLength(0);
  });

  it("con familia nueva y ninguna persona marcada como tutor se ve La familia nueva necesita al menos un tutor. y no se llama al alta", async () => {
    const api = fingirApi({ alta: () => sinRespuesta() });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await completarAlumnoJuan(usuario);
    await elegir(usuario, campoCategoria(), "Empleado");
    await cargarPersonaNueva(usuario, {
      nombre: "Raúl",
      apellido: "Pérez",
      telefono: "3517654321",
      tutor: false,
    });
    await usuario.click(botonRegistrar());

    expect(await screen.findByText(SIN_TUTOR)).toBeInTheDocument();
    expect(llamadasA(api, "POST", "/api/v1/alumnos")).toHaveLength(0);
  });

  it("con familia existente y sin personas se llama al alta con el familia_id, sin categoria y con personas vacía", async () => {
    const api = fingirApi({
      familias: (apellido) => respuestaJson(200, apellido === "Pé" ? [FAMILIA_PEREZ_JUAN] : []),
      alta: () => sinRespuesta(),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await completarAlumnoJuan(usuario);
    await elegirFamiliaExistente(usuario, "Pé", "Pérez – Juan");
    await screen.findByText(porTexto("Categoría: Empleado"));
    await usuario.click(botonRegistrar());

    await waitFor(() => expect(altasEnviadas(api)).toHaveLength(1));
    expect(altasEnviadas(api)[0]).toEqual({
      nombre: "Juan",
      apellido: "Pérez",
      fecha_nacimiento: "2020-03-10",
      grupo_id: DELFINES_MANANA.id,
      familia_id: FAMILIA_PEREZ_JUAN.id,
      personas: [],
    });
  });
});

describe("Envío del alta desde la pantalla", () => {
  it("con el alta correcta se ve Juan Pérez quedó inscripto en Delfines (Mañana). Familia: Pérez – Juan. y Nombre y Apellido quedan vacíos", async () => {
    const api = fingirApi({ alta: () => respuestaJson(201, alumnoRegistradoJuan()) });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await completarAltaJuan(usuario);
    await usuario.click(botonRegistrar());

    expect(await screen.findByText(EXITO)).toBeInTheDocument();
    await waitFor(() => expect(campoAlumno("Nombre")).toHaveValue(""));
    expect(campoAlumno("Apellido")).toHaveValue("");

    // Se mando que se registra, con las claves del contrato y nada mas:
    // ningun monto ni la etiqueta de la familia.
    const altas = altasEnviadas(api);
    expect(altas).toHaveLength(1);
    const cuerpo = altas[0] as Record<string, unknown>;
    for (const clave of Object.keys(cuerpo)) expect(CLAVES_ALTA).toContain(clave);
    expect(cuerpo).toMatchObject({
      nombre: "Juan",
      apellido: "Pérez",
      fecha_nacimiento: "2020-03-10",
      grupo_id: DELFINES_MANANA.id,
      categoria: "empleado",
    });
    expect(cuerpo.familia_id ?? null).toBeNull();
    const personas = cuerpo.personas as Record<string, unknown>[];
    expect(personas).toHaveLength(1);
    for (const clave of Object.keys(personas[0] as object)) {
      expect(CLAVES_PERSONA_NUEVA).toContain(clave);
    }
    expect(personas[0]).toEqual({
      nombre: "María",
      apellido: "Pérez",
      telefono: "3511234567",
      dni: "30111222",
      es_tutor: true,
    });
  });

  it("mientras el alta espera respuesta el botón Registrar está deshabilitado", async () => {
    const api = fingirApi({ alta: () => sinRespuesta() });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await completarAltaJuan(usuario);
    await usuario.click(botonRegistrar());

    await waitFor(() => expect(altasEnviadas(api)).toHaveLength(1));
    await waitFor(() => expect(botonRegistrar()).toBeDisabled());
  });

  it("con un error en el DNI de una persona el mensaje se ve junto a su DNI y no en un aviso general, y Nombre conserva lo escrito", async () => {
    fingirApi({
      alta: () =>
        respuestaJson(422, {
          detail: [
            { loc: ["body", "personas", 0, "dni"], msg: DNI_YA_CARGADO, type: "regla_de_negocio" },
          ],
        }),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    const maria = await completarAltaJuan(usuario);
    await usuario.click(botonRegistrar());

    expect(await screen.findByText(DNI_YA_CARGADO)).toBeInTheDocument();
    expect(maria.dni).toHaveAccessibleDescription(contiene(DNI_YA_CARGADO));
    expect(maria.dni).toHaveAttribute("aria-invalid", "true");
    expect(maria.nombre).not.toHaveAccessibleDescription(contiene(DNI_YA_CARGADO));
    expect(alertasCon(DNI_YA_CARGADO)).toHaveLength(0);
    expect(campoAlumno("Nombre")).toHaveValue("Juan");
    expect(maria.dni).toHaveValue("30111222");
  });

  it("si el alta de un Profesor se rechaza por el grupo se ve el mensaje en un aviso general y el formulario conserva lo cargado", async () => {
    fingirApi({
      usuario: profesor(),
      alta: () => respuestaJson(403, { detail: GRUPO_AJENO }),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    const maria = await completarAltaJuan(usuario);
    await usuario.click(botonRegistrar());

    expect(await screen.findByText(GRUPO_AJENO)).toBeInTheDocument();
    await waitFor(() => expect(alertasCon(GRUPO_AJENO).length).toBeGreaterThan(0));
    expect(campoAlumno("Nombre")).toHaveValue("Juan");
    expect(campoAlumno("Apellido")).toHaveValue("Pérez");
    expect(campoAlumno("Fecha de nacimiento")).toHaveValue("2020-03-10");
    expect(textoElegido(campoGrupo())).toBe("Delfines · Mañana");
    expect(maria.nombre).toHaveValue("María");
    expect(maria.tutor).toBeChecked();
    await waitFor(() => expect(botonRegistrar()).toBeEnabled());
  });
});
