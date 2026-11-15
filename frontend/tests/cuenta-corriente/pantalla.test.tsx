/**
 * Tests de la pantalla «Cuenta corriente» (`/cuenta-corriente`) con la sesion
 * de un Admin y la API fingida.
 *
 * Spec: openspec/changes/cuenta-corriente/specs/cuenta-corriente/spec.md,
 * Requirement «Pantalla «Cuenta corriente»», los Scenarios que no son del
 * Coordinador (ese esta en acceso.test.tsx). Un `it` por Scenario.
 */
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import {
  ABONO_DIA_JUAN,
  ABONO_MES_JUAN,
  FAMILIA_GOMEZ_LUCIA,
  FAMILIA_PEREZ_ANA,
  PREINSCRIPCION_ANA,
  abrirCuentaCorriente,
  campoFamilia,
  cuentaDe,
  cuentasPedidas,
  elegirFamilia,
  esperar,
  esperarRenglon,
  esperarValorJunto,
  fingirApi,
  hayTextoEn,
  montoDelRenglon,
  normalizar,
  renglonDeCargo,
  respuestaJson,
  textoDeLaPagina,
  valorJunto,
  type CargoEnCuenta,
} from "./pantalla";

const ABONO_MES_1 = "Abono · Mes 1";
const ABONO_DIA = "Abono · Día 08/01/2027";
const PREINSCRIPCION = "Preinscripción";

describe("Pantalla «Cuenta corriente»", () => {
  it("al elegir Pérez – Ana se ven Empleado, Saldo pendiente $ 60.000, el renglón Abono · Mes 1 con Juan Pérez · Mañana, Total $ 85.000, Pagado $ 40.000, Saldo $ 45.000 y sus dos pagos", async () => {
    const api = fingirApi({
      cuenta: (id) =>
        id === FAMILIA_PEREZ_ANA.id
          ? respuestaJson(
              200,
              cuentaDe(FAMILIA_PEREZ_ANA, {
                total_cargos: "105000.00",
                total_pagado: "45000.00",
                saldo_pendiente: "60000.00",
                cargos: [ABONO_MES_JUAN],
              }),
            )
          : respuestaJson(404, { detail: "La familia no existe." }),
    });
    await abrirCuentaCorriente();
    const usuario = userEvent.setup();

    await elegirFamilia(usuario, "Pér", "Pérez – Ana");

    const renglon = await esperarRenglon(
      ABONO_MES_1,
      [
        "Juan Pérez · Mañana",
        "$ 85.000",
        "$ 40.000",
        "$ 45.000",
        "02/11/2026 · $ 30.000",
        "05/11/2026 · $ 10.000",
      ],
      [],
    );
    expect(hayTextoEn(renglon, "Juan Pérez · Mañana")).toBe(true);
    montoDelRenglon(renglon, "Total", "$ 85.000");
    montoDelRenglon(renglon, "Pagado", "$ 40.000");
    montoDelRenglon(renglon, "Saldo", "$ 45.000");
    expect(hayTextoEn(renglon, "02/11/2026 · $ 30.000")).toBe(true);
    expect(hayTextoEn(renglon, "05/11/2026 · $ 10.000")).toBe(true);

    valorJunto("Saldo pendiente", "$ 60.000", [ABONO_MES_1]);
    expect(screen.getAllByText(/\bEmpleado\b/).length).toBeGreaterThan(0);
    expect(cuentasPedidas(api)).toEqual([FAMILIA_PEREZ_ANA.id]);
  });

  it("se ven el renglón Preinscripción con Ana Pérez y el renglón Abono · Día 08/01/2027 con Juan Pérez · Tarde", async () => {
    fingirApi({
      cuenta: () =>
        respuestaJson(
          200,
          cuentaDe(FAMILIA_PEREZ_ANA, {
            total_cargos: "29000.00",
            total_pagado: "5000.00",
            saldo_pendiente: "24000.00",
            cargos: [PREINSCRIPCION_ANA, ABONO_DIA_JUAN],
          }),
        ),
    });
    await abrirCuentaCorriente();
    const usuario = userEvent.setup();

    await elegirFamilia(usuario, "Pér", "Pérez – Ana");

    const preinscripcion = await esperarRenglon(PREINSCRIPCION, ["Ana Pérez"], [ABONO_DIA]);
    const dia = renglonDeCargo(ABONO_DIA, ["Juan Pérez · Tarde"], [PREINSCRIPCION]);
    expect(normalizar(preinscripcion.textContent)).not.toContain("Juan Pérez");
    expect(normalizar(dia.textContent)).not.toContain("Ana Pérez");
  });

  it("se ven Saldo $ 12.345,67 y Saldo pendiente $ 99.999,99, los que mandó la API, y no la resta", async () => {
    // A proposito, ni el saldo del cargo ni el de la familia son la resta:
    // una pantalla que calcule mostraria $ 55.000.
    const cargo: CargoEnCuenta = {
      ...ABONO_MES_JUAN,
      monto_total: "85000.00",
      pagado: "30000.00",
      saldo: "12345.67",
      pagos: [{ id: 701, monto: "30000.00", fecha_pago: "2026-11-02" }],
    };
    fingirApi({
      cuenta: () =>
        respuestaJson(
          200,
          cuentaDe(FAMILIA_PEREZ_ANA, {
            total_cargos: "85000.00",
            total_pagado: "30000.00",
            saldo_pendiente: "99999.99",
            cargos: [cargo],
          }),
        ),
    });
    await abrirCuentaCorriente();
    const usuario = userEvent.setup();

    await elegirFamilia(usuario, "Pér", "Pérez – Ana");

    const renglon = await esperarRenglon(ABONO_MES_1, ["$ 12.345,67"], []);
    montoDelRenglon(renglon, "Saldo", "$ 12.345,67");
    await esperarValorJunto("Saldo pendiente", "$ 99.999,99", [ABONO_MES_1]);
    expect(textoDeLaPagina()).not.toContain("$ 55.000");
  });

  it("el renglón del cargo con saldo 0.00 dice Saldado y no ofrece Registrar pago", async () => {
    const saldado: CargoEnCuenta = {
      ...PREINSCRIPCION_ANA,
      monto_total: "20000.00",
      pagado: "20000.00",
      saldo: "0.00",
      pagos: [{ id: 703, monto: "20000.00", fecha_pago: "2026-11-01" }],
    };
    fingirApi({
      cuenta: () =>
        respuestaJson(
          200,
          cuentaDe(FAMILIA_PEREZ_ANA, {
            total_cargos: "105000.00",
            total_pagado: "60000.00",
            saldo_pendiente: "45000.00",
            cargos: [saldado, ABONO_MES_JUAN],
          }),
        ),
    });
    await abrirCuentaCorriente();
    const usuario = userEvent.setup();

    await elegirFamilia(usuario, "Pér", "Pérez – Ana");

    // Lo que si se ve en el renglon saldado: su alumno y `Saldado`.
    const renglon = await esperarRenglon(PREINSCRIPCION, ["Ana Pérez", "Saldado"], [ABONO_MES_1]);
    expect(within(renglon).getByText(/\bSaldado\b/)).toBeInTheDocument();
    expect(within(renglon).queryByRole("button", { name: /Registrar pago/ })).toBeNull();
    expect(within(renglon).queryByRole("link", { name: /Registrar pago/ })).toBeNull();
  });

  it("la familia sin cargos muestra La familia no tiene cargos en la temporada. y Saldo pendiente $ 0", async () => {
    fingirApi({
      cuenta: () => respuestaJson(200, cuentaDe(FAMILIA_PEREZ_ANA, { cargos: [] })),
    });
    await abrirCuentaCorriente();
    const usuario = userEvent.setup();

    await elegirFamilia(usuario, "Pér", "Pérez – Ana");

    expect(
      await screen.findByText("La familia no tiene cargos en la temporada."),
    ).toBeInTheDocument();
    await esperarValorJunto("Saldo pendiente", "$ 0", []);
  });

  it("si la respuesta de Gómez – Lucía llega antes que la de Pérez – Ana, la cuenta corriente que queda es la de Gómez – Lucía", async () => {
    let liberarPerez: ((r: Response) => void) | undefined;
    let liberarGomez: ((r: Response) => void) | undefined;
    const respuestaPerez = new Promise<Response>((resolver) => {
      liberarPerez = resolver;
    });
    const respuestaGomez = new Promise<Response>((resolver) => {
      liberarGomez = resolver;
    });
    const api = fingirApi({
      familias: [FAMILIA_PEREZ_ANA, FAMILIA_GOMEZ_LUCIA],
      cuenta: (id) => {
        if (id === FAMILIA_PEREZ_ANA.id) return respuestaPerez;
        if (id === FAMILIA_GOMEZ_LUCIA.id) return respuestaGomez;
        return respuestaJson(404, { detail: "La familia no existe." });
      },
    });
    const preinscripcionLucia: CargoEnCuenta = {
      ...PREINSCRIPCION_ANA,
      id: 950,
      alumno_id: 60,
      nombre: "Lucía",
      apellido: "Gómez",
      monto_total: "20000.00",
      pagado: "13000.00",
      saldo: "7000.00",
      pagos: [{ id: 750, monto: "13000.00", fecha_pago: "2026-11-04" }],
    };
    await abrirCuentaCorriente();
    const usuario = userEvent.setup();

    await elegirFamilia(usuario, "Pér", "Pérez – Ana");
    await waitFor(() => expect(cuentasPedidas(api)).toContain(FAMILIA_PEREZ_ANA.id));

    await usuario.clear(campoFamilia());
    await elegirFamilia(usuario, "Góm", "Gómez – Lucía");
    await waitFor(() => expect(cuentasPedidas(api)).toContain(FAMILIA_GOMEZ_LUCIA.id));

    // Llega primero la de Gómez – Lucía.
    liberarGomez!(
      respuestaJson(
        200,
        cuentaDe(FAMILIA_GOMEZ_LUCIA, {
          total_cargos: "20000.00",
          total_pagado: "13000.00",
          saldo_pendiente: "7000.00",
          cargos: [preinscripcionLucia],
        }),
      ),
    );
    await esperarRenglon(PREINSCRIPCION, ["Lucía Gómez", "$ 13.000"], []);

    // Despues, la de Pérez – Ana, que ya no vale.
    liberarPerez!(
      respuestaJson(
        200,
        cuentaDe(FAMILIA_PEREZ_ANA, {
          total_cargos: "105000.00",
          total_pagado: "45000.00",
          saldo_pendiente: "60000.00",
          cargos: [ABONO_MES_JUAN],
        }),
      ),
    );
    await esperar(100);

    renglonDeCargo(PREINSCRIPCION, ["Lucía Gómez", "$ 13.000"], []);
    valorJunto("Saldo pendiente", "$ 7.000", [PREINSCRIPCION]);
    expect(screen.getAllByText(/\bSocio\b/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/\bEmpleado\b/)).toBeNull();
    expect(textoDeLaPagina()).not.toContain(ABONO_MES_1);
    expect(textoDeLaPagina()).not.toContain("Juan Pérez");
    expect(textoDeLaPagina()).not.toContain("$ 60.000");
  });
});
