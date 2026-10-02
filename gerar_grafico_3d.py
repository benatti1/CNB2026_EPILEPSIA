"""Export a slide-ready static 3D view of the three original KPIs."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.plot_dependencies'))
os.environ['MPLCONFIGDIR'] = str(ROOT / '.matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import proj3d
import pandas as pd
import numpy as np

df = pd.read_csv(ROOT / 'dados_clusters_completo.csv', sep=';', decimal=',')
state_abbreviations = {
    'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM',
    'Bahia': 'BA', 'Ceará': 'CE', 'Distrito Federal': 'DF',
    'Espírito Santo': 'ES', 'Goiás': 'GO', 'Maranhão': 'MA',
    'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG',
    'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE',
    'Piauí': 'PI', 'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN',
    'Rio Grande do Sul': 'RS', 'Rondônia': 'RO', 'Roraima': 'RR',
    'Santa Catarina': 'SC', 'São Paulo': 'SP', 'Sergipe': 'SE', 'Tocantins': 'TO',
}
assert set(df['Estado']) == set(state_abbreviations), 'Check federative unit names.'
colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6']
markers = ['o', 's', '^', 'D']
x, y, z = 'Custo_Medio_R$', 'Tempo_Medio_Permanencia_Dias', 'Mortalidade_Hospitalar_%'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
fig = plt.figure(figsize=(14, 9), dpi=150, facecolor='white')
ax = fig.add_axes([-0.045, 0.09, 0.86, 0.84], projection='3d', proj_type='ortho')
ax.set_box_aspect((1.5, 1.1, 1.0), zoom=1.08)
for cluster, data in df.groupby('Cluster'):
    ax.scatter(data[x], data[y], data[z], s=95, c=colors[cluster],
               marker=markers[cluster], edgecolors='#333333', linewidths=0.6,
               alpha=0.95, depthshade=False, label=f'Cluster {cluster} (n={len(data)})')
ax.set_xlabel('MCA (R$)', labelpad=15, fontsize=19, fontweight='normal')
ax.set_ylabel('MLS (days)', labelpad=15, fontsize=19, fontweight='normal')
ax.set_zlabel('HMR (%)', labelpad=15, fontsize=19, fontweight='normal')
ax.set_xlim(200, 2600)
ax.set_ylim(3.5, 10.3)
ax.set_zlim(0, 8)
ax.set_xticks([500, 1000, 1500, 2000, 2500])
ax.set_yticks([4, 6, 8, 10])
ax.set_zticks([0, 2, 4, 6, 8])
ax.view_init(elev=23, azim=-57)
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor('#f3f6f9')
    axis.pane.set_edgecolor('#dce2e8')
    axis._axinfo['grid']['color'] = '#dce2e8'
fig.suptitle('Epilepsy Care Profiles in the Brazilian Public Health System (SUS)',
             fontsize=20, weight='bold', y=0.96)
fig.legend(*ax.get_legend_handles_labels(), title='Clusters', loc='upper left', bbox_to_anchor=(0.755, 0.78),
          frameon=False, fontsize=16, title_fontsize=18, labelspacing=1.0, markerscale=1.2)

# Place labels in the final 2D projection, preventing overlaps in the exported view.
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
projected = []
for _, row in df.iterrows():
    px, py, _ = proj3d.proj_transform(row[x], row[y], row[z], ax.get_proj())
    projected.append((px, py, state_abbreviations[row['Estado']]))
occupied = []
for px, py, _ in projected:
    sx, sy = ax.transData.transform((px, py))
    occupied.append(matplotlib.transforms.Bbox.from_bounds(sx-11, sy-11, 22, 22))
for px, py, name in sorted(projected, key=lambda p: p[1], reverse=True):
    candidates = [(6, 6), (6, -12), (-6, 6), (-6, -12)]
    candidates += [(dx, dy) for dy in (18, -24, 30, -36, 42, -48, 54, -60)
                   for dx in (8, -8, 35, -35, 65, -65)]
    annotation = None
    for dx, dy in candidates:
        annotation = ax.annotate(name, (px, py), xytext=(dx, dy),
            textcoords='offset points', fontsize=9, ha='left' if dx > 0 else 'right',
            va='bottom', color='#202b33', zorder=100,
            arrowprops=dict(arrowstyle='-', color='#89939d', lw=0.5),
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.75, pad=0.6))
        annotation.update_positions(renderer)
        # Use the text bounding box rather than the leader line for collisions.
        box = matplotlib.text.Text.get_window_extent(annotation, renderer).expanded(1.07, 1.15)
        if not any(box.overlaps(other) for other in occupied):
            occupied.append(box)
            break
        annotation.remove()
    else:
        raise RuntimeError(f'No free label position for {name}')

fig.text(0.04, 0.025, 'Source: Author', fontsize=16, color='#444444')
fig.savefig(ROOT / 'clusters_epilepsia_3d_en.png', dpi=300)
fig.savefig(ROOT / 'clusters_epilepsia_3d_en.svg')
plt.close(fig)
print('Exported 3D chart with all 27 federative units, preserving saved cluster assignments.')
