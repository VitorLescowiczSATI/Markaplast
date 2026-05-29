# Deploy com Render + Cloudflare

Este guia assume que a empresa já tem um domínio existente na Cloudflare.

## Subdomínios recomendados

Use dois subdomínios:

```txt
app.seudominio.com.br  -> frontend Render
api.seudominio.com.br  -> backend Render
```

Exemplo:

```txt
app.markaplast.com.br
api.markaplast.com.br
```

## Render

1. Suba o repositório para o GitHub.
2. No Render, crie um Blueprint usando o `render.yaml`.
3. O Render criará:
   - `giras-db`
   - `giras-api`
   - `giras-web`
4. Em `giras-web`, adicione o custom domain do frontend:
   - `app.seudominio.com.br`
5. Em `giras-api`, adicione o custom domain da API:
   - `api.seudominio.com.br`
6. O Render mostrará os destinos DNS esperados, normalmente CNAMEs apontando para hosts `.onrender.com`.

## Cloudflare DNS

No painel DNS da Cloudflare, crie os registros:

```txt
Type: CNAME
Name: app
Target: giras-web.onrender.com
Proxy: DNS only durante a validação

Type: CNAME
Name: api
Target: giras-api.onrender.com
Proxy: DNS only durante a validação
```

Depois que o Render validar os domínios e emitir SSL, você pode manter `DNS only` ou ativar proxy Cloudflare. Se ativar proxy, use SSL/TLS em `Full` ou `Full (strict)`.

## Variáveis de ambiente

No `giras-web`:

```env
VITE_API_URL=https://api.seudominio.com.br
```

No `giras-api`:

```env
CORS_ORIGINS=https://app.seudominio.com.br,https://sistemainterno.markaplast.com.br
DATABASE_URL=<preenchido automaticamente pelo Render>
ENVIRONMENT=production
FISCAL_EMIT_ENABLED=false
FOCUS_NFE_TOKEN=
FOCUS_NFE_BASE_URL=https://api.focusnfe.com.br/v2
```

Quando for ativar NF-e em homologação:

```env
FISCAL_EMIT_ENABLED=true
FOCUS_NFE_TOKEN=<token_do_provedor>
```

## Checklist antes de liberar para uso real

- Validar login/autenticação antes de entregar para operação.
- Usar Postgres pago se o sistema for usado de verdade.
- Confirmar backup do banco no plano contratado.
- Validar CORS com o domínio final.
- Testar cadastro de pedido, reserva de estoque, pré-NF-e e finalização.
- Revisar dados fiscais com contador antes de habilitar emissão real.
