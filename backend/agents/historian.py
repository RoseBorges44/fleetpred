import json
import re
import time

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from agents.llm_config import get_llm, load_prompt
from tools.fleet_tools import (
    consultar_historico_veiculo as _consultar_historico,
    buscar_padroes_frota as _buscar_padroes,
)


@tool
def consultar_historico_tool(veiculo_id: int) -> str:
    """Busca as últimas manutenções de um veículo específico.
    Usar quando precisar entender o histórico de manutenção de um veículo
    para identificar padrões de falha recorrentes."""
    return json.dumps(_consultar_historico(veiculo_id), ensure_ascii=False)


@tool
def buscar_padroes_tool(sistema: str, sintomas: list[str]) -> str:
    """Busca ocorrências de outros veículos com o mesmo sistema e sintomas parecidos.
    Usar quando precisar comparar com casos similares na frota."""
    return json.dumps(_buscar_padroes(sistema, sintomas), ensure_ascii=False)


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


def run(sistema: str, sintomas: list[str], veiculo_id: int) -> dict:
    start = time.time()
    prompt = load_prompt("historian")
    tools = [consultar_historico_tool, buscar_padroes_tool]
    tools_map = {t.name: t for t in tools}
    llm = get_llm(temperature=0.1).bind_tools(tools)

    user_msg = (
        f"Sistema: {sistema}\n"
        f"Sintomas: {', '.join(sintomas)}\n"
        f"Veículo ID: {veiculo_id}"
    )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_msg),
    ]

    response = llm.invoke(messages)
    while response.tool_calls:
        messages.append(response)
        for tc in response.tool_calls:
            result = tools_map[tc["name"]].invoke(tc["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        response = llm.invoke(messages)

    elapsed = time.time() - start
    print(f"[Historian] concluído em {elapsed:.1f}s")
    return _parse_json(response.content)
