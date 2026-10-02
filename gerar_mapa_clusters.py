"""Mapa coroplético categórico dos clusters existentes, sem recalcular o K-means.

Instalação: python -m pip install -r requirements_mapa.txt
Validação sem imagem: python gerar_mapa_clusters.py --validate-only
Exportação quando desejada: python gerar_mapa_clusters.py

Fonte cartográfica: https://servicodados.ibge.gov.br/api/docs/malhas?versao=3
A primeira execução armazena a malha do IBGE para permitir reprodução offline.
"""
from pathlib import Path
import argparse
import csv
import gzip
import json
import os
import sys
import urllib.request
from collections import Counter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.plot_dependencies'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.matplotlib'))
URL = ('https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR'
       '?intrarregiao=UF&formato=application/vnd.geo%2Bjson&qualidade=intermediaria')
CACHE = ROOT / 'brasil_ufs_ibge.geojson'
# Mesmos valores hexadecimais dos gráficos anteriores (cluster 0: coral).
COLORS = {0: '#e74c3c', 1: '#3498db', 2: '#2ecc71', 3: '#9b59b6'}
UF = {
    'Rondônia': ('11', 'RO'), 'Acre': ('12', 'AC'),
    'Amazonas': ('13', 'AM'), 'Roraima': ('14', 'RR'),
    'Pará': ('15', 'PA'), 'Amapá': ('16', 'AP'), 'Tocantins': ('17', 'TO'),
    'Maranhão': ('21', 'MA'), 'Piauí': ('22', 'PI'), 'Ceará': ('23', 'CE'),
    'Rio Grande do Norte': ('24', 'RN'), 'Paraíba': ('25', 'PB'),
    'Pernambuco': ('26', 'PE'), 'Alagoas': ('27', 'AL'), 'Sergipe': ('28', 'SE'),
    'Bahia': ('29', 'BA'), 'Minas Gerais': ('31', 'MG'),
    'Espírito Santo': ('32', 'ES'), 'Rio de Janeiro': ('33', 'RJ'),
    'São Paulo': ('35', 'SP'), 'Paraná': ('41', 'PR'),
    'Santa Catarina': ('42', 'SC'), 'Rio Grande do Sul': ('43', 'RS'),
    'Mato Grosso do Sul': ('50', 'MS'), 'Mato Grosso': ('51', 'MT'),
    'Goiás': ('52', 'GO'), 'Distrito Federal': ('53', 'DF'),
}


def load_data():
    with (ROOT / 'dados_clusters_completo.csv').open(encoding='utf-8-sig', newline='') as f:
        records = list(csv.DictReader(f, delimiter=';'))
    if len(records) != 27 or {r['Estado'] for r in records} != set(UF):
        raise ValueError('A tabela deve conter exatamente as 27 unidades federativas.')
    lookup = {}
    for row in records:
        code, abbr = UF[row['Estado']]
        cluster = int(row['Cluster'])
        if cluster not in COLORS:
            raise ValueError(f'Cluster desconhecido: {cluster}')
        lookup[code] = dict(Cluster=cluster, UF=abbr)
    if CACHE.exists():
        geo = json.loads(CACHE.read_text(encoding='utf-8'))
    else:
        with urllib.request.urlopen(URL, timeout=60) as response:
            raw = response.read()
        if raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        geo = json.loads(raw)
    features = geo.get('features', [])
    codes = [str(f['properties']['codarea']) for f in features]
    if len(codes) != 27 or set(codes) != set(lookup):
        raise ValueError('A malha deve conter uma geometria para cada uma das 27 UFs.')
    for feature in features:
        if feature['geometry']['type'] not in ('Polygon', 'MultiPolygon'):
            raise ValueError('Geometria inesperada na malha do IBGE.')
    if not CACHE.exists():
        CACHE.write_text(json.dumps(geo, ensure_ascii=False), encoding='utf-8')
    # Acrescenta os clusters somente à cópia em memória; preserva a malha original.
    for feature in features:
        feature['properties'].update(lookup[str(feature['properties']['codarea'])])
    return geo, Counter(r['Cluster'] for r in lookup.values())


def draw_map(geo, counts):
    import geopandas as gpd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    from matplotlib.patches import Patch

    # Projeção equivalente: preserva áreas e evita desenhar longitude/latitude como plano.
    projection = '+proj=aea +lat_1=-2 +lat_2=-22 +lat_0=-12 +lon_0=-54 +datum=WGS84 +units=m +no_defs'
    from shapely import make_valid
    from shapely.ops import unary_union

    def repair_polygon(geometry):
        fixed = make_valid(geometry)
        if fixed.geom_type == 'GeometryCollection':
            fixed = unary_union([part for part in fixed.geoms
                                 if part.geom_type in ('Polygon', 'MultiPolygon')])
        return fixed

    states = gpd.GeoDataFrame.from_features(geo['features'], crs='EPSG:4326')
    states.geometry = states.geometry.map(repair_polygon)
    states = states.to_crs(projection)
    states.geometry = states.geometry.map(repair_polygon)
    if states.geometry.is_empty.any() or not states.geometry.is_valid.all():
        raise ValueError('Há geometrias vazias ou inválidas na malha.')
    fig, ax = plt.subplots(figsize=(14, 9), facecolor='white')
    fig.subplots_adjust(left=0.01, right=0.76, bottom=0.08, top=0.925)
    states.plot(ax=ax, color=states['Cluster'].map(COLORS),
                edgecolor='white', linewidth=1.0)
    # Destaque do DF por contorno e chamada, sem ampliar sua área territorial.
    states[states.UF == 'DF'].boundary.plot(ax=ax, color='#333333', linewidth=0.9)
    offsets = {'RN': (35, 16), 'PB': (44, 5), 'PE': (52, -8),
               'AL': (44, -15), 'SE': (35, -26), 'ES': (28, 0),
               'RJ': (25, -12), 'DF': (28, 18)}
    for row in states.itertuples():
        geometry = row.geometry
        # Escolhe a parte continental/maior polígono para posicionar a sigla.
        mainland = max(geometry.geoms, key=lambda p: p.area) if geometry.geom_type == 'MultiPolygon' else geometry
        point = mainland.representative_point()
        offset = offsets.get(row.UF, (0, 0))
        label = ax.annotate(row.UF, (point.x, point.y), xytext=offset,
            textcoords='offset points', ha='left' if offset[0] else 'center',
            va='center', fontsize=12, weight='bold', color='#202b33',
            arrowprops=dict(arrowstyle='-', color='#444444', lw=0.7) if offset != (0, 0) else None)
        label.set_path_effects([pe.withStroke(linewidth=2.5, foreground='white')])
    ax.set_aspect('equal')
    ax.margins(0.015)
    ax.set_axis_off()
    fig.suptitle('Epilepsy Care Profiles in the Brazilian Public Health System (SUS)',
                 fontsize=20, weight='bold', y=0.96)
    handles = [Patch(facecolor=COLORS[c], edgecolor='#555555',
                     label=f'Cluster {c} (n={counts[c]})') for c in sorted(COLORS)]
    fig.legend(handles=handles, title='Clusters', loc='center left',
               bbox_to_anchor=(0.755, 0.55), frameon=False,
               fontsize=17, title_fontsize=19, labelspacing=1.2)
    fig.text(0.77, 0.32, 'n = federative units', fontsize=12, color='#555555')
    fig.text(0.04, 0.025, 'Boundaries: IBGE | Cluster assignments: study data',
             fontsize=16, color='#444444')
    for suffix in ('png', 'svg'):
        path = ROOT / f'mapa_clusters_brasil_en.{suffix}'
        fig.savefig(path, dpi=300, facecolor='white')
        print(path)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true', help='Valida dados e malha sem desenhar ou exportar imagem.')
    args = parser.parse_args()
    geometry, counts = load_data()
    print('UFs verificadas: 27. Contagens por cluster:', dict(sorted(counts.items())))
    if not args.validate_only:
        draw_map(geometry, counts)
