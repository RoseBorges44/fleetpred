from fastapi import APIRouter
from database import get_connection

router = APIRouter(prefix="/api/manutencoes", tags=["manutenções"])


@router.get("/agendadas")
def listar_agendadas():
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            m.*,
            v.placa,
            v.modelo
        FROM manutencoes m
        JOIN veiculos v ON v.id = m.veiculo_id
        WHERE m.status = 'agendada'
        ORDER BY m.data_agendada ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/prioridade")
def listar_por_prioridade():
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            m.*,
            v.placa,
            v.modelo,
            d.probabilidade_falha,
            d.horizonte_dias,
            d.componente AS diagnostico_componente
        FROM manutencoes m
        JOIN veiculos v ON v.id = m.veiculo_id
        LEFT JOIN diagnosticos d ON d.veiculo_id = m.veiculo_id
            AND d.id = (
                SELECT MAX(d2.id) FROM diagnosticos d2
                WHERE d2.veiculo_id = m.veiculo_id
            )
        WHERE m.status = 'agendada'
        ORDER BY
            CASE m.tipo
                WHEN 'corretiva'  THEN 0
                WHEN 'preditiva'  THEN 1
                WHEN 'preventiva' THEN 2
            END,
            COALESCE(d.probabilidade_falha, 0) DESC,
            m.data_agendada ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
