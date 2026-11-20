import requests, os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_selection import VarianceThreshold, SelectFwe, f_classif, chi2

def get_dpe(type, params):
    # Fonction qui questionne l'API selon le type de logement
    # et un certain nombre de paramètres 
    # et renvoie un dataframe avec l'entièrté des lignes récupérer
    if type == "existant":
        url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines"
    elif type == "neuf":
        url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe02neuf/lines"
    else:
        print("Type de logement introuvable")
        return None

    print(f"Récupérations des dpe {type}")
    # Entièreté des lignes récupéré
    toutes_les_lignes = []

    try : # Afin de gérer tout problèmes lié à la connexion et de ne pas faire planté le programmes
        while url:       
            response = requests.get(url, params=params)
            data = response.json()

            # Pour afficher le nombre total de ligne à récupérer 
            if params != None :
                print(f"    Nombre total de ligne : {data.get('total')}")

                if data.get('total') == 0:
                    print("    Aucune données en plus")
                    return None
                
            # Ajout des lignes dans la liste
            toutes_les_lignes.extend(data["results"])

            # Suivre l'avancement des téléchargements
            print(f"    Nombre de lignes faites : {len(toutes_les_lignes)}")

            # Récupération de la suite des pages et mise à None des paramettres qui deviennent inutiles
            url = data.get("next")
            params = None

        # Transformation en DataFrame
        df = pd.DataFrame(toutes_les_lignes)
        return df
    except :
        return None

def premier_import_dpe(type) :
    # Paramètre pour le premier imports des données
    # -> toutes les lignes de la région de Corse
    params = {
            "qs": "code_region_ban:94",
            "size": "500" #Afin de récupérer peu à peu les données
            # Après plusieurs test 500 semblait un bon paramètres assez rapide 
        }
    # Récupère les informations 
    df = get_dpe(type, params)
    return df

def fusion_df(existant,neuf): 
    # Fusion des deux dpe (neuf et existant)
    # Ajout des valeurs importantes
    neuf = neuf.assign(logement="neuf", annee_construction=2026)
    existant["logement"] = "ancien"

    # On garde que les colones communes
    column_commune = neuf.columns.intersection(existant.columns)

    data = pd.concat([neuf.loc[:,column_commune],existant.loc[:,column_commune]], ignore_index=True)
    return data

def preselection():
    # Récupération des variables de l'api existante
    variables = requests.get("http://data.ademe.fr/data-fair/api/v1/datasets/meg-83tjwtg8dyz4vv7h1dqe/schema?mimeType=application%2Fschema%2Bjson")
    if variables : 
        variables = variables.json()
        data = pd.DataFrame(variables["properties"]).transpose() 

        #Récupération des informations qui ont été considéré comme inutiles/à garder
        administratif = data[data["x-group"] == "Administratif"].index.tolist()[1:] # On retirer le numéro DPE qu'on gardera en index (vu qu'il est un identifiant unique)

        # Récupération des étiquête DPE -> cible
        dpe = data[data["x-group"] == "Bilan DPE"].index.tolist()

        # Récupération des consomations -> cibles
        consomation = data[(data["x-group"] == "Consommation en énergie primaire") | (data["x-group"] == "Consommation en énergie finale")].index.tolist()

        # Récupération de variable de locations -> a supprimé
        localisation = data[data["x-group"] == "Localisation"].index.tolist()
        # Celle-ci peuvent se révélé utile dans l'analyse / sont utile à la création de la carte
        variable_a_garder = ["classe_altitude","zone_climatique","coordonnee_cartographique_x_ban","coordonnee_cartographique_y_ban"]
        localisation = [x for x in localisation if x not in variable_a_garder]

        # A supprimer
        apport_et_besoin = data[data["x-group"] == "Apport et besoin"].index.tolist()

        # A supprimer (lié au DPE trop fortement)
        emission = data[data["x-group"] == "Emissions de GES"].index.tolist()

        # A supprimer (lié au DPE trop fortement)
        bilan_energie = data[data["x-group"] == "Bilan par énergie"].index.tolist()

        # A supprimer (lié au DPE trop fortement)
        cout = data[data["x-group"] == "Coûts"].index.tolist()

        variable_a_suppr = administratif + apport_et_besoin + cout + bilan_energie + emission + localisation
        variable_cible = dpe + consomation

        return variable_a_suppr, variable_cible
    else :
        print("Problème à la récupération du json des variables")
        return None

def verification_type(data):
    # Vérification du type booléen 
    # Si min = 0 et max = 1 -> c'est du booléen
    min0 = data.min()==0
    max1 = data.max()==1

    bool_cols = data.columns[min0 & max1]

    data[bool_cols] = data[bool_cols].astype(bool)
    return data

def selection_variables(data):
    # Variable qui va garder toutes les variables à supprimé selon les traitements
    col_a_sup = []

    # Variable avec trop de valeurs manquantes
    na = data.columns[(data.isna().sum()*100/data.shape[0])>=50]
    col_a_sup.extend(na)

    # Valeurs unique/identique pour tous
    # Si la variable est identique partout
    identique = data.nunique()==1
    not_this_col = data.columns[identique] #On récupère son nom
    col_a_sup.extend(not_this_col)

    # Si la variable est différente partout
    unique = data.nunique()==data.shape[0]
    not_this_col = data.columns[unique] #On récupère son nom
    col_a_sup.extend(not_this_col)

    # Variable quali avec plus de 13 modalité
    trop_quali = data.select_dtypes(include="str").nunique()>13
    col_a_sup.extend(data.select_dtypes(include="str").columns[trop_quali])

    # Variable binaire avec présence trop importante d'une classe
    # Var(x) = p(1-p), ici p = 75%, on supprime alors toutes les variables binaires 
    # qui ont une catégorie avec 75% ou plus d'observation (et donc une plus faible)
    # Source : Guide pratique du machine learning avec Python, chapitre 10 p.198

    thresholder_bool = VarianceThreshold(threshold=0.75*(1-0.75)) 
    thresholder_bool.fit_transform(data.select_dtypes(include="bool"))
    col_a_sup.extend(data.select_dtypes(include="bool").columns[~thresholder_bool.get_support()]) 

    # Variables fortement corrélé entre-elle (90%)
    # Matrice de corrélation
    corr_matrix = data.select_dtypes(include=["int","float"]).corr().abs()
    # On récupère que la diagonale supérieur (car la matrice est symétrique, un seul coté suffit)
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape),k=1).astype(bool))
    # On cherche les colones qui ont plus de 90% de corrélation avec une autre variable
    to_drop = [col for col in upper.columns if any(upper[col] > 0.90)]
    col_a_sup.extend(to_drop)

    # On supprime les valeurs doubles des colones
    col_a_sup = set(col_a_sup) 
    data = data.drop(columns=col_a_sup)
    # On supprime en plus certaine variable considéré comme inutiles / que les utilisateurs n'aurons pas
    # Pour l'annee_construction, plusieurs données manquantes ont été remarqué
    # Or, une variable periode de construction existe et n'a aucune valeurs manquante
    # Le choix c'est fait de garder uniquement cette variables
    a_retirer = data.filter(regex="^_|deperditions_|_n1|annee_construction|ubat_w_par_m2_k|production_electricite_pv_kwhep_par_an").columns.tolist()
    data = data.drop(columns=a_retirer)

    return data
    
def impute(data): 
    # Imutation des données manquantes par la médian (variable quanti) ou par une nouvelle modalité "Inconnue"
    for col in data.columns:
        try:
            data[col] = data[col].fillna(data[col].median()) #Imputation par la médiane des variables quanti
        except:
            try:
                data[col] = data[col].fillna("Inconnue") #Imputation par une nouvelle catégorie "Inconnue"
            except:
                pass
    return data

def selection_variables2(data,Y):
    XQuali = data.select_dtypes(include=["str","bool"])
    XQuali_encoded = pd.get_dummies(XQuali, dtype=int)
    XQuanti = data.select_dtypes(exclude=["str","bool"])

    sel = SelectFwe(f_classif, alpha=0.001) # Si significativité de + de 99,9%, on sélectionne
    sel.fit(XQuanti, Y["etiquette_dpe"])
    col_quanti_garde = XQuanti.columns[sel.pvalues_ < 0.001]

    chi2_selector = SelectFwe(chi2, alpha=0.05)
    XQuali_kbest = chi2_selector.fit_transform(XQuali_encoded, Y["etiquette_dpe"])
    
    colonnes_selectionnees = XQuali_encoded.columns[chi2_selector.get_support()]
    # On va récupéré les vrais nom des colones :
    col_quali_garde= []
    for col in colonnes_selectionnees :
        if col not in XQuali.columns:
            col = col.split("_")[:-1] # On enlève le rajout du get dummies
            col ="_".join(col) # On reconstruit comme il faut le nom de la colonne
            if col not in col_quali_garde and col in XQuali: 
                col_quali_garde.append(col)
        else:
            col_quali_garde.append(col)

    data = pd.concat([XQuanti[col_quanti_garde], XQuali[col_quali_garde]], ignore_index=False, axis=1)
    return data
    
def outliers_quali(data):
    outlier = []
    for x in data.select_dtypes(include=["str","bool"]).columns:
        # On regarde les fréquences
        frequences = data[x].value_counts(normalize=True)
        # On considère comme modalité rare une modalité avec - de 2% des valeurs
        modalites_rares = frequences[frequences<0.02].index.tolist()

        # Suppression des individus avec "Inconnue" si cette modalité est rare
        if "Inconnue" in modalites_rares:
            ind = data[data[x] == "Inconnue"].index
            outlier.extend(ind.tolist())
            data = data.drop(index=ind)

            # Recalcule des fréquences
            frequences = data[x].value_counts(normalize=True)
            modalites_rares = frequences[frequences < 0.05].index.tolist()

        # Regroupement des modalités rares par Autre
        if len(modalites_rares) > 1:
            data[x] = data[x].replace(modalites_rares, "Autre")

        # S'il y a qu'une modalité rare autre que "Autre" -> suppression des individus
        elif len(modalites_rares) == 1 and modalites_rares[0] != "Autre":
            ind = data[data[x] == modalites_rares[0]].index
            outlier.extend(ind.tolist())
            data = data.drop(index=ind)

        modalite = data[x].value_counts(normalize=True).index.tolist()

        # Si inconnue et autre cohexite, regroupé sous Autre
        if "Inconnue" in modalite and "Autre" in modalite:
            data[x] = data[x].replace("Inconnue", "Autre")

    return outlier, data

def suppression_ind(data,Y,illu):
    # Les index manquant dans la VD
    index_manquants = Y[Y.isna().any(axis=1)].index

    print(type(data))
    data = data.drop(index=index_manquants)
    Y = Y.drop(index=index_manquants)
    illu = illu.drop(index=index_manquants)

    #Les outliers
    outliers, data = outliers_quali(data)

    #Les outliers quanti
    col = data.select_dtypes(exclude=["str","bool"]).columns
    seuils = {
        col[0]: None,  # On conserve tout
        col[1]: 2500, # On a fixé des seuils 
        col[2]: 100,
        col[3]: None   # On conserve tout
    }

    for col, seuil in seuils.items():
        if seuil is not None:
            ind = data[data[col] > seuil].index
            outliers.extend(ind.tolist())
            data = data.drop(index=ind)

    Y = Y.drop(index=outliers)
    illu = illu.drop(index=outliers)

    return data, Y, illu

def preprocessing():
    print("Importation des données")
    # Import des deux jeux de données 
    dpe_existant = premier_import_dpe("existant")
    dpe_neuf = premier_import_dpe("neuf")
    
    # Fusion des dataframes pour en faire qu'un seul
    data = fusion_df(existant=dpe_existant, neuf=dpe_neuf)

    # Passage du numéro dpe en index
    data.index = data["numero_dpe"]
    data = data.drop(columns="numero_dpe")

    print("Préselection")
    variable_a_suppr, variable_cible = preselection()

    # On vérifie que les variables sont bien présente
    variable_a_suppr = [var for var in variable_a_suppr if var in data.columns]
    variable_cible = [var for var in variable_cible if var in data.columns]

    # On supprime les variables à supprimer 
    data = data.drop(columns=variable_a_suppr)

    # On garde les variables cibles et supprime de data
    Y = data.loc[:,variable_cible]
    data = data.drop(columns=variable_cible)

    # Idem pour les variables illustrative
    ILLU = data.filter(regex="coordonnee_cartographique_")
    data = data.drop(columns=ILLU.columns)

    # Vérification des types
    print("Vérification des types")
    data = verification_type(data)

    # Première sélection de variables -> valeurs manquantes, trop de modalité etc...
    print("sélections de variables")
    data = selection_variables(data)

    # Imputation données manquantes
    print("imputation des données")
    data = impute(data)

    # Deuxième sélection de variables -> pas assez correlé à la VD
    print("Deuxième sélection de variables")
    data = selection_variables2(data, Y)

    #Supprésion des outliers / var Y manquante 
    print("Suppréssion des outliers")
    data, Y, ILLU = suppression_ind(data,Y,ILLU)

    print("Enregistrement des csv")
    #Format compressé pour les déposé dans le git
    data.to_csv("Data/dpe_explicative.csv.gz", index=True, encoding="utf-8")
    Y.to_csv("Data/dpe_cible.csv.gz", index=True, encoding="utf-8")
    ILLU.to_csv("Data/dpe_illu.csv.gz", index=True, encoding="utf-8")

    pd.concat([data,ILLU,Y], axis=1, ignore_index=False).to_csv("Data/dpe.csv.gz", index=True, encoding="utf-8")

# Fonctionnalité experte ! 
def suite_import_dpe() :
    # Après tout les traitements effectuer, on est capable de questionné plus spécifiquement l'API
    # En sélectionnant que les variables qui nous intéressent 
    # Et en ne prenant que les DPE renseigné après notre dernier "refresh"
    date = datetime.fromtimestamp(os.path.getmtime(f"Data/dpe.csv")).strftime("%Y-%m-%d")
    
    # A OPPTIMISER 
    # On récupère les données existantes
    data = pd.read_csv(f"Data/dpe.csv", index_col="numero_dpe")
    col = ",".join(data.columns)

    params = {
        "qs": "code_region_ban:94", # On se base dans la région CORSE
        "size": "500",
        "date_reception_dpe_gt" : date,
        "select" : col
    }

    # Récupération pour les logements neuf
    dfneuf = get_dpe("neuf", params)
    dfexist = get_dpe("existant", params)
    if dfneuf != None :
        dfneuf.index = dfneuf["numero_dpe"]
        dfneuf = dfneuf.drop(columns="numero_dpe")
        dfneuf = dfneuf.loc[~dfneuf.index.isin(data.index)] #supprime les index déjà présent    
    if dfexist != None :
        dfexist.index = dfexist["numero_dpe"]
        dfexist = dfexist.drop(columns="numero_dpe")
        dfexist = dfexist.loc[~dfexist.index.isin(data.index)] #supprime les index déjà présent

    if (dfneuf != None) and (dfexist != None) :
        df = pd.concat([dfneuf,dfexist], ignore_index=True, axis=1)
    elif dfneuf != None :
        df = dfneuf
    else :
        df = dfexist

    # On conserve les données dans un espace dédié
    df.to_csv("Data/dpe_plus.csv.gz", mode="w", encoding="utf-8", index=True)

# Traitement à effectuer : exemple
if not os.path.exists("Data/dpe.csv.gz"):
    preprocessing()

data = pd.read_csv("Data/dpe.csv.gz", index_col="numero_dpe")
print(data.head(3))