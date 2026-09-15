import { describe, expect, it } from "vitest";
import { filtrarCargasFaturamento } from "./domain.js";

describe("cargas parcialmente faturadas", () => {
  const cargas = [{ id: 1, pedidos: [{ id: 10, status: "Pronto para o envio" }, { id: 11, status: "Nota emitida" }] }, { id: 2, pedidos: [{ id: 20, status: "Nota emitida" }] }];
  it("mantém pendentes e oculta cargas totalmente emitidas", () => {
    const resultado = filtrarCargasFaturamento(cargas);
    expect(resultado.map((c) => c.id)).toEqual([1]);
    expect(resultado[0].pedidos.map((p) => p.id)).toEqual([10]);
    expect(cargas[0].pedidos).toHaveLength(2);
  });
  it("mostra apenas pedidos emitidos ao selecionar o filtro", () => {
    expect(filtrarCargasFaturamento(cargas, "Nota emitida").flatMap((c) => c.pedidos.map((p) => p.id))).toEqual([11, 20]);
  });
});
