📜 Stable Diffusion Prompt Creator – Guide de déploiement Windows
================================================================

Ce projet permet de générer des prompts optimisés pour Stable Diffusion en utilisant les tags Danbooru.

⚙️ 1. Prérequis
---------------
- Windows 10/11
- Python 3.10 ou supérieur
- Node.js (version 18 ou supérieure)
- Git installé
- Connexion Internet

📦 2. Installation du projet
----------------------------
1. Cloner le dépôt GitHub :
   git clone https://github.com/<ton-user>/<ton-repo>.git
   cd <ton-repo>

2. Lancer le script d’installation automatique :
   Double-clique sur :
      bootstrap_windows.bat

   Ce script :
   - Crée un environnement virtuel Python (.venv)
   - Installe les dépendances Python
   - Installe les dépendances Node.js du frontend
   - Prépare les caches nécessaires

🚀 3. Démarrage du projet
-------------------------
1. Lancer le backend :
   - Ouvrir un terminal
   - Activer l’environnement virtuel :
     .venv\Scripts\activate
   - Démarrer le serveur :
     uvicorn main:app --reload

2. Lancer le frontend :
   - Ouvrir un deuxième terminal
   - Aller dans le dossier frontend :
     cd frontend
   - Démarrer le serveur frontend :
     npm run dev

3. Accéder à l’application :
   Ouvre ton navigateur et va sur :
      http://localhost:3000

🧹 4. Nettoyage avant envoi sur GitHub
--------------------------------------
Avant de pousser sur GitHub, lancer :
   cleanup_windows.bat
Cela supprime les fichiers lourds (.venv, node_modules, caches) pour garder le repo léger.

📂 5. Structure du projet
-------------------------
- backend : code Python (API + logique)
- frontend : code React/Vue (interface)
- scripts : outils divers (.bat, .py)
- assets : images, ressources
- docs : documentation
- data : données export/import

✉️ Contact
----------
Auteur : <ton-nom-ou-pseudo>
Repo GitHub : https://github.com/<ton-user>/<ton-repo>
