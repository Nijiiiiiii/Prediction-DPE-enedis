import streamlit as st
import pandas as pd
from pathlib import Path

# Chemin robuste, indépendant du dossier de lancement
DATA_PATH = Path(__file__).resolve().parent.parent / "Data" / "dpe.csv.gz"

@st.cache_data
def charger_donnees():
    return pd.read_csv(DATA_PATH, index_col="numero_dpe")