import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from streamlit_folium import st_folium

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from util import *
from graphique import *

st.set_page_config(page_title="Graphique", layout="wide")
df = charger_donnees()

KPI = {
    "Étiquette DPE": [
        ("Répartition des classes DPE (Camembert)", cam_dpe),
        ("Répartition des classes DPE (Histogramme)", hist_dpe),
        ("Consommation / DPE", vio_dpe_conso),
        ("Carte des logements par DPE", carte_dpe)
    ],

    "Étiquette GES": [
        ("Répartition des classes GES (Camembert)", cam_ges),
        ("Répartition des classes GES (Histogramme)", hist_ges),
        ("Consommation / GES", vio_ges_conso)
    ],

    "Période de construction": [
        ("Répartition des périodes de construction (Camembert)", cam_periodes),
        ("Répartition des périodes de construction (Histogramme)", hist_periodes),
        ("Consommation par période de construction", vio_per_conso),
        ("DPE par période de construction", bar_dpe_periode),
        ("GES par période de construction", bar_ges_periode),
    ],

    "Type de bâtiment": [
        ("Répartition des types de bâtiments (Camembert)", cam_typelog),
        ("Répartition des types de bâtiments (Histogramme)", hist_typelog),
        ("Consommation par type de bâtiment", vio_log_conso),
        ("DPE par type de bâtiment", bar_dpe_log),
        ("GES par type de bâtiment", bar_ges_log),
    ],

    "Type d'énergie principale": [
        ("Répartition des types d'énergie (Camembert)", cam_energie),
        ("Répartition des types d'énergie (Histogramme)", hist_energie),
        ("Consommation par type d'énergie", vio_ener_conso),
        ("DPE par type d'énergie", bar_dpe_energ),
        ("GES par type d'énergie", bar_ges_energ)
    ]
}

st.title("📊 Graphiques")

df_filtre = filtres(df)

kpi = st.pills("Choisis un KPI", list(KPI), default=list(KPI)[0], selection_mode="single")

if kpi is None:
    st.info("Sélectionne un KPI.")
else:
    graphiques = KPI[kpi]
    n_visibles = 2

    # repartir à 0 quand on change de KPI
    if st.session_state.get("kpi_actuel") != kpi:
        st.session_state["kpi_actuel"] = kpi
        st.session_state["debut"] = 0

    debut = st.session_state["debut"]
    debut_max = max(0, len(graphiques) - n_visibles)

    g, _, d = st.columns([1, 8, 1])
    if g.button("◀", disabled=debut == 0, key="prev"):
        st.session_state["debut"] -= 1
        st.rerun()
    if d.button("▶", disabled=debut >= debut_max, key="next"):
        st.session_state["debut"] += 1
        st.rerun()

    visibles = graphiques[debut:debut + n_visibles]
    for col, (titre, fonction) in zip(st.columns(n_visibles), visibles):
        with col:
            st.subheader(titre)
            afficher(fonction, df_filtre, titre, titre)