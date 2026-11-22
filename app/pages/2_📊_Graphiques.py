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

st.title("Graphiques")

df_filtre = filtres(df)

afficher_graphique(histogramme(df_filtre), "distribution_etiquette_dpe", "histdpe")

carte = carte_dpe(df)

if carte is None:
    st.warning("Aucun logement à afficher avec ces filtres.")
else:
    st_folium(carte, height=600, use_container_width=True, returned_objects=[])