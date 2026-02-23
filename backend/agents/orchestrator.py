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


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
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
    result = diagnostician.run(
        sistema=state["sistema"],
        sintomas=state["sintomas"],
        veiculo_id=state["veiculo_id"],
        km_atual=state["km"],
    )
    return {"diagnostico": result}


def analisar_historico_node(state: OrchestratorState) -> dict:
    result = historian.run(
        sistema=state["sistema"],
        sintomas=state["sintomas"],
        veiculo_id=state["veiculo_id"],
    )
    return {"historico": result}


def planejar_node(state: OrchestratorState) -> dict:
    result = planner.run(
        diagnostico=state["diagnostico"],
        historico=state["historico"],
    )
    return {"planejamento": result}


def analisar_financeiro_node(state: OrchestratorState) -> dict:
    componente = state["diagnostico"].get("componente", state["sistema"])
    result = financial.run(
        sistema=state["sistema"],
        componente=componente,
        modelo_veiculo=state["modelo_veiculo"],
    )
    return {"financeiro": result}


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
    result = _parse_json(response.content)
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
