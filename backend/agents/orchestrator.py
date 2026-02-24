import json
import re
import time
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from agents.llm_config import get_llm, load_prompt
from agents import diagnostician, historian, planner, financial
from database import get_connection
from mock_ai import generate_mock_diagnostic


class OrchestratorState(TypedDict):
    veiculo_id: int
    sistema: str
    sintomas: list[str]
    descricao: str
    severidade: str
    km: float
    modelo_veiculo: str
    diagnostico: dict
    historico: dict
    planejamento: dict
    financeiro: dict
    resultado_final: dict


def _safe_dict(value, label="") -> dict:
    """Converte qualquer retorno de agente/LLM em dict de forma segura."""
    if isinstance(value, dict):
        return value

    if isinstance(value, list):
        print(f"[parsing:{label}] recebeu list (len={len(value)}), extraindo primeiro elemento")
        if not value:
            return {}
        return _safe_dict(value[0], label)

    if not isinstance(value, str):
        print(f"[parsing:{label}] tipo inesperado: {type(value).__name__}, convertendo para str")
        value = str(value)

    # Remove blocos markdown ```json ... ``` ou ``` ... ```
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", value.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

    # Tenta parse direto
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list) and parsed:
            print(f"[parsing:{label}] JSON parseado era list, pegando primeiro elemento")
            return parsed[0] if isinstance(parsed[0], dict) else {}
        return {}
    except (json.JSONDecodeError, TypeError):
        pass

    # Tenta extrair {...} do texto com regex
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    print(f"[parsing:{label}] FALHOU — conteúdo recebido: {value[:200]}")
    return {}


# ── Graph nodes ──────────────────────────────────────────────────────────


def classificar_node(state: OrchestratorState) -> dict:
    conn = get_connection()
    veiculo = conn.execute(
        "SELECT modelo FROM veiculos WHERE id = ?", (state["veiculo_id"],)
    ).fetchone()
    conn.close()
    modelo = veiculo["modelo"] if veiculo else "Desconhecido"
    print(f"[Orchestrator] Veículo {state['veiculo_id']} — modelo: {modelo}")
    return {"modelo_veiculo": modelo}


def diagnosticar_node(state: OrchestratorState) -> dict:
    try:
        result = diagnostician.run(
            sistema=state["sistema"],
            sintomas=state["sintomas"],
            veiculo_id=state["veiculo_id"],
            km_atual=state["km"],
        )
        return {"diagnostico": _safe_dict(result, "diagnosticador")}
    except Exception as e:
        print(f"[diagnosticar] ERRO: {type(e).__name__}: {e}")
        return {"diagnostico": {}}


def analisar_historico_node(state: OrchestratorState) -> dict:
    try:
        result = historian.run(
            sistema=state["sistema"],
            sintomas=state["sintomas"],
            veiculo_id=state["veiculo_id"],
        )
        return {"historico": _safe_dict(result, "historiador")}
    except Exception as e:
        print(f"[analisar_historico] ERRO: {type(e).__name__}: {e}")
        return {"historico": {}}


def planejar_node(state: OrchestratorState) -> dict:
    try:
        result = planner.run(
            diagnostico=state["diagnostico"],
            historico=state["historico"],
        )
        return {"planejamento": _safe_dict(result, "planejador")}
    except Exception as e:
        print(f"[planejar] ERRO: {type(e).__name__}: {e}")
        return {"planejamento": {}}


def analisar_financeiro_node(state: OrchestratorState) -> dict:
    try:
        componente = state["diagnostico"].get("componente", state["sistema"])
        result = financial.run(
            sistema=state["sistema"],
            componente=componente,
            modelo_veiculo=state["modelo_veiculo"],
        )
        return {"financeiro": _safe_dict(result, "financeiro")}
    except Exception as e:
        print(f"[analisar_financeiro] ERRO: {type(e).__name__}: {e}")
        return {"financeiro": {}}


def decidir_rota(state: OrchestratorState) -> str:
    if state["severidade"] in ("alta", "critica"):
        return "planejar"
    return "consolidar"


def consolidar_node(state: OrchestratorState) -> dict:
    prompt = load_prompt("orchestrator")
    llm = get_llm(temperature=0.1)

    context = {
        "sistema": state["sistema"],
        "sintomas": state["sintomas"],
        "severidade": state["severidade"],
        "km": state["km"],
        "modelo_veiculo": state["modelo_veiculo"],
        "diagnostico": state["diagnostico"],
        "historico": state["historico"],
        "planejamento": state.get("planejamento", {}),
        "financeiro": state.get("financeiro", {}),
    }

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=json.dumps(context, ensure_ascii=False, indent=2)),
    ]

    response = llm.invoke(messages)
    result = _safe_dict(response.content, "consolidar")
    return {"resultado_final": result}


# ── Build the graph ──────────────────────────────────────────────────────

_builder = StateGraph(OrchestratorState)
_builder.add_node("classificar", classificar_node)
_builder.add_node("diagnosticar", diagnosticar_node)
_builder.add_node("analisar_historico", analisar_historico_node)
_builder.add_node("planejar", planejar_node)
_builder.add_node("analisar_financeiro", analisar_financeiro_node)
_builder.add_node("consolidar", consolidar_node)

_builder.set_entry_point("classificar")
_builder.add_edge("classificar", "diagnosticar")
_builder.add_edge("diagnosticar", "analisar_historico")
_builder.add_conditional_edges("analisar_historico", decidir_rota, {
    "planejar": "planejar",
    "consolidar": "consolidar",
})
_builder.add_edge("planejar", "analisar_financeiro")
_builder.add_edge("analisar_financeiro", "consolidar")
_builder.add_edge("consolidar", END)

graph = _builder.compile()


# ── Public API ───────────────────────────────────────────────────────────


def orchestrate(
    veiculo_id: int,
    sistema: str,
    sintomas: list[str],
    descricao: str,
    severidade: str,
    km: float,
) -> dict:
    start = time.time()
    print(f"[Orchestrator] Iniciando diagnóstico — veículo {veiculo_id}, sistema {sistema}")

    try:
        initial_state = {
            "veiculo_id": veiculo_id,
            "sistema": sistema,
            "sintomas": sintomas,
            "descricao": descricao,
            "severidade": severidade,
            "km": km,
            "modelo_veiculo": "",
            "diagnostico": {},
            "historico": {},
            "planejamento": {},
            "financeiro": {},
            "resultado_final": {},
        }

        result = graph.invoke(initial_state)
        final = result["resultado_final"]

        output = {
            "componente": final.get("componente", f"{sistema} — componente não identificado"),
            "probabilidade_falha": final.get("probabilidade_falha", 0.5),
            "horizonte_dias": final.get("horizonte_dias", 15),
            "severidade": final.get("severidade", severidade),
            "sintomas_correlacionados": final.get("sintomas_correlacionados", sintomas),
            "recomendacao": final.get("recomendacao", f"Realizar inspeção do sistema de {sistema.lower()}."),
            "pecas_sugeridas": final.get("pecas_sugeridas", []),
            "economia_estimada": final.get("economia_estimada", 0.0),
            "base_historica": final.get("base_historica", "Análise realizada por IA multi-agente"),
        }

        elapsed = time.time() - start
        print(f"[Orchestrator] Diagnóstico completo em {elapsed:.1f}s")
        return output

    except Exception as e:
        elapsed = time.time() - start
        print(f"[Orchestrator] ERRO após {elapsed:.1f}s: {e}")
        print("[Orchestrator] Usando fallback mock_ai")
        return generate_mock_diagnostic(
            sistema=sistema,
            sintomas=sintomas,
            veiculo_km=km,
        )
