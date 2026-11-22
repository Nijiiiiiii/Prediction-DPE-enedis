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

colnum = df.select_dtypes(include="number").columns
colcat = df.select_dtypes(exclude="number").columns

masque = pd.Series(True, index=df.index)

# Filtres catégoriels
with st.expander("Variables catégorielles", expanded=False):
    for col in colcat:
        modalites = sorted(df[col].unique())
        choix = st.multiselect(col, modalites, default=modalites, key=f"cat_{col}")
        if len(choix) != len(modalites): # filtre actif seulement si on a décoché
            masque &= df[col].isin(choix)

# Filtres numériques 
with st.expander("Variables numériques", expanded=False):
    for col in colnum:
        mini = df[col].min()
        maxi = df[col].max()
        if pd.isna(mini) or mini == maxi: 
            continue
        
        bas, haut = st.slider(col, mini, maxi, (mini, maxi), key=f"num_{col}")
        if (bas, haut) != (mini, maxi):
            masque &= df[col].between(bas, haut)

df_filtre = df[masque]


st.dataframe(df_filtre.head(n), use_container_width=True, height=500)