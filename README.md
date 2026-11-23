
# Prédiction DPE – ENEDIS

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Application-red)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)

## Présentation du projet

Dans le cadre du Master **Statistique et Informatique pour la Science des Données (SISE)**, ce projet porte sur le développement de modèles prédictifs permettant d'estimer l'étiquette du Diagnostic de Performance Énergétique (DPE) ainsi que la consommation énergétique des logements.

Les données utilisées proviennent de l'API de l'**ADEME** (Agence de la transition écologique). Le périmètre géographique de l'étude a été limité aux logements situés en **Corse**.

L'objectif est de proposer une application interactive permettant de visualiser les données, d'explorer les résultats et d'effectuer des prédictions à partir des modèles développés.

## Application

L'application est accessible selon plusieurs modalités : directement en ligne, via Docker ou en installation locale.

### Application web

L'application est accessible à l'adresse suivante :

[https://prediction-dpe-enedis.onrender.com](https://prediction-dpe-enedis.onrender.com)

Cette solution permet d'utiliser directement l'application depuis un navigateur, sans installation préalable.

Il convient toutefois de noter que les temps de chargement peuvent être plus importants sur la version en ligne, en raison des ressources et des limitations associées à l'hébergement sur Render. Cette solution reste néanmoins la plus simple et la plus pratique.

### Image Docker

L'application peut également être exécutée à partir de son image Docker, permettant de disposer d'un environnement reproductible sans avoir à installer manuellement les dépendances Python.

**Construction de l'image :**

```bash
docker build -t application-dpe .
```

**Lancement du conteneur :**

```bash
docker run -p 8501:8501 application-dpe
```

L'application est ensuite accessible à l'adresse :

[http://localhost:8501](http://localhost:8501)

### Installation et exécution en local

Une exécution locale est également possible à condition de disposer de Python et de Git.

**1. Cloner le dépôt**

```bash
git clone https://github.com/Nijiiiiiii/Prediction-DPE-enedis
```

**2. Accéder au répertoire du projet**

```bash
cd Prediction-DPE-enedis
```

**3. Créer un environnement virtuel**

```bash
python -m venv .venv
```

**4. Activer l'environnement virtuel**

Sous Windows :

```bash
.venv\Scripts\activate
```

Sous Linux / macOS :

```bash
source .venv/bin/activate
```

**5. Installer les dépendances**

```bash
pip install -r requirements.txt
```

**6. Lancer l'application**

```bash
streamlit run app/1_📖_Contexte.py
```

L'application est alors accessible à l'adresse :

[http://localhost:8501](http://localhost:8501)

## Technologies utilisées

- **Python** : développement et traitement des données.
- **Streamlit** : création de l'application web interactive.
- **Docker** : conteneurisation de l'application.
- **Render** : hébergement de l'application web.

## Structure du projet

```
Prediction-DPE-enedis
├── app/
│   ├── pages/
│   │   ├── 2_📊_Graphiques.py
│   │   └── 3_📈_Prediction.py
│   ├── 1_📖_Contexte.py
│   ├── util.py
│   ├── preparation.py
│   └── graphique.py
│
├── Data/
|   ├── dpe.csv.gz
|   ├── dpe_cible.csv.gz
|   ├── dpe_explicative.csv.gz
│   └── dpe_illu.csv.gz
|
├── Notebooks/
|   ├── ImportationExplorationDonnee.ipynb
|   ├── Modeles_classification.ipynb
|   ├── Modeles_regression.ipynb
│   └── pre_selection_variable.ipynb
│
├── src/
│   └── modeles/
│   |   ├── Modele_consomation.sav
│   |   └── Modele_dpe.sav
|   ├── importation.py
|   └── modeles.py
│
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── README.md
```

## Auteurs

Projet réalisé dans le cadre du Master Statistique et Informatique pour la Science des Données (SISE).
