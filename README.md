# Giras Markaplast

Sistema inicial para controle de pedidos, produção, faturamento, financeiro e logística da Markaplast.

## Stack

- Frontend: React + Vite + Tailwind.
- Backend: FastAPI + SQLAlchemy.
- Banco: PostgreSQL.
- Deploy: Render Blueprint via `render.yaml`.

## O que o produto já entrega

- Cadastro de pedidos por área comercial, com vários itens (produto/modelo, cor, tampa, quantidade e preço) no mesmo pedido.
- Login com sessão expirada e acesso restrito à área de cada usuário.
- Perfil Administrador com acesso a todas as áreas e gestão de usuários.
- Cadastro de clientes com consulta de CEP via API.
- Cadastro de produtos/SKUs e controle de estoque.
- Reserva automática de estoque de todos os itens quando um pedido é criado.
- Baixa de estoque quando o pedido é finalizado.
- Histórico de alterações por pedido.
- Dashboard de gestão com status, vendedores, produtos, estoque crítico e alertas.
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
3. PCP movimenta o pedido entre Novo pedido, A produzir, Em produção e Prontos.
4. Logística direciona o pedido para retirada ou monta uma carga para envio.
5. Fiscal prepara a pré-NF-e e Faturamento emite a nota.
6. Financeiro marca o pagamento como pago ou pendente.

## Acessos iniciais

No primeiro boot, a API cria o usuário `admin` e um usuário para cada área: `inteligencia`, `comercial`, `clientes`, `estoque`, `pcp`, `logistica`, `faturamento`, `financeiro` e `fiscal`.

O perfil Administrador navega por todas as áreas sem trocar de sessão e pode cadastrar usuários, alterar perfis, ativar ou desativar acessos e redefinir senhas temporárias.

Todos recebem inicialmente a senha definida em `AUTH_INITIAL_PASSWORD`. A variável deve ser configurada antes do primeiro deploy e não altera senhas de usuários que já existam. As sessões expiram conforme `AUTH_TOKEN_MINUTES` (12 horas por padrão), e `AUTH_SECRET` deve ser um valor longo e aleatório.

No ambiente local do `docker compose`, a senha inicial de desenvolvimento é `Marka@2026`. Ela não deve ser reutilizada em produção.

## Observações técnicas

O backend cria as tabelas automaticamente na inicialização para facilitar o MVP. Antes de virar produção crítica, a próxima etapa correta é adicionar Alembic para migrations versionadas e recuperação/troca de senha pelo próprio usuário.
