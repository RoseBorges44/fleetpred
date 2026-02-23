import json
import re
import time

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from agents.llm_config import get_llm, load_prompt
from tools.fleet_tools import consultar_saude_componentes as _consultar_saude


@tool
def consultar_saude_componentes_tool(veiculo_id: int) -> str:
    """Retorna a saúde percentual de cada componente de um veículo.
    Usar quando precisar avaliar o estado atual dos componentes para
    correlacionar sintomas reportados com degradação real do equipamento."""
    return json.dumps(_consultar_saude(veiculo_id), ensure_ascii=False)


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


def run(sistema: str, sintomas: list[str], veiculo_id: int, km_atual: float) -> dict:
    start = time.time()
    prompt = load_prompt("diagnostician")
    tools = [consultar_saude_componentes_tool]
    tools_map = {t.name: t for t in tools}
    llm = get_llm(temperature=0.2).bind_tools(tools)

    user_msg = (
        f"Sistema: {sistema}\n"
        f"Sintomas: {', '.join(sintomas)}\n"
        f"Veículo ID: {veiculo_id}\n"
        f"KM atual: {km_atual}"
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
    print(f"[Diagnostician] concluído em {elapsed:.1f}s")
    return _parse_json(response.content)
