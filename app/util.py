import streamlit as st
import pandas as pd
from pathlib import Path
import io
import matplotlib.pyplot as plt
from pandas.api.types import is_bool_dtype, is_integer_dtype, is_numeric_dtype

# Chemin robuste, indépendant du dossier de lancement
DATA_PATH = Path(__file__).resolve().parent.parent / "Data" / "dpe.csv.gz"
EXPLI_PATH = Path(__file__).resolve().parent.parent / "Data" / "dpe_explicative.csv.gz"

@st.cache_data
def charger_donnees():
    return pd.read_csv(DATA_PATH, index_col="numero_dpe")

@st.cache_data(show_spinner="Chargement des données…")
def load_metadata():
    #Charge le CSV et ne garde que ce qui est utile au formulaire
    #(type, catégories, min / max / médiane), pour éviter de garder
    #tout le DataFrame en mémoire.
    df = pd.read_csv(EXPLI_PATH, index_col="numero_dpe")
 
    meta = {}
    for col in df.columns:
        serie = df[col].dropna()
        if serie.empty:
            continue
 
        # Quantitatif : numérique et non booléen
        if is_numeric_dtype(serie) and not is_bool_dtype(serie):
            meta[col] = {
                "type": "quantitative",
                "is_int": bool(is_integer_dtype(serie)),
                "min": float(serie.min()),
                "max": float(serie.max()),
                "median": float(serie.median())
            }
        # Sinon : string / objet / booléen -> catégoriel
        else:
            meta[col] = {
                "type": "categorielle",
                "categories": sorted(serie.astype(str).unique().tolist()),
            }
 
    return {"columns": list(meta.keys()), "meta": meta, "n_rows": len(df)}


def filtres(df):
    colnum = df.select_dtypes(include="number").columns
    colcat = df.select_dtypes(exclude="number").columns

    masque = pd.Series(True, index=df.index)
    with st.expander("Filtres", expanded=True):
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

    return df[masque]

def afficher(fonction, data, cle, nom_fichier = None):
    """Affiche selon le type d'objet retourné."""
    obj = fonction(data)
    if obj is None:
        st.info("Aucune donnée à afficher.")
    elif isinstance(obj, plt.Figure):
        st.pyplot(obj)
        buffer = io.BytesIO()
        obj.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
        st.download_button(
            "Télécharger (PNG)",
            data=buffer.getvalue(),
            file_name=f"{nom_fichier}.png",
            mime="image/png",
            key=cle,
        )
        plt.close(obj)
    else:
        import streamlit.components.v1 as components
        components.html(obj.get_root().render(), height=350)