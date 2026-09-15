import { describe, expect, it } from "vitest";
import { FILTRO_CARGAS_OCULTAR, filtrarCargasFaturamento } from "./domain.js";

describe("cargas montadas", () => {
  const cargas = [
    { id: 1, pedidos: [{ id: 10, status: "Pronto para o envio" }, { id: 11, status: "Nota emitida" }] },
    { id: 2, pedidos: [{ id: 20, status: "Nota emitida" }] },
  ];

  it("some da lista assim que a carga é confirmada", () => {
    expect(filtrarCargasFaturamento(cargas)).toEqual([]);
    expect(filtrarCargasFaturamento(cargas, FILTRO_CARGAS_OCULTAR)).toEqual([]);
  });

  it("mantém pendentes e oculta cargas totalmente emitidas", () => {
    const resultado = filtrarCargasFaturamento(cargas, "Pendentes");
    expect(resultado.map((c) => c.id)).toEqual([1]);
    expect(resultado[0].pedidos.map((p) => p.id)).toEqual([10]);
    expect(cargas[0].pedidos).toHaveLength(2);
  });

  it("mostra apenas pedidos emitidos ao selecionar o filtro", () => {
    expect(filtrarCargasFaturamento(cargas, "Nota emitida").flatMap((c) => c.pedidos.map((p) => p.id))).toEqual([11, 20]);
  });
});
