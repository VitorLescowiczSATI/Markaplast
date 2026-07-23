## Resumo
Primeira leva do MVP Markaplast: as mudanças de UI pedidas + as fundações de valor (preço automático por cliente, catálogo estruturado com travas de entrada e BI de metas). São 4 lotes, cada um validado (testes + smoke).

## O que entra
### UI quick wins
- Remove a aba/menu "Gestor"
- Comercial: cards compactos (clica pra expandir); pedidos Cancelado/Faturado somem da view principal (só via filtro); filtro por intervalo de datas
- PCP: cards compactos

### Preço por cliente
- Nova tabela `precos_cliente` + API `/api/precos` (list/lookup/upsert/delete)
- Pedido auto-preenche valor da embalagem/tampa ao escolher cliente + produto
- Gestão de preço por produto na tela de Clientes

### Catálogo estruturado + travas
- Produto ganha capacidade/modelo/peso/alça (migração aditiva + backfill derivado do nome)
- Cor e Tampa viram dropdown obrigatório; validação lista os campos faltando

### BI com metas + duplicar pedido
- Nova tabela `metas` + API `/api/metas`
- Inteligência reformulada: barras de meta (empresa dia/mês/trimestre + por vendedor); remove Alertas/Estoque crítico/Auditoria/Top produtos
- Botão "Repetir último pedido deste cliente"

## Migrações
Aditivas e automáticas no startup (`create_all` p/ tabelas novas; `_add_missing_columns` p/ colunas de produto). Nada destrutivo.

## Testes
- Backend: pytest 16/16 + smokes HTTP (preços, catálogo, metas)
- Frontend: build limpo + vitest 5/5

## Fora deste PR (próximos)
- PCP/Logística: separar + reordenar (logística antes do faturamento)
- Logins / RBAC
- Trocar as listas placeholder de cor/tampa pelas reais

🤖 Generated with [Claude Code](https://claude.com/claude-code)
