import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from streamlit_folium import st_folium
from graphique import carte_dpe

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from util import *
from graphique import *

st.set_page_config(page_title="Graphique", layout="wide")
df = charger_donnees()

KPI = {
    "Etiquette DPE": [
        ("Distribution des classes", hist_dpe),
        ("Carte des logements", carte_dpe)
    ],

    "Etiquette GES": [
        ("Distribution des classes", hist_ges)
    ]
}

st.title("Graphiques")

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
            afficher(fonction, df, titre, titre)