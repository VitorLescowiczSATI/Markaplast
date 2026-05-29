import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  CheckCircle2,
  ClipboardList,
  Factory,
  FileText,
  LayoutDashboard,
  Loader2,
  PackageCheck,
  Plus,
  Printer,
  RefreshCw,
  Search,
  Trash2,
  Truck,
  Users,
  WalletCards,
  Warehouse,
} from "lucide-react";

import { Badge, Button, Card, EmptyState, Field, IconButton, Input, SelectBox, StatCard, TextArea } from "./components/ui.jsx";
import { ClientesLayout, EstoqueLayout, FiscalLayout, InteligenciaLayout } from "./components/ValueModules.jsx";
import { api } from "./lib/api.js";
import {
  emptyForm,
  financeiroStatusList,
  produtos,
  setores,
  statusList,
  tiposEntrega,
  tiposFaturamento,
  tiposFrete,
  vendedores,
} from "./lib/constants.js";
import { calcularResumo, currency, filtrarPedidos, financeiroColor, statusColor, valorTotalPedido } from "./lib/domain.js";

function payloadFromForm(form) {
  return {
    ...form,
    quantidade: Number(form.quantidade || 0),
    valor: Number(form.valor || 0),
    valorTampa: Number(form.valorTampa || 0),
  };
}

function pedidoFieldsFromCliente(cliente, form) {
  return {
    ...form,
    cliente: cliente.nome || "",
    cnpj: cliente.cnpj || "",
    cep: cliente.cep || "",
    logradouro: cliente.logradouro || "",
    numero: cliente.numero || "",
    bairro: cliente.bairro || "",
    cidade: cliente.cidade || "",
    uf: cliente.uf || "",
    pagamento: cliente.condicaoPagamento || form.pagamento,
  };
}

function perfilIcon(perfil) {
  const props = { size: 18 };
  if (perfil === "Inteligência") return <BarChart3 {...props} />;
  if (perfil === "Clientes") return <Users {...props} />;
  if (perfil === "Estoque") return <Warehouse {...props} />;
  if (perfil === "PCP/Logística") return <Factory {...props} />;
  if (perfil === "Faturamento") return <FileText {...props} />;
  if (perfil === "Financeiro") return <WalletCards {...props} />;
  if (perfil === "Fiscal") return <FileText {...props} />;
  if (perfil === "Logística") return <Truck {...props} />;
  if (perfil === "Gestor") return <LayoutDashboard {...props} />;
  return <ClipboardList {...props} />;
}

function ResumoCards({ pedidos }) {
  const resumo = useMemo(() => calcularResumo(pedidos), [pedidos]);

  return (
    <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
      <StatCard label="Novos" value={resumo.novos} tone="amber" />
      <StatCard label="Vai produzir" value={resumo.vaiProduzir} tone="sky" />
      <StatCard label="Em produção" value={resumo.producao} tone="sky" />
      <StatCard label="Notas emitidas" value={resumo.notasEmitidas} tone="green" />
      <StatCard label="Valor em carteira" value={currency(resumo.total)} tone="teal" />
    </section>
  );
}

function PedidoCard({ pedido, layout = "comercial", atualizarStatus, atualizarFinanceiro, excluirPedido }) {
  const total = valorTotalPedido(pedido);
  const temDetalhePcp =
    pedido.pcpPrevisaoProducao || pedido.pcpPrevisaoPronto || Number(pedido.pcpQuantidadeProduzida || 0) > 0 || pedido.pcpObservacoes;

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-bold">Pedido #{pedido.id}</h3>
            <IconButton label="Excluir pedido" onClick={() => excluirPedido(pedido.id)}>
              <Trash2 size={16} />
            </IconButton>
            <Badge className={statusColor(pedido.status)}>{pedido.status}</Badge>
            {(layout === "financeiro" || layout === "gestor") && (
              <Badge className={financeiroColor(pedido.statusFinanceiro)}>{pedido.statusFinanceiro}</Badge>
            )}
          </div>

          <p className="text-sm text-slate-700">
            <strong>{pedido.cliente}</strong> - {pedido.cidade || "cidade não informada"}
          </p>
          {(pedido.logradouro || pedido.cep || pedido.uf || pedido.cnpj) && (
            <p className="text-sm text-slate-600">
              {pedido.cnpj && (
                <span>
                  CNPJ: <strong>{pedido.cnpj}</strong> -{" "}
                </span>
              )}
              {pedido.logradouro || "Endereco nao informado"} {pedido.numero} {pedido.bairro ? `- ${pedido.bairro}` : ""}
              {pedido.cep ? ` - CEP ${pedido.cep}` : ""} {pedido.uf ? `- ${pedido.uf}` : ""}
            </p>
          )}
          <p className="text-sm text-slate-600">
            {pedido.produto} - {pedido.cor || "cor não informada"} - <strong>{pedido.quantidade} un</strong>
          </p>
          {pedido.tampa && (
            <p className="text-sm text-slate-600">
              Tampa: <strong>{pedido.tampa}</strong>
            </p>
          )}
          <div className="grid grid-cols-1 gap-2 text-sm text-slate-600 md:grid-cols-2">
            <p>
              Frete: <strong>{pedido.tipoFrete || "Não informado"}</strong>
            </p>
            <p>Transporte: {pedido.transporte || "Não informado"}</p>
            <p>
              Faturamento: <strong>{pedido.faturamento || "Não informado"}</strong>
            </p>
            <p>
              Entrega: <strong>{pedido.tipoEntrega || "Não definido"}</strong>
            </p>
            <p>
              Vendedor: <strong>{pedido.vendedor || "Não informado"}</strong>
            </p>
            <p>Pagamento: {pedido.pagamento || "Não informado"}</p>
          </div>
          {pedido.tipoFrete === "FOB" && pedido.detalheFOB && (
            <p className="text-sm text-slate-600">
              Detalhe FOB: <strong>{pedido.detalheFOB}</strong>
            </p>
          )}
          {pedido.observacoes && <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">{pedido.observacoes}</p>}
          {temDetalhePcp && (
            <div className="rounded-lg border border-sky-100 bg-sky-50 p-3 text-sm text-slate-700">
              <p className="mb-2 text-xs font-bold uppercase tracking-wide text-sky-800">Detalhes PCP</p>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                <p>
                  Vai produzir: <strong>{pedido.pcpPrevisaoProducao || "-"}</strong>
                </p>
                <p>
                  Pronto: <strong>{pedido.pcpPrevisaoPronto || "-"}</strong>
                </p>
                <p>
                  Produzido: <strong>{Number(pedido.pcpQuantidadeProduzida || 0)} un</strong>
                </p>
              </div>
              {pedido.pcpObservacoes && <p className="mt-2">{pedido.pcpObservacoes}</p>}
            </div>
          )}
        </div>

        <div className="space-y-3 lg:min-w-64">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Valor do pedido</p>
            <p className="text-2xl font-bold">{currency(total)}</p>
            <p className="mt-1 text-xs text-slate-500">
              Embalagem {currency(pedido.valor)} + tampa {currency(pedido.valorTampa)}
            </p>
          </div>

          {layout === "financeiro" ? (
            <>
              <Button onClick={() => atualizarFinanceiro(pedido.id, "Pago")} className="w-full bg-green-600 text-white hover:bg-green-700">
                <CheckCircle2 size={16} />
                Marcar pago
              </Button>
              <Button
                onClick={() => atualizarFinanceiro(pedido.id, "Aguardando pagamento")}
                className="w-full border border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100"
              >
                Aguardando pagamento
              </Button>
            </>
          ) : layout === "faturamento" ? (
            <Button onClick={() => atualizarStatus(pedido.id, "Nota emitida")} className="w-full bg-green-600 text-white hover:bg-green-700">
              <FileText size={16} />
              Nota fiscal emitida
            </Button>
          ) : layout === "logistica" ? (
            <div className="grid grid-cols-1 gap-2">
              {["Separado para entrega", "Enviado", "Finalizado"].map((status) => (
                <Button
                  key={status}
                  onClick={() => atualizarStatus(pedido.id, status)}
                  className={status === "Finalizado" ? "bg-green-600 text-white hover:bg-green-700" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}
                >
                  {status}
                </Button>
              ))}
            </div>
          ) : (
            <SelectBox value={pedido.status} onChange={(status) => atualizarStatus(pedido.id, status)}>
              {statusList.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </SelectBox>
          )}
        </div>
      </div>
    </article>
  );
}

function ComercialLayout({ pedidos, clientes = [], criarPedido, atualizarStatus, excluirPedido, salvando }) {
  const [busca, setBusca] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("Todos");
  const [vendedorFiltro, setVendedorFiltro] = useState("Todos");
  const [clienteSelecionadoId, setClienteSelecionadoId] = useState("");
  const [form, setForm] = useState(emptyForm);
  const clientesOrdenados = useMemo(() => [...clientes].sort((a, b) => String(a.nome || "").localeCompare(String(b.nome || ""))), [clientes]);
  const pedidosFiltrados = useMemo(
    () => filtrarPedidos(pedidos, busca, statusFiltro, vendedorFiltro, "Comercial"),
    [pedidos, busca, statusFiltro, vendedorFiltro]
  );

  function selecionarCliente(clienteId) {
    setClienteSelecionadoId(clienteId);
    if (!clienteId) return;
    const cliente = clientes.find((item) => String(item.id) === String(clienteId));
    if (cliente) setForm((atual) => pedidoFieldsFromCliente(cliente, atual));
  }

  async function submit(event) {
    event.preventDefault();
    if (!form.cliente || !form.produto || !form.quantidade) {
      window.alert("Preencha pelo menos Cliente, Produto e Quantidade.");
      return;
    }
    const salvo = await criarPedido(payloadFromForm(form));
    if (salvo) {
      setForm(emptyForm);
      setClienteSelecionadoId("");
    }
  }

  return (
    <div className="space-y-6">
      <ResumoCards pedidos={pedidos} />

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[420px_1fr]">
        <Card className="p-5">
          <div className="mb-5 flex items-center gap-2">
            <Plus size={20} className="text-teal-700" />
            <h2 className="text-lg font-bold">Novo pedido</h2>
          </div>

          <form onSubmit={submit} className="space-y-3">
            <Field label="Cliente cadastrado">
              <SelectBox value={clienteSelecionadoId} onChange={selecionarCliente}>
                <option value="">Preencher manualmente</option>
                {clientesOrdenados.map((cliente) => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nome} {cliente.cnpj ? `- ${cliente.cnpj}` : ""}
                  </option>
                ))}
              </SelectBox>
            </Field>
            <Field label="Cliente">
              <Input value={form.cliente} onChange={(e) => setForm({ ...form, cliente: e.target.value })} placeholder="Nome da empresa" />
            </Field>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Field label="CNPJ">
                <Input value={form.cnpj} onChange={(e) => setForm({ ...form, cnpj: e.target.value })} placeholder="00.000.000/0001-00" />
              </Field>
              <Field label="CEP">
                <Input value={form.cep} onChange={(e) => setForm({ ...form, cep: e.target.value })} placeholder="00000-000" />
              </Field>
            </div>
            <Field label="Endereco">
              <Input value={form.logradouro} onChange={(e) => setForm({ ...form, logradouro: e.target.value })} placeholder="Rua / avenida" />
            </Field>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <Field label="Numero">
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
              <Input value={form.cidade} onChange={(e) => setForm({ ...form, cidade: e.target.value })} placeholder="Curitiba" />
            </Field>
            <Field label="Produto">
              <SelectBox value={form.produto} onChange={(produto) => setForm({ ...form, produto })}>
                <option value="">Selecione</option>
                {produtos.map((produto) => (
                  <option key={produto} value={produto}>
                    {produto}
                  </option>
                ))}
              </SelectBox>
            </Field>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Field label="Cor">
                <Input value={form.cor} onChange={(e) => setForm({ ...form, cor: e.target.value })} placeholder="Branco, natural, azul" />
              </Field>
              <Field label="Quantidade">
                <Input type="number" min="1" value={form.quantidade} onChange={(e) => setForm({ ...form, quantidade: e.target.value })} placeholder="1500" />
              </Field>
            </div>
            <Field label="Tampa">
              <Input value={form.tampa} onChange={(e) => setForm({ ...form, tampa: e.target.value })} placeholder="Tampa lacre, dosadora" />
            </Field>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Field label="Valor da embalagem">
                <Input type="number" step="0.01" value={form.valor} onChange={(e) => setForm({ ...form, valor: e.target.value })} placeholder="0,00" />
              </Field>
              <Field label="Valor da tampa">
                <Input type="number" step="0.01" value={form.valorTampa} onChange={(e) => setForm({ ...form, valorTampa: e.target.value })} placeholder="0,00" />
              </Field>
            </div>
            <Field label="Tipo de pagamento">
              <Input value={form.pagamento} onChange={(e) => setForm({ ...form, pagamento: e.target.value })} placeholder="PIX, boleto 28 dias" />
            </Field>
            <Field label="Vendedor">
              <SelectBox value={form.vendedor} onChange={(vendedor) => setForm({ ...form, vendedor })}>
                <option value="">Selecione</option>
                {vendedores.map((vendedor) => (
                  <option key={vendedor} value={vendedor}>
                    {vendedor}
                  </option>
                ))}
              </SelectBox>
            </Field>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Field label="Tipo de frete">
                <SelectBox
                  value={form.tipoFrete}
                  onChange={(tipoFrete) =>
                    setForm({
                      ...form,
                      tipoFrete,
                      transporte: tipoFrete === "FOB" ? "" : form.transporte,
                      tipoEntrega: tipoFrete === "CIF" ? "Entrega CIF" : form.tipoEntrega,
                    })
                  }
                >
                  <option value="">Selecione</option>
                  {tiposFrete.map((tipo) => (
                    <option key={tipo} value={tipo}>
                      {tipo}
                    </option>
                  ))}
                </SelectBox>
              </Field>
              <Field label="Separação entrega">
                <SelectBox value={form.tipoEntrega} onChange={(tipoEntrega) => setForm({ ...form, tipoEntrega })}>
                  <option value="">Selecione</option>
                  {tiposEntrega.map((tipo) => (
                    <option key={tipo} value={tipo}>
                      {tipo}
                    </option>
                  ))}
                </SelectBox>
              </Field>
            </div>
            {form.tipoFrete === "FOB" && (
              <Field label="Detalhes FOB">
                <Input value={form.detalheFOB} onChange={(e) => setForm({ ...form, detalheFOB: e.target.value })} placeholder="Cliente retira ou transportadora" />
              </Field>
            )}
            {form.tipoFrete === "CIF" && (
              <Field label="Transporte CIF">
                <Input value={form.transporte} onChange={(e) => setForm({ ...form, transporte: e.target.value })} placeholder="Transportadora da empresa" />
              </Field>
            )}
            <Field label="Faturamento">
              <SelectBox value={form.faturamento} onChange={(faturamento) => setForm({ ...form, faturamento })}>
                <option value="">Selecione</option>
                {tiposFaturamento.map((tipo) => (
                  <option key={tipo} value={tipo}>
                    {tipo}
                  </option>
                ))}
              </SelectBox>
            </Field>
            <Field label="Observações">
              <TextArea value={form.observacoes} onChange={(e) => setForm({ ...form, observacoes: e.target.value })} placeholder="Detalhes do pedido" />
            </Field>
            <Button type="submit" disabled={salvando} className="w-full bg-teal-700 text-white hover:bg-teal-800">
              {salvando ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
              Cadastrar pedido
            </Button>
          </form>
        </Card>

        <Card className="p-5">
          <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="text-lg font-bold">Pedidos comerciais</h2>
              <p className="text-sm text-slate-500">{pedidosFiltrados.length} pedidos no filtro atual</p>
            </div>
            <div className="grid grid-cols-1 gap-2 lg:grid-cols-[220px_220px_220px]">
              <div className="relative">
                <Search size={16} className="pointer-events-none absolute left-3 top-2.5 text-slate-400" />
                <Input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar" className="pl-9" />
              </div>
              <SelectBox value={statusFiltro} onChange={setStatusFiltro}>
                <option value="Todos">Todos status</option>
                {statusList.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </SelectBox>
              <SelectBox value={vendedorFiltro} onChange={setVendedorFiltro}>
                <option value="Todos">Todos vendedores</option>
                {vendedores.map((vendedor) => (
                  <option key={vendedor} value={vendedor}>
                    {vendedor}
                  </option>
                ))}
              </SelectBox>
            </div>
          </div>

          <div className="space-y-3">
            {pedidosFiltrados.length === 0 && <EmptyState>Nenhum pedido encontrado.</EmptyState>}
            {pedidosFiltrados.map((pedido) => (
              <PedidoCard key={pedido.id} pedido={pedido} atualizarStatus={atualizarStatus} excluirPedido={excluirPedido} />
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}

function PCPLogisticaLayout({ pedidos, cargas, atualizarStatus, atualizarPedido, criarCarga, excluirPedido, salvando }) {
  const [busca, setBusca] = useState("");
  const [regiaoCarga, setRegiaoCarga] = useState("");
  const [motoristaCarga, setMotoristaCarga] = useState("");
  const [placaCarga, setPlacaCarga] = useState("");
  const [pedidosCarga, setPedidosCarga] = useState([]);
  const [draggingId, setDraggingId] = useState(null);
  const resumo = useMemo(() => calcularResumo(pedidos), [pedidos]);
  const statusKanban = ["Novo pedido", "Vai produzir", "Em produção", "Pronto para faturar"];
  const termo = busca.toLowerCase();
  const pedidosVisiveis = pedidos.filter((pedido) => {
    const texto =
      `${pedido.id} ${pedido.cliente} ${pedido.cidade} ${pedido.produto} ${pedido.cor} ${pedido.tampa} ${pedido.transporte} ${pedido.pcpPrevisaoProducao} ${pedido.pcpPrevisaoPronto} ${pedido.pcpQuantidadeProduzida} ${pedido.pcpObservacoes}`.toLowerCase();
    return statusKanban.includes(pedido.status) && texto.includes(termo);
  });
  const pedidosDisponiveisParaCarga = pedidos.filter((pedido) => statusKanban.includes(pedido.status));

  function togglePedidoCarga(id) {
    setPedidosCarga((prev) => (prev.includes(id) ? prev.filter((pedidoId) => pedidoId !== id) : [...prev, id]));
  }

  function handleDrop(statusDestino) {
    if (!draggingId) return;
    atualizarStatus(draggingId, statusDestino);
    setDraggingId(null);
  }

  async function submitCarga() {
    if (!regiaoCarga || pedidosCarga.length === 0) {
      window.alert("Preencha a região e selecione ao menos um pedido.");
      return;
    }

    await criarCarga({
      regiao: regiaoCarga,
      motorista: motoristaCarga,
      placa: placaCarga,
      pedidoIds: pedidosCarga,
      statusDestino: "Pronto para faturar",
    });
    setPedidosCarga([]);
    setRegiaoCarga("");
    setMotoristaCarga("");
    setPlacaCarga("");
  }

  function PedidoCompacto({ pedido }) {
    const [aberto, setAberto] = useState(false);
    const [detalhes, setDetalhes] = useState(() => ({
      pcpPrevisaoProducao: pedido.pcpPrevisaoProducao || "",
      pcpPrevisaoPronto: pedido.pcpPrevisaoPronto || "",
      pcpQuantidadeProduzida: String(pedido.pcpQuantidadeProduzida || ""),
      pcpObservacoes: pedido.pcpObservacoes || "",
    }));
    const selecionado = pedidosCarga.includes(pedido.id);
    const quantidadeProduzida = Number(pedido.pcpQuantidadeProduzida || 0);
    const percentualProduzido = Math.min(100, Math.round((quantidadeProduzida / Number(pedido.quantidade || 1)) * 100));
    const temDetalhePcp =
      pedido.pcpPrevisaoProducao || pedido.pcpPrevisaoPronto || quantidadeProduzida > 0 || pedido.pcpObservacoes;

    function atualizarDetalhe(campo, valor) {
      setDetalhes((prev) => ({ ...prev, [campo]: valor }));
    }

    async function salvarDetalhesPcp() {
      const salvo = await atualizarPedido(pedido.id, {
        ...detalhes,
        pcpQuantidadeProduzida: Number(detalhes.pcpQuantidadeProduzida || 0),
      });
      if (salvo) setAberto(false);
    }

    return (
      <article
        draggable={!aberto}
        onDragStart={() => setDraggingId(pedido.id)}
        onDragEnd={() => setDraggingId(null)}
        className={`cursor-grab rounded-lg border bg-white p-3 shadow-sm transition active:cursor-grabbing ${
          selecionado ? "border-teal-500 ring-2 ring-teal-100" : "border-slate-200 hover:border-teal-300"
        }`}
      >
        <div className="mb-2 flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => togglePedidoCarga(pedido.id)}
            className={`h-5 w-5 rounded border ${selecionado ? "border-teal-700 bg-teal-700" : "border-slate-300 bg-white"}`}
            aria-label="Selecionar para carga"
          />
          <p className="flex-1 text-sm font-bold">#{pedido.id}</p>
          <IconButton label="Excluir pedido" onClick={() => excluirPedido(pedido.id)}>
            <Trash2 size={15} />
          </IconButton>
        </div>
        <p className="truncate text-sm font-semibold text-slate-800">{pedido.cliente || "Cliente não informado"}</p>
        <p className="truncate text-xs text-slate-500">{pedido.cidade || "Cidade não informada"}</p>
        <div className="mt-2 rounded-lg bg-slate-50 px-2 py-2">
          <p className="truncate text-xs font-medium text-slate-700">{pedido.produto}</p>
          <div className="mt-1 flex items-center justify-between text-xs text-slate-500">
            <span>{pedido.quantidade || 0} un</span>
            <span className="font-bold text-slate-700">{currency(valorTotalPedido(pedido))}</span>
          </div>
        </div>

        {temDetalhePcp && (
          <div className="mt-3 space-y-2 rounded-lg border border-sky-100 bg-sky-50 p-3 text-xs text-slate-700">
            <div className="flex items-center justify-between gap-2">
              <span className="font-bold text-sky-800">PCP</span>
              <span className="font-semibold">{percentualProduzido}% produzido</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white">
              <div className="h-full rounded-full bg-sky-500" style={{ width: `${percentualProduzido}%` }} />
            </div>
            {pedido.pcpPrevisaoProducao && (
              <p>
                Vai produzir: <strong>{pedido.pcpPrevisaoProducao}</strong>
              </p>
            )}
            {pedido.pcpPrevisaoPronto && (
              <p>
                Pronto: <strong>{pedido.pcpPrevisaoPronto}</strong>
              </p>
            )}
            {pedido.pcpObservacoes && <p className="line-clamp-2">{pedido.pcpObservacoes}</p>}
          </div>
        )}

        <Button onClick={() => setAberto((valor) => !valor)} className="mt-3 w-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-50">
          {aberto ? "Fechar detalhes PCP" : temDetalhePcp ? "Editar detalhes PCP" : "Adicionar detalhes PCP"}
        </Button>

        {aberto && (
          <div className="mt-3 space-y-3 border-t border-slate-200 pt-3">
            <Field label="Quando vai produzir">
              <Input
                value={detalhes.pcpPrevisaoProducao}
                onChange={(event) => atualizarDetalhe("pcpPrevisaoProducao", event.target.value)}
                placeholder="Ex: 29/05 pela manha"
              />
            </Field>
            <Field label="Previsao de ficar pronto">
              <Input
                value={detalhes.pcpPrevisaoPronto}
                onChange={(event) => atualizarDetalhe("pcpPrevisaoPronto", event.target.value)}
                placeholder="Ex: 30/05 ate 16h"
              />
            </Field>
            <Field label="Quantidade produzida">
              <Input
                type="number"
                min="0"
                value={detalhes.pcpQuantidadeProduzida}
                onChange={(event) => atualizarDetalhe("pcpQuantidadeProduzida", event.target.value)}
                placeholder="0"
              />
            </Field>
            <Field label="Observacao PCP">
              <TextArea
                value={detalhes.pcpObservacoes}
                onChange={(event) => atualizarDetalhe("pcpObservacoes", event.target.value)}
                placeholder="Detalhes de producao, atraso, materia-prima, setup..."
              />
            </Field>
            <Button onClick={salvarDetalhesPcp} disabled={salvando} className="w-full bg-sky-700 text-white hover:bg-sky-800">
              Salvar detalhes PCP
            </Button>
          </div>
        )}
      </article>
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatCard label="Novos pedidos" value={resumo.novos} tone="amber" />
        <StatCard label="Vai produzir" value={resumo.vaiProduzir} tone="sky" />
        <StatCard label="Em produção" value={resumo.producao} tone="sky" />
        <StatCard label="Cargas montadas" value={cargas.length} tone="teal" />
      </section>

      <Card className="p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-bold">Painel PCP / Logística</h2>
            <p className="text-sm text-slate-500">Arraste pedidos entre etapas e monte cargas para liberar o faturamento.</p>
          </div>
          <Input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, pedido, produto ou rota" className="md:w-80" />
        </div>
      </Card>

      <section className="flex gap-4 overflow-x-auto pb-2">
        {statusKanban.map((status) => {
          const pedidosColuna = pedidosVisiveis.filter((pedido) => pedido.status === status);
          return (
            <Card
              key={status}
              className="min-h-[520px] min-w-[320px] max-w-[320px] flex-shrink-0 p-4"
              onDragOver={(event) => event.preventDefault()}
              onDrop={() => handleDrop(status)}
            >
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-bold">{status === "Novo pedido" ? "Novos pedidos" : status}</h3>
                <Badge className={statusColor(status)}>{pedidosColuna.length}</Badge>
              </div>
              <div className="max-h-[430px] space-y-2 overflow-y-auto pr-1">
                {pedidosColuna.length === 0 && <EmptyState>Solte pedidos aqui.</EmptyState>}
                {pedidosColuna.map((pedido) => (
                  <PedidoCompacto key={pedido.id} pedido={pedido} />
                ))}
              </div>
            </Card>
          );
        })}
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[420px_1fr]">
        <Card className="p-5">
          <h3 className="text-xl font-bold">Montagem de carga</h3>
          <p className="mb-4 text-sm text-slate-500">Pedidos selecionados mudam para Pronto para faturar.</p>
          <div className="space-y-3">
            <Field label="Região / rota">
              <Input value={regiaoCarga} onChange={(e) => setRegiaoCarga(e.target.value)} placeholder="Norte PR, SC, SP" />
            </Field>
            <Field label="Motorista">
              <Input value={motoristaCarga} onChange={(e) => setMotoristaCarga(e.target.value)} placeholder="Nome do motorista" />
            </Field>
            <Field label="Placa">
              <Input value={placaCarga} onChange={(e) => setPlacaCarga(e.target.value)} placeholder="ABC-1234" />
            </Field>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h4 className="font-bold">Selecionados</h4>
                <Badge className="border-teal-200 bg-teal-50 text-teal-800">{pedidosCarga.length}</Badge>
              </div>
              <div className="max-h-56 space-y-2 overflow-auto pr-1">
                {pedidosCarga.length === 0 && <EmptyState>Nenhum pedido selecionado.</EmptyState>}
                {pedidosDisponiveisParaCarga
                  .filter((pedido) => pedidosCarga.includes(pedido.id))
                  .map((pedido) => (
                    <button
                      key={pedido.id}
                      type="button"
                      onClick={() => togglePedidoCarga(pedido.id)}
                      className="w-full rounded-lg border border-teal-200 bg-white p-3 text-left transition hover:bg-teal-50"
                    >
                      <div className="flex items-center justify-between">
                        <strong>#{pedido.id}</strong>
                        <Badge className={statusColor(pedido.status)}>{pedido.status}</Badge>
                      </div>
                      <p className="text-sm text-slate-700">{pedido.cliente}</p>
                      <p className="text-xs text-slate-500">
                        {pedido.cidade} - {pedido.quantidade} un
                      </p>
                    </button>
                  ))}
              </div>
            </div>
            <Button onClick={submitCarga} disabled={salvando} className="w-full bg-teal-700 text-white hover:bg-teal-800">
              <Printer size={16} />
              Imprimir etiqueta da carga
            </Button>
          </div>
        </Card>

        <CargasMontadas cargas={cargas} statusLabel="Pronto para faturar" />
      </section>
    </div>
  );
}

function CargasMontadas({ cargas, statusLabel }) {
  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold">Cargas montadas</h3>
          <p className="text-sm text-slate-500">Agrupamento de pedidos por região.</p>
        </div>
        <Badge className="border-green-200 bg-green-50 text-green-800">{cargas.length} cargas</Badge>
      </div>
      <div className="space-y-4">
        {cargas.length === 0 && <EmptyState>Nenhuma carga montada.</EmptyState>}
        {cargas.map((carga) => {
          const valorCarga = carga.pedidos.reduce((acc, pedido) => acc + valorTotalPedido(pedido), 0);
          const statusDaCarga = statusLabel || carga.statusDestino;
          return (
            <article key={carga.id} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h4 className="text-lg font-bold">{carga.regiao}</h4>
                  <p className="text-sm text-slate-500">Criada em {new Date(`${carga.data}T00:00:00`).toLocaleDateString("pt-BR")}</p>
                </div>
                <Badge className="border-teal-200 bg-teal-50 text-teal-800">{carga.pedidos.length} pedidos</Badge>
              </div>
              <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-3">
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Motorista</p>
                  <p className="font-bold">{carga.motorista || "Não informado"}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Placa</p>
                  <p className="font-bold">{carga.placa || "Não informado"}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Valor da carga</p>
                  <p className="font-bold">{currency(valorCarga)}</p>
                </div>
              </div>
              <div className="space-y-2">
                {carga.pedidos.map((pedido) => (
                  <div key={pedido.id} className="flex flex-col gap-2 rounded-lg border border-slate-200 p-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="font-semibold">
                        Pedido #{pedido.id} - {pedido.cliente}
                      </p>
                      <p className="text-sm text-slate-500">
                        {pedido.cidade} - {pedido.quantidade} un
                      </p>
                    </div>
                    <Badge className={statusColor(statusDaCarga || pedido.status)}>{statusDaCarga || pedido.status}</Badge>
                  </div>
                ))}
              </div>
            </article>
          );
        })}
      </div>
    </Card>
  );
}

function FaturamentoLayout({ pedidos, atualizarStatus, excluirPedido }) {
  const [busca, setBusca] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("Pronto para faturar");
  const pedidosFaturamento = useMemo(() => filtrarPedidos(pedidos, busca, statusFiltro, "Todos", "Faturamento"), [pedidos, busca, statusFiltro]);
  const pedidosProntos = pedidos.filter((pedido) => pedido.status === "Pronto para faturar");
  const notasEmitidas = pedidos.filter((pedido) => pedido.status === "Nota emitida");
  const valorParaFaturar = pedidosProntos.reduce((acc, pedido) => acc + valorTotalPedido(pedido), 0);

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard label="Prontos para faturar" value={pedidosProntos.length} tone="green" />
        <StatCard label="Notas emitidas" value={notasEmitidas.length} tone="teal" />
        <StatCard label="Valor para faturar" value={currency(valorParaFaturar)} />
      </section>

      <Card className="p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-bold">Faturamento</h2>
            <p className="text-sm text-slate-500">Pedidos liberados pelo PCP e notas emitidas.</p>
          </div>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-[260px_220px]">
            <Input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar pedido, cliente ou produto" />
            <SelectBox value={statusFiltro} onChange={setStatusFiltro}>
              <option value="Pronto para faturar">Pronto para faturar</option>
              <option value="Nota emitida">Nota emitida</option>
              <option value="Todos">Todos</option>
            </SelectBox>
          </div>
        </div>
      </Card>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {tiposEntrega.map((tipoEntrega) => {
          const items = pedidosFaturamento.filter((pedido) => pedido.tipoEntrega === tipoEntrega);
          return (
            <Card key={tipoEntrega} className="p-4">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h3 className="font-bold">{tipoEntrega}</h3>
                  <p className="text-xs text-slate-500">{tipoEntrega === "Entrega CIF" ? "Entrega feita pela empresa" : "Cliente retira na fábrica"}</p>
                </div>
                <Badge className="border-slate-200 bg-slate-50 text-slate-700">{items.length}</Badge>
              </div>
              <div className="space-y-2">
                {items.length === 0 && <EmptyState>Nenhum pedido aqui.</EmptyState>}
                {items.slice(0, 5).map((pedido) => (
                  <div key={pedido.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <strong>#{pedido.id}</strong>
                      <Badge className={statusColor(pedido.status)}>{pedido.status}</Badge>
                    </div>
                    <p className="truncate font-semibold text-slate-800">{pedido.cliente}</p>
                    <p className="truncate text-xs text-slate-500">
                      {pedido.cidade} - {pedido.produto} - {pedido.quantidade} un
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          );
        })}
      </section>

      <div className="space-y-4">
        {pedidosFaturamento.length === 0 && <EmptyState>Nenhum pedido aguardando faturamento.</EmptyState>}
        {pedidosFaturamento.map((pedido) => (
          <PedidoCard
            key={pedido.id}
            pedido={pedido}
            layout="faturamento"
            atualizarStatus={atualizarStatus}
            excluirPedido={excluirPedido}
          />
        ))}
      </div>
    </div>
  );
}

function FinanceiroLayout({ pedidos, atualizarFinanceiro, excluirPedido }) {
  const [busca, setBusca] = useState("");
  const [financeiroFiltro, setFinanceiroFiltro] = useState("Todos");
  const [tipoPagamentoFiltro, setTipoPagamentoFiltro] = useState("Todos");
  const [clienteAberto, setClienteAberto] = useState(null);
  const tiposPagamento = useMemo(
    () => ["Todos", ...Array.from(new Set(pedidos.filter((pedido) => pedido.status === "Nota emitida").map((pedido) => pedido.pagamento || "Não informado")))],
    [pedidos]
  );
  const pedidosFinanceiro = useMemo(
    () =>
      filtrarPedidos(pedidos, busca, "Todos", "Todos", "Financeiro", financeiroFiltro).filter(
        (pedido) => tipoPagamentoFiltro === "Todos" || (pedido.pagamento || "Não informado") === tipoPagamentoFiltro
      ),
    [pedidos, busca, financeiroFiltro, tipoPagamentoFiltro]
  );
  const pedidosComNF = pedidos.filter((pedido) => pedido.status === "Nota emitida");
  const pagos = pedidosComNF.filter((pedido) => pedido.statusFinanceiro === "Pago");
  const pendentes = pedidosComNF.filter((pedido) => pedido.statusFinanceiro !== "Pago");
  const valorPago = pagos.reduce((acc, pedido) => acc + valorTotalPedido(pedido), 0);
  const valorPendente = pendentes.reduce((acc, pedido) => acc + valorTotalPedido(pedido), 0);
  const clientesFinanceiro = useMemo(() => {
    const mapa = new Map();
    pedidosFinanceiro.forEach((pedido) => {
      const nome = pedido.cliente || "Cliente não informado";
      if (!mapa.has(nome)) {
        mapa.set(nome, { nome, cidade: pedido.cidade || "", pedidos: [], total: 0, pago: 0, pendente: 0 });
      }
      const cliente = mapa.get(nome);
      const valor = valorTotalPedido(pedido);
      cliente.pedidos.push(pedido);
      cliente.total += valor;
      if (pedido.statusFinanceiro === "Pago") cliente.pago += valor;
      else cliente.pendente += valor;
    });
    return Array.from(mapa.values()).sort((a, b) => b.pendente - a.pendente || b.total - a.total);
  }, [pedidosFinanceiro]);
  const clienteSelecionado = clientesFinanceiro.find((cliente) => cliente.nome === clienteAberto);

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatCard label="NF emitida" value={pedidosComNF.length} />
        <StatCard label="Pagos" value={pagos.length} detail={currency(valorPago)} tone="green" />
        <StatCard label="Aguardando pagamento" value={pendentes.length} detail={currency(valorPendente)} tone="amber" />
        <StatCard label="Valor total NF" value={currency(valorPago + valorPendente)} />
      </section>

      <Card className="p-5">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <h2 className="text-xl font-bold">Financeiro por cliente</h2>
            <p className="text-sm text-slate-500">Cada quadro representa um cliente com NF emitida.</p>
          </div>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
            <Input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, pedido ou pagamento" />
            <SelectBox value={financeiroFiltro} onChange={setFinanceiroFiltro}>
              <option value="Todos">Todos pagamentos</option>
              {financeiroStatusList.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </SelectBox>
            <SelectBox value={tipoPagamentoFiltro} onChange={setTipoPagamentoFiltro}>
              {tiposPagamento.map((tipo) => (
                <option key={tipo} value={tipo}>
                  {tipo}
                </option>
              ))}
            </SelectBox>
          </div>
        </div>
      </Card>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {clientesFinanceiro.length === 0 && <EmptyState>Nenhum cliente financeiro no filtro atual.</EmptyState>}
        {clientesFinanceiro.map((cliente) => (
          <button
            key={cliente.nome}
            type="button"
            onClick={() => setClienteAberto(cliente.nome)}
            className="rounded-lg border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-teal-300 hover:shadow-md"
          >
            <div className="mb-3 flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-bold">{cliente.nome}</p>
                <p className="truncate text-xs text-slate-500">{cliente.cidade || "Cidade não informada"}</p>
              </div>
              <Badge className={cliente.pendente > 0 ? "border-amber-200 bg-amber-50 text-amber-800" : "border-green-200 bg-green-50 text-green-800"}>
                {cliente.pedidos.length}
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Total</p>
                <p className="font-bold text-slate-900">{currency(cliente.total)}</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-green-50 p-2">
                  <p className="text-xs text-green-700">Pago</p>
                  <p className="text-sm font-bold text-green-800">{currency(cliente.pago)}</p>
                </div>
                <div className="rounded-lg bg-amber-50 p-2">
                  <p className="text-xs text-amber-700">Pendente</p>
                  <p className="text-sm font-bold text-amber-800">{currency(cliente.pendente)}</p>
                </div>
              </div>
            </div>
          </button>
        ))}
      </section>

      {clienteSelecionado && (
        <Card className="p-5">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="text-xl font-bold">Detalhamento financeiro - {clienteSelecionado.nome}</h3>
              <p className="text-sm text-slate-500">Pedidos com NF emitida deste cliente.</p>
            </div>
            <Button onClick={() => setClienteAberto(null)} className="border border-slate-200 bg-white text-slate-700 hover:bg-slate-50">
              Fechar detalhes
            </Button>
          </div>

          <div className="space-y-3">
            {clienteSelecionado.pedidos.map((pedido) => (
              <PedidoCard
                key={pedido.id}
                pedido={pedido}
                layout="financeiro"
                atualizarFinanceiro={atualizarFinanceiro}
                excluirPedido={excluirPedido}
              />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

function LogisticaLayout({ pedidos, cargas, atualizarStatus, criarCarga, excluirPedido, salvando }) {
  const [busca, setBusca] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("Todos");
  const [regiaoCarga, setRegiaoCarga] = useState("");
  const [motoristaCarga, setMotoristaCarga] = useState("");
  const [placaCarga, setPlacaCarga] = useState("");
  const [pedidosCarga, setPedidosCarga] = useState([]);
  const statusLogistica = ["Todos", "Nota emitida", "Separado para entrega", "Enviado", "Finalizado"];
  const pedidosLogistica = useMemo(() => filtrarPedidos(pedidos, busca, statusFiltro, "Todos", "Logística"), [pedidos, busca, statusFiltro]);
  const aguardandoSeparacao = pedidos.filter((pedido) => pedido.status === "Nota emitida");
  const separados = pedidos.filter((pedido) => pedido.status === "Separado para entrega");
  const enviados = pedidos.filter((pedido) => pedido.status === "Enviado");
  const finalizados = pedidos.filter((pedido) => pedido.status === "Finalizado");
  const colunas = [
    { titulo: "Aguardando separação", status: "Nota emitida" },
    { titulo: "Separado para entrega", status: "Separado para entrega" },
    { titulo: "Enviado", status: "Enviado" },
    { titulo: "Finalizado", status: "Finalizado" },
  ];

  function togglePedidoCarga(id) {
    setPedidosCarga((prev) => (prev.includes(id) ? prev.filter((pedidoId) => pedidoId !== id) : [...prev, id]));
  }

  async function submitCarga() {
    if (!regiaoCarga || pedidosCarga.length === 0) {
      window.alert("Preencha a região e selecione ao menos um pedido.");
      return;
    }
    await criarCarga({
      regiao: regiaoCarga,
      motorista: motoristaCarga,
      placa: placaCarga,
      pedidoIds: pedidosCarga,
      statusDestino: "Separado para entrega",
    });
    setPedidosCarga([]);
    setRegiaoCarga("");
    setMotoristaCarga("");
    setPlacaCarga("");
  }

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatCard label="Aguardando separação" value={aguardandoSeparacao.length} tone="amber" />
        <StatCard label="Separados" value={separados.length} tone="sky" />
        <StatCard label="Enviados" value={enviados.length} tone="teal" />
        <StatCard label="Finalizados" value={finalizados.length} tone="green" />
      </section>

      <Card className="p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-bold">Logística</h2>
            <p className="text-sm text-slate-500">Separação, montagem de cargas e entrega.</p>
          </div>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-[260px_220px]">
            <Input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente, pedido ou transporte" />
            <SelectBox value={statusFiltro} onChange={setStatusFiltro}>
              {statusLogistica.map((status) => (
                <option key={status} value={status}>
                  {status === "Todos" ? "Todos status logística" : status}
                </option>
              ))}
            </SelectBox>
          </div>
        </div>
      </Card>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[420px_1fr]">
        <Card className="p-5">
          <h3 className="text-xl font-bold">Montagem de carga</h3>
          <p className="mb-4 text-sm text-slate-500">Agrupe pedidos com nota emitida ou já separados.</p>
          <div className="space-y-3">
            <Field label="Região / rota">
              <Input value={regiaoCarga} onChange={(e) => setRegiaoCarga(e.target.value)} placeholder="Norte PR, SC, SP" />
            </Field>
            <Field label="Motorista">
              <Input value={motoristaCarga} onChange={(e) => setMotoristaCarga(e.target.value)} placeholder="Nome do motorista" />
            </Field>
            <Field label="Placa">
              <Input value={placaCarga} onChange={(e) => setPlacaCarga(e.target.value)} placeholder="ABC-1234" />
            </Field>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h4 className="font-bold">Pedidos selecionados</h4>
                <Badge className="border-teal-200 bg-teal-50 text-teal-800">{pedidosCarga.length}</Badge>
              </div>
              <div className="max-h-72 space-y-2 overflow-auto pr-1">
                {pedidos
                  .filter((pedido) => ["Nota emitida", "Separado para entrega"].includes(pedido.status))
                  .map((pedido) => {
                    const selecionado = pedidosCarga.includes(pedido.id);
                    return (
                      <button
                        key={pedido.id}
                        type="button"
                        onClick={() => togglePedidoCarga(pedido.id)}
                        className={`w-full rounded-lg border p-3 text-left transition ${
                          selecionado ? "border-teal-500 bg-teal-50" : "border-slate-200 bg-white hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <strong>#{pedido.id}</strong>
                          <Badge className={statusColor(pedido.status)}>{pedido.status}</Badge>
                        </div>
                        <p className="text-sm text-slate-700">{pedido.cliente}</p>
                        <p className="text-xs text-slate-500">{pedido.cidade}</p>
                      </button>
                    );
                  })}
              </div>
            </div>
            <Button onClick={submitCarga} disabled={salvando} className="w-full bg-teal-700 text-white hover:bg-teal-800">
              <Truck size={16} />
              Criar carga
            </Button>
          </div>
        </Card>

        <CargasMontadas cargas={cargas} />
      </section>

      <section className="grid grid-cols-1 gap-5 xl:grid-cols-4">
        {colunas.map((coluna) => {
          const pedidosColuna = pedidosLogistica.filter((pedido) => pedido.status === coluna.status);
          return (
            <Card key={coluna.status} className="p-4">
              <div className="mb-4 flex items-center justify-between gap-2">
                <h3 className="text-lg font-bold">{coluna.titulo}</h3>
                <Badge className={statusColor(coluna.status)}>{pedidosColuna.length}</Badge>
              </div>
              <div className="space-y-3">
                {pedidosColuna.length === 0 && <EmptyState>Nenhum pedido aqui.</EmptyState>}
                {pedidosColuna.map((pedido) => (
                  <PedidoCard
                    key={pedido.id}
                    pedido={pedido}
                    layout="logistica"
                    atualizarStatus={atualizarStatus}
                    excluirPedido={excluirPedido}
                  />
                ))}
              </div>
            </Card>
          );
        })}
      </section>
    </div>
  );
}

function GestorLayout({ pedidos, cargas, atualizarStatus, excluirPedido }) {
  const [busca, setBusca] = useState("");
  const pedidosFiltrados = useMemo(() => filtrarPedidos(pedidos, busca, "Todos", "Todos", "Gestor"), [pedidos, busca]);
  const resumo = useMemo(() => calcularResumo(pedidos), [pedidos]);

  return (
    <div className="space-y-6">
      <ResumoCards pedidos={pedidos} />
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard label="Prontos para faturar" value={resumo.faturar} tone="green" />
        <StatCard label="Financeiro pendente" value={resumo.financeiroPendente} tone="amber" />
        <StatCard label="Cargas" value={cargas.length} tone="teal" />
      </section>
      <Card className="p-5">
        <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-bold">Visão geral</h2>
            <p className="text-sm text-slate-500">Todos os pedidos cadastrados no sistema.</p>
          </div>
          <Input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar pedido, cliente, produto ou status" className="md:w-96" />
        </div>
        <div className="space-y-3">
          {pedidosFiltrados.length === 0 && <EmptyState>Nenhum pedido encontrado.</EmptyState>}
          {pedidosFiltrados.map((pedido) => (
            <PedidoCard
              key={pedido.id}
              pedido={pedido}
              layout="gestor"
              atualizarStatus={atualizarStatus}
              excluirPedido={excluirPedido}
            />
          ))}
        </div>
      </Card>
    </div>
  );
}

export default function App() {
  const [perfil, setPerfil] = useState("Inteligência");
  const [pedidos, setPedidos] = useState([]);
  const [cargas, setCargas] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [produtosCatalogo, setProdutosCatalogo] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [notas, setNotas] = useState([]);
  const [historico, setHistorico] = useState([]);
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [error, setError] = useState("");

  async function loadData(showSpinner = true) {
    if (showSpinner) setLoading(true);
    setError("");
    try {
      const [
        pedidosResponse,
        cargasResponse,
        clientesResponse,
        produtosResponse,
        dashboardResponse,
        notasResponse,
        historicoResponse,
      ] = await Promise.all([
        api.listPedidos(),
        api.listCargas(),
        api.listClientes(),
        api.listProdutos(),
        api.getDashboard(),
        api.listNotas(),
        api.historicoRecente(),
      ]);
      setPedidos(pedidosResponse);
      setCargas(cargasResponse);
      setClientes(clientesResponse);
      setProdutosCatalogo(produtosResponse);
      setDashboard(dashboardResponse);
      setNotas(notasResponse);
      setHistorico(historicoResponse);
    } catch (err) {
      setError(err.message || "Não foi possível carregar os dados.");
    } finally {
      if (showSpinner) setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function runAction(action) {
    setSalvando(true);
    setError("");
    try {
      await action();
      return true;
    } catch (err) {
      setError(err.message || "Operação não concluída.");
      return false;
    } finally {
      setSalvando(false);
    }
  }

  async function criarPedido(payload) {
    return runAction(async () => {
      await api.createPedido(payload);
      await loadData(false);
    });
  }

  async function atualizarStatus(id, status) {
    await runAction(async () => {
      await api.updateStatus(id, status);
      await loadData(false);
    });
  }

  async function atualizarPedido(id, payload) {
    return runAction(async () => {
      await api.updatePedido(id, payload);
      await loadData(false);
    });
  }

  async function atualizarFinanceiro(id, statusFinanceiro) {
    await runAction(async () => {
      await api.updateFinanceiro(id, statusFinanceiro);
      await loadData(false);
    });
  }

  async function excluirPedido(id) {
    if (!window.confirm("Deseja realmente excluir este pedido?")) return;
    await runAction(async () => {
      await api.deletePedido(id);
      await loadData(false);
    });
  }

  async function criarCarga(payload) {
    await runAction(async () => {
      await api.createCarga(payload);
      await loadData(false);
    });
  }

  async function prepararNfe(pedidoId) {
    await runAction(async () => {
      await api.prepararNfe(pedidoId);
      await loadData(false);
    });
  }

  async function marcarNfeEmitida(notaId) {
    await runAction(async () => {
      await api.marcarNfeEmitida(notaId);
      await loadData(false);
    });
  }

  async function enviarNfeHomologacao(notaId) {
    await runAction(async () => {
      await api.enviarNfeHomologacao(notaId);
      await loadData(false);
    });
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 md:px-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <PackageCheck className="text-teal-700" size={26} />
              <h1 className="text-2xl font-bold tracking-tight">Giras Markaplast</h1>
            </div>
            <p className="mt-1 text-sm text-slate-500">Pedidos, produção, faturamento, financeiro e logística</p>
          </div>

          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            <Button onClick={loadData} disabled={loading} className="border border-slate-200 bg-white text-slate-700 hover:bg-slate-50">
              {loading ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
              Atualizar
            </Button>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-500">Área</span>
              <SelectBox value={perfil} onChange={setPerfil} className="w-56">
                {setores.map((setor) => (
                  <option key={setor} value={setor}>
                    {setor}
                  </option>
                ))}
              </SelectBox>
            </div>
          </div>
        </div>
        <nav className="mx-auto flex max-w-7xl gap-2 overflow-x-auto px-4 pb-3 md:px-6">
          {setores.map((setor) => (
            <button
              key={setor}
              type="button"
              onClick={() => setPerfil(setor)}
              className={`inline-flex items-center gap-2 whitespace-nowrap rounded-lg border px-3 py-2 text-sm font-semibold transition ${
                perfil === setor ? "border-teal-700 bg-teal-700 text-white" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              {perfilIcon(setor)}
              {setor}
            </button>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-7xl p-4 md:p-6">
        {error && (
          <div className="mb-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex min-h-[420px] items-center justify-center rounded-lg border border-slate-200 bg-white">
            <Loader2 size={28} className="animate-spin text-teal-700" />
          </div>
        ) : perfil === "Inteligência" ? (
          <InteligenciaLayout dashboard={dashboard} historico={historico} produtos={produtosCatalogo} />
        ) : perfil === "Clientes" ? (
          <ClientesLayout clientes={clientes} onRefresh={() => loadData(false)} salvando={salvando} />
        ) : perfil === "Estoque" ? (
          <EstoqueLayout produtos={produtosCatalogo} onRefresh={() => loadData(false)} />
        ) : perfil === "PCP/Logística" ? (
          <PCPLogisticaLayout
            pedidos={pedidos}
            cargas={cargas}
            atualizarStatus={atualizarStatus}
            atualizarPedido={atualizarPedido}
            criarCarga={criarCarga}
            excluirPedido={excluirPedido}
            salvando={salvando}
          />
        ) : perfil === "Faturamento" ? (
          <FaturamentoLayout pedidos={pedidos} atualizarStatus={atualizarStatus} excluirPedido={excluirPedido} />
        ) : perfil === "Financeiro" ? (
          <FinanceiroLayout pedidos={pedidos} atualizarFinanceiro={atualizarFinanceiro} excluirPedido={excluirPedido} />
        ) : perfil === "Fiscal" ? (
          <FiscalLayout
            pedidos={pedidos}
            notas={notas}
            prepararNfe={prepararNfe}
            marcarNfeEmitida={marcarNfeEmitida}
            enviarNfeHomologacao={enviarNfeHomologacao}
          />
        ) : perfil === "Logística" ? (
          <LogisticaLayout
            pedidos={pedidos}
            cargas={cargas}
            atualizarStatus={atualizarStatus}
            criarCarga={criarCarga}
            excluirPedido={excluirPedido}
            salvando={salvando}
          />
        ) : perfil === "Gestor" ? (
          <GestorLayout pedidos={pedidos} cargas={cargas} atualizarStatus={atualizarStatus} excluirPedido={excluirPedido} />
        ) : (
          <ComercialLayout
            pedidos={pedidos}
            clientes={clientes}
            criarPedido={criarPedido}
            atualizarStatus={atualizarStatus}
            excluirPedido={excluirPedido}
            salvando={salvando}
          />
        )}
      </main>
    </div>
  );
}
