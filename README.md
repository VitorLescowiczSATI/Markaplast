# Giras Markaplast

Sistema inicial para controle de pedidos, produção, faturamento, financeiro e logística da Markaplast.

## Stack

- Frontend: React + Vite + Tailwind.
- Backend: FastAPI + SQLAlchemy.
- Banco: PostgreSQL.
- Deploy: Render Blueprint via `render.yaml`.

## O que o produto já entrega

- Cadastro de pedidos por área comercial.
- Cadastro de clientes com consulta de CEP via API.
- Cadastro de produtos/SKUs e controle de estoque.
- Reserva automática de estoque quando um pedido é criado.
- Baixa de estoque quando o pedido é finalizado.
- Histórico de alterações por pedido.
- Dashboard de gestão com status, vendedores, produtos, estoque crítico e alertas.
- Alertas automáticos de estoque, financeiro, faturamento, PCP e logística.
- Pré-NF-e com payload fiscal preparado para provedor externo.
- Integração fiscal opcional com Focus NFe em homologação, bloqueada por padrão até configurar token.

## Rodar local com Docker

```bash
docker compose up --build
```

Depois acesse:

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Health check: http://localhost:8000/health

## Rodar local sem Docker

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

## Deploy no Render

1. Crie um repositório no GitHub com estes arquivos.
2. No Render, crie um novo Blueprint e selecione o repositório.
3. O Render vai ler o `render.yaml` e criar:
   - `giras-db`: PostgreSQL.
   - `giras-api`: backend FastAPI.
   - `giras-web`: frontend estático.
4. Depois do primeiro deploy, confirme se as URLs batem com as variáveis:
   - `VITE_API_URL` no `giras-web` deve apontar para a URL pública do `giras-api`.
   - `CORS_ORIGINS` no `giras-api` deve apontar para a URL pública do `giras-web`.

Para usar domínio existente com Cloudflare, siga o guia em `docs/DEPLOY_RENDER_CLOUDFLARE.md`.

## Integrações

### CEP

O backend expõe `GET /api/integracoes/cep/{cep}`. Ele consulta ViaCEP primeiro e usa BrasilAPI como fallback. Isso evita expor chamadas externas diretamente no frontend e facilita trocar fornecedor depois.

### NF-e

O módulo fiscal cria uma pré-NF-e a partir do pedido em `POST /api/fiscal/pedidos/{pedido_id}/preparar-nfe`.

O envio real para Focus NFe fica bloqueado por padrão. Para homologação:

```env
FISCAL_EMIT_ENABLED=true
FOCUS_NFE_TOKEN=token_da_focus
FOCUS_NFE_BASE_URL=https://api.focusnfe.com.br/v2
```

Depois disso, use `POST /api/fiscal/notas/{nota_id}/enviar-homologacao`.

Antes de produção fiscal real, valide com contador: certificado A1, emitente, IE, regime tributário, NCM, CFOP, CST/CSOSN, IPI, PIS/COFINS e regras do estado.

## Fluxo operacional

1. Comercial cadastra o pedido.
2. O sistema cria/atualiza o cliente e reserva estoque do SKU.
3. PCP/Logística movimenta o pedido entre Novo pedido, Vai produzir e Em produção.
4. PCP/Logística monta a carga e libera para Pronto para faturar.
5. Fiscal prepara a pré-NF-e e Faturamento emite a nota.
6. Financeiro marca o pagamento como pago ou pendente.
7. Logística separa, envia e finaliza o pedido, baixando o estoque reservado.

## Observações técnicas

O backend cria as tabelas automaticamente na inicialização para facilitar o MVP. Antes de virar produção crítica, a próxima etapa correta é adicionar Alembic para migrations versionadas e autenticação por usuário/perfil.
