import json
from datetime import date, timedelta
from database import get_connection, init_db

today = date.today()


def já_tem_dados() -> bool:
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM veiculos").fetchone()[0]
    conn.close()
    return count > 0


def seed():
    init_db()

    if já_tem_dados():
        print("Banco já contém dados — seed ignorado.")
        return

    conn = get_connection()
    c = conn.cursor()

    # ── Veículos ──────────────────────────────────────────────────────────
    veiculos = [
        ("ABC-1234", "Scania R450",   2021, 342100, "DC13 450cv",  "critico",  320000),
        ("DEF-5678", "Volvo FH540",   2020, 215800, "D13K 540cv",  "atencao",  200000),
        ("GHI-9012", "MB Actros 2651",2022, 128400, "OM471 510cv", "ok",       120000),
        ("JKL-3456", "Scania R500",   2019, 412700, "DC13 500cv",  "ok",       400000),
        ("MNO-7890", "DAF XF480",     2023,  87200, "MX-13 480cv", "atencao",   80000),
        ("PQR-2345", "Volvo FH460",   2021, 198500, "D13K 460cv",  "ok",       190000),
        ("STU-6789", "Scania G450",   2022, 156300, "DC13 450cv",  "ok",       150000),
        ("VWX-0123", "MB Actros 2546",2023,  64200, "OM471 460cv", "ok",        60000),
        ("YZA-4567", "DAF XF530",     2020, 287600, "MX-13 530cv", "ok",       280000),
        ("BCD-1100", "Iveco S-Way",   2021, 231400, "Cursor 13 480cv","ok",    220000),
    ]

    for v in veiculos:
        c.execute(
            "INSERT INTO veiculos (placa, modelo, ano, km_atual, motor, status, ultimo_oleo_km, data_cadastro) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (*v, (today - timedelta(days=180)).isoformat()),
        )

    conn.commit()

    # mapeamento id por placa
    placas = {row["placa"]: row["id"] for row in c.execute("SELECT id, placa FROM veiculos")}

    # ── Componentes (7 por veículo) ───────────────────────────────────────
    nomes_comp = ["Motor", "Transmissão", "Freios", "Arrefecimento", "Suspensão", "Sistema Elétrico", "Pneus"]

    # saúde coerente com o status do veículo
    saude_por_status = {
        "critico": [38, 55, 60, 25, 70, 65, 45],
        "atencao": [62, 70, 55, 68, 75, 80, 60],
        "ok":      [92, 88, 85, 90, 87, 95, 82],
    }

    for v in veiculos:
        placa, _, _, _, _, status, _ = v
        vid = placas[placa]
        saudes = saude_por_status[status]
        for nome, saude in zip(nomes_comp, saudes):
            c.execute(
                "INSERT INTO componentes (veiculo_id, nome, saude_pct, ultima_inspecao) VALUES (?, ?, ?, ?)",
                (vid, nome, saude, (today - timedelta(days=15)).isoformat()),
            )

    # ── Manutenções (~15) ─────────────────────────────────────────────────
    manutencoes = [
        # concluídas com custo real
        (placas["ABC-1234"], "corretiva",  "Troca bomba d'água e termostato",
         (today - timedelta(days=45)).isoformat(), None, 340200, 4850.00, "concluida",
         "Bomba d'água, termostato, mangueiras", "Vazamento detectado na inspeção"),
        (placas["ABC-1234"], "preventiva", "Troca de óleo e filtros",
         (today - timedelta(days=90)).isoformat(), None, 320000, 1200.00, "concluida",
         "Óleo 15W40, filtro óleo, filtro combustível", None),
        (placas["DEF-5678"], "preventiva", "Revisão sistema de freios",
         (today - timedelta(days=30)).isoformat(), None, 213500, 3200.00, "concluida",
         "Pastilhas, discos dianteiros", "Desgaste acima do normal no eixo dianteiro"),
        (placas["GHI-9012"], "preventiva", "Troca de óleo e filtros",
         (today - timedelta(days=60)).isoformat(), None, 125000, 1350.00, "concluida",
         "Óleo sintético, filtro óleo, filtro ar", None),
        (placas["JKL-3456"], "corretiva",  "Reparo embreagem",
         (today - timedelta(days=20)).isoformat(), None, 410000, 8500.00, "concluida",
         "Kit embreagem completo", "Patinação em subida carregado"),
        (placas["MNO-7890"], "preventiva", "Primeira revisão programada",
         (today - timedelta(days=10)).isoformat(), None, 85000, 980.00, "concluida",
         "Filtros, óleo", None),
        (placas["PQR-2345"], "preventiva", "Alinhamento e balanceamento",
         (today - timedelta(days=25)).isoformat(), None, 195000, 450.00, "concluida",
         None, None),
        (placas["STU-6789"], "corretiva",  "Substituição alternador",
         (today - timedelta(days=55)).isoformat(), None, 152000, 2800.00, "concluida",
         "Alternador 28V 150A", "Falha na carga da bateria"),
        (placas["YZA-4567"], "preventiva", "Troca de óleo e filtros",
         (today - timedelta(days=40)).isoformat(), None, 280000, 1200.00, "concluida",
         "Óleo 15W40, filtros", None),
        (placas["BCD-1100"], "preventiva", "Revisão geral 200.000km",
         (today - timedelta(days=35)).isoformat(), None, 220000, 5600.00, "concluida",
         "Kit revisão completo", "Revisão programada de fábrica"),

        # agendadas para semana corrente
        (placas["ABC-1234"], "preditiva",  "Inspeção arrefecimento — monitoramento pós-reparo",
         None, (today + timedelta(days=1)).isoformat(), None, None, "agendada",
         None, "Acompanhamento da troca da bomba d'água"),
        (placas["DEF-5678"], "preditiva",  "Verificação desgaste freios traseiros",
         None, (today + timedelta(days=2)).isoformat(), None, None, "agendada",
         None, "Desgaste assimétrico identificado"),
        (placas["MNO-7890"], "preventiva", "Troca correia do alternador",
         None, (today + timedelta(days=3)).isoformat(), None, None, "agendada",
         "Correia poly-V", "Ruído detectado pelo motorista"),
        (placas["VWX-0123"], "preventiva", "Troca de óleo e filtros",
         None, (today + timedelta(days=4)).isoformat(), None, None, "agendada",
         "Óleo, filtros", None),
        (placas["BCD-1100"], "preditiva",  "Verificação suspensão dianteira",
         None, (today + timedelta(days=2)).isoformat(), None, None, "agendada",
         None, "Vibração relatada acima de 80 km/h"),
    ]

    for m in manutencoes:
        c.execute(
            "INSERT INTO manutencoes "
            "(veiculo_id, tipo, descricao, data_realizada, data_agendada, km_realizada, custo, status, pecas, observacoes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            m,
        )

    # ── Ocorrências (4) ──────────────────────────────────────────────────
    ocorrencias = [
        (placas["ABC-1234"], (today - timedelta(days=2)).isoformat(), "Arrefecimento",
         json.dumps(["temperatura elevada", "perda de líquido", "vapor no capô"]),
         "Temperatura subiu acima de 105°C durante subida na Serra do Rio do Rastro. "
         "Motorista parou e identificou vazamento.",
         "alta", 341800, "em_analise"),
        (placas["DEF-5678"], (today - timedelta(days=5)).isoformat(), "Freios",
         json.dumps(["ruído metálico", "vibração ao frear", "pedal longo"]),
         "Ruído constante ao frear em baixa velocidade. Pedal com curso maior que o normal.",
         "media", 215200, "aberta"),
        (placas["MNO-7890"], (today - timedelta(days=1)).isoformat(), "Motor",
         json.dumps(["falha de ignição", "fumaça escura", "perda de potência"]),
         "Perda de potência em rodovia, fumaça escura na aceleração. "
         "Diagnóstico OBD indicou falha no cilindro 3.",
         "alta", 87100, "em_analise"),
        (placas["BCD-1100"], (today - timedelta(days=3)).isoformat(), "Suspensão",
         json.dumps(["vibração", "ruído na suspensão", "desgaste irregular pneus"]),
         "Vibração persistente acima de 80 km/h e desgaste irregular nos pneus dianteiros.",
         "media", 231000, "aberta"),
    ]

    for o in ocorrencias:
        c.execute(
            "INSERT INTO ocorrencias "
            "(veiculo_id, data_ocorrencia, sistema, sintomas, descricao, severidade, km_ocorrencia, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            o,
        )

    conn.commit()
    ocorrencia_ids = {
        row["sistema"]: row["id"]
        for row in c.execute(
            "SELECT id, sistema FROM ocorrencias ORDER BY id"
        )
    }

    # ── Diagnósticos mock (2) ─────────────────────────────────────────────
    diagnosticos = [
        (ocorrencia_ids["Arrefecimento"], placas["ABC-1234"],
         (today - timedelta(days=1)).isoformat(),
         "Bomba d'água", 0.82, 5, "alta",
         json.dumps(["temperatura elevada", "perda de líquido"]),
         "Substituir bomba d'água e verificar cabeçote. Risco de superaquecimento com dano ao motor.",
         json.dumps(["Bomba d'água", "Junta do cabeçote", "Termostato"]),
         12500.00,
         "Baseado em 847 casos similares de Scania R450 com >300.000km"),
        (ocorrencia_ids["Motor"], placas["MNO-7890"],
         today.isoformat(),
         "Bico injetor cilindro 3", 0.74, 8, "alta",
         json.dumps(["falha de ignição", "fumaça escura", "perda de potência"]),
         "Substituir bico injetor do cilindro 3. Verificar pressão do rail e filtro de combustível.",
         json.dumps(["Bico injetor", "Filtro combustível", "Anel vedação"]),
         6800.00,
         "Baseado em 312 casos similares de DAF XF480 com <100.000km"),
    ]

    for d in diagnosticos:
        c.execute(
            "INSERT INTO diagnosticos "
            "(ocorrencia_id, veiculo_id, data_diagnostico, componente, probabilidade_falha, "
            "horizonte_dias, severidade, sintomas_correlacionados, recomendacao, "
            "pecas_sugeridas, economia_estimada, base_historica) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            d,
        )

    conn.commit()
    diag_ids = [row["id"] for row in c.execute("SELECT id FROM diagnosticos ORDER BY id")]

    # ── Alertas (4) ───────────────────────────────────────────────────────
    alertas = [
        (placas["ABC-1234"], diag_ids[0], "critico",
         "URGENTE: Risco de falha na bomba d'água do ABC-1234 (Scania R450). "
         "Probabilidade 82% nos próximos 5 dias. Agendar manutenção imediata.",
         (today - timedelta(days=1)).isoformat(), 0),
        (placas["MNO-7890"], diag_ids[1], "critico",
         "Falha no bico injetor cil. 3 do MNO-7890 (DAF XF480). "
         "Probabilidade 74% em 8 dias. Verificar sistema de injeção.",
         today.isoformat(), 0),
        (placas["DEF-5678"], None, "atencao",
         "Desgaste anormal nos freios do DEF-5678 (Volvo FH540). "
         "Inspeção recomendada antes da próxima viagem.",
         (today - timedelta(days=5)).isoformat(), 0),
        (placas["BCD-1100"], None, "info",
         "Vibração reportada no BCD-1100 (Iveco S-Way). "
         "Verificação de suspensão agendada para esta semana.",
         (today - timedelta(days=3)).isoformat(), 1),
    ]

    for a in alertas:
        c.execute(
            "INSERT INTO alertas (veiculo_id, diagnostico_id, tipo, mensagem, data_criacao, lido) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            a,
        )

    conn.commit()
    conn.close()

    print("Seed concluído com sucesso!")
    print("  - 10 veículos")
    print("  - 70 componentes")
    print("  - 15 manutenções")
    print("  - 4 ocorrências")
    print("  - 2 diagnósticos")
    print("  - 4 alertas")


if __name__ == "__main__":
    seed()
