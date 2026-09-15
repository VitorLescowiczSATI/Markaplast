import { useState } from "react";

import { Button, Card, EmptyState, Field, Input } from "./ui.jsx";
import { currency, itensPedido, valorTotalPedido } from "../lib/domain.js";

// O pedido faturado ou já em rota não pode mais mudar de quantidade (o backend devolve 409).
const STATUS_SEM_EDICAO = ["Nota emitida", "Cancelado", "Separado para entrega", "Enviado", "Finalizado"];

export function EditarQuantidades({ pedido, atualizarPedido }) {
  const [aberto, setAberto] = useState(false);
  const [quantidades, setQuantidades] = useState([]);
  const [salvando, setSalvando] = useState(false);

  if (!atualizarPedido || STATUS_SEM_EDICAO.includes(pedido.status)) return null;
  const itens = itensPedido(pedido);

  function alternar() {
    setQuantidades(itens.map((item) => String(item.quantidade)));
    setAberto((valor) => !valor);
  }

  async function salvar(event) {
    event.preventDefault();
    if (quantidades.some((quantidade) => !Number.isInteger(Number(quantidade)) || Number(quantidade) <= 0)) return;
    setSalvando(true);
    try {
      const salvo = await atualizarPedido(pedido.id, {
        itens: itens.map((item, indice) => ({ ...item, quantidade: Number(quantidades[indice]) })),
      });
      if (salvo) setAberto(false);
    } finally {
      setSalvando(false);
    }
  }

  return (
    // O card do PCP é arrastável: o clique e o arraste da edição não podem subir para ele.
    <div className="mt-2 w-full" onClick={(event) => event.stopPropagation()} onDragStart={(event) => event.stopPropagation()}>
      <Button type="button" className="w-full border border-teal-200 text-teal-800" onClick={alternar}>
        {aberto ? "Fechar edição" : "Editar quantidades"}
      </Button>
      {aberto && (
        <form onSubmit={salvar} className="mt-2 space-y-3 rounded-lg bg-slate-50 p-3">
          {itens.map((item, indice) => (
            <Field key={item.id || indice} label={`${item.produto} · ${item.cor || "Sem cor"} · ${item.tampa || "Sem tampa"}`}>
              <Input
                aria-label={`Quantidade de ${item.produto}, item ${indice + 1}`}
                type="number"
                min="1"
                step="1"
                required
                value={quantidades[indice]}
                onChange={(event) =>
                  setQuantidades((atual) => atual.map((quantidade, i) => (i === indice ? event.target.value : quantidade)))
                }
              />
            </Field>
          ))}
          <Button type="submit" disabled={salvando} className="bg-teal-700 text-white">
            Salvar quantidades
          </Button>
        </form>
      )}
    </div>
  );
}

export function HistoricoVendedores({ pedidos, vendedor, compacto = false }) {
  const emitidos = pedidos.filter((pedido) => pedido.status === "Nota emitida");
  const nomes = vendedor ? [vendedor] : [...new Set(emitidos.map((pedido) => pedido.vendedor || "Não informado"))].sort();

  const conteudo = (
    <>
      {!compacto && <h3 className="mb-3 text-lg font-bold">Faturamento por vendedor</h3>}
      {nomes.length === 0 && <EmptyState>Nenhuma nota emitida.</EmptyState>}
      {nomes.map((nome) => {
        const vendas = emitidos
          .filter((pedido) => (pedido.vendedor || "Não informado") === nome)
          .sort(
            (a, b) =>
              (b.dataEmissao || b.data || "").localeCompare(a.dataEmissao || a.data || "") || b.id - a.id
          );
        const total = vendas.reduce((acumulado, pedido) => acumulado + valorTotalPedido(pedido), 0);
        return (
          <details key={nome} className="mb-2 rounded-lg border border-slate-200 p-3">
            <summary className="cursor-pointer text-sm font-semibold">
              {/* No modo compacto o nome já aparece na barra logo acima. */}
              {compacto ? "Notas emitidas" : nome} · {vendas.length} {vendas.length === 1 ? "nota" : "notas"} · {currency(total)}
            </summary>
            {vendas.length === 0 ? (
              <EmptyState>Nenhuma nota emitida neste período.</EmptyState>
            ) : (
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr>
                      <th className="p-2">Cliente</th>
                      <th className="p-2">Nota fiscal</th>
                      <th className="p-2">Valor da nota</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vendas.map((pedido) => (
                      <tr key={pedido.id} className="border-t border-slate-100">
                        <td className="p-2">
                          {pedido.cliente}
                          <span className="block text-xs text-slate-500">Pedido #{pedido.id}</span>
                        </td>
                        <td className="p-2">{pedido.numeroNota || "Não informado"}</td>
                        <td className="p-2">{currency(valorTotalPedido(pedido))}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </details>
        );
      })}
    </>
  );

  return compacto ? <div>{conteudo}</div> : <Card className="p-5">{conteudo}</Card>;
}
