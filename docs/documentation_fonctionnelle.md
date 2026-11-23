# Documentation fonctionnelle — Prediction DPE ENEDIS

## 1. À quoi sert l'application ?

Cette application est interactive et est consacrée à l'exploration des diagnostics de performance énergétique des logements en Corse. Elle permet de consulter les données ADEME, d'observer leur répartition et d'obtenir une estimation de la consommation énergétique et de l'étiquette DPE d'un logement à partir de ses caractéristiques.

L'application est un outil d'information et de simulation.

## 2. Accéder à l'application

L'application peut être utilisée directement en ligne :

[Ouvrir l'application hébergée](https://prediction-dpe-enedis.onrender.com)

Elle peut également être lancée localement ou avec Docker ; les instructions sont disponibles dans le README du projet.

## 3. Les rubriques de l'application

### 3.1 Contexte

Cette page présente l'objectif du projet et les données mobilisées. Elle affiche le nombre de logements et le nombre de variables disponibles. Des filtres permettent de sélectionner des modalités de variables catégorielles ou des intervalles de variables numériques. Un tableau permet ensuite de consulter un extrait des données filtrées ; le nombre de lignes affichées peut être ajusté.

### 3.2 Graphiques

Cette rubrique propose une exploration visuelle des logements. Les graphiques sont organisés par grands thèmes :

- étiquette DPE ;
- étiquette GES ;
- période de construction ;
- type de bâtiment ;
- énergie principale.

Selon le thème, l'utilisateur peut consulter des répartitions, histogrammes, comparaisons de consommation ou répartitions par catégorie. Une carte localise les logements disposant de coordonnées valides et colore les points selon leur classe DPE. Les filtres permettent de restreindre les données représentées.

Les graphiques peuvent être téléchargés au format PNG.

### 3.3 Prédiction

La page de prédiction permet de simuler un logement :

1. Renseigner les caractéristiques demandées dans le formulaire.
2. Cliquer sur **Prédire**.
3. Lire les résultats affichés.

Deux résultats sont fournis :

- **Consommation prédite** : estimation en kWh/m²/an.
- **Classe DPE prédite** : étiquette estimée de A à G.

Un graphique complémentaire présente les probabilités estimées pour les différentes classes DPE lorsque le modèle les fournit.

## 4. Comprendre les résultats

### Consommation

La valeur correspond à une estimation selon notre modèle de la consommation conventionnelle des cinq usages par mètre carré et par an. Elle s'exprime en kWh/m²/an.

### Étiquette DPE

Les classes vont de A (logement très performant) à G (logement très énergivore). La classe affichée est celle que le modèle juge la plus probable au regard des caractéristiques saisies.

### Probabilités par classe

Le graphique indique la répartition des probabilités estimées par le classifieur. Une probabilité plus élevée pour une classe signifie que le modèle privilégie cette classe parmi les possibilités.

## 5. Conseils d'utilisation et limites

- Garder à l'esprit que les modèles ont été construits à partir de logements situés en Corse : leur fiabilité n'est pas établie pour d'autres territoires.
- En cas d'erreur lors du calcul, vérifier les valeurs saisies et réessayer. Si le problème persiste, contacter l'équipe responsable de l'application.

## 6. En résumé

L'application permet de passer de l'observation d'un parc de logements à une simulation individuelle : la rubrique **Contexte** aide à comprendre les données, **Graphiques** permet d'en explorer les tendances et **Prédiction** estime la consommation et la classe DPE d'un logement décrit par l'utilisateur.

## Liens utiles

- [Application en ligne](https://prediction-dpe-enedis.onrender.com)
- [Code source et instructions d'installation](https://github.com/Nijiiiiiii/Prediction-DPE-enedis)
