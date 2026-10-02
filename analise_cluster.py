# -*- coding: utf-8 -*-
"""
Análise de Clusters - Perfis de Assistência à Epilepsia no SUS (2021-2025)
Script para Congresso Brasileiro de Neurologia 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

# Configuração para gráficos
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10


def carregar_e_limpar_dados(filepath):
    """Carrega e limpa os dados do CSV."""
    # Carregar com separador ; e encoding UTF-8, todas as colunas como string
    df = pd.read_csv(filepath, sep=';', encoding='utf-8', dtype=str)

    # Remover linha de Total
    df = df[~df['Unidade da Federação'].str.contains('Total', case=False, na=False)]

    # Limpar nomes dos estados (remover código numérico inicial e aspas)
    df['Estado'] = df['Unidade da Federação'].str.replace(r'^"?\d+\s*', '', regex=True)
    df['Estado'] = df['Estado'].str.replace('"', '', regex=False).str.strip()

    # Converter colunas numéricas (formato brasileiro: vírgula como decimal)
    colunas_numericas = ['Internações', 'Valor total', 'Dias permanência', 'Óbitos']

    for col in colunas_numericas:
        # Remover aspas se houver
        df[col] = df[col].str.replace('"', '', regex=False)
        # Remover pontos de milhar e substituir vírgula por ponto
        df[col] = df[col].str.replace('.', '', regex=False)
        df[col] = df[col].str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Remover linhas com valores nulos
    df = df.dropna(subset=colunas_numericas)

    # Reset index
    df = df.reset_index(drop=True)

    return df


def calcular_kpis(df):
    """Calcula os indicadores de performance (KPIs)."""
    df['Mortalidade_Hospitalar_%'] = (df['Óbitos'] / df['Internações']) * 100
    df['Custo_Medio_R$'] = df['Valor total'] / df['Internações']
    df['Tempo_Medio_Permanencia_Dias'] = df['Dias permanência'] / df['Internações']

    return df


def metodo_cotovelo(X_scaled, k_range=(2, 7)):
    """Aplica o Método do Cotovelo para determinar o K ideal."""
    inertias = []
    K_values = range(k_range[0], k_range[1])

    for k in K_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)

    # Gerar gráfico do cotovelo
    plt.figure(figsize=(8, 5))
    plt.plot(K_values, inertias, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Número de Clusters (K)', fontsize=12)
    plt.ylabel('Inércia (Within-Cluster Sum of Squares)', fontsize=12)
    plt.title('Método do Cotovelo - Determinação do K Ideal', fontsize=14)
    plt.xticks(K_values)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('elbow_method.png', bbox_inches='tight')
    plt.close()

    print("Gráfico do Método do Cotovelo salvo em: elbow_method.png")
    return inertias


def aplicar_kmeans(df, X_scaled, n_clusters=4):
    """Aplica K-Means clustering."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(X_scaled)

    # Calcular Silhouette Score
    sil_score = silhouette_score(X_scaled, df['Cluster'])

    return df, kmeans, sil_score


def gerar_scatter_plot(df):
    """Gera gráfico de dispersão Custo Médio vs Mortalidade por Cluster."""
    plt.figure(figsize=(12, 8))

    # Cores para os clusters
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6']
    markers = ['o', 's', '^', 'D']

    for cluster in sorted(df['Cluster'].unique()):
        cluster_data = df[df['Cluster'] == cluster]
        plt.scatter(
            cluster_data['Custo_Medio_R$'],
            cluster_data['Mortalidade_Hospitalar_%'],
            c=colors[cluster],
            marker=markers[cluster],
            s=120,
            label=f'Cluster {cluster}',
            alpha=0.8,
            edgecolors='black',
            linewidth=0.5
        )

        # Adicionar rótulos dos estados
        for _, row in cluster_data.iterrows():
            plt.annotate(
                row['Estado'],
                (row['Custo_Medio_R$'], row['Mortalidade_Hospitalar_%']),
                fontsize=7,
                ha='left',
                va='bottom',
                xytext=(5, 5),
                textcoords='offset points'
            )

    plt.xlabel('Custo Médio por Internação (R$)', fontsize=12)
    plt.ylabel('Mortalidade Hospitalar (%)', fontsize=12)
    plt.title('Perfis de Assistência à Epilepsia no SUS por Estado (2021-2025)\nAnálise de Clusters: Custo Médio vs Mortalidade', fontsize=14)
    plt.legend(title='Clusters', loc='upper right', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('clusters_epilepsia.png', bbox_inches='tight')
    plt.close()

    print("Gráfico de clusters salvo em: clusters_epilepsia.png")


def exportar_perfil_clusters(df):
    """Exporta tabela com perfil médio de cada cluster."""
    kpi_cols = ['Mortalidade_Hospitalar_%', 'Custo_Medio_R$', 'Tempo_Medio_Permanencia_Dias']

    perfil = df.groupby('Cluster')[kpi_cols].agg(['mean', 'std', 'count'])
    perfil.columns = ['_'.join(col).strip() for col in perfil.columns.values]

    # Simplificar para média apenas
    perfil_simples = df.groupby('Cluster')[kpi_cols].mean().round(2)
    perfil_simples['N_Estados'] = df.groupby('Cluster').size()

    perfil_simples.to_csv('perfil_clusters.csv', sep=';', decimal=',')
    print("Perfil dos clusters salvo em: perfil_clusters.csv")

    return perfil_simples


def classificar_cluster(row, df_perfil):
    """Classifica o cluster com base nos indicadores."""
    mort = row['Mortalidade_Hospitalar_%']
    custo = row['Custo_Medio_R$']
    tempo = row['Tempo_Medio_Permanencia_Dias']

    # Medianas gerais para comparação
    mort_med = df_perfil['Mortalidade_Hospitalar_%'].median()
    custo_med = df_perfil['Custo_Medio_R$'].median()

    if mort > mort_med and custo > custo_med:
        return "High Cost / High Mortality"
    elif mort > mort_med and custo <= custo_med:
        return "Low Cost / High Mortality"
    elif mort <= mort_med and custo > custo_med:
        return "High Cost / Low Mortality"
    else:
        return "Low Cost / Low Mortality"


def gerar_texto_abstract(df, sil_score):
    """Gera texto em inglês para a seção RESULTS do abstract."""

    # Calcular estatísticas por cluster
    kpi_cols = ['Mortalidade_Hospitalar_%', 'Custo_Medio_R$', 'Tempo_Medio_Permanencia_Dias']
    perfil = df.groupby('Cluster')[kpi_cols].mean()

    # Ordenar clusters por mortalidade para nomenclatura consistente
    perfil_sorted = perfil.sort_values('Mortalidade_Hospitalar_%')

    # Calcular medianas gerais para classificação
    mort_median = perfil['Mortalidade_Hospitalar_%'].median()
    custo_median = perfil['Custo_Medio_R$'].median()
    los_median = perfil['Tempo_Medio_Permanencia_Dias'].median()

    # Definir perfis dos clusters com nomes mais descritivos
    cluster_profiles = {}
    profile_names_used = []

    for idx, (cluster, row) in enumerate(perfil_sorted.iterrows()):
        estados = df[df['Cluster'] == cluster]['Estado'].tolist()

        # Classificar baseado em relação às medianas
        mort_level = "High" if row['Mortalidade_Hospitalar_%'] > mort_median else "Low"
        custo_level = "High" if row['Custo_Medio_R$'] > custo_median else "Low"
        los_level = "Long" if row['Tempo_Medio_Permanencia_Dias'] > los_median else "Short"

        # Criar nome descritivo único
        if row['Mortalidade_Hospitalar_%'] == perfil['Mortalidade_Hospitalar_%'].max():
            profile_name = "Critical - Highest Mortality"
        elif row['Mortalidade_Hospitalar_%'] == perfil['Mortalidade_Hospitalar_%'].min():
            profile_name = "Efficient Care - Lowest Mortality"
        elif mort_level == "Low" and custo_level == "Low":
            profile_name = "Cost-Effective - Moderate Outcomes"
        elif mort_level == "High" and custo_level == "High":
            profile_name = "High Resource / High Mortality"
        elif mort_level == "Low" and custo_level == "High":
            profile_name = "High Investment / Good Outcomes"
        else:
            profile_name = "Low Cost / Elevated Mortality"

        cluster_profiles[cluster] = {
            'name': profile_name,
            'mortality': row['Mortalidade_Hospitalar_%'],
            'cost': row['Custo_Medio_R$'],
            'los': row['Tempo_Medio_Permanencia_Dias'],
            'states': estados
        }

    # Estatísticas gerais
    total_internacoes = df['Internações'].sum()
    total_obitos = df['Óbitos'].sum()
    mort_geral = (total_obitos / total_internacoes) * 100
    custo_medio_geral = df['Valor total'].sum() / total_internacoes
    tempo_medio_geral = df['Dias permanência'].sum() / total_internacoes

    print("\n" + "="*80)
    print("RESULTS SECTION (English - For Abstract)")
    print("="*80)

    text = f"""
RESULTS

A total of {total_internacoes:,} epilepsy-related hospitalizations were analyzed across 27 Brazilian states (2021-2025), with an overall hospital mortality rate of {mort_geral:.2f}%, mean cost of R$ {custo_medio_geral:,.2f} per admission, and average length of stay of {tempo_medio_geral:.1f} days.

K-Means clustering analysis (K=4) identified four distinct healthcare assistance profiles with a Silhouette Score of {sil_score:.3f}, indicating {"good" if sil_score > 0.5 else "moderate" if sil_score > 0.25 else "weak"} cluster separation:

"""

    # Ordenar por mortalidade para apresentação
    for cluster in perfil_sorted.index:
        info = cluster_profiles[cluster]
        states_str = ", ".join(info['states'])
        text += f"""**Cluster {cluster} - {info['name']}** (n={len(info['states'])} states):
Mortality: {info['mortality']:.2f}% | Mean Cost: R$ {info['cost']:,.2f} | Mean LOS: {info['los']:.1f} days
States: {states_str}

"""

    # Adicionar interpretação
    text += f"""
These findings reveal significant regional disparities in epilepsy care across Brazil's public health system (SUS). The clustering analysis demonstrates that hospital mortality rates vary substantially among states, ranging from {perfil['Mortalidade_Hospitalar_%'].min():.2f}% to {perfil['Mortalidade_Hospitalar_%'].max():.2f}%, suggesting heterogeneous healthcare quality and resource allocation patterns.
"""

    print(text)

    # Salvar em arquivo
    with open('results_abstract.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("\nTexto salvo em: results_abstract.txt")

    return text


def main():
    print("="*60)
    print("ANÁLISE DE CLUSTERS - EPILEPSIA NO SUS (2021-2025)")
    print("Congresso Brasileiro de Neurologia 2026")
    print("="*60)

    # 1. Carregar e limpar dados
    print("\n[1/6] Carregando e limpando dados...")
    df = carregar_e_limpar_dados('epilepsia_estados.csv')
    print(f"    Estados carregados: {len(df)}")

    # 2. Calcular KPIs
    print("\n[2/6] Calculando indicadores (KPIs)...")
    df = calcular_kpis(df)
    print("    - Mortalidade Hospitalar (%)")
    print("    - Custo Médio por Internação (R$)")
    print("    - Tempo Médio de Permanência (Dias)")

    # Exibir estatísticas descritivas
    print("\n    Estatísticas Descritivas dos KPIs:")
    kpi_cols = ['Mortalidade_Hospitalar_%', 'Custo_Medio_R$', 'Tempo_Medio_Permanencia_Dias']
    print(df[kpi_cols].describe().round(2).to_string())

    # 3. Normalização
    print("\n[3/6] Normalizando dados (Z-score)...")
    scaler = StandardScaler()
    X = df[kpi_cols].values
    X_scaled = scaler.fit_transform(X)
    print("    Dados normalizados com StandardScaler")

    # 4. Método do Cotovelo
    print("\n[4/6] Aplicando Método do Cotovelo...")
    inertias = metodo_cotovelo(X_scaled)

    # 5. K-Means com K=4
    print("\n[5/6] Aplicando K-Means (K=4)...")
    df, kmeans, sil_score = aplicar_kmeans(df, X_scaled, n_clusters=4)
    print(f"    Silhouette Score: {sil_score:.3f}")

    # Exibir distribuição dos clusters
    print("\n    Distribuição dos Estados por Cluster:")
    for cluster in sorted(df['Cluster'].unique()):
        estados = df[df['Cluster'] == cluster]['Estado'].tolist()
        print(f"    Cluster {cluster}: {len(estados)} estados")
        print(f"        {', '.join(estados)}")

    # 6. Visualização e exportação
    print("\n[6/6] Gerando visualizações e exportando resultados...")
    gerar_scatter_plot(df)
    perfil = exportar_perfil_clusters(df)

    print("\n    Perfil Médio dos Clusters:")
    print(perfil.to_string())

    # Gerar texto para abstract
    gerar_texto_abstract(df, sil_score)

    # Salvar dados completos
    df_export = df[['Estado', 'Internações', 'Óbitos', 'Valor total', 'Dias permanência',
                    'Mortalidade_Hospitalar_%', 'Custo_Medio_R$',
                    'Tempo_Medio_Permanencia_Dias', 'Cluster']]
    df_export.to_csv('dados_clusters_completo.csv', sep=';', decimal=',', index=False)
    print("\nDados completos salvos em: dados_clusters_completo.csv")

    print("\n" + "="*60)
    print("ANÁLISE CONCLUÍDA COM SUCESSO!")
    print("="*60)


if __name__ == "__main__":
    main()
