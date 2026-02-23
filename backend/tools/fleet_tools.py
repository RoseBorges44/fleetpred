import json
from database import get_connection


def consultar_historico_veiculo(veiculo_id: int, limite: int = 10) -> dict:
    """
    Busca as últimas N manutenções de um veículo específico.
    Usar quando precisar entender o histórico de manutenção de um veículo
    para identificar padrões de falha recorrentes ou avaliar o estado geral.
    """
    try:
        conn = get_connection()

        veiculo = conn.execute(
            "SELECT placa, modelo, km_atual FROM veiculos WHERE id = ?",
            (veiculo_id,),
        ).fetchone()

        if not veiculo:
            conn.close()
            return {"erro": f"Veículo {veiculo_id} não encontrado"}

        manutencoes = conn.execute(
            """
            SELECT tipo, descricao, data_realizada, custo, pecas
            FROM manutencoes
            WHERE veiculo_id = ?
            ORDER BY data_realizada DESC
            LIMIT ?
            """,
            (veiculo_id, limite),
        ).fetchall()

        conn.close()

        lista_manutencoes = []
        for m in manutencoes:
            pecas = json.loads(m["pecas"]) if m["pecas"] else []
            lista_manutencoes.append({
                "tipo": m["tipo"],
                "descricao": m["descricao"],
                "data": m["data_realizada"],
                "custo": m["custo"],
                "pecas": pecas,
            })

        return {
            "veiculo": {
                "placa": veiculo["placa"],
                "modelo": veiculo["modelo"],
                "km_atual": veiculo["km_atual"],
            },
            "manutencoes": lista_manutencoes,
        }

    except Exception as e:
        return {"erro": str(e)}


def buscar_padroes_frota(sistema: str, sintomas: list[str]) -> dict:
    """
    Busca ocorrências de outros veículos com o mesmo sistema afetado e sintomas
    parecidos, incluindo o diagnóstico e resultado quando disponível.
    Usar quando precisar comparar uma ocorrência atual com casos similares
    na frota para identificar padrões de falha comuns.
    """
    try:
        conn = get_connection()

        ocorrencias = conn.execute(
            """
            SELECT o.id, o.veiculo_id, o.sintomas, o.descricao, o.severidade,
                   o.km_ocorrencia, o.status, o.data_ocorrencia,
                   v.modelo, v.placa,
                   d.componente, d.probabilidade_falha, d.recomendacao
            FROM ocorrencias o
            JOIN veiculos v ON v.id = o.veiculo_id
            LEFT JOIN diagnosticos d ON d.ocorrencia_id = o.id
            WHERE o.sistema = ?
            ORDER BY o.data_ocorrencia DESC
            """,
            (sistema,),
        ).fetchall()

        conn.close()

        casos_similares = []
        for oc in ocorrencias:
            sintomas_oc = json.loads(oc["sintomas"]) if oc["sintomas"] else []

            # Verifica se há interseção entre sintomas buscados e da ocorrência
            sintomas_em_comum = set(s.lower() for s in sintomas) & set(
                s.lower() for s in sintomas_oc
            )
            if not sintomas_em_comum:
                continue

            casos_similares.append({
                "veiculo": f"{oc['placa']} ({oc['modelo']})",
                "data": oc["data_ocorrencia"],
                "sintomas": sintomas_oc,
                "sintomas_em_comum": list(sintomas_em_comum),
                "severidade": oc["severidade"],
                "km": oc["km_ocorrencia"],
                "status": oc["status"],
                "diagnostico": oc["componente"],
                "probabilidade_falha": oc["probabilidade_falha"],
                "recomendacao": oc["recomendacao"],
            })

        return {
            "casos_similares": casos_similares,
            "total": len(casos_similares),
        }

    except Exception as e:
        return {"erro": str(e)}


def consultar_saude_componentes(veiculo_id: int) -> dict:
    """
    Retorna a saúde percentual de cada componente de um veículo.
    Usar quando precisar avaliar o estado atual dos componentes para
    correlacionar sintomas reportados com degradação real do equipamento.
    """
    try:
        conn = get_connection()

        componentes = conn.execute(
            """
            SELECT nome, saude_pct, ultima_inspecao
            FROM componentes
            WHERE veiculo_id = ?
            ORDER BY saude_pct ASC
            """,
            (veiculo_id,),
        ).fetchall()

        conn.close()

        if not componentes:
            return {"erro": f"Nenhum componente encontrado para veículo {veiculo_id}"}

        return {
            "componentes": [
                {
                    "nome": c["nome"],
                    "saude_pct": c["saude_pct"],
                    "ultima_inspecao": c["ultima_inspecao"],
                }
                for c in componentes
            ]
        }

    except Exception as e:
        return {"erro": str(e)}


def calcular_economia(sistema: str, componente: str, modelo_veiculo: str) -> dict:
    """
    Calcula a economia estimada de manutenção preventiva vs corretiva para
    um componente, baseado em dados históricos reais do banco.
    Usar quando precisar justificar financeiramente uma intervenção preventiva
    ou preditiva comparando com o custo de uma falha corretiva.
    """
    try:
        conn = get_connection()

        # Busca custos reais de manutenções preventivas neste sistema
        preventivas = conn.execute(
            """
            SELECT AVG(m.custo) as custo_medio, COUNT(*) as total
            FROM manutencoes m
            JOIN veiculos v ON v.id = m.veiculo_id
            WHERE m.tipo = 'preventiva'
              AND m.custo IS NOT NULL
              AND m.descricao LIKE ?
            """,
            (f"%{sistema}%",),
        ).fetchone()

        # Busca custos reais de manutenções corretivas neste sistema
        corretivas = conn.execute(
            """
            SELECT AVG(m.custo) as custo_medio, COUNT(*) as total
            FROM manutencoes m
            JOIN veiculos v ON v.id = m.veiculo_id
            WHERE m.tipo = 'corretiva'
              AND m.custo IS NOT NULL
              AND m.descricao LIKE ?
            """,
            (f"%{sistema}%",),
        ).fetchone()

        conn.close()

        # Estimativas de mercado brasileiro para caminhões pesados em mineração
        estimativas_mercado = {
            "Motor": {"preventiva": 4500, "corretiva": 28000},
            "Freios": {"preventiva": 2800, "corretiva": 12000},
            "Arrefecimento": {"preventiva": 1800, "corretiva": 9500},
            "Transmissão": {"preventiva": 5500, "corretiva": 35000},
            "Suspensão": {"preventiva": 3200, "corretiva": 15000},
            "Sistema Elétrico": {"preventiva": 1500, "corretiva": 7000},
            "Pneus": {"preventiva": 4000, "corretiva": 8000},
        }

        fallback = estimativas_mercado.get(
            sistema, {"preventiva": 3000, "corretiva": 15000}
        )

        # Usa dados reais se houver pelo menos 2 registros, senão usa estimativa
        custo_prev = (
            round(preventivas["custo_medio"], 2)
            if preventivas["total"] and preventivas["total"] >= 2
            else fallback["preventiva"]
        )

        custo_corr = (
            round(corretivas["custo_medio"], 2)
            if corretivas["total"] and corretivas["total"] >= 2
            else fallback["corretiva"]
        )

        economia = round(custo_corr - custo_prev, 2)
        fator = round(custo_corr / custo_prev, 1) if custo_prev > 0 else 0

        fonte_prev = (
            f"histórico ({preventivas['total']} registros)"
            if preventivas["total"] and preventivas["total"] >= 2
            else "estimativa de mercado"
        )
        fonte_corr = (
            f"histórico ({corretivas['total']} registros)"
            if corretivas["total"] and corretivas["total"] >= 2
            else "estimativa de mercado"
        )

        return {
            "custo_preventiva": custo_prev,
            "custo_corretiva": custo_corr,
            "economia": economia,
            "fator_multiplicador": f"{fator}x",
            "fonte_dados": {
                "preventiva": fonte_prev,
                "corretiva": fonte_corr,
            },
            "modelo_veiculo": modelo_veiculo,
            "sistema": sistema,
            "componente": componente,
        }

    except Exception as e:
        return {"erro": str(e)}
