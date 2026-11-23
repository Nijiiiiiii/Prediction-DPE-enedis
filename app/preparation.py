from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd

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