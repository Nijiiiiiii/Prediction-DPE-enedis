# Documentation technique — Prediction DPE ENEDIS

## 1. Présentation et architecture

Le projet collecte et exploite des données de diagnostics de performance énergétique (DPE) issues de l'ADEME. Il expose une application web Streamlit qui permet de consulter les données, d'explorer des graphiques et une carte, puis d'estimer la consommation énergétique et l'étiquette DPE d'un logement.

L'application est organisée en trois couches logiques :

1. **Données et modèles** : fichiers CSV compressés et modèles sérialisés.
2. **Traitement métier** : préparation des variables, chargement, filtrage, génération de graphiques et prédiction.
3. **Présentation** : pages Streamlit et composants de visualisation.

## 2. Organisation du dépôt

| Répertoire / fichier | Rôle |
|---|---|
| `app/1_📖_Contexte.py` | Page d'accueil et aperçu des données |
| `app/pages/2_📊_Graphiques.py` | Exploration graphique et cartographique |
| `app/pages/3_📈_Prediction.py` | Formulaire et affichage des prédictions |
| `app/util.py` | Chargement/cache des données et modèles, filtres et rendu |
| `app/preparation.py` | Transformateur scikit-learn `Preparation` |
| `app/graphique.py` | Fonctions de visualisation Matplotlib, Seaborn et Folium |
| `Data/dpe.csv.gz` | Jeu de données utilisé par l'application |
| `Data/dpe_explicative.csv.gz` | Variables explicatives utilisées à l'entraînement et pour les métadonnées du formulaire |
| `Data/dpe_cible.csv.gz` | Variables cibles : étiquette DPE et consommation |
| `Data/dpe_illu.csv.gz` | Jeu complémentaire d'illustration |
| `src/modeles/Modele_dpe.sav` | Pipeline de classification sérialisé |
| `src/modeles/Modele_consomation.sav` | Pipeline de régression sérialisé |
| `Dockerfile` | Construction et lancement du conteneur |
| `requirements.txt` | Dépendances Python |

## 3. Flux de données et exécution

### 3.1 Au démarrage

`app/util.py` construit les chemins à partir de `Path(__file__).resolve()` afin de ne pas dépendre du répertoire courant. Les données sont chargées avec `pandas.read_csv`. Les fonctions `charger_donnees` et `charger_metadata` utilisent `st.cache_data`; `charger_model` utilise `st.cache_resource` pour éviter de relire les fichiers à chaque interaction.

Les deux modèles sont chargés depuis `src/modeles/`. Un désérialiseur personnalisé redirige les références à la classe `Preparation` qui auraient été enregistrées sous `__main__` vers la classe de `app/preparation.py`.

### 3.2 Pendant une prédiction

1. Les métadonnées de `dpe_explicative.csv.gz` définissent les champs du formulaire : cases à cocher pour les booléens, listes déroulantes pour les variables catégorielles et champs numériques initialisés à la médiane observée.
2. Au clic sur **Prédire**, les valeurs sont assemblées dans un DataFrame d'une ligne.
3. Les colonnes sont remises dans l'ordre attendu par chaque pipeline (`align_columns`).
4. Le pipeline de régression renvoie `conso_5_usages_par_m2_ef`; le pipeline de classification renvoie `etiquette_dpe`.
5. `predict_proba` fournit les probabilités associées aux classes DPE, affichées sous forme de graphique en barres.

## 4. Prétraitement et modèles en production

Le transformateur `Preparation` convertit les chaînes en variables catégorielles et définit un ordre explicite pour certaines familles ordinales : période de construction, qualités d'isolation/confort et classe d'altitude. Le `ColumnTransformer` applique ensuite :

- `OneHotEncoder(drop="first")` aux variables catégorielles nominales ;
- `OrdinalEncoder` aux variables ordinales ;
- `StandardScaler` aux variables quantitatives.

Les pipelines finaux sont des `HistGradientBoosting` scikit-learn. La régression utilise `learning_rate=0.05`, `max_iter=300`, `max_leaf_nodes=50`. La classification utilise `learning_rate=0.1`, `max_leaf_nodes=30` et `class_weight=None`. Les paramètres sont visibles dans `src/modeles.py` et dans les notebooks d'expérimentation.

## 5. Installation et lancement

Les informations lié au lancement de l'application sont disponible sur le répositoire Git dans le [README.md](https://github.com/Nijiiiiiii/Prediction-DPE-enedis/blob/main/README.md).

## 6. Dépendances

Le fichier `requirements.txt` référence les différentes librairie utilisé pour le projet.