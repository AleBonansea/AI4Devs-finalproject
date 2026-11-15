/**
 * Tests del formulario de pago de la pantalla «Cuenta corriente» con la
 * sesion de un Admin y la API fingida.
 *
 * Spec: openspec/changes/cuenta-corriente/specs/pagos/spec.md, Requirements
 * «Registrar un pago desde la pantalla» (4 Scenarios) y «Enviar el pago desde
 * la pantalla» (6). Un `it` por Scenario, mas un control positivo marcado.
 */
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { contiene, sinRespuesta } from "../cargos/pantalla";
import {
  ABONO_MES_JUAN,
  FAMILIA_PEREZ_ANA,
  cuentaDe,
  cuentasPedidas,
  esperar,
  esperarRenglon,
  normalizar,
  respuestaJson,
  textoDeLaPagina,
  valorJunto,
  type CargoEnCuenta,
  type CuentaCorriente,
} from "./pantalla";
import {
  abrirFormularioDePago,
  botonCancelar,
  botonRegistrarPago,
  campoFechaDelPago,
  campoMonto,
  cargoConSaldo,
  escribirMonto,
  fingirApiDePago,
  hoyDelEntorno,
  pagoRegistrado,
  pagosEnviados,
  pedidosACargos,
  ponerFecha,
} from "./pago";

const ABONO_MES_1 = "Abono · Mes 1";

/** El «Abono · Mes 1» de Juan con un pago de 30000.00 y saldo 55000.00. */
const ABONO_SALDO_55000: CargoEnCuenta = cargoConSaldo(ABONO_MES_JUAN, {
  monto_total: "85000.00",
  pagado: "30000.00",
  saldo: "55000.00",
  pagos: [{ id: 701, monto: "30000.00", fecha_pago: "2026-11-01" }],
});

function cuentaCon(cargo: CargoEnCuenta, saldoPendiente: string): CuentaCorriente {
  return cuentaDe(FAMILIA_PEREZ_ANA, {
    total_cargos: cargo.monto_total,
    total_pagado: cargo.pagado,
    saldo_pendiente: saldoPendiente,
    cargos: [cargo],
  });
}

afterEach(() => {
  vi.useRealTimers();
});

describe("Registrar un pago desde la pantalla", () => {
  it("al pulsar Registrar pago en el Abono · Mes 1 se ven Abono · Mes 1, Saldo del cargo $ 55.000, Monto 55.000 y Fecha del pago con la fecha de hoy", async () => {
    fingirApiDePago({ cuenta: () => cuentaCon(ABONO_SALDO_55000, "70000.00") });
    const usuario = userEvent.setup();

    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    expect(normalizar(dialogo.textContent)).toContain(ABONO_MES_1);
    const saldo = valorJunto("Saldo del cargo", "$ 55.000", ["Saldo pendiente"]);
    expect(dialogo.contains(saldo)).toBe(true);
    expect(campoMonto(dialogo)).toHaveValue("55.000");
    expect(campoFechaDelPago(dialogo)).toHaveValue(hoyDelEntorno());
  });

  it("con saldo 4462.50 el Monto propuesto es 4.462,50", async () => {
    const cargo = cargoConSaldo(ABONO_MES_JUAN, {
      monto_total: "8925.00",
      pagado: "4462.50",
      saldo: "4462.50",
      pagos: [{ id: 701, monto: "4462.50", fecha_pago: "2026-11-01" }],
    });
    fingirApiDePago({ cuenta: () => cuentaCon(cargo, "4462.50") });
    const usuario = userEvent.setup();

    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    expect(campoMonto(dialogo)).toHaveValue("4.462,50");
  });

  it("con el reloj en el 2027-01-05 a las 21:30 de Argentina la Fecha del pago propuesta es 2027-01-05", async () => {
    // Solo se finge `Date`, para no dormir los temporizadores de userEvent
    // ni las promesas. Se deshace con `vi.useRealTimers()` en el afterEach.
    vi.useFakeTimers({ toFake: ["Date"] });
    const noche = new Date(2027, 0, 5, 21, 30, 0);
    vi.setSystemTime(noche);
    // Control del entorno: en UTC ya es el dia siguiente.
    expect(noche.toISOString()).toBe("2027-01-06T00:30:00.000Z");

    fingirApiDePago({ cuenta: () => cuentaCon(ABONO_SALDO_55000, "70000.00") });
    const usuario = userEvent.setup();

    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    expect(campoFechaDelPago(dialogo)).toHaveValue("2027-01-05");
  });

  it("al pulsar Cancelar el formulario se cierra y no se envía ningún pedido a /api/v1/cargos", async () => {
    const api = fingirApiDePago({
      cuenta: () => cuentaCon(ABONO_SALDO_55000, "70000.00"),
      pagar: () => respuestaJson(201, pagoRegistrado({})),
    });
    const usuario = userEvent.setup();
    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    await usuario.click(botonCancelar(dialogo));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    // Lo que si se ve: el renglon del cargo, con su Registrar pago.
    await esperarRenglon(ABONO_MES_1, ["Juan Pérez", "Registrar pago"], []);
    await esperar(100);
    expect(pedidosACargos(api)).toHaveLength(0);
  });
});

describe("Enviar el pago desde la pantalla", () => {
  it("con 30.000 y 2026-11-02 el cuerpo tiene exactamente monto 30000.00 y fecha_pago 2026-11-02, se ve el mensaje con $ 30.000 y $ 40.000, el formulario se cierra y se vuelve a pedir la cuenta corriente", async () => {
    const despues = cargoConSaldo(ABONO_MES_JUAN, {
      monto_total: "85000.00",
      pagado: "60000.00",
      saldo: "25000.00",
      pagos: [
        { id: 701, monto: "30000.00", fecha_pago: "2026-11-01" },
        { id: 801, monto: "30000.00", fecha_pago: "2026-11-02" },
      ],
    });
    const api = fingirApiDePago({
      cuenta: (_id, vez) =>
        vez === 1 ? cuentaCon(ABONO_SALDO_55000, "70000.00") : cuentaCon(despues, "40000.00"),
      pagar: (cargoId) =>
        respuestaJson(
          201,
          pagoRegistrado({
            cargo_id: cargoId,
            monto: "30000.00",
            fecha_pago: "2026-11-02",
            saldo_cargo: "25000.00",
            saldo_pendiente: "40000.00",
          }),
        ),
    });
    const usuario = userEvent.setup();
    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    await escribirMonto(usuario, dialogo, "30.000");
    await ponerFecha(campoFechaDelPago(dialogo), "2026-11-02");
    await usuario.click(botonRegistrarPago(dialogo));

    await waitFor(() =>
      expect(textoDeLaPagina()).toContain(
        "Pago registrado por $ 30.000. Saldo pendiente de la familia: $ 40.000.",
      ),
    );
    const enviados = pagosEnviados(api, ABONO_MES_JUAN.id);
    expect(enviados).toHaveLength(1);
    const cuerpo = enviados[0]?.cuerpo as Record<string, unknown>;
    expect(Object.keys(cuerpo).sort()).toEqual(["fecha_pago", "monto"]);
    expect(cuerpo).toEqual({ monto: "30000.00", fecha_pago: "2026-11-02" });
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    await waitFor(() =>
      expect(cuentasPedidas(api)).toEqual([FAMILIA_PEREZ_ANA.id, FAMILIA_PEREZ_ANA.id]),
    );
  });

  it("con 4.462,50 en Monto el cuerpo enviado tiene monto 4462.50", async () => {
    const api = fingirApiDePago({
      cuenta: () => cuentaCon(ABONO_SALDO_55000, "70000.00"),
      pagar: () =>
        respuestaJson(
          201,
          pagoRegistrado({
            monto: "4462.50",
            fecha_pago: hoyDelEntorno(),
            saldo_cargo: "50537.50",
            saldo_pendiente: "65537.50",
          }),
        ),
    });
    const usuario = userEvent.setup();
    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    await escribirMonto(usuario, dialogo, "4.462,50");
    await usuario.click(botonRegistrarPago(dialogo));

    await waitFor(() => expect(pagosEnviados(api, ABONO_MES_JUAN.id)).toHaveLength(1));
    const cuerpo = pagosEnviados(api, ABONO_MES_JUAN.id)[0]?.cuerpo as Record<string, unknown>;
    expect(cuerpo.monto).toBe("4462.50");
  });

  it("con 4,462.50 en Monto se ve Escribí el monto como 4.462,50. junto a Monto y no se envía ningún pedido", async () => {
    const api = fingirApiDePago({
      cuenta: () => cuentaCon(ABONO_SALDO_55000, "70000.00"),
      pagar: () => respuestaJson(201, pagoRegistrado({})),
    });
    const usuario = userEvent.setup();
    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    await escribirMonto(usuario, dialogo, "4,462.50");
    await usuario.click(botonRegistrarPago(dialogo));

    const mensaje = "Escribí el monto como 4.462,50.";
    await waitFor(() => expect(campoMonto(dialogo)).toHaveAccessibleDescription(contiene(mensaje)));
    await esperar(100);
    expect(pedidosACargos(api)).toHaveLength(0);
  });

  it("con Monto vacío se ve Este dato es obligatorio. junto a Monto y no se envía ningún pedido", async () => {
    const api = fingirApiDePago({
      cuenta: () => cuentaCon(ABONO_SALDO_55000, "70000.00"),
      pagar: () => respuestaJson(201, pagoRegistrado({})),
    });
    const usuario = userEvent.setup();
    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    await escribirMonto(usuario, dialogo, "");
    await usuario.click(botonRegistrarPago(dialogo));

    await waitFor(() =>
      expect(campoMonto(dialogo)).toHaveAccessibleDescription(
        contiene("Este dato es obligatorio."),
      ),
    );
    await esperar(100);
    expect(pedidosACargos(api)).toHaveLength(0);
  });

  it("si la API responde 422 con El monto supera el saldo del cargo. en monto, el mensaje se ve junto a Monto y el formulario sigue abierto con lo escrito", async () => {
    const mensaje = "El monto supera el saldo del cargo.";
    const api = fingirApiDePago({
      cuenta: () => cuentaCon(ABONO_SALDO_55000, "70000.00"),
      pagar: () =>
        respuestaJson(422, {
          detail: [{ loc: ["body", "monto"], msg: mensaje, type: "regla_de_negocio" }],
        }),
    });
    const usuario = userEvent.setup();
    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    await escribirMonto(usuario, dialogo, "55.000,01");
    await usuario.click(botonRegistrarPago(dialogo));

    await waitFor(() => expect(pagosEnviados(api, ABONO_MES_JUAN.id)).toHaveLength(1));
    const abierto = await screen.findByRole("dialog");
    await waitFor(() => expect(campoMonto(abierto)).toHaveAccessibleDescription(contiene(mensaje)));
    expect(campoMonto(abierto)).toHaveValue("55.000,01");
    expect(within(abierto).getByRole("button", { name: "Registrar pago" })).toBeInTheDocument();
  });

  it("mientras el pedido no responde, Registrar pago está deshabilitado y un segundo clic no envía otro pedido", async () => {
    const api = fingirApiDePago({
      cuenta: () => cuentaCon(ABONO_SALDO_55000, "70000.00"),
      pagar: () => sinRespuesta(),
    });
    const usuario = userEvent.setup();
    const dialogo = await abrirFormularioDePago(usuario, ABONO_MES_1, ["Juan Pérez"]);

    await usuario.click(botonRegistrarPago(dialogo));

    await waitFor(() => expect(pagosEnviados(api, ABONO_MES_JUAN.id)).toHaveLength(1));
    await waitFor(() => expect(botonRegistrarPago(dialogo)).toBeDisabled());

    // Segundo clic sobre el boton deshabilitado (sin la comprobacion de
    // pointer-events, para que el clic llegue de verdad).
    const sinComprobar = userEvent.setup({ pointerEventsCheck: 0 });
    await sinComprobar.click(botonRegistrarPago(dialogo));
    await esperar(100);

    expect(pagosEnviados(api, ABONO_MES_JUAN.id)).toHaveLength(1);
    expect(botonRegistrarPago(dialogo)).toBeDisabled();
  });
});
