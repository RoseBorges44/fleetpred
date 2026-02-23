import json
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_connection
from mock_ai import generate_mock_diagnostic
from agents.orchestrator import orchestrate

router = APIRouter(prefix="/api/ocorrencias", tags=["ocorrências"])


class OcorrenciaCreate(BaseModel):
    veiculo_id: int
    sistema: str
    sintomas: list[str]
    descricao: str
    severidade: str
    km_ocorrencia: float


@router.get("/")
def listar_ocorrencias():
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            o.*,
            v.placa,
            v.modelo
        FROM ocorrencias o
        JOIN veiculos v ON v.id = o.veiculo_id
        ORDER BY o.data_ocorrencia DESC
    """).fetchall()
    conn.close()

    result = []
    for r in rows:
        item = dict(r)
        item["sintomas"] = json.loads(item["sintomas"]) if item["sintomas"] else []
        result.append(item)
    return result


@router.post("/", status_code=201)
def criar_ocorrencia(payload: OcorrenciaCreate):
    conn = get_connection()

    # Verificar se veículo existe
    veiculo = conn.execute(
        "SELECT * FROM veiculos WHERE id = ? AND ativo = 1", (payload.veiculo_id,)
    ).fetchone()
    if not veiculo:
        conn.close()
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    # 1. Inserir ocorrência
    cursor = conn.execute(
        "INSERT INTO ocorrencias (veiculo_id, data_ocorrencia, sistema, sintomas, descricao, severidade, km_ocorrencia, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'em_analise')",
        (
            payload.veiculo_id,
            date.today().isoformat(),
            payload.sistema,
            json.dumps(payload.sintomas),
            payload.descricao,
            payload.severidade,
            payload.km_ocorrencia,
        ),
    )
    ocorrencia_id = cursor.lastrowid

    # 2. Gerar diagnóstico via multi-agente LLM (fallback: mock)
    try:
        diag = orchestrate(
            veiculo_id=payload.veiculo_id,
            sistema=payload.sistema,
            sintomas=payload.sintomas,
            descricao=payload.descricao,
            severidade=payload.severidade,
            km=payload.km_ocorrencia,
        )
    except Exception as e:
        print(f"LLM falhou, usando mock: {e}")
        diag = generate_mock_diagnostic(
            sistema=payload.sistema,
            sintomas=payload.sintomas,
            veiculo_km=payload.km_ocorrencia,
        )

    # 3. Salvar diagnóstico
    cursor = conn.execute(
        "INSERT INTO diagnosticos "
        "(ocorrencia_id, veiculo_id, componente, probabilidade_falha, horizonte_dias, "
        "severidade, sintomas_correlacionados, recomendacao, pecas_sugeridas, "
        "economia_estimada, base_historica) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            ocorrencia_id,
            payload.veiculo_id,
            diag["componente"],
            diag["probabilidade_falha"],
            diag["horizonte_dias"],
            diag["severidade"],
            json.dumps(diag["sintomas_correlacionados"]),
            diag["recomendacao"],
            json.dumps(diag["pecas_sugeridas"]),
            diag["economia_estimada"],
            diag["base_historica"],
        ),
    )
    diagnostico_id = cursor.lastrowid

    # 4. Criar alerta
    tipo_alerta = "critico" if diag["severidade"] in ("alta", "critica") else "atencao"
    mensagem = (
        f"{tipo_alerta.upper()}: {diag['componente']} no {veiculo['placa']} ({veiculo['modelo']}). "
        f"Probabilidade de falha {int(diag['probabilidade_falha'] * 100)}% "
        f"em {diag['horizonte_dias']} dias. {diag['recomendacao'][:80]}..."
    )

    conn.execute(
        "INSERT INTO alertas (veiculo_id, diagnostico_id, tipo, mensagem) VALUES (?, ?, ?, ?)",
        (payload.veiculo_id, diagnostico_id, tipo_alerta, mensagem),
    )

    conn.commit()
    conn.close()

    return {
        "ocorrencia_id": ocorrencia_id,
        "diagnostico": {
            "id": diagnostico_id,
            **diag,
        },
    }
