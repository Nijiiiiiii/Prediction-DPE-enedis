import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import folium
import pandas as pd
from folium.plugins import MarkerCluster
from pyproj import Transformer

COULEURS_DPE = {
    'A': '#00845A', 'B': '#50A65A', 'C': '#B5C94A', 'D': '#F5D547',
    'E': '#F3A23A', 'F': '#E76B32', 'G': '#D93636'
}

ordre_dpe = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

def hist_dpe(data):
    return histogramme(data,"dpe")

def hist_ges(data):
    return histogramme(data,"ges")

def histogramme(data, etiquette):
    dpe_counts = (data[f'etiquette_{etiquette.lower()}'].value_counts().reindex(ordre_dpe, fill_value=0))

    # Calcul des pourcentages
    dpe_percentages = dpe_counts / dpe_counts.sum() * 100

    # Création du graphique
    fig, ax = plt.subplots(figsize=(10, 6))   

    sns.barplot(
        x=dpe_counts.index,
        y=dpe_counts.values,
        hue=dpe_counts.index,
        palette=COULEURS_DPE,
        legend=False,
        ax=ax                                    
    )

    for i, valeur in enumerate(dpe_counts.values):
        ax.text(
            i, valeur,
            f'{valeur:,}\n({dpe_percentages.iloc[i]:.1f}%)',
            ha='center', va='bottom', fontsize=10
        )

    ax.set_title(f'Distribution des classes énergétiques {etiquette.upper()}',
                    fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel(f'Classe énergétique {etiquette.upper()}', fontsize=12)
    ax.set_ylabel('Nombre de logements', fontsize=12)

    sns.despine(ax=ax)
    fig.tight_layout()

    return fig

def carte_dpe(df, n_max=10000, random_state=42):
    """Retourne une carte folium des logements colorés par classe DPE."""
    col_x = 'coordonnee_cartographique_x_ban'
    col_y = 'coordonnee_cartographique_y_ban'

    # 1. Sélection et nettoyage
    geo = df[[col_x, col_y, 'etiquette_dpe']].dropna().copy()
    geo = geo[(geo[col_x] != 0) & (geo[col_y] != 0)]
    geo = geo[geo['etiquette_dpe'].isin(COULEURS_DPE)]

    if geo.empty:
        return None                      # rien à afficher (ex. filtres trop stricts)

    # 2. Échantillonnage (avant la conversion, c'est moins coûteux)
    geo = geo.sample(n=min(n_max, len(geo)), random_state=random_state)

    # 3. Conversion Lambert-93 -> WGS84
    transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)
    geo['longitude'], geo['latitude'] = transformer.transform(
        geo[col_x].values, geo[col_y].values
    )

    # 4. Création de la carte
    carte = folium.Map(
        location=[geo['latitude'].median(), geo['longitude'].median()],
        zoom_start=6,
        tiles=None
    )
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles © Esri',
        name='Esri World Street Map',
        overlay=False,
        control=True
    ).add_to(carte)

    # 5. Marqueurs (itertuples est bien plus rapide que iterrows)
    cluster = MarkerCluster(name='Logements DPE').add_to(carte)

    for lat, lon, classe in zip(geo['latitude'], geo['longitude'], geo['etiquette_dpe']):
        couleur = COULEURS_DPE[classe]
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color=couleur,
            fill=True,
            fill_color=couleur,
            fill_opacity=0.75,
            weight=1,
            popup=folium.Popup(
                f"<b>Classe DPE :</b> {classe}<br>"
                f"<b>Latitude :</b> {lat:.5f}<br>"
                f"<b>Longitude :</b> {lon:.5f}",
                max_width=250
            )
        ).add_to(cluster)

    # 6. Légende
    legende = (
        '<div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; '
        'background-color: white; padding: 12px; border: 2px solid grey; '
        'border-radius: 8px; font-size: 14px;">'
        '<b>Classes énergétiques DPE</b><br>'
    )
    for classe, couleur in COULEURS_DPE.items():
        legende += (f'<span style="color:{couleur}; font-size:20px;">&#9679;</span> '
                    f'Classe {classe}<br>')
    legende += '</div>'
    carte.get_root().html.add_child(folium.Element(legende))

    # 7. Contrôle des couches
    folium.LayerControl().add_to(carte)

    return carte


