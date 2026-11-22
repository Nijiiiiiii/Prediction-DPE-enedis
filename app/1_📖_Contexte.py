import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from util import charger_donnees

st.set_page_config(page_title="Contexte", layout="wide")
df = charger_donnees()

st.title("Contexte")
st.write("Bla bla bla, image dpe, bla bla")

st.header("Données")
st.write(f"Nous possédons un total de {df.shape[0]:,} lignes sur {df.shape[1]} colonnes")

st.subheader("Filtres")

n = st.slider("Nombre de lignes à afficher", 10, 1000, 100)

cols_num = df.select_dtypes(include="number").columns
cols_cat = df.select_dtypes(exclude="number").columns

masque = pd.Series(True, index=df.index)

st.dataframe(df.head(n), use_container_width=True, height=500)