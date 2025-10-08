import re


#### Reorder the dataframe columns

new_order = ['MMSI', 'VesselName', 'IMO', 'CallSign', 'VesselType', 'TransceiverClass', 
             'BaseDateTime', 'LAT', 'LON', 'SOG', 'COG', 'Heading', 'Status', 
             'Length', 'Width', 'Draft', 'Cargo']

df = df[new_order]

# ----------------------------------- \\\\\ ------------------------------------------- 


#### 3.1 Nettoyage et uniformisation des textes

# Fonction de nettoyage pour les noms de navires
def clean_vessel_name(name):
    if pd.isna(name):
        return None
    # Supprimer caractères spéciaux, trim espaces, tout en majuscules
    name = re.sub(r"[^A-Za-z0-9 ]", "", name).strip().upper()
    return name

df["VesselName"] = df["VesselName"].apply(clean_vessel_name)

# Uniformiser texte des colonnes catégorielles
for col in ["Cargo", "VesselType", "Status"]:
    df[col] = df[col].astype(str).str.strip().str.upper()





# ----------------------------------- \\\\\ ------------------------------------------- 

#### 3.2 Vérification des bornes physiques

def check_range(value, min_val, max_val):
    if pd.isna(value):
        return None
    if value < min_val or value > max_val:
        return None   # ou np.nan, ou correction par cap
    return value

df["Length"] = df["Length"].apply(lambda x: check_range(x, 5, 400))
df["Width"]  = df["Width"].apply(lambda x: check_range(x, 2, 60))
df["Draft"]  = df["Draft"].apply(lambda x: check_range(x, 0.5, 20))



# ----------------------------------- \\\\\ ------------------------------------------- 

#### 3.3 Validation des dates


df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"], errors="coerce")

# Vérifier s'il y a des valeurs invalides
invalid_dates = df[df["BaseDateTime"].isna()]
print("Dates invalides :", invalid_dates.shape[0])


# ----------------------------------- \\\\\ ------------------------------------------- 



#### 3.4 Vérification des identifiants

# MMSI → doit être 9 chiffres
# IMO → doit être "IMO" + 7 chiffres ou NaN
# CallSign → 3 à 7 caractères alphanumériques

df_valid = pd.DataFrame({
    "MMSI_valid": df["MMSI"].astype(str).str.match(r"^\d{9}$"),
    "IMO_valid": df["IMO"].astype(str).str.match(r"^\d{7}$"),
    "CallSign_valid": df["CallSign"].astype(str).str.match(r"^[A-Z0-9]{3,7}$")
})



# ----------------------------------- \\\\\ ------------------------------------------- 


#### 3.5 Arrondir LAT et LON à 2 décimales


df['LAT'] = df['LAT'].round(2)
df['LON'] = df['LON'].round(2)

