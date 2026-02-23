# Decisões de Design dos Prompts

## 1. Por que persona específica para cada agente

Cada agente tem uma persona de domínio, não genérica:

- **Orchestrator**: "coordenador de diagnóstico" — precisa saber o que delegar e quando. Uma persona genérica ("assistente") não saberia que freios exigem sempre alta severidade.
- **Diagnostician**: "engenheiro de confiabilidade sênior" — ativa conhecimento técnico profundo sobre motores DC13, transmissões I-Shift, etc. O modelo já tem esse conhecimento, a persona faz ele acessar.
- **Historian**: "analista de dados de frota" — foca em padrões estatísticos, não em diagnóstico técnico. Sem a persona, ele tentaria diagnosticar ao invés de analisar dados.
- **Planner**: "gestor de manutenção" — equilibra segurança vs disponibilidade. Um "engenheiro" sempre pararia o caminhão; um "gestor" pondera custo operacional.
- **Financial**: "analista de custos" — foco em ROI e justificativa financeira, não em diagnóstico técnico.

A especificidade da persona evita sobreposição de responsabilidades entre agentes e reduz alucinação fora do escopo.

## 2. Por que XML tags nas restrições do diagnosticador

```xml
<restricoes>
- Se probabilidade > 60%, nunca recomende "continuar operando"
- Sistemas de segurança: severidade mínima "alta"
</restricoes>
```

O diagnosticador é o agente com maior risco de gerar recomendações perigosas. As XML tags `<restricoes>` servem como **delimitadores semânticos** que o modelo Gemini interpreta como regras invioláveis, não como sugestões. Isso é mais eficaz do que simplesmente listar em texto corrido porque:

- Cria separação visual e semântica entre "o que fazer" e "o que nunca fazer"
- Modelos treinados com dados web reconhecem XML como estrutura, não prosa
- Facilita auditoria humana — basta buscar `<restricoes>` nos prompts para encontrar todas as regras de segurança

Os outros agentes não precisam disso porque suas saídas não geram risco de segurança operacional.

## 3. Por que temperatura diferente por agente

| Agente         | Temperatura | Justificativa |
|----------------|-------------|---------------|
| Diagnostician  | 0.2         | Diagnóstico técnico precisa ser determinístico. Dado os mesmos sintomas, deve dar o mesmo resultado. |
| Historian      | 0.1         | Análise de dados é factual. Não pode "inventar" padrões que não existem no banco. |
| Planner        | 0.3         | Planejamento precisa de alguma flexibilidade para ponderar trade-offs entre urgência e disponibilidade. |
| Financial      | 0.1         | Cálculos financeiros são determinísticos. Números errados destroem credibilidade. |
| Orchestrator   | 0.2         | Coordenação precisa ser consistente, mas com flexibilidade para decidir quais agentes acionar. |

Regra geral: quanto mais factual/numérico a saída, menor a temperatura. Quanto mais há decisão subjetiva, levemente maior.

## 4. Por que few-shot não é necessário aqui

Em sistemas de prompt único, few-shot é essencial para alinhar formato e tom. Aqui não é necessário porque:

1. **O contexto vem das tools, não do prompt**: Os agentes recebem dados estruturados (JSON) das ferramentas. O "exemplo" é o dado real, não um exemplo fabricado.

2. **Os agentes se complementam**: O orquestrador recebe as saídas dos outros agentes como contexto. Cada agente funciona como "few-shot" para o próximo.

3. **JSON schema no prompt já define o formato**: Especificar o schema exato da saída é mais eficaz que mostrar um exemplo, porque o modelo segue o schema como contrato.

4. **Risco de viés**: Few-shot com dados de mineração poderia enviesar o modelo para sempre diagnosticar os mesmos problemas do exemplo, ignorando sinais diferentes nos dados reais.

Se no futuro a qualidade das saídas cair, few-shot deve ser a primeira coisa a adicionar — mas começa sem para medir o baseline.

## 5. Por que JSON estrito

Todos os agentes retornam JSON puro, sem texto explicativo:

- **Frontend precisa parsear**: O React faz `JSON.parse()` da resposta. Qualquer texto fora do JSON quebra o parsing.
- **Agentes intermediários consomem a saída**: O orquestrador precisa ler os JSONs dos outros agentes programaticamente.
- **Auditabilidade**: JSON estruturado permite logs queryáveis, dashboards de qualidade, e detecção de drift.
- **Instrução explícita "APENAS JSON"**: Sem essa instrução, modelos tendem a adicionar "Claro! Aqui está..." antes do JSON.
