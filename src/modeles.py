import os, pickle
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier

# -----------------------
# Préparation des données
# -----------------------
class Preparation(BaseEstimator, TransformerMixin):
    # Fonction permettant des trié dans l'ordre croissant les différentes periodes de construction 
    def get_per(slef, periode_construction):
        # Etant données que dans les periodes il y a une periode "avant" et une "après",
        # il a fallut placer le "avant" en première position qui, en triant la liste, se retrouve forcément à la fin
        # Le reste étant déjà trié par le sorted 
        triee = sorted(periode_construction)
        return [triee[-1]] + triee[:-1]
    
    def fit(self, X, y=None):
        self.per_ = self.get_per(X['periode_construction'].unique())
        
        # Selon le type de colone / la colone, les modalité sont pas identique.
        # il a été décidé de plassé la classe "Inconnue", comme dernière
        # ce choix c'est fait arbitrairement
        self.ordre_ = {
            'periode_construction': self.per_,
            'qualite_': ['Inconnue', 'insuffisante', 'moyenne', 'bonne', 'très bonne'],
            'indicateur_confort_ete': ['Inconnue', 'insuffisant', 'moyen', 'bon'],
            'classe_altitude': ['Inconnue', 'inférieur à 400m', '400-800m'],
        }

        return self

    def transform(self, X):
        X = X.copy()

        # On met tout les str comme catégorie
        for col in X.select_dtypes(include=['str']).columns:
            X[col] = pd.Categorical(X[col])

        # On gère les catégories ordinales via nos filtres de colones et les catégories
        for filtre, modalites in self.ordre_.items():
            for col in X.filter(regex=f"^{filtre}").columns:
                X[col] = pd.Categorical(X[col], categories=modalites, ordered=True)

        return X

    # Pour lié le fit et le transforme
    def fit_transform(self, X, y = None, **fit_params):
        return super().fit_transform(X, y, **fit_params)

# -----------------------
# Importation des données
# -----------------------
# On se plasse dans le bon endroit pour accedé plus facilement aux fichiers
while "Notebooks" not in os.listdir():
    os.chdir("../")

# On importe nos données
X = pd.read_csv("Data/dpe_explicative.csv.gz", index_col=0)
Y = pd.read_csv("Data/dpe_cible.csv.gz", index_col=0)
Ydpe = Y.etiquette_dpe
Yconso = Y.conso_5_usages_par_m2_ef

# -------------------------------------------------------------
# Création des étapes de la pipeline de préparation des données
# -------------------------------------------------------------
# On a besoin de récupérer les colones lié aux différents traitements (numérique, catégoriel, catégoriel ordinal)
# Pour se faire on doit entrainé la préparation pour récupérer les colones
Xbis = Preparation().fit_transform(X)

cate_ord = [col for col in Xbis.select_dtypes(include="category").columns if Xbis[col].cat.ordered]
cate = [col for col in Xbis.select_dtypes(include="category").columns if not Xbis[col].cat.ordered]
cate += [col for col in Xbis.select_dtypes(include="bool")]
num = [col for col in Xbis.select_dtypes(exclude=["category","bool"])]

# Les traitements a effectué sont
#   Un one hot encoding pour les variables catégorielles
#   Un Ordinal encoding pour les variables ordinalles
#   Et une standardisation pour les variables quantitative 
encodeur = ColumnTransformer(
    transformers=[
        ('cate', OneHotEncoder(drop='first'), cate),
        ('cate_ordo', OrdinalEncoder(categories=[list(Xbis[c].cat.categories) for c in cate_ord]), cate_ord),
        ('numerique', StandardScaler(), num)
    ]
)

# Il regroupe les deux traitements 
preprocessor = Pipeline([
    ("typage", Preparation()),
    ("encodage", encodeur)
])

# --------------------
# Création des modèles
# --------------------
modeleconso = Pipeline(steps=[
    ('preprocessing', preprocessor),
    ('hgb', HistGradientBoostingRegressor(learning_rate = 0.05,
                                          max_iter = 300,
                                          max_leaf_nodes = 50))
])

modeledpe = Pipeline([
    ('preprocessing', preprocessor),
    ('hgb', HistGradientBoostingClassifier(class_weight = None,
                                           learning_rate = 0.1,
                                           max_leaf_nodes = 30))
])

# ------------------------
# Entrainement des modèles
# ------------------------
# On va entrainé le modèle qu'on a estimé comme meilleur via les notebook sur l'ensemble de nos données
modeleconso.fit(X,Yconso)
modeledpe.fit(X,Ydpe)

# ----------------------
# Sauvegarde des modèles
# ----------------------
os.makedirs("src/modeles", exist_ok=True)

with open("src/modeles/Modele_consomation.sav", "wb") as f:
    pickle.dump(modeleconso,f)

with open("src/modeles/Modele_dpe.sav", "wb") as f:
    pickle.dump(modeledpe,f)
