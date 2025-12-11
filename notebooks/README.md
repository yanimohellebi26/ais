# 📓 Notebooks

Ce dossier contient des **Jupyter Notebooks** utilisés pour explorer, analyser et visualiser des données dans le cadre du projet.  
Les notebooks permettent de combiner du code (Python), des visualisations et de la documentation dans un même document interactif.

---

## 🚀 Lancer un notebook

### 1. Installer les dépendances
Assurez-vous d’avoir **Python** installé, puis installez les paquets nécessaires :  

```bash
pip install -r requirement.txt
```

### 2. Lancer JupyterLab (que si pas d'IDE)
Les IDE propose normalemnet un serveur jupyter intégré, si non faite ceci

Dans le dossier du projet `/notebooks`, exécutez : (L'IDE peut l'avoir fait automatiquement)
```bash 
jupyter lab 
```

Dans le shell, utiliser le lien donné avec le token pour accéder a une interface web pour travailler sur le notebook.

### 3. 📂 Organisation
- Chaque notebook est stocké dans ce dossier /notebooks.

- Les notebooks peuvent contenir :
  - du code Python pour tester et analyser,
  - des visualisations de données,
  - des explications/documentation pour mieux comprendre le travail effectué.

### 4. Dataset

Les fichiers de **dataset** (**.csv**,**.json** ...) ne doivent pas être push sur github (normalement bloqué par le **.gitignore**)

Si vous voulez partager un fichier de dataset spécifique pour des tests, ajouter le manuellement (**via git add**) mais veillez 
à ce qu'il soit minimale (petit fichier)