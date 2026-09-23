# Gimak PCP

Sistema de planejamento e controle de produção da Gimak, que fabrica e instala máquinas sob encomenda.

Roda no mesmo deploy da Markaplast, mas é outro produto: banco, login, usuários e interface próprios. Nada é compartilhado entre as duas empresas além da infraestrutura já contratada.

Endereço: https://gimak-pcp-web.onrender.com

## A dor que resolve

Antes, o andamento da fábrica vivia na cabeça das pessoas e no WhatsApp.

- Ninguém sabia o que cada um estava fazendo agora sem levantar e perguntar.
- Quando uma atividade parava, o motivo não ficava registrado em lugar nenhum. Se a diretoria perguntasse por que atrasou, a resposta dependia de alguém lembrar.
- O tempo gasto em cada etapa não era medido, então não dava para saber onde a montagem realmente consome as horas.
- Quem planeja não conseguia enxergar de bate-pronto se esqueceu de dar tarefa para alguém no dia.
- A assistência técnica, que é a maior parte do time, se organizava por mensagem solta. O que foi feito no cliente ficava numa ficha de papel, e o que ficou faltando se perdia até alguém lembrar.

O sistema centraliza isso em um lugar só, sem burocratizar o trabalho de quem está na bancada.

## O princípio: simples para quem executa

Essa foi a regra de projeto mais importante. Quem está na fábrica não é usuário de computador e não vai preencher formulário.

Para o operador, o sistema inteiro é: abrir a atividade, clicar em Iniciar, e no fim clicar em Concluir. Pausar e marcar como não realizada pedem uma justificativa em uma frase, porque é exatamente essa informação que faltava antes. Nada além disso.

Todo o resto, o registro de quem fez, a hora, o cronômetro, o histórico, os indicadores, o sistema deriva sozinho desses cliques. O operador nunca digita hora, nunca escolhe data, nunca preenche relatório de produção.

## As telas

### Painel da fábrica

O quadro do dia, em quatro colunas: A fazer, Em execução, Não realizado e Concluído. Filtra por colaborador e por hoje ou pela semana inteira.

Cada card mostra a ordem, o título, o projeto, o responsável, o prazo e o tempo já registrado. O card de quem está executando mostra o cronômetro correndo.

Abrir a atividade dá acesso aos botões de situação e ao histórico completo dela.

### Calendário

O que está marcado por dia, em dois modos.

- **Mês**: a grade do mês com tarefas e assistências, coloridas pela situação, com filtro por colaborador.
- **Semana por pessoa**: uma linha por quem executa e uma coluna por dia. O dia vazio fica hachurado. É assim que o PCP enxerga quem ficou sem tarefa antes do dia começar.

Assistência de mais de um dia ocupa todos os dias da viagem, marcada como 1/3, 2/3 e 3/3, para o técnico não parecer livre no meio dela.

### Projetos

Cada equipamento vendido é um projeto, com cliente e nome do equipamento. Abrindo, mostra o que ainda está pendente e o que já foi realizado, com o tempo gasto em cada etapa.

Projeto encerrado sai da lista de andamento e só volta pelo filtro de concluídos, com a data do encerramento. Dá para reabrir.

### Assistências e instalações

O trabalho feito fora da empresa, que na Gimak é a maior parte do time.

O PCP agenda informando tipo, cliente, endereço, técnico, data de ida, hora de sair da empresa, hora prevista de volta e, quando a visita passa de um dia, a data de volta.

O técnico abre, clica em "Estou saindo para o atendimento", e a situação vira **Em atendimento**, com a hora real da saída registrada. Na volta, ele escreve o relatório do que foi feito e conclui.

Se ficou alguma coisa faltando, ele registra a pendência ali mesmo, sem sair da tela e sem perder o relatório que está digitando.

### Pendências

Aba dentro de Assistências, com contador do que está aberto.

É o caso clássico: o técnico foi, resolveu, escreveu o relatório, mas faltou um componente que precisa entrar na máquina. Isso ia morrer no relatório. Agora vira um item que o administrador acompanha, escreve como foi resolvido e fecha.

### Modo TV

Painel somente leitura para a televisão do chão de fábrica. Mostra o que está em execução com cronômetro correndo, as pausas, o plano do dia, os projetos, o gráfico dos últimos sete dias e os últimos apontamentos.

Atualiza sozinho a cada trinta segundos, os cards alternam a cada quinze, cabe em uma tela em 1080p, 768p e 720p, e mantém a tela acesa.

### Indicadores

Tela do administrador. Entregas, taxa de conclusão, entregas no prazo, pendências vencidas, motivos de pausa, ranking por responsável e uso dos apontamentos por pessoa, com período selecionável.

Os critérios de cálculo ficam escritos na própria tela, porque número de produção sem o critério ao lado vira discussão.

### Apresentação pública

Rota aberta em `/apresentacao`, fora do login: uma página só, em rolagem, que explica a dor que o sistema resolve, o princípio de projeto, as sete telas, os perfis, o registro por dentro e a infraestrutura.

Serve para mandar o link para quem ainda não tem acesso. Vive em [Apresentacao.jsx](../gimak-frontend/src/Apresentacao.jsx) e é escolhida em `main.jsx` pelo caminho da URL, antes do app carregar. O Render reescreve qualquer rota para o `index.html`, então não precisa de configuração nova.

O quadro de exemplo no topo da página é dado de demonstração escrito à mão, não vem da API.

### Demonstração

Rota `/demo`: o sistema inteiro, com as mesmas telas, rodando com dados fictícios e sem falar com a API. Serve para mostrar o PCP a quem não pode ver os dados reais da fábrica.

- Nada sai do navegador. O [api.js](../gimak-frontend/src/api.js) troca a API real pela [demoApi.js](../gimak-frontend/src/demoApi.js) quando o caminho é `/demo`, com a mesma interface.
- Entra direto como administrador. O selo no canto troca de perfil (Administrador, PCP, Fábrica, TV) e tem o botão Recomeçar.
- O que a pessoa faz fica só no navegador dela e os dados são recriados todo dia, relativos à data de hoje, para o quadro do dia nunca ficar vazio.
- Na demonstração a marca é **PCP na mão** e a fábrica é a fictícia **Metalúrgica Modelo** (constante `MARCA` em [mode.js](../gimak-frontend/src/mode.js)). Fora de `/demo` continua Gimak.
- Um roteiro de três passos guia quem abre o link sozinho: iniciar uma tarefa (marcado sozinho quando acontece), ver como operador e abrir a TV. No celular aparece só o passo da vez.
- O botão "Quero na minha fábrica" abre o WhatsApp com mensagem pronta. O número fica em `CONTATO_WHATSAPP` no `mode.js`. Vazio, o botão não aparece.
- As regras de situação, cronômetro, permissões, indicadores e painel da TV são uma cópia em JavaScript do `api.py` e do `analytics.py`. **Mudou uma regra no backend, precisa mudar na demoApi.js também**, senão a demonstração mostra um sistema que não existe.

### Usuários

Só o administrador. Cria acesso, define perfil e cargo, corrige nome e redefine senha.

Corrigir o nome de alguém leva o histórico junto: as tarefas e assistências que estavam no nome antigo passam para o novo, senão o histórico ficaria órfão e fora do ranking.

## Perfis e permissões

| O que faz | Admin | PCP | Fábrica | TV |
|---|---|---|---|---|
| Ver quadro, projetos e assistências | sim | sim | sim | não |
| Apontar tarefa e concluir assistência | sim | sim | sim | não |
| Criar tarefa, projeto e assistência | sim | sim | não | não |
| Concluir e reabrir projeto | sim | sim | não | não |
| Registrar e resolver pendência | sim | sim | sim | não |
| Excluir tarefa, assistência e pendência | sim | não | não | não |
| Indicadores e gestão de usuários | sim | não | não | não |
| Modo TV | sim | sim | sim | só isso |

O perfil TV é uma conta cega, feita para ficar logada na televisão. Sessão de trinta dias e nenhum acesso a tarefa, projeto ou usuário.

## Como o registro funciona por dentro

Toda mudança de situação de uma tarefa grava um apontamento com a situação anterior, a nova, quem fez, quando e a justificativa quando existe. É daí que sai o histórico e é daí que saem os indicadores.

O cronômetro acumula em segundos. Iniciar marca o começo, pausar soma o intervalo ao acumulado, retomar recomeça a contagem. Clicar em Iniciar ou Concluir duas vezes não tem efeito, de propósito, para não mexer no tempo nem na data de conclusão. Já "Não realizada" pode ser reenviada, porque aí o objetivo é corrigir a justificativa.

## Arquitetura

```
API giras-api (a mesma da Markaplast)
├── Markaplast: /api/...
└── Gimak:      /api/gimak/...

PostgreSQL (a mesma instância)
├── banco giras      (Markaplast)
└── banco gimak_pcp  (Gimak)

Sites estáticos
├── giras-web       (Markaplast)
└── gimak-pcp-web   (Gimak)
```

- Stack igual à da Markaplast: FastAPI e SQLAlchemy no backend, React e Vite no frontend, PostgreSQL.
- Banco lógico separado na mesma instância. Nenhuma tabela e nenhum usuário em comum com a Markaplast.
- Autenticação própria, com segredo próprio (`GIMAK_AUTH_SECRET`).
- A inicialização da Gimak é isolada em um try no start da API: se falhar, registra no log e não impede a Markaplast de subir.
- Custo adicional de infraestrutura: zero. Reaproveita a API e o PostgreSQL já contratados, e o site estático do Render é gratuito.

### Evolução do banco

O banco da Gimak não usa Alembic. As tabelas nascem por `create_all`, que cria tabela nova mas nunca altera tabela existente.

Colunas acrescentadas depois do primeiro deploy entram por `ensure_gimak_columns`, no arquivo [db.py](../backend/app/gimak/db.py), que confere o que falta e aplica o `ALTER TABLE`. É o mesmo padrão que a Markaplast já usa em `ensure_runtime_migrations`.

Quem for mexer precisa saber disso: **acrescentar uma coluna no model não basta**, tem que registrar em `COLUNAS_ACRESCENTADAS` também, senão o deploy sobe e a tela quebra em produção.

## Variáveis de ambiente

| Variável | Para que serve |
|---|---|
| `GIMAK_DATABASE_NAME` | Nome do banco lógico. Padrão `gimak_pcp`. |
| `GIMAK_DATABASE_URL` | Opcional. Só se um dia a Gimak sair para um banco próprio. |
| `GIMAK_AUTH_SECRET` | Segredo do token, separado do da Markaplast. |
| `GIMAK_INITIAL_ADMIN_PASSWORD` | Senha do primeiro administrador. Sem ela o usuário `admin` não é criado. |
| `GIMAK_AUTH_TOKEN_MINUTES` | Duração da sessão. Padrão 720 minutos. O perfil TV ignora e usa trinta dias. |

## Rodar local

A partir de `backend/`:

```bash
GIMAK_INITIAL_ADMIN_PASSWORD='SuaSenha@123' PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --port 8000
```

Sem `DATABASE_URL` de Postgres, o backend cai em SQLite e a Gimak usa `gimak_dev.db`.

A partir de `gimak-frontend/`:

```bash
npm install && npm run dev
```

Testes da Gimak:

```bash
cd backend && PYTHONPATH=. .venv/bin/python -m pytest tests -q -k gimak
```

## Confirmar um deploy

O `/health` da API não traz o SHA do commit, então ele não prova que a versão nova subiu. O que prova:

- **API**: `curl -s https://giras-api.onrender.com/openapi.json` e procurar a rota ou o campo novo.
- **Frontend**: baixar o bundle `/assets/index-*.js` do site e procurar um texto que só existe na versão nova.
- **Banco da Gimak**: `curl -s https://giras-api.onrender.com/api/gimak/health`.

Atenção a uma janela real: o site estático fica pronto antes da API. Nesses poucos minutos a tela nova pode chamar uma rota que ainda não existe e o carregamento falha inteiro. Passa sozinho quando a API termina.

## O que ainda não existe

- Anexo de arquivo na tarefa, por exemplo a lista de corte de material. Depende de armazenamento de arquivo, que o plano atual não tem.
- Aplicativo no celular com notificação push e foto na assistência. As telas já funcionam bem no navegador do celular, o que falta é a notificação e o campo de foto.
- Mais de um responsável na mesma tarefa. Parado por decisão, até definir o que acontece quando um sai e o outro continua.
- Ranking visível para quem está na fábrica. Hoje o ranking existe, mas só o administrador enxerga.
