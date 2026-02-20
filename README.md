# 🚛 FleetPred — Manutenção Preditiva de Frota

> Avaliação Intermediária · IA Generativa · UniSENAI

**Endpoint:** [https://f6bf-179-48-116-161.ngrok-free.app/](https://f6bf-179-48-116-161.ngrok-free.app/)  
**Repositório:** https://github.com/RoseBorges44/fleetpred

---

## O Problema

Quem trabalha com manutenção de frota pesada em mineração sabe: manutenção corretiva é o pesadelo da operação. Um caminhão fora de estrada que para no meio do ciclo de carregamento não é só o custo do reparo — é produção parada, fila na mina, replanejamento de despacho e, dependendo do componente, guincho de equipamento pesado que por si só já custa uma fortuna.

Já vi caminhão parar na rampa de acesso por desgaste de componente que a análise de óleo tinha apontado semanas antes — excesso de ferro indicando desgaste interno no motor, e ninguém cruzou a informação a tempo. O custo da corretiva foi umas 4x o que teria sido uma preventiva programada. E esse tipo de coisa acontece porque a informação existe — resultado de análise de óleo, histórico de troca de peças, horímetro acumulado — mas fica espalhada em planilhas, ordens de serviço e na cabeça do mecânico sênior.

O FleetPred é um sistema de manutenção preditiva que tenta resolver isso. O técnico reporta sintomas (vibração, temperatura alta, ruído, consumo anormal), o sistema cruza com o histórico daquele equipamento e de equipamentos parecidos na frota, e gera um diagnóstico com probabilidade de falha, prazo estimado e recomendação de ação.

Nessa versão (intermediária), a parte da IA está mockada — as respostas de diagnóstico são simuladas. Mas o mock já retorna JSON estruturado no formato exato que o LLM vai retornar na versão final, via function calling ou structured output.

### Por que esse problema?

Trabalho com manutenção de ativos móveis em mineração. Conheço o dia a dia: operador que reporta "caminhão sem força na rampa", mecânico que precisa traduzir isso pra um diagnóstico técnico, e gestor de manutenção que precisa decidir qual equipamento tirar de operação primeiro — sabendo que cada hora parada é produção perdida. O sistema tenta formalizar esse fluxo e dar visibilidade sobre a saúde da frota toda num lugar só.

---

## Como a IA vai ser integrada (versão final)

Hoje o arquivo `backend/mock_ai.py` tem um mapeamento estático de diagnósticos por sistema e sintoma. Na versão final, esse módulo vai ser substituído por chamadas à API de um LLM (provavelmente Claude via Anthropic SDK). O modelo vai receber:

- Os sintomas que o técnico reportou
- Histórico de manutenções daquele equipamento (puxado do SQLite)
- Dados de saúde dos componentes
- Padrões de falha de equipamentos com perfil parecido na frota

E vai retornar um JSON com probabilidade, horizonte de falha, peças sugeridas e economia estimada. O formato já tá definido no mock — foi pensado pra ser o schema do structured output.

Exemplo do que o mock retorna hoje (e que o LLM vai retornar depois):

```json
{
  "componente": "Sistema de Arrefecimento",
  "probabilidade_falha": 0.82,
  "horizonte_dias": 12,
  "severidade": "alta",
  "pecas_sugeridas": ["Válvula termostática", "Mangueira superior"],
  "economia_estimada": 5800,
  "base_historica": "3 veículos similares falharam com sintomas idênticos"
}
```

Isso não é texto livre — é dado estruturado que alimenta o calendário de manutenção, calcula ROI e prioriza a fila. Em mineração, a decisão de parar um caminhão pra manutenção compete com a meta de produção. O gestor não aceita "acho que pode ser o turbo" — precisa de: qual componente, qual a chance de falhar, em quantos dias, quanto custa agora vs. quanto custa se quebrar.

---

## Escolhas de Design

### FastAPI + React + SQLite

**FastAPI:** preciso servir JSON pro frontend e, no futuro, fazer chamadas assíncronas pra API do LLM. FastAPI tem async nativo e valida dados com Pydantic — importa porque o diagnóstico da IA vai vir como JSON tipado. Considerei Flask, mas perdia a validação automática e os docs gerados no `/docs` (ajudaram bastante no desenvolvimento pra testar as rotas).

**React + Vite:** o sistema tem 6 telas com navegação, formulários dinâmicos e gráficos. Pensei em Streamlit no começo — seria mais rápido — mas Streamlit não lida bem com navegação entre páginas nem com formulários condicionais (os sintomas mudam dependendo do sistema selecionado). Além disso, React + API se integra melhor com LLM no futuro: o backend chama o modelo e devolve resultado, frontend nem sabe como foi gerado.

**SQLite:** zero configuração, é um arquivo. Pra uma frota de 10-50 equipamentos com histórico, aguenta tranquilo. Em produção com múltiplos usuários simultâneos migraria pra Postgres, mas pro protótipo é pragmatismo.

### Tema escuro

Em operação de mina, o pessoal do despacho e CCO (centro de controle) fica em sala escura com múltiplas telas monitorando frota, britagem, carregamento. Tema escuro é padrão nesses ambientes — não é preferência estética, é condição de trabalho. Fundo escuro reduz fadiga visual e faz os indicadores de cor (verde/amarelo/vermelho) saltarem mais. O despachante precisa bater o olho e em 2 segundos saber quantos equipamentos estão críticos.

### Semáforo de cores (verde/amarelo/vermelho)

Qualquer pessoa de operação entende sem treinamento. Na manutenção de frota pesada, a decisão mais urgente é sempre: "qual equipamento eu tiro de operação primeiro?". O código de cores responde isso instantaneamente. É o mesmo padrão usado em sistemas de despacho de mina.

### Formulário condicional

Essa decisão vem direto do domínio. Na mineração, o operador reporta "caminhão sem força na rampa" e o mecânico precisa traduzir: é motor? Transmissão? Restrição no filtro de ar? Cada sistema tem seus sintomas. Separar por sistema no formulário imita o fluxo real de triagem — primeiro identifica o sistema, depois detalha o defeito. Isso também evita que o operador marque "vibração" sem dizer onde, o que não ajuda em nada o diagnóstico.

### Sidebar fixa

Considerei tabs no topo, mas com 6 telas fica apertado e não escala (se adicionar controle de pneus, gestão de operadores, análise de óleo...). Sidebar é padrão de sistemas de gestão e de despacho porque permite navegar rápido sem perder contexto.

### 6 tabelas no banco

Ocorrência, diagnóstico e manutenção são entidades diferentes com ciclos de vida diferentes. Técnico registra ocorrência (imediato), IA gera diagnóstico (processamento), gestor agenda manutenção (decisão). Juntar tudo numa tabela ia criar acoplamento e dificultar rastreabilidade. Alertas ficam separados porque podem vir de diagnósticos da IA ou de regras simples (ex: horímetro desde último óleo > limite).

### Mock com JSON estruturado

O mock não retorna texto livre. Retorna dict com campos tipados: probabilidade (float), horizonte (int), peças (array), economia (float). Simula exatamente o que vou pedir ao LLM via structured output. Quando trocar o mock pelo LLM, o resto do sistema não muda — só a fonte do diagnóstico. Esse era o objetivo.

---

## O que Funcionou

### Agente de codificação

Usei Claude Code pra gerar a maior parte do código.

**Estrutura do projeto:** pedi a estrutura de pastas e arquivos base (backend com FastAPI + rotas + banco, frontend com React). Veio certo de primeira — separação backend/frontend, imports corretos.

**CSS e tema:** o tema escuro com variáveis CSS ficou consistente. Pedi uma vez a paleta de cores e ele manteve em todos os componentes sem eu precisar corrigir.

**Schema do banco:** descrevi as tabelas em linguagem natural e gerou SQL com constraints (CHECK, FK) adequadas. As relações entre tabelas ficaram corretas.

**Abordagem incremental:** pedir uma camada por vez (banco → rotas → layout → tela por tela) funcionou muito melhor do que pedir tudo junto. Quando tentei pedir o frontend completo num prompt só, veio bagunçado.

---

## O que Não Funcionou

**allowedHosts do Vite:** o agente não configurou o Vite pra aceitar conexões externas. Quando subi o ngrok, dava "Blocked request — this host is not allowed". Levei um tempo até descobrir que precisava adicionar `allowedHosts: true` e `host: true` no `vite.config.js`. Nenhum dos prompts iniciais gerou isso.

**Seed data genérico:** tentei fazer o seed com problemas mais próximos de mineração (análise de óleo com partículas de ferro, desgaste de pneu off-road, superaquecimento em rampa) mas o agente gerou sintomas genéricos de caminhão rodoviário. Tive que revisar os termos pra ficarem mais coerentes.

**Prompt genérico demais:** quando pedi "faça o frontend completo com todas as telas" num prompt só, o resultado veio desorganizado — componentes misturados, layout quebrado. Funcionou muito melhor pedindo uma tela de cada vez com os detalhes do que eu queria em cada uma.

**OneDrive + Git:** meu projeto estava na pasta do OneDrive e o Git não conseguia deletar pastas porque o OneDrive travava os arquivos. Tive que fechar o OneDrive pra conseguir fazer operações no repositório.

**O que faria diferente:** teria planejado os dados do seed com mais cuidado antes de começar, pensando nos cenários reais de mineração desde o início. E não teria colocado o projeto dentro do OneDrive.

---

## Uso do Agente de Codificação

**Ferramenta:** Claude Code (CLI da Anthropic)

**Processo:** comecei com um esboço das telas (wireframe) antes de pedir código. Depois fui incrementalmente: backend primeiro (banco, seed, rotas), depois frontend tela por tela. Commit a cada módulo funcional.

**Prompts usados (resumo):**

1. Estrutura + schema do banco + seed data + mock IA → commit
2. Rotas da API (5 arquivos separados por domínio) → commit
3. Frontend base (layout, sidebar, CSS, api service) → commit
4. Dashboard + Ficha do Veículo → commit
5. Formulário de Ocorrência com campos condicionais → commit
6. Diagnóstico IA + Plano de Manutenção + Relatórios com gráficos → commit
7. Ajustes finais (start.sh, gitignore, favicon) → commit

**Proporção estimada:**
- Gerado pelo agente: ~80%
- Ajustado manualmente: ~15%
- Escrito do zero: ~5%

---

## Como Executar

**Pré-requisitos:** Python 3.10+ e Node.js 18+

```bash
git clone https://github.com/RoseBorges44/fleetpred.git
cd fleetpred

# Terminal 1 — Backend:
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend:
cd frontend
npm install
npm run dev

# Terminal 3 — Expor publicamente:
ngrok http 5173
```

**Acessar:** http://localhost:5173 (frontend) · http://localhost:8000/docs (API)

---

## Estrutura do Projeto

```
fleetpred/
├── backend/
│   ├── main.py              # App FastAPI, CORS, registro de rotas
│   ├── database.py          # Schema SQLite — 6 tabelas
│   ├── seed_data.py         # 10 caminhões com dados realistas
│   ├── mock_ai.py           # Diagnóstico simulado (substituir por LLM)
│   ├── requirements.txt
│   └── routes/
│       ├── veiculos.py      # Dashboard stats, lista, detalhe
│       ├── ocorrencias.py   # Registro + geração de diagnóstico
│       ├── manutencoes.py   # Agendadas + fila de prioridade
│       ├── relatorios.py    # Custos, disponibilidade, tendência
│       └── alertas.py       # Alertas + diagnóstico detalhado
├── frontend/
│   └── src/
│       ├── App.jsx          # Sidebar + rotas React Router
│       ├── index.css        # Tema escuro com CSS variables
│       ├── services/api.js  # Camada de comunicação com API
│       └── pages/           # 6 telas da aplicação
├── prompts/                 # System prompt (pra versão final)
├── tools/                   # Definição de ferramentas (pra versão final)
├── start.sh
├── .gitignore
└── README.md
```

---

## Próximos Passos (versão final)

- Trocar `mock_ai.py` por chamadas reais via Anthropic SDK
- System prompt com persona de engenheiro de confiabilidade de frota pesada
- Tools: consultar histórico, buscar padrões na frota, calcular economia preventiva vs. corretiva
- Temperatura baixa (diagnóstico precisa de consistência, não criatividade)
- Documentar todas as decisões de engenharia de LLM
