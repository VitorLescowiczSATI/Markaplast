# Roadmap

## MVP atual

- Cadastro de pedidos pelo Comercial.
- Fluxo de status separado por Comercial, PCP, Logística, Faturamento, Financeiro e Fiscal.
- Autenticação por usuário e perfil, com cada acesso restrito à sua área.
- Persistência em PostgreSQL.
- Montagem de cargas com pedidos vinculados.
- Deploy separado no Render para API, frontend e banco.
- Cadastro de clientes com consulta de CEP.
- Cadastro de produtos/SKUs.
- Estoque com reserva automática e baixa na finalização.
- Dashboard gerencial com gráficos simples.
- Pré-NF-e pronta para integração fiscal.
- Envio para Focus NFe em homologação quando token for configurado.

## Próximas melhorias recomendadas

1. Gestão de usuários, troca e recuperação de senha.
2. Migrations com Alembic antes de uso em produção real.
3. Cadastro fiscal completo do emitente, NCM, CFOP, CST/CSOSN e regras tributárias por produto.
4. Impressão real de etiquetas por carga.
5. Importação/exportação por Excel.
6. Relatórios comerciais e financeiros por período.
7. Webhooks fiscais para atualizar nota automaticamente.
8. WhatsApp/e-mail automático para vendedor, cliente e financeiro.
