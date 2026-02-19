# PROMPT PARA CLAUDE CODE — FleetPred

Cole este prompt inteiro no Claude Code (claude cli). Ele contém todas as especificações para gerar o projeto completo.

---

Crie um projeto completo chamado **FleetPred** — Sistema de Manutenção Preditiva de Frota de Caminhões.

## CONTEXTO

Este é um trabalho acadêmico de IA Generativa. O sistema deve estar 100% funcional como protótipo de UI, com dados simulados. **Nenhum LLM é integrado ainda** — onde a IA atuaria, usar respostas mock/placeholder que demonstrem como o sistema funcionará com IA no futuro. O mock deve retornar JSON estruturado (não texto livre), simulando o que um LLM retornaria via function calling / structured output.

## STACK OBRIGATÓRIA

- **Backend:** Python + FastAPI (com CORS habilitado para `*`)
- **Frontend:** React 18 + Vite + React Router DOM v6 + Recharts (gráficos) + Lucide React (ícones opcionais)
- **Banco de dados:** SQLite (arquivo único `fleetpred.db`, sem Docker)
- **Fontes Google:** JetBrains Mono (mono) + Inter (sans)
- Proxy do Vite: configurar `/api` para redirecionar para `http://localhost:8000`

## ESTRUTURA DE DIRETÓRIOS

```
fleetpred/
├── backend/
│   ├── main.py                # FastAPI app principal
│   ├── database.py            # Schema SQLite (6 tabelas)
│   ├── seed_data.py           # Dados realistas de frota
│   ├── mock_ai.py             # Serviço mock de IA (simula LLM)
│   ├── requirements.txt       # fastapi, uvicorn, pydantic
│   └── routes/
│       ├── __init__.py
│       ├── veiculos.py        # CRUD + dashboard stats
│       ├── ocorrencias.py     # Registro + geração automática de diagnóstico mock
│       ├── manutencoes.py     # Agendadas + fila de prioridade
│       ├── relatorios.py      # Custos, disponibilidade, tendência
│       └── alertas.py         # Listagem + diagnóstico detalhado
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx            # Layout com sidebar + Routes
│       ├── index.css          # Tema escuro com CSS variables
│       ├── services/
│       │   └── api.js         # Camada de comunicação com a API
│       └── pages/
│           ├── Dashboard.jsx
│           ├── VeiculoDetalhe.jsx
│           ├── Ocorrencia.jsx
│           ├── Diagnostico.jsx
│           ├── PlanoManutencao.jsx
│           └── Relatorios.jsx
├── start.sh                   # Script bash que sobe backend + frontend
├── .gitignore
└── README.md
```

---

## BANCO DE DADOS — 6 TABELAS (database.py)

```sql
CREATE TABLE veiculos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    placa TEXT UNIQUE NOT NULL,
    modelo TEXT NOT NULL,
    ano INTEGER NOT NULL,
    km_atual REAL NOT NULL DEFAULT 0,
    motor TEXT,
    status TEXT NOT NULL DEFAULT 'ok' CHECK(status IN ('ok', 'atencao', 'critico')),
    ultimo_oleo_km REAL DEFAULT 0,
    data_cadastro TEXT DEFAULT (datetime('now')),
    ativo INTEGER DEFAULT 1
);

CREATE TABLE componentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    nome TEXT NOT NULL,
    saude_pct INTEGER NOT NULL DEFAULT 100 CHECK(saude_pct BETWEEN 0 AND 100),
    ultima_inspecao TEXT
);

CREATE TABLE ocorrencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    data_ocorrencia TEXT NOT NULL DEFAULT (datetime('now')),
    sistema TEXT NOT NULL,
    sintomas TEXT NOT NULL,  -- JSON array de strings
    descricao TEXT,
    severidade TEXT NOT NULL DEFAULT 'media' CHECK(severidade IN ('baixa', 'media', 'alta', 'critica')),
    km_ocorrencia REAL,
    status TEXT NOT NULL DEFAULT 'aberta' CHECK(status IN ('aberta', 'em_analise', 'resolvida'))
);

CREATE TABLE manutencoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    tipo TEXT NOT NULL CHECK(tipo IN ('preventiva', 'preditiva', 'corretiva')),
    descricao TEXT NOT NULL,
    data_realizada TEXT,
    data_agendada TEXT,
    km_realizada REAL,
    custo REAL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'agendada' CHECK(status IN ('agendada', 'em_andamento', 'concluida', 'cancelada')),
    pecas TEXT,
    observacoes TEXT
);

CREATE TABLE diagnosticos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ocorrencia_id INTEGER REFERENCES ocorrencias(id),
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    data_diagnostico TEXT NOT NULL DEFAULT (datetime('now')),
    componente TEXT NOT NULL,
    probabilidade_falha REAL NOT NULL,
    horizonte_dias INTEGER,
    severidade TEXT NOT NULL,
    sintomas_correlacionados TEXT,  -- JSON array
    recomendacao TEXT,
    pecas_sugeridas TEXT,           -- JSON array
    economia_estimada REAL,
    base_historica TEXT
);

CREATE TABLE alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    diagnostico_id INTEGER REFERENCES diagnosticos(id),
    tipo TEXT NOT NULL CHECK(tipo IN ('critico', 'atencao', 'info')),
    mensagem TEXT NOT NULL,
    data_criacao TEXT NOT NULL DEFAULT (datetime('now')),
    lido INTEGER DEFAULT 0
);
```

Usar `PRAGMA foreign_keys = ON` em toda conexão. Usar `row_factory = sqlite3.Row` para retornar dicts.

---

## SEED DATA (seed_data.py)

Inserir dados realistas ao iniciar o app (verificar se já existe dados antes de re-inserir):

### 10 Veículos:
| Placa     | Modelo           | Ano  | Km Atual | Motor          | Status  | Último Óleo Km |
|-----------|------------------|------|----------|----------------|---------|----------------|
| ABC-1234  | Scania R450      | 2021 | 342.100  | DC13 - 450cv   | critico | 328.400        |
| DEF-5678  | Volvo FH 540     | 2020 | 215.800  | D13K - 540cv   | atencao | 210.000        |
| GHI-9012  | MB Actros 2651   | 2022 | 128.400  | OM471 - 510cv  | ok      | 125.000        |
| JKL-3456  | Scania R500      | 2019 | 412.700  | DC13 - 500cv   | ok      | 400.000        |
| MNO-7890  | DAF XF 480       | 2023 | 87.200   | MX-13 - 480cv  | atencao | 80.000         |
| PQR-2233  | Volvo FH 460     | 2021 | 198.500  | D13K - 460cv   | ok      | 195.000        |
| STU-4455  | Scania G450      | 2020 | 267.300  | DC13 - 450cv   | ok      | 260.000        |
| VWX-6677  | MB Actros 2546   | 2022 | 156.800  | OM471 - 460cv  | ok      | 150.000        |
| YZA-8899  | DAF XF 530       | 2021 | 289.400  | MX-13 - 530cv  | ok      | 285.000        |
| BCD-1100  | Volvo FM 500     | 2019 | 378.200  | D13K - 500cv   | atencao | 370.000        |

### 7 Componentes por veículo:
Motor, Transmissão, Freios, Arrefecimento, Suspensão, Sistema Elétrico, Pneus.

Saúde (%) customizada por veículo. Exemplos:
- ABC-1234 (crítico): Motor 72%, Transmissão 91%, Freios 45%, Arrefecimento 58%, Suspensão 84%, Sist. Elétrico 90%, Pneus 67%
- GHI-9012 (ok): todos acima de 85%
- Veículos "atencao": pelo menos 2 componentes entre 50-70%
- Gerar valores realistas para os demais veículos, coerentes com o status.

### ~15 Manutenções:
Mix de concluídas (com data_realizada, km_realizada, custo) e agendadas (com data_agendada, status='agendada').
- Incluir pelo menos 2 preditivas (geradas por IA), 5 preventivas, 2 corretivas.
- Datas das agendadas devem cair na semana corrente para aparecer no calendário.
- Custos realistas: preventiva R$ 600-1.500, preditiva R$ 800-2.500, corretiva R$ 3.000-8.500.

### 4 Ocorrências:
1. ABC-1234, Arrefecimento, sintomas: ["Temperatura elevada", "Consumo de líquido"], severidade alta, status em_analise
2. DEF-5678, Freios, sintomas: ["Ruído ao frear", "Pedal longo"], severidade alta, status em_analise
3. MNO-7890, Motor, sintomas: ["Vibração anormal", "Perda de potência"], severidade media, status aberta
4. BCD-1100, Suspensão, sintomas: ["Instabilidade", "Ruído em irregularidades"], severidade media, status aberta

### 2 Diagnósticos (mock):
1. Para ocorrência 1 (ABC-1234): componente "Sistema de Arrefecimento", prob 0.82, horizonte 12 dias, severidade alta, peças: ["Válvula termostática", "Mangueira superior do radiador", "Junta do cabeçote (preventivo)"], economia R$ 5.800
2. Para ocorrência 2 (DEF-5678): componente "Sistema de Freios", prob 0.75, horizonte 20 dias, severidade alta, peças: ["Lonas de freio traseiro", "Tambor de freio", "Regulador automático"], economia R$ 4.200

### 4 Alertas:
Vinculados aos diagnósticos e ocorrências. 2 críticos, 2 atenção. Pelo menos 1 não lido.

---

## MOCK AI SERVICE (mock_ai.py)

Criar um módulo que simula respostas de LLM. A função principal:

```python
def generate_mock_diagnostic(sistema: str, sintomas: list[str], veiculo_km: float = 0) -> dict:
```

Deve retornar um dict com EXATAMENTE estes campos (simulando structured output do LLM):
```json
{
  "componente": "Sistema de Arrefecimento — Válvula Termostática",
  "probabilidade_falha": 0.85,
  "horizonte_dias": 12,
  "severidade": "alta",
  "sintomas_correlacionados": ["Temperatura elevada", "Consumo de líquido", "(outros inferidos pelo LLM)"],
  "recomendacao": "Inspeção preventiva imediata. Agendar parada em até 48h.",
  "pecas_sugeridas": ["Válvula termostática", "Mangueira superior", "Junta do cabeçote"],
  "economia_estimada": 5800,
  "base_historica": "3 veículos similares apresentaram falha com sintomas idênticos entre 10-15 dias.",
  "modelo_versao": "mock-v1.0 (substituir por LLM)",
  "confianca_dados": "simulada"
}
```

Ter um mapeamento de diagnósticos por sistema (Motor, Freios, Arrefecimento, Transmissão, Suspensão) e por sintomas específicos. Adicionar pequena variância aleatória (±5% na probabilidade, ±2 dias no horizonte) para parecer mais realista.

Incluir comentários explicando que na versão final este módulo será substituído por chamadas à API Claude via function calling.

---

## ROTAS DA API

### GET /api/veiculos/stats/dashboard
Retorna: total_veiculos, veiculos_ativos, status_breakdown (ok/atencao/critico com contagem), alertas_pendentes, alertas_criticos, manutencoes_hoje, disponibilidade_pct.

### GET /api/veiculos/
Lista veículos com saúde média (AVG dos componentes) e contagem de alertas pendentes. Ordenar: críticos primeiro, depois atenção, depois ok.

### GET /api/veiculos/{id}
Retorna veículo + componentes (ordenados por saude_pct ASC) + últimas 10 manutenções + últimos 5 alertas.

### GET /api/ocorrencias/
Lista ocorrências com placa e modelo do veículo. Parsear o campo sintomas de JSON string para array.

### POST /api/ocorrencias/
Recebe: veiculo_id, sistema, sintomas (array), descricao, severidade, km_ocorrencia.
**Fluxo automático:** (1) Inserir ocorrência → (2) Chamar `generate_mock_diagnostic()` → (3) Salvar diagnóstico no banco → (4) Criar alerta vinculado. Retornar o diagnóstico no response.

### GET /api/manutencoes/agendadas
Manutenções com status='agendada', ordenadas por data. Incluir placa e modelo.

### GET /api/manutencoes/prioridade
Fila de prioridade: agendadas ordenadas por tipo (corretiva > preditiva > preventiva) e data. Incluir probabilidade_falha e horizonte_dias do diagnóstico mais recente se existir.

### GET /api/relatorios/custos
Custo total, por tipo (COUNT + SUM + AVG), top 5 veículos por custo, economia preditiva acumulada.

### GET /api/relatorios/disponibilidade
Total veículos, parados, disponibilidade_pct, histórico mock de horas paradas por mês (6 meses, valores decrescentes para mostrar melhoria).

### GET /api/relatorios/tendencia
Dados mock para gráficos: 6 meses, arrays de custos por tipo (preventiva, preditiva, corretiva), com tendência de corretiva caindo e preditiva subindo (para demonstrar o valor da IA).

### GET /api/alertas/?lido=0|1 (opcional)
Lista alertas com dados do veículo e do diagnóstico vinculado.

### PUT /api/alertas/{id}/lido
Marca alerta como lido.

### GET /api/alertas/diagnostico/{diagnostico_id}
Detalhes completos do diagnóstico com dados do veículo e da ocorrência. Parsear campos JSON (sintomas_correlacionados, pecas_sugeridas).

---

## FRONTEND — DESIGN VISUAL

### Tema escuro obrigatório com estas CSS variables:
```css
--bg: #0f1117;
--surface: #1a1d27;
--surface-alt: #222633;
--border: #2e3345;
--border-light: #3d4460;
--accent: #f59e0b;         /* âmbar — cor primária */
--accent-dim: rgba(245, 158, 11, 0.15);
--accent-text: #fbbf24;
--danger: #ef4444;
--danger-dim: rgba(239, 68, 68, 0.15);
--warning: #f59e0b;
--warning-dim: rgba(245, 158, 11, 0.15);
--success: #22c55e;
--success-dim: rgba(34, 197, 94, 0.15);
--text: #e2e8f0;
--text-muted: #94a3b8;
--text-dim: #64748b;
```

### Layout: Sidebar fixa (220px) à esquerda + conteúdo principal à direita.

### Sidebar:
- Logo: "🚛 FLEET**PRED**" (FLEET em âmbar, PRED em branco), subtítulo "MANUTENÇÃO PREDITIVA" em JetBrains Mono
- 6 links de navegação com ícones: ◫ Dashboard, ◉ Ficha Veículo, ✎ Registro Ocorrência, ⚡ Diagnóstico IA, ▦ Plano Manutenção, ◰ Relatórios
- Link ativo: fundo accent-dim, texto accent-text, borda esquerda accent, font-weight 600
- Footer: "FleetPred v1.0 / Avaliação IA Generativa"

### Componentes visuais reutilizáveis:
- **KPI Card:** fundo surface-alt, borda esquerda 3px colorida, label (uppercase, mono, text-dim), value (26px, bold, mono), sub (text-muted)
- **Box:** borda 1.5px solid border, border-radius 8, padding 16px, label posicionada absolute top -9px com background surface
- **Badge:** padding 3px 10px, border-radius 20px, font 10px mono bold. Classes: .ok/.preventiva/.concluida (verde), .atencao/.preditiva/.agendada (amarelo), .critico/.corretiva (vermelho)
- **Vehicle Row:** flex row, borda esquerda 3px (verde/amarelo/vermelho conforme status), hover muda background, cursor pointer
- **Health Bar:** label 110px + track (height 8px, bg border, border-radius 4px) + fill (cor conforme %) + texto %
- **Chip/Selector:** botões toggleable com estado ativo (accent-dim + accent border)
- **Mock Banner:** fundo accent-dim, borda accent, ícone ⚡, texto "RESPOSTA SIMULADA (MOCK)" + subtítulo explicando que será substituído por LLM

---

## TELAS DO FRONTEND (6 páginas)

### 1. Dashboard (/)
- **Header:** "◫ Dashboard da Frota" + subtítulo
- **4 KPI cards em row:** Veículos Ativos (success), Alertas Preditivos (danger), Manutenções Hoje (accent), Disponibilidade % (warning)
- **Layout flex:** 2/3 lista de veículos + 1/3 alertas
- **Lista de veículos:** Buscar GET /api/veiculos/. Para cada veículo: ícone 🚛, placa (bold), modelo + km formatado (pt-BR), badge de status, seta →. Clicar navega para /veiculo/{id}
- **Alertas recentes (box highlight):** Buscar GET /api/alertas/?lido=0. Cards com badge tipo + placa + mensagem. Clicar navega para /diagnostico/{diagnostico_id}
- **Mini gráfico status da frota:** 3 barras verticais (OK/Atenção/Crítico) com contagem acima, proporcionais ao total

### 2. Ficha do Veículo (/veiculo e /veiculo/:id)
- **Seletor de veículo:** Chips com todas as placas. Chip ativo = accent. Clicar carrega o veículo.
- Se nenhum selecionado, mostrar "Selecione um veículo acima".
- **Layout grid 2 colunas:**
  - **Dados do Ativo (box):** Grid 2x3 com Placa, Modelo, Ano, Km Atual (formatado), Motor, Último Óleo Km
  - **Saúde dos Componentes (box):** Health bars para cada componente. Cor: ≥80% verde, 50-79% amarelo, <50% vermelho.
- **Histórico de Manutenções (box):** Timeline rows com data (mono), badge tipo, descrição, km, badge status. Ordenado por data DESC.
- **2 botões de ação:** "✎ Registrar Ocorrência" (navega /ocorrencia/{id}) e "⚡ Solicitar Diagnóstico IA" (navega /diagnostico, estilo outline-accent)

### 3. Registro de Ocorrência (/ocorrencia e /ocorrencia/:veiculoId)
**ESTA É A TELA MAIS IMPORTANTE PARA DEMONSTRAR COMPLEXIDADE DE UI.**

- **Box "Identificação":** Grid 3 colunas — select de veículo (pré-selecionado se veio de /ocorrencia/:id), input km, input date
- **Box "Sistema Afetado":** Grupo de chips: Motor, Freios, Arrefecimento, Transmissão, Suspensão. Apenas 1 selecionável por vez. Box ganha classe highlight quando um sistema está selecionado.
- **Box CONDICIONAL "Sintomas — {sistema}"** (SÓ APARECE quando sistema é selecionado):
  - Nota italic: "↑ Formulário condicional: muda de acordo com o sistema selecionado"
  - Lista de checkboxes com sintomas específicos daquele sistema:
    - **Motor:** Perda de potência, Ruído anormal, Fumaça excessiva, Consumo elevado de óleo, Vibração anormal
    - **Freios:** Ruído ao frear, Pedal longo, Vibração, Desgaste de lona/pastilha, Aquecimento excessivo
    - **Arrefecimento:** Temperatura elevada, Vazamento de líquido, Ventilador não liga, Consumo de líquido
    - **Transmissão:** Dificuldade de engate, Ruído em marcha, Trancos, Patinação da embreagem
    - **Suspensão:** Instabilidade, Ruído em irregularidades, Desgaste de molas, Inclinação lateral
  - Checkbox selecionado: fundo accent-dim, borda accent
- **Box "Detalhes Adicionais":** Textarea para descrição livre + grupo de chips para severidade (Baixa/Média/Alta/Crítica). Alta e Crítica selecionadas ficam com estilo danger.
- **Botão submit (primary, full width):** "Enviar Ocorrência → Gerar Diagnóstico IA"
- **Ao submeter:** POST /api/ocorrencias/ → mostrar tela de sucesso com:
  - Banner verde "Ocorrência registrada e diagnóstico gerado!"
  - Box highlight "Diagnóstico Gerado (Mock)" com: círculo de probabilidade (%), componente, horizonte, severidade, recomendação
  - Grid 2 colunas: Peças sugeridas + JSON da resposta mock (pre, mono, font 9px)
  - Botões: "⚡ Ver Diagnósticos" e "✎ Nova Ocorrência"

### 4. Diagnóstico IA (/diagnostico e /diagnostico/:id)
- **Mock Banner** no topo: "RESPOSTAS SIMULADAS (MOCK) — Na versão final, será gerado pelo LLM"
- **Layout flex:** 1/3 lista de alertas + 2/3 detalhe do diagnóstico
- **Lista de alertas (box):** GET /api/alertas/. Cards clicáveis com badge tipo, placa, mensagem, probabilidade e horizonte. Borda accent no selecionado.
- **Detalhe do diagnóstico (box highlight):** Ao clicar, GET /api/alertas/diagnostico/{id}:
  - Círculo de probabilidade (72px, fundo danger-dim, borda danger, texto % grande e bold)
  - Nome do componente (16px bold) + "Probabilidade X · Horizonte: Y dias" + "Veículo: placa — modelo"
  - Texto da base_historica
  - Grid 2 colunas (boxes dashed): Sintomas Correlacionados (bullet list) + Peças Sugeridas (numbered list + "Economia estimada: R$ X" em verde)
- **Box "Ação Recomendada":** Bloco danger-dim com texto da recomendação + botão vermelho "Abrir Ordem de Serviço"
- **Box dashed "JSON da Resposta (mock)":** pre com JSON.stringify do diagnóstico inteiro (font 9px, mono, text-dim)
- Se nenhum selecionado: "Selecione um alerta para ver o diagnóstico"

### 5. Plano de Manutenção (/plano)
- **3 KPI cards:** "Esta Semana" (total agendadas), "Preditivas" (geradas por IA, warning), "Corretivas" (urgentes, danger)
- **Calendário semanal (box):** Grid 7 colunas (Seg-Dom). Header com dia da semana + número. Dia atual em bold + underline accent. Para cada dia, listar manutenções agendadas com data_agendada naquele dia. Cada evento: classe por tipo (preventiva=verde, preditiva=amarelo, corretiva=vermelho), mostrando placa + descrição.
- **Fila de Prioridade (box):** GET /api/manutencoes/prioridade. Lista numerada (1, 2, 3...) com círculo colorido (1=danger, 2=warning, 3=accent), placa, descrição, badge tipo, probabilidade %.
- **Legenda:** ■ Preventiva (verde) / ■ Preditiva IA (amarelo) / ■ Corretiva (vermelho)

### 6. Relatórios (/relatorios)
- **3 KPI cards:** Custo Total Mês (success), Horas Paradas (accent), Economia Preditiva (success)
- **Layout flex:** 1/3 + 2/3
  - **BarChart (Recharts):** "Custo por Tipo de Manutenção" — 3 barras (Preventiva verde, Preditiva amarelo, Corretiva vermelho). Dados de GET /api/relatorios/custos.
  - **LineChart (Recharts):** "Tendência de Custos (6 meses)" — 3 linhas. Corretiva em linha tracejada. Dados de GET /api/relatorios/tendencia. Tooltip e Legend inclusos.
- **Top 5 Veículos por custo (box):** Barras horizontais com gradiente (accent → danger), placa à esquerda, valor à direita em mono.
- **BarChart horas paradas (Recharts):** Dados de GET /api/relatorios/disponibilidade. Barras amarelas.
- **Nota italic no final:** "↑ Na versão final, os relatórios serão gerados dinamicamente + insights da IA"

Configuração dos gráficos Recharts:
- CartesianGrid: strokeDasharray="3 3", stroke="#2e3345"
- XAxis/YAxis: tick fill "#94a3b8", fontSize 10-11
- Tooltip: contentStyle background "#1a1d27", border "#2e3345", borderRadius 6
- Formatter de valores: "R$ X.XXX" com toLocaleString('pt-BR')

---

## API SERVICE LAYER (frontend/src/services/api.js)

Camada centralizada de fetch. Base: `/api`. Todas as chamadas retornam JSON. Incluir:
- getVeiculos(), getVeiculo(id), getDashboardStats()
- getOcorrencias(), createOcorrencia(data) [POST]
- getManutAgendadas(), getFilaPrioridade()
- getRelatorioCustos(), getRelatorioDisponibilidade(), getRelatorioTendencia()
- getAlertas(lido?), marcarAlertaLido(id) [PUT], getDiagnostico(id)

---

## main.py (BACKEND)

- Registrar todos os 5 routers
- CORS com allow_origins=["*"]
- @app.on_event("startup"): chamar init_db() e seed()
- GET / → retorna JSON com info do app
- GET /api/health → retorna {"status": "ok"}

---

## start.sh

Script bash que:
1. Instala deps do backend (pip install -r requirements.txt)
2. Inicia backend (uvicorn main:app --reload --port 8000) em background
3. Instala deps do frontend (npm install)
4. Inicia frontend (npm run dev) em background
5. Mostra URLs e instrução de ngrok
6. Trap Ctrl+C para matar ambos processos

---

## .gitignore

Ignorar: __pycache__, *.pyc, *.db, node_modules, frontend/dist, .env, venv, .vscode, .idea, .DS_Store, *.log

---

## README.md

Criar um README completo com seções marcadas com [PREENCHER] onde o aluno vai completar com sua experiência. Seções:

1. **Descrição do Problema e da Solução** — Explicação do problema de manutenção reativa em frotas + como o FleetPred resolve + como a IA será integrada via function calling/structured output
2. **Escolhas de Design** — Justificativas para: FastAPI (async + Pydantic + docs auto), React (SPA com 6 telas, navegação, state), SQLite (sem infra), tema escuro (monitoramento industrial), semáforo de cores (priorização rápida), formulário condicional (sintomas por sistema), sidebar fixa (escalabilidade), 6 tabelas separadas (ciclos de vida diferentes), mock com JSON estruturado (contrato de API pro LLM)
3. **O que Funcionou** — [PREENCHER] com exemplos de prompts
4. **O que Não Funcionou** — [PREENCHER] com problemas encontrados
5. **Uso do Agente de Codificação** — [PREENCHER] ferramenta, processo, prompts, % gerado vs manual
6. **Como Executar** — Instruções completas com pré-requisitos, instalação, start.sh, ngrok
7. **Estrutura do Projeto** — Árvore de diretórios com descrição de cada arquivo
8. **Links** — [PREENCHER] endpoint + repositório

---

## REGRAS GERAIS

1. Todo texto da UI em português brasileiro
2. Valores monetários formatados como "R$ X.XXX" usando toLocaleString('pt-BR')
3. Km formatado com separador de milhar (pt-BR)
4. Datas no formato DD/MM/YYYY na exibição
5. JSON armazenado como TEXT no SQLite, parseado com json.loads/json.dumps
6. Nenhuma dependência de serviço externo — tudo roda local
7. O frontend deve funcionar 100% buscando dados da API, sem dados hardcoded nas páginas
8. Cada página deve ter estado de loading enquanto busca dados
9. Gerar TODOS os arquivos listados na estrutura, sem pular nenhum
10. O código deve estar pronto para rodar com `./start.sh` sem ajustes manuais
