import json
import re
import time

from langchain_core.messages import SystemMessage, HumanMessage

from agents.llm_config import get_llm, load_prompt


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


def run(diagnostico: dict, historico: dict) -> dict:
    start = time.time()
    prompt = load_prompt("planner")
    llm = get_llm(temperature=0.3)

    user_msg = (
        f"Diagnóstico técnico:\n{json.dumps(diagnostico, ensure_ascii=False, indent=2)}\n\n"
        f"Análise histórica:\n{json.dumps(historico, ensure_ascii=False, indent=2)}"
    )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_msg),
    ]

    response = llm.invoke(messages)

    elapsed = time.time() - start
    print(f"[Planner] concluído em {elapsed:.1f}s")
    return _parse_json(response.content)
