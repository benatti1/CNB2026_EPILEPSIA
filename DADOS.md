# Dados e proveniência

## Dados hospitalares

- Arquivo de entrada: `epilepsia_estados.csv`.
- Fonte declarada no resumo: Sistema de Informações Hospitalares do SUS (SIH/SUS).
- Período declarado: 2021–2025.
- Seleção declarada: epilepsia, CID-10 G40–G41.
- Unidade analítica: unidade federativa, totalizando 27 observações após limpeza.
- Formato: UTF-8, separador ponto e vírgula, vírgula decimal.

| Campo de entrada | Uso no código |
|---|---|
| Unidade da Federação | Código e nome da UF; o código numérico é retirado do rótulo |
| Internações | Denominador dos três indicadores |
| Valor total | Soma dos valores em reais presente na extração |
| Dias permanência | Soma dos dias de permanência |
| Óbitos | Numerador da mortalidade hospitalar |

O arquivo original contém uma linha `Total` e uma linha final `&`. O código exclui a linha Total, converte os campos numéricos e elimina linhas com campos numéricos ausentes. A linha `&` é descartada nessa última etapa. O arquivo original foi mantido sem alterações.

Indicadores derivados:

- `Mortalidade_Hospitalar_%` = óbitos / internações × 100.
- `Custo_Medio_R$` = valor total / internações. Esse é o nome usado no código; não há estimativa adicional de custo econômico.
- `Tempo_Medio_Permanencia_Dias` = dias de permanência / internações.
- `Cluster` = rótulo do K-Means, de 0 a 3. Os números identificam grupos, não uma escala ordinal.

## Lacunas da extração original

Os arquivos disponíveis não registram data de extração, consulta exportada, seleção por residência ou local de internação, referência temporal por atendimento ou processamento, filtros complementares nem eventual incompletude do último ano. Não é possível reconstruir esses detalhes apenas com a tabela agregada. Período e CID são informações do resumo, não metadados verificáveis dentro do CSV.

A reprodução disponibilizada começa na tabela agregada preservada. Para reproduzir a obtenção dos dados na fonte, o autor deverá acrescentar o registro da consulta original.

## Cartografia

`brasil_ufs_ibge.geojson` é a cópia local da malha usada pelo script `gerar_mapa_clusters.py`. A URL de obtenção e a referência à documentação do IBGE estão no próprio script. O arquivo contém 27 geometrias, identificadas por `codarea`. O mapa usa projeção equivalente de Albers e associa a cada UF a classificação já salva; não recalcula os grupos.
