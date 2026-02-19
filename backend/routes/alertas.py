import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from database import get_connection

router = APIRouter(prefix="/api/alertas", tags=["alertas"])


@router.get("/")
def listar_alertas(lido: Optional[int] = Query(None, ge=0, le=1)):
    conn = get_connection()

    query = """
        SELECT
            a.*,
            v.placa,
            v.modelo,
            d.componente       AS diag_componente,
            d.probabilidade_falha AS diag_probabilidade,
            d.horizonte_dias   AS diag_horizonte,
            d.severidade       AS diag_severidade
        FROM alertas a
        JOIN veiculos v ON v.id = a.veiculo_id
        LEFT JOIN diagnosticos d ON d.id = a.diagnostico_id
    """
    params = []
    if lido is not None:
        query += " WHERE a.lido = ?"
        params.append(lido)

    query += " ORDER BY a.lido ASC, a.data_criacao DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.put("/{alerta_id}/lido")
def marcar_como_lido(alerta_id: int):
    conn = get_connection()

    alerta = conn.execute("SELECT * FROM alertas WHERE id = ?", (alerta_id,)).fetchone()
    if not alerta:
        conn.close()
        raise HTTPException(status_code=404, detail="Alerta não encontrado")

    conn.execute("UPDATE alertas SET lido = 1 WHERE id = ?", (alerta_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "alerta_id": alerta_id}


@router.get("/diagnostico/{diagnostico_id}")
def detalhe_diagnostico(diagnostico_id: int):
    conn = get_connection()

    diag = conn.execute("""
        SELECT
            d.*,
            v.placa,
            v.modelo,
            v.km_atual,
            o.sistema,
            o.descricao AS ocorrencia_descricao,
            o.severidade AS ocorrencia_severidade
        FROM diagnosticos d
        JOIN veiculos v ON v.id = d.veiculo_id
        JOIN ocorrencias o ON o.id = d.ocorrencia_id
        WHERE d.id = ?
    """, (diagnostico_id,)).fetchone()

    if not diag:
        conn.close()
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")

    conn.close()

    result = dict(diag)
    result["sintomas_correlacionados"] = (
        json.loads(result["sintomas_correlacionados"])
        if result["sintomas_correlacionados"]
        else []
    )
    result["pecas_sugeridas"] = (
        json.loads(result["pecas_sugeridas"])
        if result["pecas_sugeridas"]
        else []
    )
    return result
