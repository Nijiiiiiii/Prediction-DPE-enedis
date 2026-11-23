from pathlib import Path
import sys
import pandas as pd
import streamlit as st

 
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from util import load_metadata
 

#------------------------------------
# Génération d'un champ de formulaire
#------------------------------------
def render_field(col, info):
    if info["type"] == "categorielle":
        return st.selectbox(col, options=info["categories"], key=f"in_{col}")
 
    # Quantitatif : on demande un chiffre
    if info["is_int"]:
        return st.number_input(
            col,
            value=int(info["median"]),
            step=1,
            key=f"in_{col}",
            help=f"Min : {int(info['min'])} • Max : {int(info['max'])}",
        )
    
    return st.number_input(
        col,
        value=float(info["median"]),
        format="%.2f",
        key=f"in_{col}",
        help=f"Min : {info['min']:.2f} • Max : {info['max']:.2f}",
    )
 
 
#------
# Page
#------
st.set_page_config(page_title="Prédiction", layout="wide")
st.title("📈 Prédiction")
st.write("Renseigne les caractéristiques du logement puis lance la prédiction.")
 
 
data = load_metadata()
columns, meta = data["columns"], data["meta"]
 
n_cat = sum(m["type"] == "categorielle" for m in meta.values())
st.caption(
    f"{len(columns)} variables détectées ({n_cat} catégorielles, "
    f"{len(columns) - n_cat} quantitatives) • {data['n_rows']:,} lignes dans le jeu de données"
)
 
with st.form("form_prediction"):
    grid = st.columns(2)
    inputs = {}
    for i, col in enumerate(columns):
        with grid[i % 2]:
            inputs[col] = render_field(col, meta[col])
 
    submitted = st.form_submit_button("Prédire", type="primary")
 
if submitted:
    # Une ligne, avec les colonnes dans le même ordre que le fichier d'origine
    X_input = pd.DataFrame([inputs], columns=columns)
    st.session_state["X_input"] = X_input
 
if "X_input" in st.session_state:
    st.subheader("Données saisies")
    st.dataframe(st.session_state["X_input"], hide_index=True, use_container_width=True)