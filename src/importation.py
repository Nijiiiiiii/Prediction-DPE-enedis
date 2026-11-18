import requests, os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_selection import VarianceThreshold, SelectFwe, f_classif, chi2


# Fonction permettant de récupérer les données sur l'API de l'ADEME
def get_dpe(type, params):
    if type == "existant":
        url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines"
    elif type == "neuf":
        url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe02neuf/lines"
    else:
        print("Type de logement introuvable")
        return None

    toutes_les_lignes = []

    while url:       
        response = requests.get(url, params=params)
        data = response.json()

        # Pour afficher le nombre total de ligne à scrapper 
        if params != None :
            print(f"Nombre total de ligne : {data.get('total')}")

        toutes_les_lignes.extend(data["results"])

        print(f"Nombre de lignes faites : {len(toutes_les_lignes)}")

        url = data.get("next")

        params = None

    df = pd.DataFrame(toutes_les_lignes)
    return df

def premier_import_dpe(type) :

    params = {
            "qs": "code_region_ban:94", # On se base dans la région CORSE
            "size": "500"
        }
    df = get_dpe(type, params)
    return df
    #df = preprocessing(df)
    #df.to_csv(f"Data/dpe_{type}.csv", index=False, encoding="utf-8")

def suite_import_dpe() :

    date = datetime.fromtimestamp(os.path.getmtime(f"Data/dpe.csv")).strftime("%Y-%m-%d")
    params = {
        "qs": "code_region_ban:94", # On se base dans la région CORSE
        "size": "500",
        "date_reception_dpe_gt" : date
        
        #Rajouté la sélection des lignes
    }

    df = get_dpe("neuf", params)
    df.index = df["numero_dpe"]
    df = df.drop(columns="numero_dpe")

    #Pas forcément nécessaire mais ça peut être cool 
    data = pd.read_csv(f"Data/dpe.csv", index_col="numero_dpe")
    df = df.loc[~df.index.isin(data.index)] #supprime les index déjà présent

    df.to_csv(f"Data/dpe.csv", mode="a", header=False, encoding="utf-8", index=True, index_label="numero_dpe")

def fusion_df(existant,neuf): 
    neuf = neuf.assign(logement="neuf", annee_construction=2026)
    existant["logement"] = "ancien"

    column_commune = neuf.columns.intersection(existant.columns)

    data = pd.concat([neuf.loc[:,column_commune],existant.loc[:,column_commune]], ignore_index=True)
    return data

def preselection():
    #Récupération des variables de l'api existante
    variables = requests.get("http://data.ademe.fr/data-fair/api/v1/datasets/meg-83tjwtg8dyz4vv7h1dqe/schema?mimeType=application%2Fschema%2Bjson")
    variables = variables.json()
    data = pd.DataFrame(variables["properties"]).transpose() 

    #Récupération des informations qui ont été considéré comme inutiles/à garder
    administratif = data[data["x-group"] == "Administratif"].index.tolist()[1:] # On retirer le numéro DPE qu'on gardera en index (vu qu'il est un identifiant unique)

    dpe = data[data["x-group"] == "Bilan DPE"].index.tolist()

    consomation = data[(data["x-group"] == "Consommation en énergie primaire") | (data["x-group"] == "Consommation en énergie finale")].index.tolist()

    localisation = data[data["x-group"] == "Localisation"].index.tolist()
    variable_a_garder = ["classe_altitude","zone_climatique","coordonnee_cartographique_x_ban","coordonnee_cartographique_y_ban"]
    localisation = [x for x in localisation if x not in variable_a_garder]

    apport_et_besoin = data[data["x-group"] == "Apport et besoin"].index.tolist()

    emission = data[data["x-group"] == "Emissions de GES"].index.tolist()

    bilan_energie = data[data["x-group"] == "Bilan par énergie"].index.tolist()

    cout = data[data["x-group"] == "Coûts"].index.tolist()

    variable_a_suppr = administratif + apport_et_besoin + cout + bilan_energie + emission + localisation
    variable_cible = dpe + consomation

    return variable_a_suppr, variable_cible

def verification_type(data):
    #Variable booléenne
    #Si min = 0 et max = 1 -> c'est du booléen
    min0 = data.min()==0
    max1 = data.max()==1

    bool_cols = data.columns[min0 & max1]

    data[bool_cols] = data[bool_cols].astype(bool)
    return data

def selection_variables1(data):
    col_a_sup = []

    #variable avec trop de valeurs manquantes
    na = data.columns[(data.isna().sum()*100/data.shape[0])>=50]
    col_a_sup.extend(na)

    #Valeurs unique/identique pour tous
    #Si la variable est identique partout
    identique = data.nunique()==1
    not_this_col = data.columns[identique] #On récupère son nom
    col_a_sup.extend(not_this_col)

    #Si la variable est différente partout
    unique = data.nunique()==data.shape[0]
    not_this_col = data.columns[unique] #On récupère son nom
    col_a_sup.extend(not_this_col)

    #Variable quali avec plus de 17 modalité
    trop_quali = data.select_dtypes(include="str").nunique()>17
    col_a_sup.extend(data.select_dtypes(include="str").columns[trop_quali])

    #Variable binaire avec présence trop importante d'une classe
    # Var(x) = p(1-p), ici p = 75%, on supprime alors toutes les variables binaires 
    # qui ont une catégorie avec 75% ou plus d'observation (et donc une plus faible)

    # Source : Guide pratique du machine learning avec Python, chapitre 10 p.198
    thresholder_bool = VarianceThreshold(threshold=0.75*(1-0.75)) 
    thresholder_bool.fit_transform(data.select_dtypes(include="bool"))
    col_a_sup.extend(data.select_dtypes(include="bool").columns[~thresholder_bool.get_support()]) 

    #Variables fortement corrélé (90%)
    #Matrice de corrélation
    corr_matrix = data.select_dtypes(include=["int","float"]).corr().abs()
    #On récupère que la diagonale supérieur (car la matrice est symétrique, un seul coté suffit)
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape),k=1).astype(bool))
    #On cherche les colones qui ont plus de 90% de corrélation avec une autre variable
    to_drop = [col for col in upper.columns if any(upper[col] > 0.90)]
    col_a_sup.extend(to_drop)

    col_a_sup = set(col_a_sup) 
    data = data.drop(columns=col_a_sup)
    a_retirer = data.filter(regex="^_|deperditions_|_n1|annee_construction|ubat_w_par_m2_k|production_electricite_pv_kwhep_par_an").columns.tolist()
    data = data.drop(columns=a_retirer)

    return data
    
def impute(data):
    for col in data.columns:
        try:
            data[col] = data[col].fillna(data[col].median()) #Imputation par la médiane des variables quanti
        except:
            try:
                data[col] = data[col].fillna("Inconnue") #Imputation par une nouvelle catégorie "Inconnue"
            except:
                pass
    return data

#Ca sert à R j'avais juste fait une erreur de code LOL
def selection_variables2(data,Y):
    XQuali = data.select_dtypes(include=["str","bool"])
    XQuali_encoded = pd.get_dummies(XQuali, dtype=int)
    XQuanti = data.select_dtypes(exclude=["str","bool"])

    sel = SelectFwe(f_classif, alpha=0.001) # Si significativité de + de 99,9%, on sélectionne
    sel.fit(XQuanti, Y["etiquette_dpe"])
    col_quanti_suppr = [x for x in XQuanti.columns if x not in XQuanti.columns[sel.pvalues_ < 0.001]]

    chi2_selector = SelectFwe(chi2, alpha=0.05)
    XQuali_kbest = chi2_selector.fit_transform(XQuali_encoded, Y["etiquette_dpe"])
    
    colonnes_selectionnees = XQuali_encoded.columns[chi2_selector.get_support()]
    # On va récupéré les vrais nom des colones :
    vrai_col= []
    for col in colonnes_selectionnees :
        if col not in XQuali.columns:
            col = col.split("_")[:-1] #On enlève le rajout du get dummies
            col ="_".join(col)
            if col not in vrai_col:
                vrai_col.append(col)
        else:
            vrai_col.append(col)

    col_quali_suppr = [x for x in XQuali.columns if x not in vrai_col]

def outliers_quali(data):
    outlier = []
    for x in data.select_dtypes(include=["str"]).columns:

        frequences = data[x].value_counts(normalize=True)
        modalites_rares = frequences[frequences<0.02].index.tolist()

        #Suppression des individus avec "Inconnue" si cette modalité est rare
        if "Inconnue" in modalites_rares:
            ind = data[data[x] == "Inconnue"].index
            outlier.extend(ind.tolist())
            data = data.drop(index=ind)

            #Recalcule des fréquences
            frequences = data[x].value_counts(normalize=True)
            modalites_rares = frequences[frequences < 0.05].index.tolist()

        #Regroupement des modalités rares
        if len(modalites_rares) > 1:
            data[x] = data[x].replace(modalites_rares, "Autre")

        #Suppression d'une seule modalité rare, sauf "Autre"
        elif len(modalites_rares) == 1 and modalites_rares[0] != "Autre":
            ind = data[data[x] == modalites_rares[0]].index
            outlier.extend(ind.tolist())
            data = data.drop(index=ind)

        modalite = data[x].value_counts(normalize=True).index.tolist()

        #Si inconnue et autre cohexite, regroupé sous Autre
        if "Inconnue" in modalite and "Autre" in modalite:
            data[x] = data[x].replace("Inconnue", "Autre")

    return outlier, data

def suppression_ind(data,Y,illu):
    #Les index manquant dans la VD
    index_manquants = Y[Y.isna().any(axis=1)].index

    print(type(data))
    data = data.drop(index=index_manquants)
    Y = Y.drop(index=index_manquants)
    illu = illu.drop(index=index_manquants)

    #Les outliers
    outliers, data = outliers_quali(data)

    #Les outliers quanti
    col = data.select_dtypes(exclude="str").columns
    seuils = {
        col[0]: None,  # On conserve tout
        col[1]: 2500,
        col[2]: 100,
        col[3]: None   # On conserve tout
    }

    for col, seuil in seuils.items():
        if seuil is not None:
            ind= data[data[col] > seuil].index
            outliers.extend(ind.tolist())
            data = data.drop(index=ind)

    Y = Y.drop(index=outliers)
    illu = illu.drop(index=outliers)

    return data, Y, illu

def preprocessing():
    dpe_existant = premier_import_dpe("existant")
    dpe_neuf = premier_import_dpe("neuf")
    #dpe_existant = pd.read_csv(r"C:\Users\nijim\Documents\GitHub\Prediction-DPE-enedis\Data\dpe_existant.csv")
    #dpe_neuf = pd.read_csv(r"C:\Users\nijim\Documents\GitHub\Prediction-DPE-enedis\Data\dpe_neuf.csv")

    #Fusion des dataframes pour en faire qu'un seul
    data = fusion_df(existant=dpe_existant, neuf=dpe_neuf)

    #Passage du numéro dpe en index
    data.index = data["numero_dpe"]
    data = data.drop(columns="numero_dpe")

    print("préselection")
    variable_a_suppr, variable_cible = preselection()

    #On vérifie que les variables sont bien présente
    variable_a_suppr = [var for var in variable_a_suppr if var in data.columns]
    variable_cible = [var for var in variable_cible if var in data.columns]

    #On supprime les variables à supprimer 
    data = data.drop(columns=variable_a_suppr)

    #On garde les variables cibles et supprime de data
    Y = data.loc[:,variable_cible]
    data = data.drop(columns=variable_cible)

    #Idem pour les variables illustrative
    ILLU = data.filter(regex="coordonnee_cartographique_")
    data = data.drop(columns=ILLU.columns)

    #Vérification des types
    print("vérification des types")
    data = verification_type(data)


    #Première sélection de variables
    print("sélections de variables")
    data = selection_variables1(data)


    #Imputation données manquantes
    print("imputation des données")
    data = impute(data)

    #Supprésion des outliers / var Y manquante 
    print("suppréssion des outliers")
    data, Y, ILLU = suppression_ind(data,Y,ILLU)


    #Supprésion des variables considéré comme inutiles dans la classification (qu'on étendra à la régression)
    #data = selection_variables2(data,Y)  

    print("enregistrement des csv")
    data.to_csv("Data/dpe_explicative.csv.gz", index=True, encoding="utf-8")
    Y.to_csv("Data/dpe_cible.csv.gz", index=True, encoding="utf-8")
    ILLU.to_csv("Data/dpe_illu.csv.gz", index=True, encoding="utf-8")

    pd.concat([data,ILLU,Y], axis=1, ignore_index=False).to_csv("Data/dpe.csv.gz", index=True, encoding="utf-8")


if not os.path.exists("Data/dpe.csv.gz"):
    preprocessing()

else:
    print(pd.read_csv("Data/dpe.csv.gz", index_col="numero_dpe").head(5))
