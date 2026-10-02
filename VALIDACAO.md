# Verificação de reprodução

Verificação local em 2 de outubro de 2026, preservando os arquivos originais.

## Resultados numéricos confirmados

- 27 unidades federativas válidas.
- 320.419 internações e 9.301 óbitos.
- Indicadores recalculados iguais aos da tabela salva, dentro da tolerância numérica de `numpy.allclose`.
- Mesmas classificações individuais e mesmos rótulos de grupos.
- Contagens por grupo: 0 = 12; 1 = 8; 2 = 1; 3 = 6.
- Índice de Rand ajustado entre classificações salvas e recalculadas: 1,0.
- Silhouette recalculado: 0,3159502535430365.

## Ambiente observado

Windows; Python 3.14.0. Bibliotecas carregadas do ambiente local:

| Biblioteca | Versão |
|---|---|
| pandas | 3.0.6 |
| numpy | 2.5.3 |
| matplotlib | 3.11.2 |
| scikit-learn | 1.9.1 |
| scipy | 1.18.1 |
| geopandas | 1.2.0 |
| shapely | 2.1.2 |
| pyproj | 3.8.0 |

As versões acima documentam o ambiente utilizado; não constituem um teste de instalação limpa a partir de um registro público. Os requisitos originais foram preservados.

## Alcance

Os quatro scripts também foram executados integralmente em uma cópia temporária, com término bem-sucedido: análise principal, figuras em inglês, figura 3D e mapa. A validação isolada da correspondência entre dados e malha também terminou com sucesso. Os resultados originais do pacote foram preservados. Essa execução confirma funcionamento no ambiente local, sem equivaler a uma inspeção visual de todas as figuras regeneradas.

A confirmação numérica não verifica a extração original no SIH/SUS, nem valida as interpretações clínicas e causais do resumo. Consulte `DADOS.md` para as lacunas de proveniência.
