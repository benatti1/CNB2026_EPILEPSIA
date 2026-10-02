"""Reproduce the original figures with English text, preserving saved clusters."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.plot_dependencies'))
os.environ['MPLCONFIGDIR'] = str(ROOT / '.matplotlib')
os.environ['OMP_NUM_THREADS'] = '1'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Reuse the original plotting functions, replacing only display text and filenames.
source = (ROOT / 'analise_cluster.py').read_text(encoding='utf-8')
translations = {
    'Número de Clusters (K)': 'Number of Clusters (K)',
    'Inércia (Within-Cluster Sum of Squares)': 'Inertia (Within-Cluster Sum of Squares)',
    'Método do Cotovelo - Determinação do K Ideal': 'Elbow Method - Determining the Optimal K',
    'Custo Médio por Internação (R$)': 'Mean Cost per Hospitalization (R$)',
    'Mortalidade Hospitalar (%)': 'In-Hospital Mortality (%)',
    'Perfis de Assistência à Epilepsia no SUS por Estado (2021-2025)': 'Epilepsy Care Profiles in the Brazilian Public Health System (SUS) by State (2021-2025)',
    'Análise de Clusters: Custo Médio vs Mortalidade': 'Cluster Analysis: Mean Cost vs Mortality',
    'clusters_epilepsia.png': 'clusters_epilepsia_en.png',
    'elbow_method.png': 'elbow_method_en.png',
}
for original, translated in translations.items():
    source = source.replace(original, translated)
# Keep the legend in the empty upper-left region so Alagoas remains visible.
source = source.replace("loc='upper right'", "loc='upper left'")
namespace = {'__name__': 'original_plot_functions'}
exec(compile(source, str(ROOT / 'analise_cluster.py'), 'exec'), namespace)

os.chdir(ROOT)
df = pd.read_csv(ROOT / 'dados_clusters_completo.csv', sep=';', decimal=',')
df['Estado'] = df['Estado'].replace({'Distrito Federal': 'Federal District'})
namespace['gerar_scatter_plot'](df)
features = ['Mortalidade_Hospitalar_%', 'Custo_Medio_R$', 'Tempo_Medio_Permanencia_Dias']


def add_cluster_table(data):
    """Show arithmetic means across federative units, as in the original analysis."""
    fig = plt.gcf()
    ax = fig.add_axes([0.08, 0.065, 0.89, 0.20])
    ax.axis('off')
    means = data.groupby('Cluster')[features].mean()
    counts = data.groupby('Cluster').size()
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6']
    rows = [
        [f'Cluster {cluster}', str(counts.loc[cluster]),
         f'{row[features[0]]:.2f}', f'{row[features[2]]:.2f}',
         f'{row[features[1]]:,.2f}']
        for cluster, row in means.iterrows()
    ]
    table = ax.table(
        cellText=rows,
        colLabels=['Cluster', 'Federative units (n)', 'In-hospital mortality\n(%)',
                   'Length of stay\n(days)', 'Cost per hospitalization\n(R$)'],
        colWidths=[0.14, 0.18, 0.22, 0.22, 0.24],
        cellLoc='center', bbox=[0, 0, 1, 0.87],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor('#d6dce2')
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_facecolor('#e9eef3')
            cell.set_text_props(weight='bold', color='#172b3a')
        elif c == 0:
            cell.set_facecolor(matplotlib.colors.to_rgba(colors[int(means.index[r-1])], 0.25))
            cell.set_text_props(weight='bold')
        else:
            cell.set_facecolor('#ffffff' if r % 2 else '#f6f8fa')
    ax.text(0, 0.98, 'Mean KPI values by cluster', fontsize=13, weight='bold',
            transform=ax.transAxes, va='bottom')
    fig.text(0.08, 0.035,
             'Values are unweighted means across federative units. Clusters were defined using all three standardized KPIs.',
             fontsize=10, color='#444444')


# Reuse the same scatter drawing, reserving a separate area below for the table.
combined_source = source[source.index('def gerar_scatter_plot(df):'):source.index('def exportar_perfil_clusters(df):')]
combined_source = combined_source.replace('plt.figure(figsize=(12, 8))',
    "plt.figure(figsize=(14, 10))\n    plt.axes([0.08, 0.36, 0.89, 0.54])")
combined_source = combined_source.replace('plt.tight_layout()', 'add_cluster_table(df)')
combined_source = combined_source.replace('clusters_epilepsia_en.png', 'clusters_epilepsia_with_table_en.png')
combined_namespace = dict(namespace, add_cluster_table=add_cluster_table)
exec(compile(combined_source, '<scatter_with_table>', 'exec'), combined_namespace)
combined_namespace['gerar_scatter_plot'](df)
scaled = StandardScaler().fit_transform(df[features].values)
inertias = namespace['metodo_cotovelo'](scaled)
print('Elbow values:', inertias)
print('Preserved saved assignments for', len(df), 'federative units.')
