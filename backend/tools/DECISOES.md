# Decisões de Design das Tools

## 1. Por que 4 ferramentas e não mais

Quatro ferramentas é o ponto de equilíbrio entre cobertura e complexidade:

- **Menos de 4**: O LLM teria que inferir dados que poderia consultar (ex: sem `consultar_saude_componentes`, teria que adivinhar a saúde baseado só nos sintomas).
- **Mais de 4**: Aumenta a probabilidade de tool confusion — o modelo escolhe a ferramenta errada ou tenta chamar múltiplas quando uma bastava.

Cada ferramenta mapeia para uma **fonte de dados distinta** no banco:
1. `consultar_historico_veiculo` → tabelas `veiculos` + `manutencoes`
2. `buscar_padroes_frota` → tabelas `ocorrencias` + `veiculos` + `diagnosticos`
3. `consultar_saude_componentes` → tabela `componentes`
4. `calcular_economia` → tabela `manutencoes` (agregações) + fallback de mercado

Nenhuma ferramenta sobrepõe a outra em escopo de dados.

## 2. O que cada tool resolve que o LLM sozinho não consegue

| Tool | Sem ela, o LLM... | Com ela, o LLM... |
|------|-------------------|-------------------|
| `consultar_historico_veiculo` | Inventaria um histórico plausível mas falso | Acessa manutenções reais com datas e custos reais |
| `buscar_padroes_frota` | Não saberia que 3 outros Scania tiveram o mesmo problema | Encontra padrões reais na frota e correlaciona |
| `consultar_saude_componentes` | Estimaria saúde baseado só nos sintomas (viés de confirmação) | Vê o estado real medido — pode até contradizer os sintomas |
| `calcular_economia` | Chutaria valores de custo (alucinação numérica clássica) | Calcula baseado em dados reais ou estimativas calibradas |

**Princípio**: Toda informação que existe no banco deve vir de uma tool, não da "memória" do modelo. O modelo é bom em raciocínio, não em recall de dados específicos.

## 3. Por que as descriptions incluem "quando usar" e não só "o que faz"

Exemplo da `consultar_historico_veiculo`:
```
"Usar quando precisar entender o histórico de manutenção de um veículo
para identificar padrões de falha recorrentes ou avaliar o estado geral."
```

Isso é necessário porque:

- **O modelo decide qual tool chamar** baseado na description. Se a description diz apenas "busca manutenções", o modelo pode não perceber que essa é a ferramenta certa para "verificar se o problema é recorrente".
- **Reduz chamadas desnecessárias**: "Usar quando precisar..." dá um critério de acionamento, não apenas uma capacidade. O modelo sabe que não precisa chamar se já tem a informação.
- **Padrão do LangChain/LangGraph**: A documentação recomenda descriptions que incluem propósito + condição de uso, não apenas funcionalidade.

## 4. Por que consultar_historico e buscar_padroes são separadas

Poderiam ser uma só tool "buscar_dados"? Não, por três razões:

1. **Escopo de dados diferente**:
   - `consultar_historico_veiculo`: dados de **um** veículo (vertical, profundo)
   - `buscar_padroes_frota`: dados de **toda a frota** filtrados por similaridade (horizontal, amplo)

2. **Agentes diferentes usam cada uma**:
   - O **Historiador** usa ambas, mas em momentos distintos da análise
   - Uma tool combinada forçaria o agente a especificar "quero só este veículo" ou "quero a frota toda" via parâmetro, adicionando complexidade desnecessária

3. **Performance**:
   - Consultar histórico de 1 veículo é O(1) no índice
   - Buscar padrões na frota faz scan + comparação de sintomas — mais custoso
   - Separar permite que o agente chame só o que precisa, sem custo computacional desnecessário

4. **Granularidade de controle**:
   - Em produção, podemos limitar rate/custos por tool
   - `buscar_padroes_frota` pode precisar de cache; `consultar_historico_veiculo` não
