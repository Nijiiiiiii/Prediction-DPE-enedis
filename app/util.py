import streamlit as st
import pandas as pd
from pathlib import Path
import io
import matplotlib.pyplot as plt

# Chemin robuste, indépendant du dossier de lancement
DATA_PATH = Path(__file__).resolve().parent.parent / "Data" / "dpe.csv.gz"

@st.cache_data
def charger_donnees():
    return pd.read_csv(DATA_PATH, index_col="numero_dpe")

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

def afficher_graphique(fig, nom_fichier, cle):
    """Affiche une figure et ajoute un bouton de téléchargement PNG."""
    st.pyplot(fig)

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
    st.download_button(
        "Télécharger (PNG)",
        data=buffer.getvalue(),
        file_name=f"{nom_fichier}.png",
        mime="image/png",
        key=cle,
    )
    plt.close(fig)