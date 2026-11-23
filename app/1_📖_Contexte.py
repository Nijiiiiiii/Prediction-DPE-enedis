import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from util import charger_donnees, filtres

st.set_page_config(page_title="Contexte", layout="wide")
df = charger_donnees()

st.title("📖 Contexte")
st.write("Bla bla bla, image dpe, bla bla")

st.header("Données")
st.write(f"Nous possédons un total de {df.shape[0]:,} lignes sur {df.shape[1]} colonnes")

df_filtre =  filtres(df)

n = st.slider("Nombre de lignes à afficher", 10, 1000, 100)




st.dataframe(df_filtre.head(n), use_container_width=True, height=500)