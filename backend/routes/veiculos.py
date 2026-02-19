import json
from fastapi import APIRouter, HTTPException
from database import get_connection

router = APIRouter(prefix="/api/veiculos", tags=["veículos"])


@router.get("/stats/dashboard")
def dashboard_stats():
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) FROM veiculos WHERE ativo = 1").fetchone()[0]

    status_rows = conn.execute(
        "SELECT status, COUNT(*) as count FROM veiculos WHERE ativo = 1 GROUP BY status"
    ).fetchall()
    status_breakdown = {row["status"]: row["count"] for row in status_rows}

    alertas_pendentes = conn.execute(
        "SELECT COUNT(*) FROM alertas WHERE lido = 0"
    ).fetchone()[0]

    alertas_criticos = conn.execute(
        "SELECT COUNT(*) FROM alertas WHERE lido = 0 AND tipo = 'critico'"
    ).fetchone()[0]

    manutencoes_hoje = conn.execute(
        "SELECT COUNT(*) FROM manutencoes WHERE data_agendada = date('now') AND status = 'agendada'"
    ).fetchone()[0]

    em_operacao = status_breakdown.get("ok", 0) + status_breakdown.get("atencao", 0)
    disponibilidade_pct = round((em_operacao / total * 100), 1) if total > 0 else 0

    conn.close()
    return {
        "total_veiculos": total,
        "status_breakdown": status_breakdown,
        "alertas_pendentes": alertas_pendentes,
        "alertas_criticos": alertas_criticos,
        "manutencoes_hoje": manutencoes_hoje,
        "disponibilidade_pct": disponibilidade_pct,
    }


@router.get("/")
def listar_veiculos():
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            v.*,
            COALESCE(ROUND(AVG(c.saude_pct), 1), 0) AS saude_media,
            (SELECT COUNT(*) FROM alertas a WHERE a.veiculo_id = v.id AND a.lido = 0) AS alertas_pendentes
        FROM veiculos v
        LEFT JOIN componentes c ON c.veiculo_id = v.id
        WHERE v.ativo = 1
        GROUP BY v.id
        ORDER BY
            CASE v.status
                WHEN 'critico' THEN 0
                WHEN 'atencao' THEN 1
                ELSE 2
            END,
            v.placa
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{veiculo_id}")
def detalhe_veiculo(veiculo_id: int):
    conn = get_connection()

    veiculo = conn.execute(
        "SELECT * FROM veiculos WHERE id = ? AND ativo = 1", (veiculo_id,)
    ).fetchone()
    if not veiculo:
        conn.close()
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    componentes = conn.execute(
        "SELECT * FROM componentes WHERE veiculo_id = ? ORDER BY saude_pct ASC",
        (veiculo_id,),
    ).fetchall()

    manutencoes = conn.execute(
        "SELECT * FROM manutencoes WHERE veiculo_id = ? ORDER BY COALESCE(data_realizada, data_agendada) DESC LIMIT 10",
        (veiculo_id,),
    ).fetchall()

    alertas = conn.execute(
        "SELECT * FROM alertas WHERE veiculo_id = ? ORDER BY data_criacao DESC LIMIT 5",
        (veiculo_id,),
    ).fetchall()

    conn.close()
    return {
        "veiculo": dict(veiculo),
        "componentes": [dict(c) for c in componentes],
        "manutencoes": [dict(m) for m in manutencoes],
        "alertas": [dict(a) for a in alertas],
    }
