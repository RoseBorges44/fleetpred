import random
from datetime import date, timedelta
from fastapi import APIRouter
from database import get_connection

router = APIRouter(prefix="/api/relatorios", tags=["relatórios"])


@router.get("/custos")
def relatorio_custos():
    conn = get_connection()

    custo_total = conn.execute(
        "SELECT COALESCE(SUM(custo), 0) FROM manutencoes WHERE status = 'concluida'"
    ).fetchone()[0]

    por_tipo = conn.execute("""
        SELECT
            tipo,
            COUNT(*) AS quantidade,
            COALESCE(SUM(custo), 0) AS total,
            COALESCE(ROUND(AVG(custo), 2), 0) AS media
        FROM manutencoes
        WHERE status = 'concluida'
        GROUP BY tipo
    """).fetchall()

    top_veiculos = conn.execute("""
        SELECT
            v.placa,
            v.modelo,
            COUNT(m.id) AS total_manutencoes,
            COALESCE(SUM(m.custo), 0) AS custo_total
        FROM manutencoes m
        JOIN veiculos v ON v.id = m.veiculo_id
        WHERE m.status = 'concluida'
        GROUP BY m.veiculo_id
        ORDER BY custo_total DESC
        LIMIT 5
    """).fetchall()

    economia_preditiva = conn.execute(
        "SELECT COALESCE(SUM(economia_estimada), 0) FROM diagnosticos"
    ).fetchone()[0]

    conn.close()
    return {
        "custo_total": custo_total,
        "por_tipo": [dict(r) for r in por_tipo],
        "top_5_veiculos": [dict(r) for r in top_veiculos],
        "economia_preditiva_estimada": economia_preditiva,
    }


@router.get("/disponibilidade")
def relatorio_disponibilidade():
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) FROM veiculos WHERE ativo = 1").fetchone()[0]
    parados = conn.execute(
        "SELECT COUNT(*) FROM veiculos WHERE ativo = 1 AND status = 'critico'"
    ).fetchone()[0]
    disponibilidade_pct = round(((total - parados) / total * 100), 1) if total > 0 else 0

    conn.close()

    # Mock: horas paradas por mês (últimos 6 meses, tendência decrescente
    # simulando melhoria com manutenção preditiva)
    hoje = date.today()
    horas_paradas_mensal = []
    base_horas = 120
    for i in range(5, -1, -1):
        mes = hoje - timedelta(days=30 * i)
        horas = max(15, base_horas - (5 - i) * 18 + random.randint(-5, 5))
        horas_paradas_mensal.append({
            "mes": mes.strftime("%Y-%m"),
            "horas_paradas": horas,
        })

    return {
        "total_veiculos": total,
        "veiculos_parados": parados,
        "disponibilidade_pct": disponibilidade_pct,
        "horas_paradas_mensal": horas_paradas_mensal,
    }


@router.get("/tendencia")
def relatorio_tendencia():
    # Mock: custos por tipo nos últimos 6 meses
    # Tendência: corretiva caindo, preditiva subindo (mostra valor do sistema)
    hoje = date.today()
    meses = []
    for i in range(5, -1, -1):
        mes = hoje - timedelta(days=30 * i)
        fator = 5 - i  # 0 a 5, do mais antigo ao mais recente

        corretiva = max(500, 8000 - fator * 1200 + random.randint(-300, 300))
        preditiva = 800 + fator * 900 + random.randint(-200, 200)
        preventiva = 3000 + random.randint(-400, 400)

        meses.append({
            "mes": mes.strftime("%Y-%m"),
            "corretiva": round(corretiva, 2),
            "preditiva": round(preditiva, 2),
            "preventiva": round(preventiva, 2),
            "total": round(corretiva + preditiva + preventiva, 2),
        })

    return {"tendencia_mensal": meses}
