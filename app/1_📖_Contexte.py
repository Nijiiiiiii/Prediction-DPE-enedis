import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from util import charger_donnees, filtres
from preparation import Preparation

st.set_page_config(page_title="Contexte", layout="wide")
df = charger_donnees()

st.title("📖 Contexte")
st.write(
    "Dans le cadre de ce travail, des modèles prédictifs ont été "
    "développés afin d'estimer l'étiquette DPE ainsi que la consommation "
    "énergétique d'un logement. Pour ce faire, les données nécessaires "
    "ont été collectées à partir de l'API de l'ADEME."
)

st.header("Données")
st.write(f"Ce jeu de données est composé de {df.shape[0]:,} lignes/logements sur {df.shape[1]} colonnes")

df_filtre =  filtres(df)

n = st.slider("Nombre de lignes à afficher", 10, 1000, 100)

st.dataframe(df_filtre.head(n), use_container_width=True, height=500)