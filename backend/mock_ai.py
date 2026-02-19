"""
Módulo de IA mock para diagnóstico preditivo.

Simula a resposta de uma LLM (ex: Claude via function calling) para gerar
diagnósticos de manutenção preditiva. Será substituído pela integração real
com LLM quando o sistema estiver em produção.

Fluxo futuro:
  1. Receber ocorrência com sintomas
  2. Montar prompt com contexto do veículo + histórico
  3. Chamar LLM via API com function calling (tool_use)
  4. Parsear resposta estruturada e salvar diagnóstico
"""

import random

# ── Mapeamento de diagnósticos por sistema ────────────────────────────────
# Cada sistema tem variações por sintoma principal, permitindo respostas
# mais específicas conforme os sintomas reportados.

DIAGNOSTICOS_POR_SISTEMA = {
    "Motor": {
        "default": {
            "componente": "Motor — diagnóstico geral",
            "probabilidade_falha": 0.55,
            "horizonte_dias": 15,
            "severidade": "media",
            "recomendacao": "Realizar diagnóstico completo do motor com scanner OBD. "
                            "Verificar compressão dos cilindros e sistema de injeção.",
            "pecas_sugeridas": ["Filtro combustível", "Velas de ignição", "Junta do coletor"],
            "economia_estimada": 4500.00,
            "base_historica": "Baseado em padrões gerais de falha de motor diesel pesado",
        },
        "ruído anormal": {
            "componente": "Bronzinas / bielas",
            "probabilidade_falha": 0.72,
            "horizonte_dias": 6,
            "severidade": "alta",
            "recomendacao": "Ruído anormal no motor pode indicar desgaste de bronzinas ou folga "
                            "em biela. Parar operação e inspecionar imediatamente.",
            "pecas_sugeridas": ["Bronzinas", "Biela", "Óleo motor"],
            "economia_estimada": 15000.00,
            "base_historica": "Baseado em 203 casos de ruído anormal em motor diesel pesado",
        },
        "consumo elevado de óleo": {
            "componente": "Anéis de pistão / guias de válvula",
            "probabilidade_falha": 0.60,
            "horizonte_dias": 20,
            "severidade": "media",
            "recomendacao": "Consumo elevado de óleo indica desgaste nos anéis de pistão ou "
                            "guias de válvula. Monitorar nível e programar revisão.",
            "pecas_sugeridas": ["Anéis de pistão", "Guias de válvula", "Retentores"],
            "economia_estimada": 8000.00,
            "base_historica": "Baseado em 178 casos de consumo elevado de óleo",
        },
        "vibração anormal": {
            "componente": "Coxins do motor / volante",
            "probabilidade_falha": 0.55,
            "horizonte_dias": 14,
            "severidade": "media",
            "recomendacao": "Verificar coxins do motor e volante do motor. "
                            "Vibração anormal pode indicar desbalanceamento ou folga.",
            "pecas_sugeridas": ["Coxins do motor", "Volante motor", "Amortecedor de vibração"],
            "economia_estimada": 4500.00,
            "base_historica": "Baseado em 167 casos de vibração anormal em motor",
        },
        "falha de ignição": {
            "componente": "Bico injetor",
            "probabilidade_falha": 0.75,
            "horizonte_dias": 7,
            "severidade": "alta",
            "recomendacao": "Substituir bico injetor defeituoso. Verificar pressão do rail "
                            "e qualidade do combustível.",
            "pecas_sugeridas": ["Bico injetor", "Anel vedação", "Filtro combustível"],
            "economia_estimada": 6800.00,
            "base_historica": "Baseado em 312 casos de falha de ignição em motores diesel",
        },
        "perda de potência": {
            "componente": "Turbocompressor",
            "probabilidade_falha": 0.68,
            "horizonte_dias": 10,
            "severidade": "alta",
            "recomendacao": "Inspecionar turbocompressor para folga axial e vazamentos. "
                            "Verificar intercooler e mangueiras de pressão.",
            "pecas_sugeridas": ["Kit reparo turbo", "Mangueira intercooler", "Junta turbo"],
            "economia_estimada": 9200.00,
            "base_historica": "Baseado em 245 casos de perda de potência relacionados a turbo",
        },
        "fumaça excessiva": {
            "componente": "Sistema de injeção",
            "probabilidade_falha": 0.70,
            "horizonte_dias": 8,
            "severidade": "alta",
            "recomendacao": "Verificar bicos injetores e bomba de alta pressão. "
                            "Fumaça excessiva indica excesso de combustível ou injeção incorreta.",
            "pecas_sugeridas": ["Bico injetor", "Bomba alta pressão", "Filtro combustível"],
            "economia_estimada": 7500.00,
            "base_historica": "Baseado em 189 casos de fumaça excessiva em diesel pesado",
        },
        "fumaça escura": {
            "componente": "Sistema de injeção",
            "probabilidade_falha": 0.70,
            "horizonte_dias": 8,
            "severidade": "alta",
            "recomendacao": "Verificar bicos injetores e bomba de alta pressão. "
                            "Fumaça escura indica excesso de combustível ou injeção incorreta.",
            "pecas_sugeridas": ["Bico injetor", "Bomba alta pressão", "Filtro combustível"],
            "economia_estimada": 7500.00,
            "base_historica": "Baseado em 189 casos de fumaça escura em diesel pesado",
        },
    },
    "Freios": {
        "default": {
            "componente": "Sistema de freios — diagnóstico geral",
            "probabilidade_falha": 0.50,
            "horizonte_dias": 12,
            "severidade": "media",
            "recomendacao": "Inspeção completa do sistema de freios: pastilhas, discos, "
                            "flexíveis e cilindros.",
            "pecas_sugeridas": ["Pastilhas", "Discos", "Flexíveis"],
            "economia_estimada": 3500.00,
            "base_historica": "Baseado em padrões gerais de desgaste de freios",
        },
        "ruído ao frear": {
            "componente": "Pastilhas e discos de freio",
            "probabilidade_falha": 0.80,
            "horizonte_dias": 5,
            "severidade": "alta",
            "recomendacao": "Substituição imediata de pastilhas. Verificar discos para "
                            "desgaste abaixo do mínimo e empenamento.",
            "pecas_sugeridas": ["Kit pastilhas eixo dianteiro", "Discos de freio", "Sensor desgaste"],
            "economia_estimada": 4200.00,
            "base_historica": "Baseado em 523 casos de ruído ao frear em freios de caminhão",
        },
        "desgaste de lona/pastilha": {
            "componente": "Pastilhas e discos de freio",
            "probabilidade_falha": 0.78,
            "horizonte_dias": 6,
            "severidade": "alta",
            "recomendacao": "Substituir pastilhas/lonas. Verificar tambores/discos para "
                            "desgaste abaixo do limite mínimo de segurança.",
            "pecas_sugeridas": ["Kit pastilhas", "Lonas de freio", "Discos de freio"],
            "economia_estimada": 3800.00,
            "base_historica": "Baseado em 615 casos de desgaste de lona/pastilha",
        },
        "aquecimento excessivo": {
            "componente": "Sistema de freios — atrito",
            "probabilidade_falha": 0.70,
            "horizonte_dias": 5,
            "severidade": "alta",
            "recomendacao": "Verificar regulagem dos freios, retorno das pinças e sistema pneumático. "
                            "Aquecimento excessivo pode causar fadiga dos discos e perda de frenagem.",
            "pecas_sugeridas": ["Pinças de freio", "Flexíveis", "Regulador automático"],
            "economia_estimada": 5200.00,
            "base_historica": "Baseado em 198 casos de aquecimento excessivo de freios",
        },
        "ruído metálico": {
            "componente": "Pastilhas e discos de freio",
            "probabilidade_falha": 0.80,
            "horizonte_dias": 5,
            "severidade": "alta",
            "recomendacao": "Substituição imediata de pastilhas. Verificar discos para "
                            "desgaste abaixo do mínimo e empenamento.",
            "pecas_sugeridas": ["Kit pastilhas eixo dianteiro", "Discos de freio", "Sensor desgaste"],
            "economia_estimada": 4200.00,
            "base_historica": "Baseado em 523 casos de ruído metálico em freios de caminhão",
        },
        "vibração ao frear": {
            "componente": "Discos de freio",
            "probabilidade_falha": 0.72,
            "horizonte_dias": 7,
            "severidade": "alta",
            "recomendacao": "Retificar ou substituir discos de freio. Empenamento causa "
                            "vibração e reduz eficiência de frenagem.",
            "pecas_sugeridas": ["Discos de freio", "Pastilhas", "Rolamento cubo"],
            "economia_estimada": 5100.00,
            "base_historica": "Baseado em 298 casos de vibração ao frear",
        },
        "vibração": {
            "componente": "Discos de freio",
            "probabilidade_falha": 0.72,
            "horizonte_dias": 7,
            "severidade": "alta",
            "recomendacao": "Retificar ou substituir discos de freio. Empenamento causa "
                            "vibração e reduz eficiência de frenagem.",
            "pecas_sugeridas": ["Discos de freio", "Pastilhas", "Rolamento cubo"],
            "economia_estimada": 5100.00,
            "base_historica": "Baseado em 298 casos de vibração ao frear",
        },
        "pedal longo": {
            "componente": "Cilindro mestre / servo-freio",
            "probabilidade_falha": 0.65,
            "horizonte_dias": 10,
            "severidade": "alta",
            "recomendacao": "Verificar nível de fluido, cilindro mestre e servo-freio. "
                            "Pedal longo pode indicar entrada de ar ou vazamento interno.",
            "pecas_sugeridas": ["Cilindro mestre", "Kit reparo servo", "Fluido de freio"],
            "economia_estimada": 3800.00,
            "base_historica": "Baseado em 167 casos de pedal longo em freios pneumáticos",
        },
    },
    "Arrefecimento": {
        "default": {
            "componente": "Sistema de arrefecimento — diagnóstico geral",
            "probabilidade_falha": 0.55,
            "horizonte_dias": 12,
            "severidade": "media",
            "recomendacao": "Teste de pressão no sistema de arrefecimento. Verificar "
                            "mangueiras, radiador e bomba d'água.",
            "pecas_sugeridas": ["Mangueiras", "Abraçadeiras", "Líquido arrefecimento"],
            "economia_estimada": 3000.00,
            "base_historica": "Baseado em padrões gerais de falha de arrefecimento",
        },
        "temperatura elevada": {
            "componente": "Bomba d'água",
            "probabilidade_falha": 0.82,
            "horizonte_dias": 4,
            "severidade": "critica",
            "recomendacao": "Substituir bomba d'água urgentemente. Superaquecimento pode "
                            "causar dano irreversível ao cabeçote e bloco do motor.",
            "pecas_sugeridas": ["Bomba d'água", "Junta do cabeçote", "Termostato", "Líquido arrefecimento"],
            "economia_estimada": 12500.00,
            "base_historica": "Baseado em 847 casos de superaquecimento em motores diesel pesado",
        },
        "perda de líquido": {
            "componente": "Radiador / mangueiras",
            "probabilidade_falha": 0.70,
            "horizonte_dias": 6,
            "severidade": "alta",
            "recomendacao": "Localizar ponto de vazamento com teste de pressão. "
                            "Verificar radiador, mangueiras e conexões.",
            "pecas_sugeridas": ["Radiador", "Kit mangueiras", "Abraçadeiras"],
            "economia_estimada": 5500.00,
            "base_historica": "Baseado em 412 casos de vazamento de líquido de arrefecimento",
        },
        "vazamento de líquido": {
            "componente": "Radiador / mangueiras",
            "probabilidade_falha": 0.70,
            "horizonte_dias": 6,
            "severidade": "alta",
            "recomendacao": "Localizar ponto de vazamento com teste de pressão. "
                            "Verificar radiador, mangueiras e conexões.",
            "pecas_sugeridas": ["Radiador", "Kit mangueiras", "Abraçadeiras"],
            "economia_estimada": 5500.00,
            "base_historica": "Baseado em 412 casos de vazamento de líquido de arrefecimento",
        },
        "ventilador não liga": {
            "componente": "Ventilador / embreagem viscosa",
            "probabilidade_falha": 0.75,
            "horizonte_dias": 3,
            "severidade": "alta",
            "recomendacao": "Verificar embreagem viscosa do ventilador, sensor de temperatura "
                            "e relé. Risco de superaquecimento em operação.",
            "pecas_sugeridas": ["Embreagem viscosa", "Sensor temperatura", "Relé ventilador"],
            "economia_estimada": 4200.00,
            "base_historica": "Baseado em 156 casos de falha no ventilador",
        },
        "consumo de líquido": {
            "componente": "Junta do cabeçote / radiador",
            "probabilidade_falha": 0.65,
            "horizonte_dias": 10,
            "severidade": "alta",
            "recomendacao": "Consumo de líquido sem vazamento externo pode indicar falha na junta do cabeçote. "
                            "Realizar teste de pressão e verificar gases no reservatório.",
            "pecas_sugeridas": ["Junta do cabeçote", "Líquido arrefecimento", "Tampa reservatório"],
            "economia_estimada": 8500.00,
            "base_historica": "Baseado em 234 casos de consumo de líquido de arrefecimento",
        },
    },
    "Transmissão": {
        "default": {
            "componente": "Transmissão — diagnóstico geral",
            "probabilidade_falha": 0.50,
            "horizonte_dias": 20,
            "severidade": "media",
            "recomendacao": "Verificar nível e qualidade do óleo de câmbio. "
                            "Testar sincronizadores e engrenagens.",
            "pecas_sugeridas": ["Óleo câmbio", "Filtro câmbio", "Junta do cárter"],
            "economia_estimada": 5000.00,
            "base_historica": "Baseado em padrões gerais de falha de transmissão",
        },
        "dificuldade de engate": {
            "componente": "Sincronizadores",
            "probabilidade_falha": 0.72,
            "horizonte_dias": 12,
            "severidade": "alta",
            "recomendacao": "Verificar sincronizadores e garfos de engate. "
                            "Pode ser necessário revisão do câmbio.",
            "pecas_sugeridas": ["Kit sincronizadores", "Garfo de engate", "Óleo câmbio"],
            "economia_estimada": 11000.00,
            "base_historica": "Baseado em 156 casos de dificuldade de engate",
        },
        "ruído em marcha": {
            "componente": "Engrenagens / rolamentos do câmbio",
            "probabilidade_falha": 0.65,
            "horizonte_dias": 15,
            "severidade": "media",
            "recomendacao": "Verificar nível e qualidade do óleo do câmbio. Ruído em marcha pode "
                            "indicar desgaste de engrenagens ou rolamentos.",
            "pecas_sugeridas": ["Óleo câmbio", "Rolamentos", "Engrenagem"],
            "economia_estimada": 7500.00,
            "base_historica": "Baseado em 134 casos de ruído em marcha",
        },
        "trancos": {
            "componente": "Sincronizadores / embreagem",
            "probabilidade_falha": 0.70,
            "horizonte_dias": 10,
            "severidade": "alta",
            "recomendacao": "Trancos na troca de marcha indicam desgaste nos sincronizadores "
                            "ou regulagem incorreta da embreagem.",
            "pecas_sugeridas": ["Kit sincronizadores", "Cabo/atuador embreagem", "Óleo câmbio"],
            "economia_estimada": 9000.00,
            "base_historica": "Baseado em 187 casos de trancos na transmissão",
        },
        "patinação da embreagem": {
            "componente": "Embreagem",
            "probabilidade_falha": 0.85,
            "horizonte_dias": 5,
            "severidade": "alta",
            "recomendacao": "Substituir kit embreagem completo. Patinação indica disco "
                            "desgastado além do limite.",
            "pecas_sugeridas": ["Kit embreagem completo", "Rolamento atuador", "Volante motor"],
            "economia_estimada": 8500.00,
            "base_historica": "Baseado em 389 casos de patinação de embreagem",
        },
        "patinação": {
            "componente": "Embreagem",
            "probabilidade_falha": 0.85,
            "horizonte_dias": 5,
            "severidade": "alta",
            "recomendacao": "Substituir kit embreagem completo. Patinação indica disco "
                            "desgastado além do limite.",
            "pecas_sugeridas": ["Kit embreagem completo", "Rolamento atuador", "Volante motor"],
            "economia_estimada": 8500.00,
            "base_historica": "Baseado em 389 casos de patinação de embreagem",
        },
    },
    "Suspensão": {
        "default": {
            "componente": "Suspensão — diagnóstico geral",
            "probabilidade_falha": 0.45,
            "horizonte_dias": 18,
            "severidade": "media",
            "recomendacao": "Inspeção visual completa da suspensão. Verificar bolsas de ar, "
                            "amortecedores e buchas.",
            "pecas_sugeridas": ["Buchas", "Amortecedores", "Pinos e graxeiras"],
            "economia_estimada": 3200.00,
            "base_historica": "Baseado em padrões gerais de desgaste de suspensão",
        },
        "instabilidade": {
            "componente": "Buchas e braços de suspensão",
            "probabilidade_falha": 0.62,
            "horizonte_dias": 12,
            "severidade": "media",
            "recomendacao": "Verificar buchas, braços e barra estabilizadora. "
                            "Instabilidade pode indicar folgas nos pontos de fixação.",
            "pecas_sugeridas": ["Buchas", "Barra estabilizadora", "Braço de suspensão"],
            "economia_estimada": 3600.00,
            "base_historica": "Baseado em 234 casos de instabilidade em suspensão pneumática",
        },
        "ruído em irregularidades": {
            "componente": "Amortecedores",
            "probabilidade_falha": 0.68,
            "horizonte_dias": 10,
            "severidade": "media",
            "recomendacao": "Substituir amortecedores desgastados. Ruído em irregularidades "
                            "indica perda de vedação ou desgaste interno.",
            "pecas_sugeridas": ["Amortecedores", "Batentes", "Coifas"],
            "economia_estimada": 4200.00,
            "base_historica": "Baseado em 312 casos de ruído em suspensão",
        },
        "desgaste de molas": {
            "componente": "Molas / feixes de mola",
            "probabilidade_falha": 0.58,
            "horizonte_dias": 15,
            "severidade": "media",
            "recomendacao": "Inspecionar molas parabólicas e feixes. Desgaste de molas causa "
                            "redução da capacidade de carga e altura irregular.",
            "pecas_sugeridas": ["Feixe de molas", "Abraçadeiras", "Calço de mola"],
            "economia_estimada": 3800.00,
            "base_historica": "Baseado em 189 casos de desgaste de molas em caminhão pesado",
        },
        "inclinação lateral": {
            "componente": "Barra estabilizadora / bolsas de ar",
            "probabilidade_falha": 0.64,
            "horizonte_dias": 8,
            "severidade": "alta",
            "recomendacao": "Verificar barra estabilizadora, bolsas de ar e válvula niveladora. "
                            "Inclinação lateral compromete a estabilidade e segurança.",
            "pecas_sugeridas": ["Barra estabilizadora", "Bolsa de ar", "Válvula niveladora"],
            "economia_estimada": 5400.00,
            "base_historica": "Baseado em 156 casos de inclinação lateral",
        },
        "vibração": {
            "componente": "Amortecedores / bolsas de ar",
            "probabilidade_falha": 0.65,
            "horizonte_dias": 10,
            "severidade": "media",
            "recomendacao": "Verificar amortecedores e bolsas de ar pneumática. "
                            "Vibração pode causar fadiga prematura em outros componentes.",
            "pecas_sugeridas": ["Amortecedores", "Bolsas de ar", "Buchas estabilizador"],
            "economia_estimada": 4800.00,
            "base_historica": "Baseado em 278 casos de vibração em suspensão pneumática",
        },
        "desgaste irregular pneus": {
            "componente": "Geometria / terminais de direção",
            "probabilidade_falha": 0.60,
            "horizonte_dias": 14,
            "severidade": "media",
            "recomendacao": "Realizar alinhamento e verificar terminais de direção, "
                            "pivôs e braço pitman.",
            "pecas_sugeridas": ["Terminais de direção", "Pivô", "Alinhamento"],
            "economia_estimada": 2800.00,
            "base_historica": "Baseado em 345 casos de desgaste irregular de pneus",
        },
    },
}


def generate_mock_diagnostic(
    sistema: str,
    sintomas: list[str],
    veiculo_km: float,
) -> dict:
    """
    Gera um diagnóstico mock simulando a resposta de uma LLM.

    Em produção, esta função será substituída por uma chamada à API da LLM
    usando function calling (tool_use). O prompt incluirá:
      - Histórico de manutenções do veículo
      - Dados de telemetria (se disponíveis)
      - Base de conhecimento de falhas do modelo
      - Sintomas e contexto da ocorrência

    Args:
        sistema: Sistema afetado (Motor, Freios, Arrefecimento, etc.)
        sintomas: Lista de sintomas reportados
        veiculo_km: Quilometragem atual do veículo

    Returns:
        Dict com diagnóstico estruturado pronto para salvar na tabela diagnosticos
    """
    mapeamento = DIAGNOSTICOS_POR_SISTEMA.get(sistema, {})

    # Buscar variação mais específica pelo primeiro sintoma que bater
    # Comparação case-insensitive: o formulário envia "Temperatura elevada",
    # mas as chaves do mapeamento são em minúsculas
    mapeamento_lower = {k.lower(): v for k, v in mapeamento.items()}
    diagnostico = None
    for sintoma in sintomas:
        match = mapeamento_lower.get(sintoma.lower())
        if match:
            diagnostico = match
            break

    if diagnostico is None:
        diagnostico = mapeamento.get("default", {
            "componente": f"{sistema} — componente não mapeado",
            "probabilidade_falha": 0.50,
            "horizonte_dias": 15,
            "severidade": "media",
            "recomendacao": f"Realizar inspeção completa do sistema de {sistema.lower()}.",
            "pecas_sugeridas": [],
            "economia_estimada": 3000.00,
            "base_historica": "Sem base histórica suficiente para este caso",
        })

    # Variância aleatória para simular incerteza do modelo
    prob = diagnostico["probabilidade_falha"] + random.uniform(-0.05, 0.05)
    prob = max(0.10, min(0.99, prob))  # clamp entre 10% e 99%

    horizonte = diagnostico["horizonte_dias"] + random.randint(-2, 2)
    horizonte = max(1, horizonte)  # mínimo 1 dia

    # Ajustar severidade com base na quilometragem (veículos com muitos km
    # têm diagnósticos ligeiramente mais graves)
    severidade = diagnostico["severidade"]
    if veiculo_km > 300_000 and severidade == "media":
        severidade = "alta"

    return {
        "componente": diagnostico["componente"],
        "probabilidade_falha": round(prob, 2),
        "horizonte_dias": horizonte,
        "severidade": severidade,
        "sintomas_correlacionados": sintomas,
        "recomendacao": diagnostico["recomendacao"],
        "pecas_sugeridas": diagnostico["pecas_sugeridas"],
        "economia_estimada": diagnostico["economia_estimada"],
        "base_historica": diagnostico["base_historica"],
        "modelo_versao": "mock-v1.0",
    }
