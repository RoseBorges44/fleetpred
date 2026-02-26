# 🚛 FleetPred — Manutenção Preditiva de Frota com IA Multi-Agente

> Avaliação Final · IA Generativa · UniSENAI

**Repositório:** https://github.com/RoseBorges44/fleetpred

**Acesse em:** http://192.168.0.121:5173/

---

## O Problema

Quem trabalha com gestão de frota pesada sabe: manutenção corretiva é o pesadelo. Um caminhão que quebra na estrada não é só o custo do reparo — é frete atrasado, multa contratual, motorista parado, guincho, e às vezes perda de carga. Na prática, a maioria das frotas ainda funciona no modo reativo: quebrou, conserta. Ou no melhor caso, troca óleo e filtro a cada X km e torce pro resto.

O FleetPred é um sistema de manutenção preditiva que usa **IA multi-agente** para diagnosticar problemas em frotas de caminhões pesados operando em mineração. O técnico reporta sintomas (vibração, temperatura alta, ruído), o sistema aciona 5 agentes especializados que consultam dados reais do banco, cruzam com histórico da frota, e geram um diagnóstico com probabilidade de falha, prazo estimado, plano de ação e justificativa financeira.

### Por que esse problema?

Tenho familiaridade com manutenção de ativos móveis e o domínio de frotas pesadas. Conheço o dia a dia: técnico que descreve problema de um jeito, mecânico que interpreta de outro, gestor que precisa decidir qual caminhão parar primeiro. O sistema multi-agente replica esse fluxo real — cada agente é um especialista da equipe.

---

## Arquitetura de LLM

### Fluxo completo

```
Técnico reporta ocorrência (sintomas, sistema, severidade)
                    │
                    ▼
          ┌─────────────────┐
          │   Orquestrador  │  ← classifica, busca modelo do veículo
          │   (LangGraph)   │
          └────────┬────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌─────────────────┐ ┌─────────────────┐
│  Diagnosticador │ │   Historiador   │  ← sempre executam
│  (temp 0.2)     │ │   (temp 0.1)    │
│  tool: saúde    │ │  tools: histórico│
│  componentes    │ │  + padrões frota │
└────────┬────────┘ └────────┬────────┘
         └─────────┬─────────┘
                   │
                   ▼
         severidade alta/crítica?
          /                \
        SIM                NÃO
         │                  │
         ▼                  │
┌─────────────────┐         │
│   Planejador    │         │
│   (temp 0.3)    │         │
│   sem tools     │         │
└────────┬────────┘         │
         ▼                  │
┌─────────────────┐         │
│   Financeiro    │         │
│   (temp 0.1)    │         │
│  tool: economia │         │
└────────┬────────┘         │
         └────────┬─────────┘
                  ▼
        ┌─────────────────┐
        │  Orquestrador   │  ← consolida tudo num JSON único
        │  (consolida)    │
        └────────┬────────┘
                 ▼
          JSON padronizado
          → salva no banco
          → exibe no frontend
```

### Por que multi-agente e não um LLM só?

Um prompt único com todo o contexto ("diagnostique, analise histórico, planeje e calcule economia") gera respostas genéricas. Cada agente tem uma **especialidade e persona diferentes**, como numa equipe real de manutenção:

- O **diagnosticador** é um engenheiro de confiabilidade — pensa em componentes e modos de falha
- O **historiador** é um analista de dados — busca padrões, não opina sobre diagnóstico
- O **planejador** é um gestor de manutenção — equilibra segurança com disponibilidade
- O **financeiro** é um analista de custos — justifica a intervenção com números

Separar em agentes evita que o modelo misture papéis (ex: o historiador diagnosticando ao invés de analisar dados). Cada agente tem temperatura, tools e restrições calibradas pro seu papel.

### Por que LangGraph?

| Alternativa | Problema |
|-------------|----------|
| **API direta** (requests para Gemini) | Funciona para 1 agente, mas não orquestra múltiplos agentes com estado compartilhado |
| **LangChain AgentExecutor** | Executa 1 agente com tools, mas não tem grafo condicional nem fan-out/fan-in |
| **CrewAI** | Orquestra agentes, mas abstrai demais o fluxo — perdi controle sobre quais agentes rodam quando |
| **LangGraph** | Define o fluxo como **grafo explícito**: nós = agentes, arestas = condições. O `StateGraph` mantém estado tipado (`TypedDict`) que cada nó lê e escreve. `add_conditional_edges` implementa a rota por severidade sem if/else manual |

LangGraph foi escolhido porque o fluxo tem **decisão condicional real**: se a severidade é baixa, não faz sentido gastar tokens (e tempo) com planejamento e análise financeira. Isso é uma aresta condicional no grafo, não um if/else hardcoded.

### Por que Gemini?

- **Gratuito** na tier free → viável para uso contínuo pós-curso, sem custo
- **Tool calling nativo** via `ChatGoogleGenerativeAI` do LangChain
- **gemini-2.0-flash**: rápido (~2-5s por chamada), suficiente para o domínio
- **Context window de 1M tokens**: se no futuro alimentar com manuais técnicos inteiros, cabe

**Trade-off reconhecido**: Em produção usaria Claude pelo structured output mais robusto (o Gemini às vezes retorna markdown em volta do JSON — tive que implementar `_parse_json` com regex como fallback). Mas Gemini gratuito viabiliza uso real e contínuo sem custo.

---

## System Prompts

Cada agente tem um system prompt em `backend/prompts/`. A decisão de separar prompts em arquivos `.txt` (e não hardcoded no Python) permite iterar no prompt sem reiniciar o servidor e versionar prompts separadamente do código.

### Diagnosticador (`prompts/diagnostician.txt`)

**Persona**: Engenheiro de confiabilidade sênior especializado em frotas pesadas (Scania, Volvo, Mercedes-Benz, DAF) em mineração.

**Por que essa persona**: Ativa o conhecimento do modelo sobre motores DC13, transmissões I-Shift, sistemas pneumáticos específicos de caminhão pesado. Uma persona genérica ("assistente") não priorizaria corretamente — ex: bronzinas com ruído em motor diesel pesado é urgência diferente de um carro de passeio.

**Contexto recebido**: Sistema afetado, sintomas, veículo ID, km atual. Também recebe dados da tool `consultar_saude_componentes`.

**Restrições** (delimitadas com XML `<restricoes>`):
- Se probabilidade > 60%, **nunca** recomende "continuar operando" — regra de segurança inviolável
- Sistemas de segurança (freios, direção, suspensão): severidade **mínima** "alta" — não importa o que os dados digam, freio com problema não é "severidade baixa"
- Se dados insuficientes, recomende inspeção presencial — evita que o modelo invente dados
- Custos em Reais, realistas pro mercado brasileiro — evita alucinação numérica em USD

**Por que XML tags nas restrições**: O `<restricoes>` funciona como delimitador semântico. O modelo trata conteúdo dentro de tags XML como regras estruturadas, não como texto corrido que pode ser ignorado. Os outros agentes não precisam disso porque suas saídas não geram risco de segurança operacional.

**Saída**: JSON estrito com 6 campos tipados. Sem texto antes ou depois.

### Historiador (`prompts/historian.txt`)

**Persona**: Analista de dados de frota especializado em identificar padrões de falha.

**Por que essa persona**: Foca o modelo em **análise de dados**, não em diagnóstico técnico. Sem a persona, ele tentaria diagnosticar ao invés de buscar padrões. O historiador deve responder "3 caminhões Scania com >200.000 km tiveram o mesmo problema", não "o problema é a bomba d'água".

**Contexto recebido**: Sistema, sintomas, veículo ID. Usa 2 tools para buscar dados.

**Perguntas-guia no prompt** (1. recorrência, 2. padrões na frota, 3. correlação com km):
Direcionam a análise para informações **acionáveis** pelo planejador no próximo passo. Sem as perguntas, o modelo tende a retornar um resumo narrativo genérico.

**Saída**: JSON com `recorrencia` (bool), `intervalo_medio_falha_km` (int|null), `confianca_analise` (enum).

### Planejador (`prompts/planner.txt`)

**Persona**: Gestor de manutenção de frota pesada em mineração.

**Por que essa persona**: Um "engenheiro" sempre pararia o caminhão por segurança; um "gestor" pondera custo operacional vs risco. O prompt inclui explicitamente "equilibre segurança com disponibilidade" e "cada hora de equipamento parado custa caro" — são as tensões reais do domínio.

**Contexto recebido**: Diagnóstico do diagnosticador + análise do historiador (output dos 2 agentes anteriores). Não tem tools — raciocina sobre dados que já existem.

**Saída**: JSON com `urgencia_horas`, `tipo_manutencao`, `prioridade`, `tempo_reparo_horas`, `justificativa`.

### Financeiro (`prompts/financial.txt`)

**Persona**: Analista de custos de manutenção de frota.

**Por que essa persona**: Foco em ROI e justificativa financeira. O prompt inclui referências de custo reais do mercado brasileiro de mineração (hora parada ~R$ 800-1.200, guincho ~R$ 3.000-8.000) para **ancorar** o modelo em valores realistas e evitar alucinação numérica.

**Contexto recebido**: Sistema, componente identificado pelo diagnosticador, modelo do veículo. Usa a tool `calcular_economia` para obter dados reais de custo.

**Saída**: JSON com `economia_estimada`, `roi_preditiva`, `pecas_sugeridas` (com custos).

### Orquestrador (`prompts/orchestrator.txt`)

**Persona**: Coordenador de diagnóstico de frota pesada em mineração.

**Por que essa persona**: Não diagnostica — **consolida**. Recebe as saídas de todos os agentes e monta o JSON final padronizado. O prompt termina com "Responda APENAS com o JSON final, sem texto antes ou depois" — instrução crítica porque o orquestrador é o último passo antes do banco de dados.

**Regra de roteamento no prompt**: "SEMPRE acione Diagnosticador e Historiador; se severidade alta/crítica acione Planejador e Financeiro". Essa regra está tanto no prompt quanto implementada como `add_conditional_edges` no grafo — defesa em profundidade.

### Por que JSON estrito em todos os agentes

- O frontend faz `JSON.parse()` da resposta — qualquer texto fora do JSON quebra o parsing
- Agentes intermediários consomem a saída do anterior programaticamente
- JSON estruturado permite logs queryáveis e detecção de drift na qualidade
- Sem a instrução explícita "APENAS JSON", o Gemini adiciona "Claro! Aqui está o diagnóstico..." antes do JSON

### Por que não usar few-shot

Em sistemas de prompt único, few-shot é essencial para alinhar formato. Aqui não é necessário porque:

1. **O contexto vem das tools, não do prompt** — os agentes recebem dados reais do banco, não exemplos fabricados
2. **Os agentes se complementam** — a saída do diagnosticador funciona como "few-shot" para o planejador
3. **JSON schema no prompt já define o formato** — especificar o schema exato é mais eficaz que mostrar um exemplo
4. **Risco de viés** — few-shot com dados de mineração poderia enviesar o modelo para sempre diagnosticar os mesmos problemas do exemplo

---

## Ferramentas (Tools)

4 ferramentas implementadas em `backend/tools/fleet_tools.py`, expostas aos agentes via `@tool` decorator do LangChain em cada arquivo de agente.

### Por que 4 tools e não mais (nem menos)

- **Menos de 4**: O LLM teria que **inventar** dados que poderia consultar. Sem `consultar_saude_componentes`, estimaria a saúde baseado só nos sintomas (viés de confirmação).
- **Mais de 4**: Aumenta a probabilidade de **tool confusion** — o modelo escolhe a ferramenta errada ou tenta chamar múltiplas quando uma bastava.
- Cada ferramenta mapeia para uma **fonte de dados distinta** no banco. Nenhuma sobrepõe a outra.

**Princípio**: Toda informação que existe no banco deve vir de uma tool, não da "memória" do modelo. O modelo é bom em raciocínio, não em recall de dados específicos.

### `consultar_saude_componentes`

| | |
|---|---|
| **Usada por** | Diagnosticador |
| **O que faz** | Retorna saúde percentual (0-100%) de cada componente de um veículo |
| **Parâmetros** | `veiculo_id: int` |
| **Por que o LLM precisa** | Sem ela, estimaria saúde baseado só nos sintomas. Com ela, vê o estado **real medido** — pode até contradizer os sintomas (ex: técnico reporta vibração, mas a saúde da suspensão está em 92%) |
| **Fonte no banco** | Tabela `componentes` |

### `consultar_historico_veiculo`

| | |
|---|---|
| **Usada por** | Historiador |
| **O que faz** | Busca as últimas N manutenções de um veículo específico (tipo, descrição, data, custo, peças) |
| **Parâmetros** | `veiculo_id: int`, `limite: int = 10` |
| **Por que o LLM precisa** | Sem ela, inventaria um histórico plausível mas **falso**. Com ela, acessa manutenções reais com datas e custos reais — pode identificar recorrência |
| **Fonte no banco** | Tabelas `veiculos` + `manutencoes` |

### `buscar_padroes_frota`

| | |
|---|---|
| **Usada por** | Historiador |
| **O que faz** | Busca ocorrências de **outros veículos** com mesmo sistema e sintomas parecidos, incluindo diagnóstico e resultado |
| **Parâmetros** | `sistema: str`, `sintomas: list[str]` |
| **Por que o LLM precisa** | Sem ela, não saberia que 3 outros Scania tiveram o mesmo problema. Com ela, encontra padrões reais na frota e correlaciona |
| **Fonte no banco** | Tabelas `ocorrencias` + `veiculos` + `diagnosticos` |

### `calcular_economia`

| | |
|---|---|
| **Usada por** | Financeiro |
| **O que faz** | Calcula economia estimada: preventiva vs corretiva. Usa dados reais do banco quando disponíveis (>= 2 registros), senão usa estimativas calibradas do mercado brasileiro |
| **Parâmetros** | `sistema: str`, `componente: str`, `modelo_veiculo: str` |
| **Por que o LLM precisa** | Sem ela, **chutaria valores** de custo (alucinação numérica clássica). Com ela, calcula baseado em dados reais ou estimativas calibradas |
| **Fonte no banco** | Tabela `manutencoes` (agregações) + fallback com estimativas de mercado |

### Por que `consultar_historico` e `buscar_padroes` são separadas

Poderiam ser uma tool só? Não:

1. **Escopo diferente**: histórico é de **um** veículo (vertical, profundo); padrões é de **toda a frota** (horizontal, amplo)
2. **Performance**: histórico é O(1) no índice; padrões faz scan + comparação de sintomas — mais custoso
3. **Granularidade**: o agente pode chamar só o que precisa. Em produção, `buscar_padroes` pode precisar de cache; `consultar_historico` não

### Por que descriptions incluem "quando usar"

```
"Usar quando precisar entender o histórico de manutenção de um veículo
para identificar padrões de falha recorrentes ou avaliar o estado geral."
```

O modelo decide **qual tool chamar** baseado na description. Se diz apenas "busca manutenções", o modelo pode não perceber que é a ferramenta certa para "verificar se o problema é recorrente". O "quando usar" dá um **critério de acionamento**, não apenas uma capacidade.

### Padrão de tool execution

Todos os agentes usam um loop manual (não usa `AgentExecutor` do LangChain):

```python
response = llm_with_tools.invoke(messages)
while response.tool_calls:
    messages.append(response)
    for tc in response.tool_calls:
        result = tools_map[tc["name"]].invoke(tc["args"])
        messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
    response = llm_with_tools.invoke(messages)
```

**Por que loop manual e não AgentExecutor**: Mais controle, menos abstração. Sei exatamente quantas vezes o LLM chamou tools, posso logar cada chamada, e evito comportamentos inesperados do AgentExecutor (como loops infinitos se o modelo fica preso).

---

## Parâmetros do Modelo

| Agente | Modelo | Temperatura | Justificativa |
|--------|--------|-------------|---------------|
| Diagnosticador | gemini-2.0-flash | 0.2 | Diagnóstico técnico precisa ser determinístico. Mesmos sintomas → mesmo diagnóstico. |
| Historiador | gemini-2.0-flash | 0.1 | Consulta dados factuais. Não pode "inventar" padrões que não existem no banco. |
| Planejador | gemini-2.0-flash | 0.3 | Precisa ponderar trade-offs entre urgência e disponibilidade. Mais flexível. |
| Financeiro | gemini-2.0-flash | 0.1 | Números devem ser exatos. Cálculos financeiros são determinísticos. |
| Orquestrador (consolida) | gemini-2.0-flash | 0.1 | Consolidação final — deve ser fiel às saídas dos agentes, não criativo. |

### Por que temperatura baixa em geral

Diagnóstico de manutenção **não é tarefa criativa**. Se um técnico reporta "ruído anormal no motor" a 245.000 km, a resposta correta é bronzinas/bielas, não uma resposta criativa diferente a cada vez. Temperatura alta geraria variação indesejada: mesmos sintomas, diagnósticos diferentes → perda de confiança do operador.

### Por que o Planejador tem a mais alta (0.3)

O planejador é o único agente que faz **julgamento subjetivo**: "paro o caminhão agora e perco produção, ou arrisco mais 2 dias?". Precisa de flexibilidade para ponderar trade-offs que não têm resposta única. Mesmo assim, 0.3 é conservador — o suficiente para variar a justificativa sem inventar dados.

### Por que gemini-2.0-flash e não gemini-pro

- **Flash é gratuito** na tier free com limites generosos
- **Mais rápido** (~2-5s vs ~8-15s por chamada) — importa porque são 3-6 chamadas LLM por diagnóstico
- **Suficiente pro caso** — o raciocínio necessário aqui é "correlacionar sintomas com componentes" e "seguir instruções do prompt", não raciocínio de múltiplas etapas complexo
- Em testes, a qualidade do diagnóstico com flash vs pro foi equivalente para este domínio

---

## Resiliência: Fallback e Parsing

### Fallback para mock

Se **qualquer** exceção ocorrer no pipeline LLM (API fora, quota excedida, timeout, parsing falho), o sistema cai para o `mock_ai.generate_mock_diagnostic()` — que retorna diagnóstico baseado em mapeamento estático por sistema/sintoma. O sistema **nunca quebra** para o usuário.

```python
# Em orchestrator.py
except Exception as e:
    print(f"[Orchestrator] ERRO após {elapsed:.1f}s: {e}")
    return generate_mock_diagnostic(sistema=sistema, sintomas=sintomas, veiculo_km=km)
```

```python
# Em routes/ocorrencias.py — segunda camada de fallback
try:
    diag = orchestrate(...)
except Exception as e:
    diag = generate_mock_diagnostic(...)
```

Duas camadas de fallback: uma dentro do orchestrator (pega erros dos agentes/LLM), outra na rota (pega erros de import ou inicialização).

### Parsing robusto de JSON

O Gemini às vezes retorna JSON dentro de blocos markdown (`` ```json ... ``` ``). Todos os agentes usam `_parse_json()`:

```python
def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)              # tenta direto
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)  # busca {...} no texto
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}                            # fallback seguro: dict vazio
```

3 camadas: parse direto → regex para extrair JSON → dict vazio. O dict vazio é seguro porque o orchestrator usa `.get()` com defaults para todos os campos.

---

## O que Funcionou

### Separação de responsabilidades por agente

Quando tudo estava num prompt só, o Gemini misturava diagnóstico com planejamento — sugeria "trocar bomba d'água em 48 horas" sem antes confirmar que era a bomba d'água. Com agentes separados, o diagnosticador **primeiro confirma** o componente (consultando saúde real), e só depois o planejador define prazo.

### Restrições com XML tags no diagnosticador

A tag `<restricoes>` no prompt do diagnosticador fez diferença mensurável. Sem ela, o modelo às vezes sugeria "monitorar" para freios com probabilidade de falha de 70%. Com a tag, a regra "sistemas de segurança = severidade mínima alta" é respeitada consistentemente.

### Fallback duplo

Testado intencionalmente desligando a internet: o orchestrator pega a exceção de rede, imprime o log de erro, e retorna o mock em <1ms. O usuário recebe diagnóstico (menos preciso, mas funcional). Também testado com quota excedida (429) — mesmo comportamento.

### Tools com descriptions contextuais

Adicionar "Usar quando precisar..." nas descriptions das tools reduziu chamadas desnecessárias. Sem essa frase, o diagnosticador às vezes chamava `consultar_saude_componentes` e depois tentava chamar o histórico (que não é tool dele). Com a description contextualizada, cada agente chama apenas suas tools.

### Timing em cada agente

Cada agente imprime `[NomeAgente] concluído em X.Xs`. Permite identificar gargalos rapidamente. O diagnosticador com tool calling é o mais lento (~3-5s); o planejador sem tools é o mais rápido (~1-2s).

---

## O que Não Funcionou

### Gemini e markdown no JSON

O Gemini 2.0 Flash frequentemente retorna JSON dentro de blocos markdown (`` ```json\n{...}\n``` ``), mesmo com instrução explícita "APENAS JSON". Tentei variações do prompt:
- "Retorne apenas JSON" → ~70% sem markdown
- "Responda APENAS com o JSON, sem texto antes ou depois" → ~85% sem markdown
- Regex `_parse_json()` como fallback → 100% de sucesso no parsing

O Claude seria mais robusto aqui com structured output nativo, mas o regex resolve.

### Tool calling do Gemini vs Claude

O Gemini às vezes inventa nomes de tools que não existem no `bind_tools()`, ou passa parâmetros com tipo errado (string onde deveria ser int). Simplificar as descriptions e manter poucos parâmetros por tool (1-3) reduziu significativamente esse problema. Com descriptions longas e detalhadas, a taxa de erro subia.

### Temperatura 0.0 quebra o financeiro

Com temperatura 0.0, o financeiro ficava preso em loops: chamava `calcular_economia` → recebia resultado → chamava de novo com os mesmos parâmetros. Subir para 0.1 resolveu — aparentemente o Gemini precisa de alguma variância para sair do loop de tool calling.

### Primeiro prompt do orquestrador era longo demais

O prompt original do orquestrador tinha exemplos de cada tipo de diagnóstico (~2000 tokens). Cortei para ~600 tokens focando nas **regras de roteamento** e no **schema do JSON final**. O resultado melhorou — o modelo seguia o schema com mais consistência quando tinha menos informação competindo por atenção.

---

## Uso do Agente de Codificação

**Ferramenta:** Claude Code (CLI)

**Processo da versão final:**

1. **Planejamento**: defini a arquitetura multi-agente, quais tools cada agente precisa, e o fluxo do grafo antes de pedir código
2. **Prompts primeiro**: escrevi os system prompts e DECISOES.md antes de implementar os agentes — a engenharia de prompt guiou o código, não o contrário
3. **Implementação incremental**: llm_config → agentes individuais → orchestrator → integração na rota
4. **Teste end-to-end**: POST real na API pra validar o fluxo completo incluindo fallback

**Proporção versão final:**
- Planejamento e prompts: ~30% do tempo
- Gerado pelo agente: ~50%
- Revisão e ajuste: ~20%

---

## Como Executar

**Pré-requisitos:** Python 3.10+ e Node.js 18+

```bash
git clone https://github.com/RoseBorges44/fleetpred.git
cd fleetpred

# 1. Configurar chave da API
cp backend/.env.example backend/.env
# Edite backend/.env e cole sua GEMINI_API_KEY

# 2. Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 3. Frontend (outro terminal)
cd frontend
npm install
npm run dev
```

**Acessar:** http://localhost:5173 (frontend) · http://localhost:8000/docs (API)

**Sem chave Gemini?** O sistema funciona normalmente — usa o fallback mock_ai automaticamente.

---

## Estrutura do Projeto

```
fleetpred/
├── backend/
│   ├── main.py                  # App FastAPI, CORS, registro de rotas
│   ├── database.py              # Schema SQLite — 6 tabelas
│   ├── seed_data.py             # 10 caminhões com dados realistas
│   ├── mock_ai.py               # Diagnóstico mock — mantido como fallback
│   ├── .env                     # GEMINI_API_KEY (não versionado)
│   ├── .env.example             # Template da .env
│   ├── requirements.txt         # Dependências (LangGraph, LangChain, Gemini, etc.)
│   │
│   ├── agents/                  # Sistema multi-agente
│   │   ├── __init__.py
│   │   ├── llm_config.py        # get_llm(), load_prompt() — config centralizada
│   │   ├── orchestrator.py      # LangGraph StateGraph — orquestra o fluxo
│   │   ├── diagnostician.py     # Agente diagnosticador (temp 0.2, 1 tool)
│   │   ├── historian.py         # Agente historiador (temp 0.1, 2 tools)
│   │   ├── planner.py           # Agente planejador (temp 0.3, sem tools)
│   │   └── financial.py         # Agente financeiro (temp 0.1, 1 tool)
│   │
│   ├── prompts/                 # System prompts dos agentes
│   │   ├── orchestrator.txt     # Coordenador — consolida JSON final
│   │   ├── diagnostician.txt    # Engenheiro de confiabilidade
│   │   ├── historian.txt        # Analista de dados de frota
│   │   ├── planner.txt          # Gestor de manutenção
│   │   ├── financial.txt        # Analista de custos
│   │   └── DECISOES.md          # Justificativas de design dos prompts
│   │
│   ├── tools/                   # Ferramentas dos agentes
│   │   ├── __init__.py
│   │   ├── fleet_tools.py       # 4 tools: saúde, histórico, padrões, economia
│   │   └── DECISOES.md          # Justificativas de design das tools
│   │
│   └── routes/
│       ├── veiculos.py          # Dashboard stats, lista, detalhe
│       ├── ocorrencias.py       # Registro + chamada ao orchestrator + fallback
│       ├── manutencoes.py       # Agendadas + fila de prioridade
│       ├── relatorios.py        # Custos, disponibilidade, tendência
│       └── alertas.py           # Alertas + diagnóstico detalhado
│
├── frontend/                    # React + Vite (não alterado na versão final)
│   └── src/
│       ├── App.jsx
│       ├── index.css
│       ├── services/api.js
│       └── pages/               # 6 telas da aplicação
│
├── start.sh
├── .gitignore
└── README.md
```
