# 🚛 FleetPred — Manutenção Preditiva de Frota

> Avaliação Intermediária · IA Generativa · UniSENAI

**Endpoint:** (https://f6bf-179-48-116-161.ngrok-free.app/)
**Repositório:** https://github.com/RoseBorges44/fleetpred

---

## O Problema

Quem trabalha com gestão de frota pesada sabe: manutenção corretiva é o pesadelo. Um caminhão que quebra na estrada não é só o custo do reparo — é frete atrasado, multa contratual, motorista parado, guincho, e às vezes perda de carga. Na prática, a maioria das frotas ainda funciona no modo reativo: quebrou, conserta. Ou no melhor caso, troca óleo e filtro a cada X km e torce pro resto.

O FleetPred é um sistema de manutenção preditiva que tenta resolver isso. A ideia é simples: o técnico reporta sintomas (vibração, temperatura alta, ruído), o sistema cruza com o histórico daquele veículo e de veículos parecidos na frota, e gera um diagnóstico com probabilidade de falha, prazo estimado e recomendação de ação.

Nessa versão (intermediária), a parte da IA está mockada — as respostas de diagnóstico são simuladas. Mas o mock já retorna JSON estruturado no formato exato que o LLM vai retornar na versão final, via function calling ou structured output.

### Por que esse problema?

Tenho familiaridade com manutenção de ativos móveis e o domínio de frotas pesadas. Conheço o dia a dia: técnico que descreve problema de um jeito, mecânico que interpreta de outro, gestor que precisa decidir qual caminhão parar primeiro. O sistema tenta formalizar esse fluxo e dar visibilidade sobre a saúde da frota toda num lugar só.

---

## Como a IA vai ser integrada (versão final)

Hoje o arquivo `backend/mock_ai.py` tem um mapeamento estático de diagnósticos por sistema e sintoma. Na versão final, esse módulo vai ser substituído por chamadas à API de um LLM (provavelmente Claude via Anthropic SDK). O modelo vai receber:

- Os sintomas que o técnico reportou
- Histórico de manutenções daquele veículo (puxado do SQLite)
- Dados de saúde dos componentes
- Padrões de falha de veículos com perfil parecido na frota

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

Isso não é texto livre — é dado estruturado que alimenta o calendário de manutenção, calcula ROI e prioriza a fila.

---

## Escolhas de Design

### FastAPI + React + SQLite

**FastAPI:** preciso servir JSON pro frontend e, no futuro, fazer chamadas assíncronas pra API do LLM. FastAPI tem async nativo e valida dados com Pydantic — importa porque o diagnóstico da IA vai vir como JSON tipado. Considerei Flask, mas perdia a validação automática e os docs gerados no `/docs` (ajudaram bastante no desenvolvimento pra testar as rotas).

**React + Vite:** o sistema tem 6 telas com navegação, formulários dinâmicos e gráficos. Pensei em Streamlit no começo — seria mais rápido — mas Streamlit não lida bem com navegação entre páginas nem com formulários condicionais (os sintomas mudam dependendo do sistema selecionado). Além disso, React + API se integra melhor com LLM no futuro: o backend chama o modelo e devolve resultado, frontend nem sabe como foi gerado.

**SQLite:** zero configuração, é um arquivo. Pra 10-50 caminhões com histórico, aguenta tranquilo. Em produção com múltiplos usuários simultâneos migraria pra Postgres, mas pro protótipo é pragmatismo.

### Tema escuro

Não é estética. Interfaces de monitoramento (centro de controle, sala de operações) usam tema escuro porque o operador fica olhando pra tela por horas. Fundo escuro reduz fadiga visual e faz os indicadores de cor (verde/amarelo/vermelho) saltarem mais. O gestor precisa bater o olho e em 2 segundos saber quantos caminhões estão críticos.

### Semáforo de cores (verde/amarelo/vermelho)

Qualquer pessoa de operação entende sem treinamento. A decisão mais urgente na gestão de frota é: "qual caminhão eu paro primeiro?". O código de cores responde isso instantaneamente.

### Formulário condicional

Essa decisão vem do domínio. Técnico reportando motor não tem os mesmos sintomas que técnico reportando freio. Lista única com 25 sintomas = formulário inutilizável = técnico preenchendo qualquer coisa. Separando por sistema, o formulário fica objetivo e os dados já chegam categorizados pra IA.

### Sidebar fixa

Considerei tabs no topo, mas com 6 telas fica apertado e não escala (se adicionar estoque de peças, motoristas, rotas...). Sidebar é padrão de ERP e sistemas de gestão porque permite navegar rápido sem perder contexto.

### 6 tabelas no banco

Ocorrência, diagnóstico e manutenção são entidades diferentes com ciclos de vida diferentes. Técnico registra ocorrência (imediato), IA gera diagnóstico (processamento), gestor agenda manutenção (decisão). Juntar tudo numa tabela ia criar acoplamento e dificultar rastreabilidade. Alertas ficam separados porque podem vir de diagnósticos da IA ou de regras simples (ex: km desde último óleo > 15.000).

### Mock com JSON estruturado

O mock não retorna texto livre. Retorna dict com campos tipados: probabilidade (float), horizonte (int), peças (array), economia (float). Simula exatamente o que vou pedir ao LLM via structured output. Quando trocar o mock pelo LLM, o resto do sistema não muda — só a fonte do diagnóstico. Esse era o objetivo.

---

## O que Funcionou

### Agente de codificação

Usei Claude Code pra gerar a maior parte do código.

**Estrutura do projeto:** pedi a estrutura de pastas e arquivos base. Veio certo de primeira — separação backend/frontend, imports corretos, tudo no lugar.

**CSS e tema:** o tema escuro com variáveis CSS ficou consistente. Pedi uma vez e ele manteve a mesma paleta em todos os componentes.

**Gráficos:** pedi os gráficos de tendência e custo com Recharts. Gerou com tooltip, legend e cores corretas. Economizou tempo porque a configuração do Recharts é bem verbosa.

**Schema do banco:** descrevi as tabelas em linguagem natural e gerou SQL com constraints (CHECK, FK) adequadas.

**Prompt que funcionou bem:**

Pedir incrementalmente — uma camada por vez (banco primeiro, depois rotas, depois frontend base, depois tela por tela) — deu resultados muito melhores do que pedir tudo junto.

---

## O que Não Funcionou

**Proxy do Vite:** o agente não configurou o `allowedHosts` no Vite pra funcionar com ngrok. Dava erro de "Blocked request" até adicionar `allowedHosts: true` e `host: true` manualmente no `vite.config.js`.

**Datas hardcoded no seed:** as manutenções agendadas tinham datas fixas. Tive que conferir se estavam na semana corrente pro calendário não ficar vazio.

**Prompt genérico:** quando pedi "faça o frontend completo" num prompt só, o resultado veio desorganizado. Funcionou muito melhor pedindo uma tela por vez.

**O que faria diferente:** teria planejado os mocks de dados com mais cuidado antes de começar. Perdi tempo ajustando dados que não faziam sentido no contexto.

---

## Uso do Agente de Codificação

**Ferramenta:** Claude Code (CLI)

**Processo:** comecei com um esboço das telas antes de pedir código. Depois fui incrementalmente: backend primeiro (banco, seed, rotas), depois frontend tela por tela. Commit a cada módulo.

**Prompts usados (resumo):**

1. Estrutura do projeto + schema do banco + seed data + mock IA
2. Rotas da API (5 arquivos de rotas separados)
3. Frontend base (layout, sidebar, CSS, api service)
4. Dashboard + Ficha do Veículo
5. Formulário de Ocorrência (com campos condicionais)
6. Diagnóstico IA + Plano de Manutenção + Relatórios
7. Ajustes finais (start.sh, gitignore)

**Proporção:**
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
- System prompt com persona de especialista em manutenção de frota
- Tools: consultar histórico, buscar padrões na frota, calcular economia
- Temperatura baixa (diagnóstico precisa de consistência, não criatividade)
- Documentar todas as decisões de engenharia de LLM
