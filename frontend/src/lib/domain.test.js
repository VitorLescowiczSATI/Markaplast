import { describe, expect, it } from "vitest";

import { calcularResumo, camposFaltandoPedido, filtrarPedidos, valorTotalPedido } from "./domain.js";

describe("regras de pedidos", () => {
  it("calcula total com embalagem e tampa", () => {
    expect(valorTotalPedido({ valor: 10, valorTampa: 5, quantidade: 2 })).toBe(30);
  });

  it("filtra por tampa e vendedor", () => {
    const pedidos = [
      {
        id: 1,
        cliente: "Cliente A",
        cidade: "X",
        produto: "P",
        tampa: "dosadora",
        cor: "azul",
        status: "Novo pedido",
        pagamento: "PIX",
        statusFinanceiro: "Pago",
        transporte: "CIF",
        faturamento: "NF Markaplast",
        vendedor: "Arthur",
        logradouro: "Rua Industrial",
        pcpObservacoes: "setup da injetora confirmado",
      },
    ];

    expect(filtrarPedidos(pedidos, "dosadora", "Todos", "Todos", "Comercial")).toHaveLength(1);
    expect(filtrarPedidos(pedidos, "", "Todos", "Arthur", "Comercial")).toHaveLength(1);
    expect(filtrarPedidos(pedidos, "Industrial", "Todos", "Todos", "Comercial")).toHaveLength(1);
    expect(filtrarPedidos(pedidos, "injetora", "Todos", "Todos", "Comercial")).toHaveLength(1);
  });

  it("aponta campos obrigatórios faltando no pedido", () => {
    expect(camposFaltandoPedido({})).toEqual(["Cliente", "Produto", "Cor", "Tampa", "Quantidade", "Vendedor"]);
    expect(camposFaltandoPedido({ cliente: "A", produto: "5L M2", cor: "Branco", tampa: "Rosca", quantidade: 100, vendedor: "Arthur" })).toEqual([]);
    expect(camposFaltandoPedido({ cliente: "A", produto: "5L M2", cor: "Branco", tampa: "Rosca", quantidade: 0, vendedor: "Arthur" })).toEqual(["Quantidade"]);
  });

  it("gera resumo financeiro", () => {
    const resumo = calcularResumo([
      { status: "Novo pedido", valor: 1, valorTampa: 1, quantidade: 1 },
      { status: "Nota emitida", statusFinanceiro: "Pago", valor: 10, valorTampa: 0, quantidade: 2 },
      { status: "Cancelado", valor: 100, valorTampa: 0, quantidade: 1 },
    ]);

    expect(resumo.novos).toBe(1);
    expect(resumo.notasEmitidas).toBe(1);
    expect(resumo.financeiroPago).toBe(1);
    expect(resumo.cancelados).toBe(1);
    expect(resumo.total).toBe(22);
  });
});
