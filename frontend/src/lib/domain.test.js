import { describe, expect, it } from "vitest";

import { calcularResumo, camposFaltandoPedido, filtrarPedidos, percentualMeta, realizadoMetas, valorTotalPedido } from "./domain.js";

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

  it("soma o faturado por período e vendedor", () => {
    const hoje = new Date(2026, 5, 15); // 15/06/2026 (mês 5 = junho, trimestre 1)
    const pedidos = [
      // faturado hoje (conta em dia, mês e trimestre) - Arthur
      { status: "Nota emitida", data: "2026-06-15", vendedor: "Arthur", valor: 10, valorTampa: 0, quantidade: 100 },
      // faturado outro dia do mês (mês + trimestre) - Ingrid
      { status: "Finalizado", data: "2026-06-02", vendedor: "Ingrid", valor: 5, valorTampa: 0, quantidade: 100 },
      // faturado em abril (só trimestre) - Arthur
      { status: "Enviado", data: "2026-04-10", vendedor: "Arthur", valor: 2, valorTampa: 0, quantidade: 100 },
      // não faturado (ignorado)
      { status: "Em produção", data: "2026-06-15", vendedor: "Arthur", valor: 99, valorTampa: 0, quantidade: 100 },
      // trimestre diferente (ignorado)
      { status: "Nota emitida", data: "2026-01-15", vendedor: "Arthur", valor: 50, valorTampa: 0, quantidade: 100 },
    ];
    const r = realizadoMetas(pedidos, hoje);
    expect(r.empresa.diaria).toBe(1000); // só o de hoje
    expect(r.empresa.mensal).toBe(1500); // hoje (1000) + dia 02 (500)
    expect(r.empresa.trimestral).toBe(1700); // + abril (200)
    expect(r.porVendedor.Arthur.trimestral).toBe(1200);
    expect(r.porVendedor.Ingrid.mensal).toBe(500);
    expect(percentualMeta(1500, 3000)).toBe(50);
    expect(percentualMeta(10, 0)).toBe(0);
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
