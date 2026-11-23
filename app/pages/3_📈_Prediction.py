from pathlib import Path
import sys
import pandas as pd
import streamlit as st

 
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from util import charger_metadata, charger_model 
from preparation import Preparation

#------------------------------------
# Génération d'un champ de formulaire
#------------------------------------
def render_field(col, info):
    if info["type"] == "booleenne":
        return st.checkbox(col, value=False, key=f"in_{col}")
    
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

def align_columns(model, X: pd.DataFrame) -> pd.DataFrame:
    """Réordonne les colonnes comme à l'entraînement (si le pipeline les a mémorisées)
    et vérifie qu'il n'en manque aucune."""
    expected = getattr(model, "feature_names_in_", None)
    if expected is None:
        return X
 
    missing = [c for c in expected if c not in X.columns]
    if missing:
        raise ValueError(f"Colonnes attendues par le modèle mais absentes du formulaire : {missing}")
    return X[list(expected)]
 
#------
# Page
#------
st.set_page_config(page_title="Prédiction", layout="wide")
st.title("📈 Prédiction")
st.write("Renseigne les caractéristiques du logement puis lance la prédiction.")
 
 
data = charger_metadata()
columns, meta = data["columns"], data["meta"]

modele_dpe, modele_conso = charger_model()
 
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
 
# --------------------------------------------------------------------------
# Prédictions
# --------------------------------------------------------------------------
if submitted:
    # Une ligne, avec les colonnes dans le même ordre que le fichier d'origine
    X_input = pd.DataFrame([inputs], columns=columns)
    for col in columns:
        if meta[col]["type"] == "booleenne":
            X_input[col] = X_input[col].astype(bool)
    st.session_state["X_input"] = X_input

    try:
        # --- Consommation (régression) ---
        conso = float(modele_conso.predict(align_columns(modele_conso, X_input))[0])

        # --- Classe DPE (classification) ---
        X_dpe = align_columns(modele_dpe, X_input)
        classe = modele_dpe.predict(X_dpe)[0]

        probas = None
        if hasattr(modele_dpe, "predict_proba"):
            probas = pd.Series(
                modele_dpe.predict_proba(X_dpe)[0],
                index=[str(c) for c in modele_dpe.classes_],
                name="Probabilité",
            ).sort_index()

        st.session_state["resultats"] = {"conso": conso, "classe": classe, "probas": probas}
        st.session_state.pop("erreur_modele", None)

    except Exception as e:
        st.session_state.pop("resultats", None)
        st.session_state["erreur_modele"] = e

# 3) Affichage (toujours en dernier, après le calcul)
if "erreur_modele" in st.session_state:
    st.error("Impossible de lancer la prédiction.")
    st.exception(st.session_state["erreur_modele"])
 
if "resultats" in st.session_state:
    res = st.session_state["resultats"]
 
    st.subheader("Résultats")
    col_conso, col_dpe = st.columns(2)
 
    with col_conso:
        st.metric("Consommation prédite", f"{res['conso']:,.1f} kWh/m²/an")
 
    with col_dpe:
        st.metric("Classe DPE prédite", str(res["classe"]))
 
    if res["probas"] is not None:
        st.caption("Probabilité par classe DPE")
        st.bar_chart(res["probas"])
 
if "X_input" in st.session_state:
    with st.expander("Données saisies"):
        st.dataframe(st.session_state["X_input"], hide_index=True, use_container_width=True)