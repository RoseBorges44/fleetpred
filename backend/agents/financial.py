import json
import re
import time

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from agents.llm_config import get_llm, load_prompt
from tools.fleet_tools import calcular_economia as _calcular_economia


@tool
def calcular_economia_tool(sistema: str, componente: str, modelo_veiculo: str) -> str:
    """Calcula a economia estimada de manutenção preventiva vs corretiva.
    Usar quando precisar justificar financeiramente uma intervenção preventiva."""
    return json.dumps(_calcular_economia(sistema, componente, modelo_veiculo), ensure_ascii=False)


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


def run(sistema: str, componente: str, modelo_veiculo: str) -> dict:
    start = time.time()
    prompt = load_prompt("financial")
    tools = [calcular_economia_tool]
    tools_map = {t.name: t for t in tools}
    llm = get_llm(temperature=0.1).bind_tools(tools)

    user_msg = (
        f"Sistema: {sistema}\n"
        f"Componente: {componente}\n"
        f"Modelo do veículo: {modelo_veiculo}"
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
    print(f"[Financial] concluído em {elapsed:.1f}s")
    return _parse_json(response.content)
