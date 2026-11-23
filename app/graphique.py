import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import seaborn as sns
import folium
import pandas as pd
from folium.plugins import MarkerCluster
from pyproj import Transformer

COULEURS_ETIQUETTE = {
    'A': '#00845A', 
    'B': '#50A65A', 
    'C': '#B5C94A', 
    'D': '#F5D547',
    'E': '#F3A23A', 
    'F': '#E76B32', 
    'G': '#D93636'
}

ORDRE_ETIQUETTE = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

COULEURS_PERIODE = {
    'après 2021': '#005884',
    '2013-2021':  '#35879B',
    '2006-2012':  '#72AD87',
    '2001-2005':  '#B5C94A',
    '1989-2000':  '#E0D148',
    '1983-1988':  '#F4C443',
    '1978-1982':  '#F3A23A',
    '1975-1977':  '#EB7D35',
    '1948-1974':  '#E25933',
    'avant 1948': '#D93636'
}

ORDRE_PERIODE = ['après 2021','2013-2021','2006-2012','2001-2005','1989-2000','1983-1988','1978-1982','1975-1977','1948-1974','avant 1948']

COULEUR_TYPE_LOGEMENT = {
    'maison': '#005884',
    'immeuble':  '#E0D148',
    'appartement': '#D93636'
}

ORDRE_TYPE_LOGEMENT = ['maison', 'immeuble', 'appartement']

COULEUR_ENERGIE = {
    'Non affecté': '#C8C8C8',
    'Électricité': "#1EB67E",
    'Gaz naturel': "#B85F24",
    'GPL': "#523480",
    'Autre': '#7F7F7F'
}

ORDRE_ENERGIE = ['Non affecté', 'Électricité', 'Gaz naturel', 'GPL', 'Autre']


def carte_dpe(df, n_max=10000):
    """Retourne une carte folium des logements colorés par classe DPE."""
    col_x = 'coordonnee_cartographique_x_ban'
    col_y = 'coordonnee_cartographique_y_ban'

    # 1. Sélection et nettoyage
    geo = df[[col_x, col_y, 'etiquette_dpe']].dropna().copy()
    geo = geo[(geo[col_x] != 0) & (geo[col_y] != 0)]
    geo = geo[geo['etiquette_dpe'].isin(COULEURS_ETIQUETTE)]

    if geo.empty:
        return None                      # rien à afficher (ex. filtres trop stricts)

    # 2. Échantillonnage (avant la conversion, c'est moins coûteux)
    geo = geo.sample(n=min(n_max, len(geo)))

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
        couleur = COULEURS_ETIQUETTE[classe]
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
        '<div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999; '
        'background-color: white; padding: 12px; border: 2px solid grey; '
        'border-radius: 8px; font-size: 14px;">'
        '<b>Classes énergétiques DPE</b><br>'
    )
    for classe, couleur in COULEURS_ETIQUETTE.items():
        legende += (f'<span style="color:{couleur}; font-size:20px;">&#9679;</span> '
                    f'Classe {classe}<br>')
    legende += '</div>'
    carte.get_root().html.add_child(folium.Element(legende))

    # 7. Contrôle des couches
    folium.LayerControl().add_to(carte)

    return carte

# Camembert 

def camembert(data, VD, ordre, couleur):
    repartition = (data[VD].value_counts().reindex(ordre, fill_value=0))

    if repartition.sum() == 0:
        return None
    
    fig, ax = plt.subplots(figsize=(7, 7))

    ax.pie(
        repartition,
        labels=[c for c in repartition.index],
        autopct=lambda p: f'{p:.1f}%' if p >= 1 else '',
        startangle=90,
        counterclock=False,
        pctdistance=0.8,
        wedgeprops={'width': 0.4, 'edgecolor': 'white'},
        colors=[couleur[c] for c in repartition.index],
    )

    ax.set_title(f"Répartition des {" ".join(VD.split("_"))}", fontsize=14, fontweight='bold')
    fig.tight_layout()

    return fig

def cam_dpe(data):
    return camembert(data, "etiquette_dpe", ORDRE_ETIQUETTE, COULEURS_ETIQUETTE)

def cam_ges(data):
    return camembert(data, "etiquette_ges", ORDRE_ETIQUETTE, COULEURS_ETIQUETTE)

def cam_periodes(data):
    return camembert(data, "periode_construction", ORDRE_PERIODE, COULEURS_PERIODE)

def cam_typelog(data):
    return camembert(data, "type_batiment", ORDRE_TYPE_LOGEMENT, COULEUR_TYPE_LOGEMENT)

def cam_energie(data):
    return camembert(data, "type_energie_principale_ecs", ORDRE_ENERGIE ,COULEUR_ENERGIE)

# Histogrammes

def histogramme(data, VD, ordre, palette):
    dpe_counts = (data[VD].value_counts().reindex(ordre, fill_value=0))

    # Calcul des pourcentages
    dpe_percentages = dpe_counts / dpe_counts.sum() * 100

    # Création du graphique
    fig, ax = plt.subplots(figsize=(7, 7))   

    sns.barplot(
        x=dpe_counts.index,
        y=dpe_counts.values,
        hue=dpe_counts.index,
        palette=palette,
        legend=False,
        ax=ax                                    
    )

    for i, valeur in enumerate(dpe_counts.values):
        ax.text(
            i, valeur,
            f'{valeur:,}\n({dpe_percentages.iloc[i]:.1f}%)',
            ha='center', va='bottom', fontsize=10
        )

    ax.set_title(f'Distribution des {" ".join(VD.split("_"))}', fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel(" ".join(VD.split("_")), fontsize=12)
    ax.set_ylabel('Nombre de logements', fontsize=12)

    sns.despine(ax=ax)
    fig.tight_layout()

    return fig

def hist_dpe(data):
    return histogramme(data, "etiquette_dpe", ORDRE_ETIQUETTE, COULEURS_ETIQUETTE)

def hist_ges(data):
    return histogramme(data, "etiquette_ges", ORDRE_ETIQUETTE, COULEURS_ETIQUETTE)

def hist_periodes(data):
    return histogramme(data, "periode_construction", ORDRE_PERIODE, COULEURS_PERIODE)

def hist_typelog(data):
    return histogramme(data, "type_batiment", ORDRE_TYPE_LOGEMENT, COULEUR_TYPE_LOGEMENT)

def hist_energie(data):
    return histogramme(data, "type_energie_principale_ecs", ORDRE_ENERGIE, ORDRE_ENERGIE)

# Violin

def violin(data, VD, VI, ordre, palette) : 
    # Création du graphique
    fig, ax = plt.subplots(figsize=(7, 7))

    sns.violinplot(
        data=data,
        x=VI, # qualitatif
        y=VD, # Quantitatif
        order=ordre,
        hue=VI,
        palette=palette,
        legend=False,
        cut=0,
        inner='quart'
    )   

    ax.set_title(f"Distribution des {" ".join(VD.split("_"))} par {" ".join(VI.split("_"))}", fontsize=15, weight='bold')

    ax.set_xlabel(" ".join(VI.split("_")))
    ax.set_ylabel(" ".join(VD.split("_")))

    sns.despine(ax=ax)
    fig.tight_layout()

    return fig

def vio_dpe_conso(data):
    return violin(data, "conso_5_usages_par_m2_ef", "etiquette_dpe", ORDRE_ETIQUETTE, COULEURS_ETIQUETTE)

def vio_ges_conso(data):
    return violin(data, "conso_5_usages_par_m2_ef", "etiquette_ges", ORDRE_ETIQUETTE, COULEURS_ETIQUETTE)

def vio_per_conso(data):
    return violin(data, "conso_5_usages_par_m2_ef", "periode_construction", ORDRE_PERIODE, COULEURS_PERIODE)

def vio_log_conso(data):
    return violin(data, "conso_5_usages_par_m2_ef", "type_batiment", ORDRE_TYPE_LOGEMENT, COULEUR_TYPE_LOGEMENT)

def vio_ener_conso(data):
    return violin(data, "conso_5_usages_par_m2_ef", "type_energie_principale_ecs", ORDRE_ENERGIE, COULEUR_ENERGIE)

def bar(data, VD, VI, ordre, palette):
    # Répartition (en %) des modalités de VD selon VI
    tab = pd.crosstab(data[VI], data[VD], normalize='index') * 100
    tab = tab.reindex(columns=list(palette), fill_value=0)
    tab = tab.reindex(ordre)

    # Création du graphique
    fig, ax = plt.subplots(figsize=(7, 7))

    tab.plot(
        kind='barh',
        stacked=True,
        ax=ax,
        color=[palette[c] for c in tab.columns],
        width=0.8
    )

    ax.invert_yaxis()  # le premier élément de `ordre` s'affiche en haut

    ax.set_title(f"Répartition des {" ".join(VD.split("_"))} par {" ".join(VI.split("_"))}", fontsize=15, weight='bold')
    ax.set_xlabel("Part des logements (%)")
    ax.set_ylabel(" ".join(VI.split("_")))
    ax.legend(title=" ".join(VD.split("_")), bbox_to_anchor=(1.01, 1), loc='upper left')

    sns.despine(ax=ax)
    fig.tight_layout()

    return fig

def bar_dpe_log(data):
    return bar(data, 'type_batiment', 'etiquette_dpe', ORDRE_ETIQUETTE, COULEUR_TYPE_LOGEMENT)

def bar_dpe_energ(data):
    return bar(data, 'type_energie_principale_ecs', 'etiquette_dpe', ORDRE_ETIQUETTE, COULEUR_ENERGIE)

def bar_dpe_periode(data):
    return bar(data, 'periode_construction', 'etiquette_dpe', ORDRE_ETIQUETTE, COULEURS_PERIODE)


def bar_ges_log(data):
    return bar(data, 'type_batiment', 'etiquette_ges', ORDRE_ETIQUETTE, COULEUR_TYPE_LOGEMENT)

def bar_ges_energ(data):
    return bar(data, 'type_energie_principale_ecs', 'etiquette_ges', ORDRE_ETIQUETTE, COULEUR_ENERGIE)

def bar_ges_periode(data):
    return bar(data, 'periode_construction', 'etiquette_ges', ORDRE_ETIQUETTE, COULEURS_PERIODE)

'''
def barres_empilees_dpe(df, variable, titre=None, ordre=None):
    """Répartition (en %) des classes DPE selon une variable catégorielle."""
    tab = pd.crosstab(df[variable], df['etiquette_dpe'], normalize='index') * 100
    tab = tab.reindex(columns=list(COULEURS_DPE), fill_value=0)
    if ordre:
        tab = tab.reindex(ordre)

    fig, ax = plt.subplots(figsize=(8, 5))
    tab.plot(kind='barh', stacked=True, ax=ax,
             color=[COULEURS_DPE[c] for c in tab.columns], width=0.8)
    ax.set_xlabel("Part des logements (%)")
    ax.set_ylabel("")
    ax.set_title(titre or f"Classe DPE selon {variable}", fontweight='bold')
    ax.legend(title="Classe", bbox_to_anchor=(1.01, 1), loc='upper left')
    fig.tight_layout()
    return fig

def barres(data):
    return barres_empilees_dpe(data, "periode_construction")

def vio_dpe(data):
    return violin(data,"dpe")

def vio_ges(data):
    return violin(data,"ges")





'''