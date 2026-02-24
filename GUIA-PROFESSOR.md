# Guia de Teste — FleetPred (para o professor)

## Setup rápido

```bash
git clone https://github.com/RoseBorges44/fleetpred.git
cd fleetpred

# Configurar API key do Gemini
cp backend/.env.example backend/.env
# Editar .env e colocar: GEMINI_API_KEY=sua_chave_aqui
# (gerar chave gratuita em https://aistudio.google.com/apikey)

# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Acessar: http://localhost:5173

---

## Teste 1 — Diagnóstico multi-agente (caso crítico)

1. Clicar em **"Registro Ocorrência"**
2. Selecionar **ABC-1234** (Scania R450, 342.100 km, status crítico)
3. Km: **342100**
4. Sistema: **Motor**
5. Sintomas: **"Vibração anormal"** + **"Perda de potência"**
6. Severidade: **Alta**
7. Submeter

**O que esperar:**
- Terminal do backend mostra os 4 agentes + orquestrador sendo chamados
- Tela exibe diagnóstico com probabilidade, horizonte, peças, economia
- Como severidade é alta, TODOS os agentes são acionados (incluindo planejador e financeiro)

---

## Teste 2 — Diagnóstico simplificado (caso leve)

1. Nova ocorrência
2. Selecionar **GHI-9012** (MB Actros, 128.400 km, status ok)
3. Sistema: **Suspensão**
4. Sintomas: **"Ruído em irregularidades"**
5. Severidade: **Baixa**
6. Submeter

**O que esperar:**
- Terminal mostra APENAS diagnosticador + historiador (sem planejador/financeiro)
- O orquestrador decidiu pular agentes desnecessários por ser severidade baixa

---

## Teste 3 — Fallback (resiliência)

1. Renomear `backend/.env` para `backend/.env.bak`
2. Reiniciar o backend
3. Submeter qualquer ocorrência
4. Terminal mostra: "LLM falhou, usando mock"
5. Diagnóstico ainda funciona (via mock_ai.py)
6. Restaurar: renomear de volta pra `.env`

---

## Onde encontrar as decisões de engenharia

| O que procurar | Onde está |
|---|---|
| System prompts (5 agentes) | `prompts/*.txt` |
| Justificativas dos prompts | `prompts/DECISOES.md` |
| Definição das tools (JSON) | `tools/tool_definitions.json` |
| Justificativas das tools | `tools/DECISOES.md` |
| Implementação das tools | `backend/tools/fleet_tools.py` |
| Agentes LangGraph | `backend/agents/*.py` |
| Config do modelo (temp, etc) | `backend/agents/llm_config.py` |
| Orquestração (grafo) | `backend/agents/orchestrator.py` |
| Ponto de integração | `backend/routes/ocorrencias.py` (linha do try/except) |
| Todas as decisões consolidadas | `README.md` |
