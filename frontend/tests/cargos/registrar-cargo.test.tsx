/**
 * Tests de la pantalla «Registrar cargo» (`/cargos/nuevo`) con la sesion de
 * un Admin y la API fingida.
 *
 * Spec: openspec/changes/cobro/specs/cargos/spec.md, Requirements
 * «Pantalla «Registrar cargo»» (los Scenarios que no son del Coordinador; ese
 * esta en acceso.test.tsx), «El desglose en la pantalla» y «Registrar desde
 * la pantalla». Un `it` por Scenario.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { respuestaJson } from "../auth/montar";
import {
  DESCUENTO_EMPLEADO_2,
  FAMILIA_PEREZ_ANA,
  FAMILIA_SIN_HIJOS,
  JUAN_DELFINES_MANANA,
  ABONO,
  MENSAJE_REPETIDO,
  MES_1,
  MES_2,
  OPCION_MES_1,
  OPCION_MES_2,
  RENGLONES_ABONO,
  SIMULADO_ABONO_MES_1,
  TARIFA_MANANA_MES,
  TOTAL,
  abrirRegistrarCargo,
  botonRegistrar,
  campoFamilia,
  campoFechaSiHay,
  cargoRegistrado,
  elegirAbonoMes,
  elegirEn,
  elegirFamilia,
  elegirJuanManana,
  esperar,
  esperarRenglon,
  fingirApi,
  lista,
  listaSiHay,
  llamadasDe,
  opcionesDe,
  otrosQue,
  porTexto,
  registros,
  renglonDelDesglose,
  simulaciones,
  sinRespuesta,
  textoDeLaPagina,
  textoElegido,
  type CargoSimulado,
  type CuerpoCargo,
} from "./pantalla";

/** Espera el desglose del «Abono» del Mes de Juan, «Mes 1», con los valores de la spec. */
async function esperarDesgloseAbonoMes1() {
  await esperarRenglon(TOTAL, "$ 85.000", otrosQue(TOTAL, RENGLONES_ABONO));
}

describe("Pantalla «Registrar cargo»", () => {
  it("al elegir Pérez – Ana se ve Empleado y Alumno y turno ofrece Ana Pérez · Mañana, Juan Pérez · Mañana y Juan Pérez · Tarde", async () => {
    const api = fingirApi({
      familias: (apellido) => (apellido.startsWith("Pé") ? [FAMILIA_PEREZ_ANA] : []),
    });
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();

    await elegirFamilia(usuario, "Pér", "Pérez – Ana");

    expect(await screen.findByText(/\bEmpleado\b/)).toBeInTheDocument();
    const alumnoYTurno = await screen.findByRole("combobox", { name: /^Alumno y turno/ });
    expect(await opcionesDe(usuario, alumnoYTurno)).toEqual([
      "Ana Pérez · Mañana",
      "Juan Pérez · Mañana",
      "Juan Pérez · Tarde",
    ]);
    // Las inscripciones se pidieron para la familia elegida.
    const caminos = llamadasDe(api).map((llamada) => llamada.camino);
    const esperado = `/api/v1/familias/${FAMILIA_PEREZ_ANA.id}/inscripciones`;
    expect(caminos.some((camino) => camino.endsWith(esperado))).toBe(true);
  });

  it("una familia sin inscripciones muestra La familia no tiene hijos inscriptos en la temporada. y no muestra Alumno y turno", async () => {
    fingirApi({
      familias: () => [FAMILIA_SIN_HIJOS],
      inscripciones: () => [],
    });
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();

    await elegirFamilia(usuario, "Góm", FAMILIA_SIN_HIJOS.etiqueta);

    expect(
      await screen.findByText(porTexto("La familia no tiene hijos inscriptos en la temporada.")),
    ).toBeInTheDocument();
    expect(listaSiHay("Alumno y turno")).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/^Alumno y turno/)).not.toBeInTheDocument();
  });

  it("con Abono y Mes se ve Período solo con los del Mes y sin Fecha; con Día se ve Fecha y no Período; con Preinscripción no se ve ni Modalidad, ni Período, ni Fecha", async () => {
    fingirApi();
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();
    await elegirJuanManana(usuario);

    await elegirEn(usuario, "Tipo de cargo", "Abono");
    await elegirEn(usuario, "Modalidad", "Mes");

    const periodo = await screen.findByRole("combobox", { name: /^Período/ });
    expect(await opcionesDe(usuario, periodo)).toEqual([OPCION_MES_1, OPCION_MES_2]);
    expect(campoFechaSiHay()).not.toBeInTheDocument();

    await elegirEn(usuario, "Modalidad", "Día");

    expect(await screen.findByLabelText(/^Fecha\s*\*?$/)).toBeInTheDocument();
    expect(listaSiHay("Período")).not.toBeInTheDocument();

    await elegirEn(usuario, "Tipo de cargo", "Preinscripción");

    await waitFor(() => expect(textoElegido(lista("Tipo de cargo"))).toBe("Preinscripción"));
    await waitFor(() => {
      expect(listaSiHay("Modalidad")).not.toBeInTheDocument();
      expect(listaSiHay("Período")).not.toBeInTheDocument();
      expect(campoFechaSiHay()).not.toBeInTheDocument();
    });
    // Lo que si sigue a la vista.
    expect(textoElegido(lista("Alumno y turno"))).toBe("Juan Pérez · Mañana");
  });
});

describe("El desglose en la pantalla", () => {
  it("con la simulación del Abono del Mes se ve Tarifa base · Mañana · Mes con $ 100.000, Descuento Empleado · 2 hijos en el turno con 15 % y Total del cargo con $ 85.000, y Registrar cargo habilitado", async () => {
    const api = fingirApi({ simular: () => respuestaJson(200, SIMULADO_ABONO_MES_1) });
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();

    await elegirAbonoMes(usuario);

    await esperarRenglon(
      TARIFA_MANANA_MES,
      "$ 100.000",
      otrosQue(TARIFA_MANANA_MES, RENGLONES_ABONO),
    );
    renglonDelDesglose(
      DESCUENTO_EMPLEADO_2,
      "15 %",
      otrosQue(DESCUENTO_EMPLEADO_2, RENGLONES_ABONO),
    );
    renglonDelDesglose(TOTAL, "$ 85.000", otrosQue(TOTAL, RENGLONES_ABONO));
    await waitFor(() => expect(botonRegistrar()).toBeEnabled());
    // La simulacion se pidio con el cargo elegido.
    expect(simulaciones(api).at(-1)).toMatchObject({
      alumno_id: JUAN_DELFINES_MANANA.alumno_id,
      tipo_cargo_id: ABONO.id,
      inscripcion_id: JUAN_DELFINES_MANANA.inscripcion_id,
      modalidad: "mes",
      periodo_cobro_id: MES_1.id,
    });
  });

  it("con la simulación de la Preinscripción se ve Monto fijo con $ 20.000, Sin descuento y Total del cargo con $ 20.000", async () => {
    fingirApi();
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();

    await elegirJuanManana(usuario);
    await elegirEn(usuario, "Tipo de cargo", "Preinscripción");

    const renglones = ["Monto fijo", "Sin descuento", TOTAL];
    await esperarRenglon("Monto fijo", "$ 20.000", otrosQue("Monto fijo", renglones));
    expect(screen.getByText(porTexto("Sin descuento"))).toBeInTheDocument();
    renglonDelDesglose(TOTAL, "$ 20.000", otrosQue(TOTAL, renglones));
  });

  it("si la simulación responde 409 se ve el mensaje, no se ve Total del cargo y Registrar cargo está deshabilitado", async () => {
    fingirApi({ simular: () => respuestaJson(409, { detail: MENSAJE_REPETIDO }) });
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();

    await elegirAbonoMes(usuario);

    expect(await screen.findByText(porTexto(MENSAJE_REPETIDO))).toBeInTheDocument();
    expect(screen.queryByText(porTexto(TOTAL))).not.toBeInTheDocument();
    expect(botonRegistrar()).toBeDisabled();
  });

  it("si la respuesta del Mes 2 llega antes que la del Mes 1, el desglose que queda es el del Mes 2", async () => {
    // Totales que no se deducen de la base y el porcentaje: lo que se ve
    // tiene que ser lo que mando la API.
    const desgloseMes2: CargoSimulado = {
      ...SIMULADO_ABONO_MES_1,
      monto_base: "92000.00",
      porcentaje_aplicado: "15.00",
      monto_total: "71400.00",
    };
    let liberarMes1: ((r: Response) => void) | undefined;
    let liberarMes2: ((r: Response) => void) | undefined;
    const respuestaMes1 = new Promise<Response>((resolver) => {
      liberarMes1 = resolver;
    });
    const respuestaMes2 = new Promise<Response>((resolver) => {
      liberarMes2 = resolver;
    });
    const api = fingirApi({
      simular: (cuerpo: CuerpoCargo) => {
        if (cuerpo.periodo_cobro_id === MES_1.id) return respuestaMes1;
        if (cuerpo.periodo_cobro_id === MES_2.id) return respuestaMes2;
        return respuestaJson(404, { detail: "No encontrado." });
      },
    });
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();

    await elegirAbonoMes(usuario, OPCION_MES_1);
    await waitFor(() =>
      expect(simulaciones(api).some((c) => c.periodo_cobro_id === MES_1.id)).toBe(true),
    );

    await elegirEn(usuario, "Período", OPCION_MES_2);
    await waitFor(() =>
      expect(simulaciones(api).some((c) => c.periodo_cobro_id === MES_2.id)).toBe(true),
    );

    // Llega primero la del Mes 2.
    liberarMes2!(respuestaJson(200, desgloseMes2));
    await esperarRenglon(TOTAL, "$ 71.400", otrosQue(TOTAL, RENGLONES_ABONO));

    // Despues, la del Mes 1, que ya no vale.
    liberarMes1!(respuestaJson(200, SIMULADO_ABONO_MES_1));
    await esperar(100);

    renglonDelDesglose(TOTAL, "$ 71.400", otrosQue(TOTAL, RENGLONES_ABONO));
    renglonDelDesglose(TARIFA_MANANA_MES, "$ 92.000", otrosQue(TARIFA_MANANA_MES, RENGLONES_ABONO));
    expect(textoDeLaPagina()).not.toContain("$ 85.000");
    expect(textoDeLaPagina()).not.toContain("$ 100.000");
    expect(textoElegido(lista("Período"))).toBe(OPCION_MES_2);
  });
});

describe("Registrar desde la pantalla", () => {
  it("al registrar el Abono del Mes se envían solo alumno_id, tipo_cargo_id, inscripcion_id, modalidad y periodo_cobro_id, se ve Cargo registrado por $ 85.000. Saldo pendiente de la familia: $ 105.000. y quedan la familia elegida y Alumno y turno y Tipo de cargo vacíos", async () => {
    const api = fingirApi({
      registrar: (cuerpo) =>
        respuestaJson(201, {
          ...cargoRegistrado(cuerpo, SIMULADO_ABONO_MES_1, "105000.00"),
          monto_total: "85000.00",
        }),
    });
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();
    await elegirAbonoMes(usuario);
    await esperarDesgloseAbonoMes1();
    await waitFor(() => expect(botonRegistrar()).toBeEnabled());

    await usuario.click(botonRegistrar());

    expect(
      await screen.findByText(
        porTexto("Cargo registrado por $ 85.000. Saldo pendiente de la familia: $ 105.000."),
      ),
    ).toBeInTheDocument();

    const enviados = registros(api);
    expect(enviados).toHaveLength(1);
    const cuerpo = enviados[0] as CuerpoCargo;
    expect(Object.keys(cuerpo).sort()).toEqual([
      "alumno_id",
      "inscripcion_id",
      "modalidad",
      "periodo_cobro_id",
      "tipo_cargo_id",
    ]);
    expect(cuerpo).toEqual({
      alumno_id: JUAN_DELFINES_MANANA.alumno_id,
      tipo_cargo_id: ABONO.id,
      inscripcion_id: JUAN_DELFINES_MANANA.inscripcion_id,
      modalidad: "mes",
      periodo_cobro_id: MES_1.id,
    });

    expect(campoFamilia()).toHaveValue(FAMILIA_PEREZ_ANA.etiqueta);
    await waitFor(() => {
      expect(textoElegido(lista("Alumno y turno"))).toBe("");
      expect(textoElegido(lista("Tipo de cargo"))).toBe("");
    });
  });

  it("si el registro responde un total distinto del simulado, se ve Cargo registrado por $ 80.000. Saldo pendiente de la familia: $ 80.000.", async () => {
    // Entre la simulacion y el registro se inscribio un hermano: la API
    // registra otro total. Solo cambia lo que devuelve el registro; la
    // simulacion sigue siendo la de la spec ($ 85.000).
    fingirApi({
      registrar: (cuerpo) =>
        respuestaJson(201, {
          ...cargoRegistrado(cuerpo, SIMULADO_ABONO_MES_1, "80000.00"),
          monto_total: "80000.00",
        }),
    });
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();
    await elegirAbonoMes(usuario);
    await esperarDesgloseAbonoMes1();
    await waitFor(() => expect(botonRegistrar()).toBeEnabled());

    await usuario.click(botonRegistrar());

    expect(
      await screen.findByText(
        porTexto("Cargo registrado por $ 80.000. Saldo pendiente de la familia: $ 80.000."),
      ),
    ).toBeInTheDocument();
    expect(textoDeLaPagina()).not.toContain("Cargo registrado por $ 85.000");
  });

  it("con familia, alumno y Abono elegidos y sin modalidad, Registrar cargo está deshabilitado", async () => {
    fingirApi();
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();

    await elegirJuanManana(usuario);
    await elegirEn(usuario, "Tipo de cargo", "Abono");

    await waitFor(() => expect(textoElegido(lista("Tipo de cargo"))).toBe("Abono"));
    expect(textoElegido(lista("Modalidad"))).toBe("");
    expect(botonRegistrar()).toBeDisabled();
  });

  it("mientras el registro no responde, Registrar cargo está deshabilitado y un segundo clic no envía otro pedido", async () => {
    const api = fingirApi({ registrar: () => sinRespuesta() });
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();
    await elegirAbonoMes(usuario);
    await esperarDesgloseAbonoMes1();
    await waitFor(() => expect(botonRegistrar()).toBeEnabled());

    await usuario.click(botonRegistrar());

    await waitFor(() => expect(registros(api)).toHaveLength(1));
    await waitFor(() => expect(botonRegistrar()).toBeDisabled());

    // Segundo clic sobre el boton deshabilitado (sin la comprobacion de
    // pointer-events, para que el clic llegue de verdad).
    const sinComprobar = userEvent.setup({ pointerEventsCheck: 0 });
    await sinComprobar.click(botonRegistrar());
    await esperar(100);

    expect(registros(api)).toHaveLength(1);
    expect(botonRegistrar()).toBeDisabled();
  });

  it("si el registro responde 409 se ve el mensaje y los campos conservan lo elegido", async () => {
    fingirApi({ registrar: () => respuestaJson(409, { detail: MENSAJE_REPETIDO }) });
    await abrirRegistrarCargo();
    const usuario = userEvent.setup();
    await elegirAbonoMes(usuario);
    await esperarDesgloseAbonoMes1();
    await waitFor(() => expect(botonRegistrar()).toBeEnabled());

    await usuario.click(botonRegistrar());

    expect(await screen.findByText(porTexto(MENSAJE_REPETIDO))).toBeInTheDocument();
    expect(campoFamilia()).toHaveValue(FAMILIA_PEREZ_ANA.etiqueta);
    expect(textoElegido(lista("Alumno y turno"))).toBe("Juan Pérez · Mañana");
    expect(textoElegido(lista("Tipo de cargo"))).toBe("Abono");
    expect(textoElegido(lista("Modalidad"))).toBe("Mes");
    expect(textoElegido(lista("Período"))).toBe(OPCION_MES_1);
  });
});
