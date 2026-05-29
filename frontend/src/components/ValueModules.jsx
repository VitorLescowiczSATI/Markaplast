import { useMemo, useState } from "react";
import { AlertTriangle, BarChart3, CheckCircle2, FileText, PackagePlus, Pencil, Search, Trash2, Users, Warehouse, X } from "lucide-react";

import { Badge, Button, Card, EmptyState, Field, Input, SelectBox, StatCard, TextArea } from "./ui.jsx";
import { api } from "../lib/api.js";
import { currency, statusColor, valorTotalPedido } from "../lib/domain.js";

const emptyCliente = {
  nome: "",
  cnpj: "",
  contato: "",
  telefone: "",
  email: "",
  cep: "",
  logradouro: "",
  numero: "",
  bairro: "",
  cidade: "",
  uf: "",
  condicaoPagamento: "",
  observacoes: "",
};

const emptyProduto = {
  nome: "",
  categoria: "Embalagem",
  unidade: "un",
  precoBase: "",
  valorTampaPadrao: "",
  estoqueAtual: "",
  estoqueReservado: "0",
  estoqueMinimo: "",
  ativo: "sim",
};

function HorizontalBar({ label, value, max, detail }) {
  const width = max > 0 ? Math.max(4, Math.round((Number(value || 0) / max) * 100)) : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="truncate font-medium text-slate-700">{label}</span>
        <span className="whitespace-nowrap text-xs font-semibold text-slate-500">{detail || value}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-teal-600" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function AlertasPanel({ alertas = [] }) {
  const tone = {
    alta: "border-red-200 bg-red-50 text-red-800",
    media: "border-amber-200 bg-amber-50 text-amber-800",
    baixa: "border-slate-200 bg-slate-50 text-slate-700",
  };

  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center gap-2">
        <AlertTriangle size={20} className="text-amber-600" />
        <h2 className="text-xl font-bold">Alertas automáticos</h2>
      </div>
      <div className="space-y-2">
        {alertas.length === 0 && <EmptyState>Nenhum alerta operacional agora.</EmptyState>}
        {alertas.map((alerta, index) => (
          <div key={`${alerta.tipo}-${alerta.entidadeId}-${index}`} className={`rounded-lg border p-3 ${tone[alerta.prioridade] || tone.baixa}`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-bold">{alerta.titulo}</p>
              <Badge className="border-current bg-white/60 text-current">{alerta.prioridade}</Badge>
            </div>
            <p className="mt-1 text-sm">{alerta.detalhe}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function InteligenciaLayout({ dashboard, historico = [], produtos = [] }) {
  const resumo = dashboard?.resumo || {};
  const statusMax = Math.max(1, ...(dashboard?.porStatus || []).map((item) => Number(item.valor || 0)));
  const vendedorMax = Math.max(1, ...(dashboard?.porVendedor || []).map((item) => Number(item.valor || 0)));
  const produtoMax = Math.max(1, ...(dashboard?.porProduto || []).map((item) => Number(item.valor || 0)));
  const produtosComEstoque = produtos.filter((produto) => Number(produto.estoqueAtual || 0) > 0 || Number(produto.estoqueMinimo || 0) > 0);
  const coberturaMedia =
    produtosComEstoque.length > 0
      ? Math.round(
          produtosComEstoque.reduce((acc, produto) => acc + Number(produto.disponivel || 0) / Math.max(1, Number(produto.estoqueMinimo || 1)), 0) /
            produtosComEstoque.length
        )
      : 0;

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Pedidos ativos" value={(resumo.totalPedidos || 0) || Object.values(resumo).filter((v) => typeof v === "number").slice(0, 6).reduce((a, b) => a + b, 0)} tone="teal" />
        <StatCard label="Valor em carteira" value={currency(resumo.total || 0)} tone="teal" />
        <StatCard label="Prontos para faturar" value={resumo.faturar || 0} tone="green" />
        <StatCard label="Financeiro pendente" value={resumo.financeiroPendente || 0} tone="amber" />
        <StatCard label="Cobertura média estoque" value={`${coberturaMedia}x`} tone="sky" />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="p-5">
          <div className="mb-5 flex items-center gap-2">
            <BarChart3 size={20} className="text-teal-700" />
            <h2 className="text-xl font-bold">Indicadores comerciais</h2>
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="space-y-3">
              <h3 className="font-bold">Por status</h3>
              {(dashboard?.porStatus || []).map((item) => (
                <HorizontalBar key={item.label} label={item.label} value={item.valor} max={statusMax} />
              ))}
            </div>
            <div className="space-y-3">
              <h3 className="font-bold">Por vendedor</h3>
              {(dashboard?.porVendedor || []).slice(0, 7).map((item) => (
                <HorizontalBar key={item.label} label={item.label} value={item.valor} max={vendedorMax} detail={currency(item.valor)} />
              ))}
            </div>
            <div className="space-y-3">
              <h3 className="font-bold">Top produtos</h3>
              {(dashboard?.porProduto || []).slice(0, 7).map((item) => (
                <HorizontalBar key={item.label} label={item.label} value={item.valor} max={produtoMax} detail={currency(item.valor)} />
              ))}
            </div>
          </div>
        </Card>

        <AlertasPanel alertas={dashboard?.alertas || []} />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card className="p-5">
          <div className="mb-4 flex items-center gap-2">
            <Warehouse size={20} className="text-teal-700" />
            <h2 className="text-xl font-bold">Estoque crítico</h2>
          </div>
          <div className="space-y-2">
            {(dashboard?.estoqueCritico || []).length === 0 && <EmptyState>Nenhum item abaixo do mínimo.</EmptyState>}
            {(dashboard?.estoqueCritico || []).map((produto) => (
              <div key={produto.id} className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                <div className="flex items-center justify-between gap-3">
                  <strong>{produto.nome}</strong>
                  <Badge className="border-amber-300 bg-white text-amber-800">{produto.disponivel} disp.</Badge>
                </div>
                <p className="mt-1 text-sm text-amber-800">
                  Estoque {produto.estoqueAtual}, reservado {produto.estoqueReservado}, mínimo {produto.estoqueMinimo}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="mb-4 text-xl font-bold">Auditoria recente</h2>
          <div className="space-y-2">
            {historico.length === 0 && <EmptyState>Nenhum histórico registrado.</EmptyState>}
            {historico.slice(0, 12).map((item) => (
              <div key={item.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <strong>Pedido #{item.pedidoId}</strong>
                  <span className="text-xs text-slate-500">{new Date(item.createdAt).toLocaleString("pt-BR")}</span>
                </div>
                <p className="mt-1 text-slate-700">
                  {item.tipo}: {item.deValor || "-"} → {item.paraValor || "-"}
                </p>
                {item.observacao && <p className="mt-1 text-xs text-slate-500">{item.observacao}</p>}
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}

export function ClientesLayout({ clientes = [], onRefresh, salvando }) {
  const [form, setForm] = useState(emptyCliente);
  const [editandoId, setEditandoId] = useState(null);
  const [busca, setBusca] = useState("");
  const [cepLoading, setCepLoading] = useState(false);
  const filtrados = clientes.filter((cliente) => `${cliente.nome} ${cliente.cnpj} ${cliente.cidade}`.toLowerCase().includes(busca.toLowerCase()));

  async function buscarCep() {
    if (!form.cep) return;
    setCepLoading(true);
    try {
      const endereco = await api.lookupCep(form.cep);
      setForm({
        ...form,
        cep: endereco.cep || form.cep,
        logradouro: endereco.logradouro || "",
        bairro: endereco.bairro || "",
        cidade: endereco.cidade || "",
        uf: endereco.uf || "",
      });
    } finally {
      setCepLoading(false);
    }
  }

  async function submit(event) {
    event.preventDefault();
    if (!form.nome) {
      window.alert("Informe o nome do cliente.");
      return;
    }
    if (editandoId) {
      await api.updateCliente(editandoId, form);
    } else {
      await api.createCliente(form);
    }
    setForm(emptyCliente);
    setEditandoId(null);
    await onRefresh();
  }

  function editarCliente(cliente) {
    setEditandoId(cliente.id);
    setForm({
      nome: cliente.nome || "",
      cnpj: cliente.cnpj || "",
      contato: cliente.contato || "",
      telefone: cliente.telefone || "",
      email: cliente.email || "",
      cep: cliente.cep || "",
      logradouro: cliente.logradouro || "",
      numero: cliente.numero || "",
      bairro: cliente.bairro || "",
      cidade: cliente.cidade || "",
      uf: cliente.uf || "",
      condicaoPagamento: cliente.condicaoPagamento || "",
      observacoes: cliente.observacoes || "",
    });
  }

  function cancelarEdicao() {
    setEditandoId(null);
    setForm(emptyCliente);
  }

  async function excluirCliente(cliente) {
    if (!window.confirm(`Deseja excluir o cliente ${cliente.nome}?`)) return;
    await api.deleteCliente(cliente.id);
    if (editandoId === cliente.id) cancelarEdicao();
    await onRefresh();
  }

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard label="Clientes cadastrados" value={clientes.length} tone="teal" />
        <StatCard label="Com CNPJ" value={clientes.filter((cliente) => cliente.cnpj).length} />
        <StatCard label="Com endereço completo" value={clientes.filter((cliente) => cliente.cep && cliente.cidade && cliente.uf).length} tone="green" />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[420px_1fr]">
        <Card className="p-5">
          <div className="mb-5 flex items-center gap-2">
            <Users size={20} className="text-teal-700" />
            <h2 className="text-xl font-bold">{editandoId ? "Editar cliente" : "Cadastro de cliente"}</h2>
          </div>
          <form onSubmit={submit} className="space-y-3">
            <Field label="Nome / razão social">
              <Input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} placeholder="Cliente" />
            </Field>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Field label="CNPJ">
                <Input value={form.cnpj} onChange={(e) => setForm({ ...form, cnpj: e.target.value })} placeholder="00.000.000/0001-00" />
              </Field>
              <Field label="Condição de pagamento">
                <Input value={form.condicaoPagamento} onChange={(e) => setForm({ ...form, condicaoPagamento: e.target.value })} placeholder="Boleto 28 dias" />
              </Field>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Field label="Contato">
                <Input value={form.contato} onChange={(e) => setForm({ ...form, contato: e.target.value })} placeholder="Nome" />
              </Field>
              <Field label="Telefone">
                <Input value={form.telefone} onChange={(e) => setForm({ ...form, telefone: e.target.value })} placeholder="(00) 00000-0000" />
              </Field>
            </div>
            <Field label="E-mail">
              <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="financeiro@cliente.com.br" />
            </Field>
            <div className="grid grid-cols-[1fr_auto] gap-2">
              <Field label="CEP">
                <Input value={form.cep} onChange={(e) => setForm({ ...form, cep: e.target.value })} placeholder="00000-000" />
              </Field>
              <Button onClick={buscarCep} disabled={cepLoading} className="mt-5 border border-slate-200 bg-white text-slate-700 hover:bg-slate-50">
                <Search size={16} />
              </Button>
            </div>
            <Field label="Logradouro">
              <Input value={form.logradouro} onChange={(e) => setForm({ ...form, logradouro: e.target.value })} placeholder="Rua" />
            </Field>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <Field label="Número">
                <Input value={form.numero} onChange={(e) => setForm({ ...form, numero: e.target.value })} />
              </Field>
              <Field label="Bairro">
                <Input value={form.bairro} onChange={(e) => setForm({ ...form, bairro: e.target.value })} />
              </Field>
              <Field label="UF">
                <Input value={form.uf} onChange={(e) => setForm({ ...form, uf: e.target.value.toUpperCase() })} maxLength={2} />
              </Field>
            </div>
            <Field label="Cidade">
              <Input value={form.cidade} onChange={(e) => setForm({ ...form, cidade: e.target.value })} />
            </Field>
            <Field label="Observações">
              <TextArea value={form.observacoes} onChange={(e) => setForm({ ...form, observacoes: e.target.value })} />
            </Field>
            <Button type="submit" disabled={salvando} className="w-full bg-teal-700 text-white hover:bg-teal-800">
              {editandoId ? "Atualizar cliente" : "Salvar cliente"}
            </Button>
            {editandoId && (
              <Button onClick={cancelarEdicao} className="w-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-50">
                <X size={16} />
                Cancelar edicao
              </Button>
            )}
          </form>
        </Card>

        <Card className="p-5">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 className="text-xl font-bold">Carteira de clientes</h2>
            <Input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, CNPJ ou cidade" className="md:w-80" />
          </div>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {filtrados.length === 0 && <EmptyState>Nenhum cliente encontrado.</EmptyState>}
            {filtrados.map((cliente) => (
              <article key={cliente.id} className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="truncate font-bold">{cliente.nome}</h3>
                    <p className="text-sm text-slate-500">{cliente.cnpj || "CNPJ não informado"}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="border-teal-200 bg-teal-50 text-teal-800">{cliente.uf || "--"}</Badge>
                    <button
                      type="button"
                      onClick={() => editarCliente(cliente)}
                      className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:border-teal-200 hover:bg-teal-50 hover:text-teal-700"
                      title="Editar cliente"
                      aria-label="Editar cliente"
                    >
                      <Pencil size={15} />
                    </button>
                    <button
                      type="button"
                      onClick={() => excluirCliente(cliente)}
                      className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:border-red-200 hover:bg-red-50 hover:text-red-600"
                      title="Excluir cliente"
                      aria-label="Excluir cliente"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-700">
                  {cliente.logradouro || "Endereço não informado"} {cliente.numero} - {cliente.bairro}
                </p>
                <p className="text-sm text-slate-500">
                  {cliente.cidade || "Cidade não informada"} {cliente.cep ? `- ${cliente.cep}` : ""}
                </p>
                <p className="mt-2 text-sm text-slate-600">{cliente.condicaoPagamento || "Condição de pagamento não informada"}</p>
              </article>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}

export function EstoqueLayout({ produtos = [], onRefresh }) {
  const [produtoForm, setProdutoForm] = useState(emptyProduto);
  const [produtoId, setProdutoId] = useState("");
  const [movimento, setMovimento] = useState({ tipo: "Entrada", quantidade: "", observacao: "" });
  const criticos = produtos.filter((produto) => Number(produto.disponivel || 0) <= Number(produto.estoqueMinimo || 0));

  async function criarProduto(event) {
    event.preventDefault();
    if (!produtoForm.nome) return;
    await api.createProduto({
      ...produtoForm,
      precoBase: Number(produtoForm.precoBase || 0),
      valorTampaPadrao: Number(produtoForm.valorTampaPadrao || 0),
      estoqueAtual: Number(produtoForm.estoqueAtual || 0),
      estoqueReservado: Number(produtoForm.estoqueReservado || 0),
      estoqueMinimo: Number(produtoForm.estoqueMinimo || 0),
    });
    setProdutoForm(emptyProduto);
    await onRefresh();
  }

  async function criarMovimento(event) {
    event.preventDefault();
    if (!produtoId || !movimento.quantidade) return;
    await api.createMovimentoEstoque(produtoId, {
      tipo: movimento.tipo,
      quantidade: Number(movimento.quantidade),
      observacao: movimento.observacao,
    });
    setMovimento({ tipo: "Entrada", quantidade: "", observacao: "" });
    await onRefresh();
  }

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatCard label="SKUs cadastrados" value={produtos.length} tone="teal" />
        <StatCard label="Estoque total" value={produtos.reduce((acc, produto) => acc + Number(produto.estoqueAtual || 0), 0)} />
        <StatCard label="Reservado" value={produtos.reduce((acc, produto) => acc + Number(produto.estoqueReservado || 0), 0)} tone="amber" />
        <StatCard label="Críticos" value={criticos.length} tone="green" />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[420px_1fr]">
        <div className="space-y-6">
          <Card className="p-5">
            <div className="mb-5 flex items-center gap-2">
              <PackagePlus size={20} className="text-teal-700" />
              <h2 className="text-xl font-bold">Novo SKU</h2>
            </div>
            <form onSubmit={criarProduto} className="space-y-3">
              <Field label="Produto">
                <Input value={produtoForm.nome} onChange={(e) => setProdutoForm({ ...produtoForm, nome: e.target.value })} placeholder="5L M2 natural" />
              </Field>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Field label="Categoria">
                  <Input value={produtoForm.categoria} onChange={(e) => setProdutoForm({ ...produtoForm, categoria: e.target.value })} />
                </Field>
                <Field label="Unidade">
                  <Input value={produtoForm.unidade} onChange={(e) => setProdutoForm({ ...produtoForm, unidade: e.target.value })} />
                </Field>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Field label="Preço base">
                  <Input type="number" step="0.01" value={produtoForm.precoBase} onChange={(e) => setProdutoForm({ ...produtoForm, precoBase: e.target.value })} />
                </Field>
                <Field label="Valor tampa padrão">
                  <Input type="number" step="0.01" value={produtoForm.valorTampaPadrao} onChange={(e) => setProdutoForm({ ...produtoForm, valorTampaPadrao: e.target.value })} />
                </Field>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Field label="Estoque atual">
                  <Input type="number" value={produtoForm.estoqueAtual} onChange={(e) => setProdutoForm({ ...produtoForm, estoqueAtual: e.target.value })} />
                </Field>
                <Field label="Estoque mínimo">
                  <Input type="number" value={produtoForm.estoqueMinimo} onChange={(e) => setProdutoForm({ ...produtoForm, estoqueMinimo: e.target.value })} />
                </Field>
              </div>
              <Button type="submit" className="w-full bg-teal-700 text-white hover:bg-teal-800">
                Criar SKU
              </Button>
            </form>
          </Card>

          <Card className="p-5">
            <h2 className="mb-4 text-xl font-bold">Movimentar estoque</h2>
            <form onSubmit={criarMovimento} className="space-y-3">
              <Field label="Produto">
                <SelectBox value={produtoId} onChange={setProdutoId}>
                  <option value="">Selecione</option>
                  {produtos.map((produto) => (
                    <option key={produto.id} value={produto.id}>
                      {produto.nome}
                    </option>
                  ))}
                </SelectBox>
              </Field>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Field label="Tipo">
                  <SelectBox value={movimento.tipo} onChange={(tipo) => setMovimento({ ...movimento, tipo })}>
                    {["Entrada", "Saida", "Ajuste"].map((tipo) => (
                      <option key={tipo} value={tipo}>
                        {tipo}
                      </option>
                    ))}
                  </SelectBox>
                </Field>
                <Field label="Quantidade">
                  <Input type="number" value={movimento.quantidade} onChange={(e) => setMovimento({ ...movimento, quantidade: e.target.value })} />
                </Field>
              </div>
              <Field label="Observação">
                <Input value={movimento.observacao} onChange={(e) => setMovimento({ ...movimento, observacao: e.target.value })} placeholder="Compra, inventário, ajuste" />
              </Field>
              <Button type="submit" className="w-full bg-teal-700 text-white hover:bg-teal-800">
                Registrar movimento
              </Button>
            </form>
          </Card>
        </div>

        <Card className="p-5">
          <h2 className="mb-4 text-xl font-bold">Produtos e disponibilidade</h2>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {produtos.map((produto) => {
              const critico = Number(produto.disponivel || 0) <= Number(produto.estoqueMinimo || 0);
              return (
                <article key={produto.id} className={`rounded-lg border p-4 ${critico ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-white"}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="truncate font-bold">{produto.nome}</h3>
                      <p className="text-sm text-slate-500">{produto.categoria}</p>
                    </div>
                    <Badge className={critico ? "border-amber-300 bg-white text-amber-800" : "border-teal-200 bg-teal-50 text-teal-800"}>
                      {produto.disponivel} disp.
                    </Badge>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
                    <div className="rounded-lg bg-white/70 p-2">
                      <p className="text-xs text-slate-500">Atual</p>
                      <strong>{produto.estoqueAtual}</strong>
                    </div>
                    <div className="rounded-lg bg-white/70 p-2">
                      <p className="text-xs text-slate-500">Reservado</p>
                      <strong>{produto.estoqueReservado}</strong>
                    </div>
                    <div className="rounded-lg bg-white/70 p-2">
                      <p className="text-xs text-slate-500">Mínimo</p>
                      <strong>{produto.estoqueMinimo}</strong>
                    </div>
                  </div>
                  <p className="mt-3 text-sm text-slate-600">Preço base: {currency(produto.precoBase)}</p>
                </article>
              );
            })}
          </div>
        </Card>
      </section>
    </div>
  );
}

export function FiscalLayout({ pedidos = [], notas = [], prepararNfe, marcarNfeEmitida, enviarNfeHomologacao }) {
  const pedidosFiscais = pedidos.filter((pedido) => ["Pronto para faturar", "Nota emitida"].includes(pedido.status));
  const notasPorPedido = useMemo(() => new Map(notas.map((nota) => [nota.pedidoId, nota])), [notas]);

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatCard label="Pedidos fiscais" value={pedidosFiscais.length} tone="teal" />
        <StatCard label="Pré-NF-e geradas" value={notas.length} />
        <StatCard label="Rascunhos prontos" value={notas.filter((nota) => nota.status.includes("pronto")).length} tone="green" />
        <StatCard label="Emitidas manualmente" value={notas.filter((nota) => nota.status.includes("Emitida")).length} tone="amber" />
      </section>

      <Card className="p-5">
        <div className="mb-4 flex items-center gap-2">
          <FileText size={20} className="text-teal-700" />
          <h2 className="text-xl font-bold">Pré-faturamento fiscal</h2>
        </div>
        <div className="space-y-3">
          {pedidosFiscais.length === 0 && <EmptyState>Nenhum pedido pronto para o fiscal.</EmptyState>}
          {pedidosFiscais.map((pedido) => {
            const nota = notasPorPedido.get(pedido.id);
            return (
              <article key={pedido.id} className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-bold">Pedido #{pedido.id}</h3>
                      <Badge className={statusColor(pedido.status)}>{pedido.status}</Badge>
                      {nota && <Badge className="border-teal-200 bg-teal-50 text-teal-800">{nota.status}</Badge>}
                    </div>
                    <p className="text-sm text-slate-700">
                      <strong>{pedido.cliente}</strong> - {pedido.cnpj || "CNPJ pendente"}
                    </p>
                    <p className="text-sm text-slate-600">
                      {pedido.produto} - {pedido.quantidade} un - {currency(valorTotalPedido(pedido))}
                    </p>
                    <p className="text-sm text-slate-500">Faturamento: {pedido.faturamento || "Não informado"}</p>
                    {nota && (
                      <div className="mt-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                        Referência {nota.referencia} · Provedor {nota.provedor} · Ambiente {nota.ambiente}
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-1 gap-2 lg:min-w-64">
                    <Button onClick={() => prepararNfe(pedido.id)} className="border border-slate-200 bg-white text-slate-700 hover:bg-slate-50">
                      Preparar pré-NF-e
                    </Button>
                    {nota && (
                      <Button onClick={() => enviarNfeHomologacao(nota.id)} className="border border-sky-200 bg-sky-50 text-sky-800 hover:bg-sky-100">
                        Enviar homologação
                      </Button>
                    )}
                    {nota && (
                      <Button onClick={() => marcarNfeEmitida(nota.id)} className="bg-green-600 text-white hover:bg-green-700">
                        <CheckCircle2 size={16} />
                        Marcar emitida
                      </Button>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
