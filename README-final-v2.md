# 🚛 FleetPred — Manutenção Preditiva de Frota com IA Multi-Agente

> Avaliação Final · IA Generativa · UniSENAI  
> Rosemeri Janiski Bida de Oliveira Borges

**Repositório:** https://github.com/RoseBorges44/fleetpred  
**Endpoint:** [COLAR LINK NGROK OU RAILWAY]

---

## O Problema

Quem trabalha com manutenção de frota pesada em mineração sabe: manutenção corretiva é o pesadelo da operação. Um caminhão fora de estrada que para no meio do ciclo de carregamento não é só o custo do reparo — é produção parada, fila na mina, replanejamento de despacho e guincho de equipamento pesado.

Já vi caminhão parar na rampa de acesso por desgaste de componente que a análise de óleo tinha apontado semanas antes — excesso de ferro indicando desgaste interno no motor, e ninguém cruzou a informação a tempo. O custo da corretiva foi umas 4x o que teria sido uma preventiva programada.

O FleetPred resolve isso com IA generativa: o técnico reporta sintomas, um sistema multi-agente analisa o problema de 4 ângulos diferentes (diagnóstico técnico, histórico, planejamento e financeiro), e entrega uma recomendação estruturada com probabilidade de falha, prazo e ROI.

---

## Arquitetura de LLM

### Fluxo completo

```
Técnico reporta ocorrência (via formulário web)
        ↓
   POST /api/ocorrencias/
        ↓
  ┌─────────────────────┐
  │    ORQUESTRADOR      │  ← Avalia severidade, decide quais agentes chamar
  │  (LangGraph + Gemini)│
  └──────────┬──────────┘
             ↓
  ┌──────────────────────────────┐
  │  Execução paralela:          │
  │                              │
  │  [DIAGNOSTICADOR]            │  ← Analisa sintomas + saúde componentes
  │    tool: consultar_saude     │
  │    temp: 0.2                 │
  │                              │
  │  [HISTORIADOR]               │  ← Busca padrões na frota e histórico
  │    tools: historico, padroes │
  │    temp: 0.1                 │
  └──────────────┬───────────────┘
                 ↓
       Severidade alta/crítica?
          ┌──────┴──────┐
         SIM           NÃO
          ↓              ↓
  [PLANEJADOR]     [CONSOLIDAR]
    temp: 0.3           ↓
       ↓           JSON final
  [FINANCEIRO]
    tool: calcular_economia
    temp: 0.1
       ↓
  [CONSOLIDAR]
       ↓
  JSON final → Salva no banco → Cria alerta → Retorna pro frontend
```

### Por que multi-agente e não um LLM só

Na manutenção real de mineração, o diagnóstico não é feito por uma pessoa. É um fluxo entre especialistas: o técnico de campo reporta, o analista de dados cruza com histórico, o planejador decide prioridade, o financeiro justifica o custo. Cada um olha o mesmo problema de um ângulo diferente.

Um prompt único com "analise isso tudo" gera respostas genéricas. Separar em agentes permite:
- Cada agente ter persona e restrições específicas
- O historiador buscar dados reais do banco (via tools) antes do diagnosticador opinar
- Executar diagnosticador e historiador em paralelo (menor latência)
- Acionar planejador e financeiro apenas quando necessário (economia de tokens)
- Isolar falhas — se o financeiro der erro, o diagnóstico técnico ainda funciona

### Por que LangGraph

| Framework | Problema |
|---|---|
| **API direta** | Funciona pra 1 agente, mas não tem orquestração de múltiplos agentes com estado compartilhado |
| **LangChain** | Bom pra chains lineares, mas não tem grafo condicional (bifurcar por severidade) |
| **CrewAI** | Mais alto nível mas menos controle sobre o fluxo e estado |
| **LangGraph** ✅ | Grafo com nós condicionais, execução paralela, estado tipado, fallback por nó |

LangGraph permite definir o fluxo como grafo — o orquestrador decide quais agentes chamar dependendo da severidade. Caso crítico aciona todos. Caso leve pula planejador e financeiro.

### Por que Gemini

| Critério | Gemini | Claude | GPT |
|---|---|---|---|
| Custo | Gratuito (free tier) | Pago | Pago |
| Tool calling | ✅ Nativo | ✅ Robusto | ✅ Robusto |
| Context window | 1M tokens | 200K | 128K |
| Velocidade | Rápido (flash) | Médio | Médio |
| Uso pós-curso | ✅ Sem custo | ❌ Precisa pagar | ❌ Precisa pagar |

**Trade-off honesto:** Claude tem structured output mais robusto e o tool calling é mais preciso. Em produção, provavelmente migraria pra Claude. Mas Gemini gratuito viabiliza uso contínuo sem custo — o que o professor pediu (algo que usemos depois do curso acabar). Com o context window de 1M tokens, cabe o histórico inteiro da frota sem precisar de RAG.

---

## System Prompts

Cada agente tem seu próprio system prompt em `prompts/`. A separação é proposital — prompts diferentes permitem persona, restrições e formato diferentes por especialidade.

### Orquestrador (`prompts/orchestrator.txt`)

**Persona:** Coordenador de diagnóstico de frota em mineração.  
**Função:** Recebe a ocorrência, decide quais agentes acionar com base na severidade, e consolida o resultado final num JSON único.  
**Por que existe:** Sem orquestrador, os agentes não sabem em que ordem rodar nem quando parar. O orquestrador implementa a lógica de negócio: severidade alta/crítica aciona todos os agentes, severidade baixa pula planejador e financeiro.  
**Formato de saída:** JSON estrito com os campos que o frontend espera (componente, probabilidade_falha, horizonte_dias, etc.). A instrução "APENAS com o JSON final, sem texto antes ou depois" existe porque sem ela o modelo às vezes coloca explicações antes do JSON e o `json.loads()` quebra.

### Diagnosticador (`prompts/diagnostician.txt`)

**Persona:** Engenheiro de confiabilidade sênior, 15 anos de experiência em frotas pesadas em mineração.  
**Função:** Analisa os sintomas no contexto técnico do veículo (modelo, motor, km, saúde dos componentes).  
**Restrições críticas (XML tags):**
- Se probabilidade > 60%, nunca recomende "continuar operando" → veículo com 60%+ de chance de falhar não pode rodar em rampa de mina
- Sistemas de segurança (freios, direção, suspensão): severidade mínima "alta" → em mineração, falha de freio em rampa é fatal
- Dados insuficientes → recomende inspeção presencial (melhor ser conservador)

**Por que XML tags nas restrições:** Claude e Gemini processam melhor instruções quando a estrutura é explícita. Testei sem tags e o modelo misturava dados do veículo com instruções de formato. Com `<restricoes>...</restricoes>` cada bloco fica isolado.

### Historiador (`prompts/historian.txt`)

**Persona:** Analista de dados de frota.  
**Função:** Busca no banco de dados o histórico deste veículo e padrões em veículos similares.  
**Por que é um agente separado:** O diagnosticador não sabe o que aconteceu com outros caminhões da frota. Se 3 Scanias DC13 falharam o turbo entre 300-350 mil km, essa informação é ouro pro diagnóstico. O historiador busca esses padrões via tools e alimenta o orquestrador.

### Planejador (`prompts/planner.txt`)

**Persona:** Gestor de manutenção de frota em mineração.  
**Função:** Define urgência (horas/dias), tipo de manutenção, prioridade na fila e tempo estimado de reparo.  
**Por que temperatura 0.3 (a mais alta):** Planejamento envolve ponderar trade-offs — "paro agora e perco 4h de produção, ou arrisco mais 3 dias e faço no fim de semana?". Precisa de flexibilidade na formulação, diferente do diagnóstico técnico que é mais objetivo.

### Financeiro (`prompts/financial.txt`)

**Persona:** Analista de custos de manutenção.  
**Função:** Calcula ROI de agir preventivamente. Em mineração, inclui custo de hora de caminhão parado (~R$ 800-1.200/h), guincho (~R$ 3.000-8.000), replanejamento de despacho.  
**Por que existe:** Gestor de frota em mineração decide com base em custo. "Troque a válvula" é recomendação técnica. "Troque agora por R$ 2.400 ou arrisque R$ 12.000 de corretiva na mina" é recomendação de negócio.

---

## Ferramentas (Tools)

Definidas em `tools/tool_definitions.json` e implementadas em `backend/tools/fleet_tools.py`.

### 1. `consultar_saude_componentes(veiculo_id)`

**O que faz:** Retorna saúde (0-100%) de cada componente do veículo.  
**Por que o LLM precisa:** Sem essa tool, o modelo não sabe que o sistema de arrefecimento do ABC-1234 está em 58%. O mesmo sintoma num componente com 90% de saúde vs 45% muda completamente o diagnóstico.  
**Quem usa:** Diagnosticador.

### 2. `consultar_historico_veiculo(veiculo_id, limite)`

**O que faz:** Busca últimas N manutenções do veículo (tipo, data, custo, peças).  
**Por que o LLM precisa:** Um veículo que já trocou turbo 2 vezes pode indicar problema na causa raiz, não no componente. Sem histórico, diagnóstico é genérico.  
**Quem usa:** Historiador.

### 3. `buscar_padroes_frota(sistema, sintomas)`

**O que faz:** Busca ocorrências de outros veículos com mesmo sistema e sintomas semelhantes.  
**Por que o LLM precisa:** Essa tool transforma o sistema de "chatbot de manutenção" em "preditivo de verdade". Se 3 veículos similares falharam com os mesmos sintomas, a probabilidade de falha sobe.  
**Quem usa:** Historiador.  
**Por que separada de consultar_historico:** Uma olha o veículo específico, outra olha a frota toda. Nem sempre precisa das duas.

### 4. `calcular_economia(sistema, componente, modelo_veiculo)`

**O que faz:** Compara custo de preventiva agora vs. corretiva eventual (incluindo guincho, produção parada).  
**Por que é uma tool e não hardcoded:** Custos variam por modelo, componente e região. A tool consulta dados reais do banco quando disponíveis e usa estimativas de mercado como fallback.  
**Quem usa:** Financeiro.

### Por que as descriptions incluem "quando usar"

Testei com descriptions genéricas ("busca dados do veículo") e o modelo chamava todas as tools em sequência, sempre. Com descriptions que dizem quando usar ("Use para embasar o diagnóstico com dados reais da frota"), o modelo passou a ser seletivo — só chama quando relevante.

---

## Parâmetros do Modelo

| Agente | Modelo | Temperatura | Por quê |
|---|---|---|---|
| Diagnosticador | gemini-2.0-flash | 0.2 | Diagnóstico técnico precisa de consistência. Mesmos sintomas → mesmo diagnóstico. |
| Historiador | gemini-2.0-flash | 0.1 | Consulta e interpreta dados. Deve ser o mais determinístico possível. |
| Planejador | gemini-2.0-flash | 0.3 | Precisa ponderar trade-offs (segurança vs. disponibilidade). Um pouco mais de flexibilidade. |
| Financeiro | gemini-2.0-flash | 0.1 | Números precisam ser consistentes. R$ 5.800 não pode virar R$ 12.000 na próxima chamada. |
| Orquestrador | gemini-2.0-flash | 0.2 | Coordena fluxo e consolida. Precisa de consistência no formato JSON. |

**Por que temperatura baixa em geral:** Diagnóstico de manutenção não é criativo. Se o técnico reporta os mesmos sintomas duas vezes, o sistema precisa dar o mesmo diagnóstico (ou muito parecido). Temperatura alta (0.7+) fazia o modelo variar a probabilidade entre 65% e 88% pro mesmo caso — inaceitável pra um sistema de decisão.

**Por que gemini-2.0-flash:** É o modelo gratuito mais rápido. O multi-agente faz 3-5 chamadas por diagnóstico — latência importa. O modelo "pro" é mais preciso mas pago e mais lento. Para o caso de uso (diagnóstico estruturado com tools), flash é suficiente.

**O que testei:**
- Temperatura 0: totalmente determinístico, mas recomendações ficavam robotizadas ("Substituir componente X. Agendar para data Y.")
- Temperatura 0.2: consistência nos números, leve variação na redação
- Temperatura 0.7: probabilidades variavam demais entre chamadas idênticas

---

## Escolha de Framework

### Por que LangGraph e não alternativas

**API direta (google-generativeai):** Funciona pra um agente. Pra multi-agente, eu teria que implementar manualmente: orquestração, passagem de contexto entre agentes, execução condicional, tratamento de erro por agente. LangGraph já tem tudo isso.

**LangChain sozinho:** Bom pra chains lineares (entrada → processamento → saída). Mas meu fluxo tem bifurcação condicional (severidade alta aciona mais agentes) e execução paralela (diagnosticador e historiador rodam ao mesmo tempo). LangChain não tem grafo nativo.

**CrewAI:** Mais alto nível, menos código. Mas menos controle sobre o fluxo e o estado compartilhado entre agentes. Em LangGraph, eu defino exatamente quais dados cada nó recebe e passa adiante.

**LangGraph:** Grafo com nós tipados, edges condicionais, execução paralela nativa, e StateGraph que mantém o estado entre agentes. Cada agente é um nó, cada transição é um edge, e a condição de bifurcação é uma função Python pura.

---

## Fallback e Tratamento de Erros

O sistema tem fallback em cascata:

1. Orquestrador tenta chamar os agentes com Gemini
2. Se Gemini falhar (timeout, quota, erro de parsing), cai pro `mock_ai.py` original
3. O mock retorna diagnóstico estático (mesma estrutura JSON) — sistema nunca quebra

```python
try:
    diagnostic = orchestrate(veiculo_id, sistema, sintomas, ...)
except Exception as e:
    print(f"LLM falhou, usando mock: {e}")
    diagnostic = generate_mock_diagnostic(sistema, sintomas, km)
```

O professor pode verificar isso desligando a internet e submetendo uma ocorrência — o diagnóstico ainda funciona (via mock).

---

## O que Funcionou

**Multi-agente com contexto compartilhado:** O historiador busca padrões na frota e o diagnosticador usa essa informação pra ajustar a probabilidade. Isso gera diagnósticos mais fundamentados do que um LLM único.

**Fallback pro mock:** Quando a API do Gemini atingiu o rate limit, o sistema continuou funcionando com o mock. Pra um sistema de produção, esse tipo de resiliência é essencial.

**Separação de responsabilidades:** Cada agente tem um prompt enxuto e focado. Prompt do diagnosticador não precisa saber sobre custos, prompt do financeiro não precisa saber sobre sintomas técnicos. Isso melhora a qualidade de cada resposta.

**Tools consultando o banco real:** Os diagnósticos são baseados em dados concretos (histórico de manutenções, saúde dos componentes), não em conhecimento genérico do LLM.

---

## O que Não Funcionou

**Rate limit do Gemini:** O tier gratuito tem limites apertados. Em testes intensivos, a cota esgotou e o sistema caiu pro fallback. Em produção, precisaria de um plano pago ou modelo local.

**Parsing de JSON:** O Gemini às vezes retorna markdown (```json ... ```) em volta do JSON, ou adiciona texto explicativo antes. Tive que implementar parsing manual que procura `{` e `}` no texto pra extrair o JSON.

**Latência do multi-agente:** 3-5 chamadas sequenciais ao Gemini somam 10-30 segundos. Pro usuário, é perceptível. Amenizei com execução paralela (diagnosticador + historiador ao mesmo tempo), mas ainda é mais lento que o mock.

**Tool calling com Gemini:** O tool calling do Gemini é menos robusto que o do Claude. Às vezes ignora tools disponíveis e "adivinha" dados que deveria ter buscado. Simplifiquei as descriptions das tools pra serem mais diretas.

---

## Como Executar

### Pré-requisitos
- Python 3.10+
- Node.js 18+
- Chave de API do Google Gemini (gratuita em https://aistudio.google.com/apikey)

### Instalação

```bash
git clone https://github.com/RoseBorges44/fleetpred.git
cd fleetpred

# Configurar API key
cp backend/.env.example backend/.env
# Editar backend/.env e colocar sua GEMINI_API_KEY

# Terminal 1 — Backend:
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --port 8000

# Terminal 2 — Frontend:
cd frontend
npm install
npm run dev
```

### Testar o Multi-Agente

1. Abrir http://localhost:5173
2. Ir em **"Registro Ocorrência"**
3. Selecionar veículo **ABC-1234** (Scania R450, status crítico)
4. Km: **342100**
5. Sistema: **Motor**
6. Marcar: **"Vibração anormal"** e **"Perda de potência"**
7. Severidade: **Alta**
8. Clicar **"Enviar Ocorrência"**

**No terminal do backend** deve aparecer:
```
[Orchestrator] Iniciando diagnóstico — veículo 1, sistema Motor
[Orchestrator] Veículo 1 — modelo: Scania R450
[Diagnosticador] Analisando sintomas: ['Vibração anormal', 'Perda de potência']
[Historiador] Buscando histórico do veículo 1
[Historiador] Buscando padrões na frota: Motor
[Planejador] Definindo urgência (severidade: alta)
[Financeiro] Calculando economia
[Orchestrator] Diagnóstico consolidado em Xs
```

**Na tela** deve aparecer o diagnóstico com:
- Componente identificado (ex: Turbocompressor)
- Probabilidade de falha (ex: 82%)
- Horizonte em dias (ex: 12)
- Peças sugeridas
- Economia estimada
- JSON completo da resposta

### Testar o Fallback

1. Renomear `backend/.env` pra `backend/.env.bak` (desativa a API key)
2. Reiniciar o backend
3. Submeter uma ocorrência
4. Deve funcionar usando o mock (terminal mostra "Usando fallback mock_ai")
5. Restaurar: renomear de volta pra `.env`

---

## Estrutura do Projeto

```
fleetpred/
├── backend/
│   ├── main.py              # FastAPI, CORS, registro de rotas
│   ├── database.py          # Schema SQLite — 6 tabelas
│   ├── seed_data.py         # 10 caminhões com dados realistas
│   ├── mock_ai.py           # Fallback quando LLM falha
│   ├── .env.example         # Template da API key
│   ├── requirements.txt
│   ├── agents/              # Sistema multi-agente
│   │   ├── orchestrator.py  # Orquestrador LangGraph
│   │   ├── diagnostician.py # Agente diagnosticador (temp 0.2)
│   │   ├── historian.py     # Agente historiador (temp 0.1)
│   │   ├── planner.py       # Agente planejador (temp 0.3)
│   │   ├── financial.py     # Agente financeiro (temp 0.1)
│   │   └── llm_config.py   # Config Gemini
│   ├── tools/
│   │   └── fleet_tools.py   # Implementação das tools (consulta banco)
│   └── routes/
│       ├── veiculos.py
│       ├── ocorrencias.py   # Chama orchestrator → agentes → banco
│       ├── manutencoes.py
│       ├── relatorios.py
│       └── alertas.py
├── frontend/                # React + Vite (NÃO alterado na versão final)
├── prompts/
│   ├── orchestrator.txt     # Prompt do orquestrador
│   ├── diagnostician.txt    # Prompt do diagnosticador
│   ├── historian.txt        # Prompt do historiador
│   ├── planner.txt          # Prompt do planejador
│   ├── financial.txt        # Prompt do financeiro
│   └── DECISOES.md          # Justificativas de cada prompt
├── tools/
│   ├── tool_definitions.json # Definições no formato JSON
│   └── DECISOES.md          # Justificativas das tools
├── start.sh
├── .gitignore
└── README.md
```
