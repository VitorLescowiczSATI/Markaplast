/** Filtro de período das telas de Projetos e Assistências: um mês, todos ou um intervalo de datas. */

export function mesAtual(hoje = new Date()) {
  return `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}`;
}

/** "2026-10-05" ou um ISO com hora vira "2026-10", sempre no fuso de quem está olhando. */
export function mesDe(valor) {
  if (!valor) return "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(valor)) return valor.slice(0, 7);
  return mesAtual(new Date(valor));
}

export function diaDe(valor) {
  if (!valor) return "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(valor)) return valor;
  const data = new Date(valor);
  return `${mesAtual(data)}-${String(data.getDate()).padStart(2, "0")}`;
}

function rotuloMes(mes) {
  const [ano, numero] = mes.split("-").map(Number);
  const texto = new Date(ano, numero - 1, 1).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

export const PERIODO_INICIAL = { modo: "mes", mes: mesAtual(), de: "", ate: "" };

/** Faixa [inicio, fim] em "AAAA-MM-DD" do período escolhido; null nas pontas abertas. */
export function faixaDoPeriodo(periodo) {
  if (periodo.modo === "mes") return [`${periodo.mes}-01`, `${periodo.mes}-31`];
  if (periodo.modo === "datas") return [periodo.de || null, periodo.ate || null];
  return [null, null];
}

/** O intervalo [inicio, fim] de um registro cruza o período? */
export function cruzaPeriodo(periodo, inicio, fim = inicio) {
  const [de, ate] = faixaDoPeriodo(periodo);
  if (!inicio) return periodo.modo === "todos";
  return (!ate || inicio <= ate) && (!de || (fim || inicio) >= de);
}

export function PeriodoFiltro({ periodo, onChange, meses }) {
  const opcoes = Array.from(new Set([mesAtual(), ...meses.filter(Boolean)])).sort((a, b) => b.localeCompare(a));
  const valor = periodo.modo === "mes" ? periodo.mes : periodo.modo;
  function escolher(novo) {
    if (novo === "todos" || novo === "datas") onChange({ ...periodo, modo: novo });
    else onChange({ ...periodo, modo: "mes", mes: novo });
  }
  return (
    <div className="periodo">
      <select aria-label="Período" value={valor} onChange={(event) => escolher(event.target.value)}>
        {opcoes.map((mes) => <option key={mes} value={mes}>{rotuloMes(mes)}</option>)}
        <option value="todos">Todos os meses</option>
        <option value="datas">Escolher datas</option>
      </select>
      {periodo.modo === "datas" && (
        <span className="periodo-datas">
          <input type="date" aria-label="De" value={periodo.de} onChange={(event) => onChange({ ...periodo, de: event.target.value })} />
          <span>até</span>
          <input type="date" aria-label="Até" value={periodo.ate} min={periodo.de || undefined} onChange={(event) => onChange({ ...periodo, ate: event.target.value })} />
        </span>
      )}
    </div>
  );
}
