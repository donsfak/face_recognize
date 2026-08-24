# Système de Pointage par Reconnaissance Faciale (IA)

Une application web complète et temps réel de contrôle d'accès et de pointage, propulsée par l'Intelligence Artificielle. Ce système capture le flux vidéo, identifie les individus grâce à une base vectorielle, intègre une sécurité anti-spoofing (Liveness 3D), et historise les pointages dans le cloud.

## ✨ Fonctionnalités

- **Reconnaissance Faciale Temps Réel :** Extraction d'embeddings via InsightFace et recherche de similarité ultra-rapide avec FAISS.
- **Détection Anti-Spoofing (Liveness) :** Analyse géométrique des ratios 3D du visage couplée à un historique de lissage (smoothing) pour bloquer les tentatives de fraude par photo ou écran.
- **Enrôlement Multi-Captures Intelligent :** Interface permettant d'ajouter de nouveaux utilisateurs à chaud via la webcam. Le système prend 5 captures automatisées, calcule le vecteur moyen et met à jour l'index vectoriel en mémoire sans redémarrage.
- **Communication Asynchrone :** Traitement vidéo fluide via WebSockets pour éviter les goulots d'étranglement.
- **Dashboard Cloud :** Historisation instantanée et sécurisée des présences sur une base de données Supabase (PostgreSQL).
- **Architecture Conteneurisée :** Prêt pour la production avec Docker et Portainer.

## 🛠️ Stack Technique

- **Backend :** Python 3.10, FastAPI, Uvicorn, WebSockets
- **Intelligence Artificielle :** InsightFace, OpenCV, FAISS, ONNXRuntime, NumPy
- **Frontend :** HTML5, CSS3, JavaScript (Vanilla)
- **Base de données :** Supabase (PostgreSQL)
- **DevOps :** Docker, Docker Compose, Portainer

## 📂 Architecture du Projet

```text
face_recognize/
├── models/
│   └── encodings_arcface.npz    # Base vectorielle des visages (générée dynamiquement)
├── web/
│   ├── database/
│   │   └── crud.py              # Logique d'interaction avec Supabase
│   ├── engine/
│   │   ├── recognition.py       # Cœur de l'IA (InsightFace, FAISS, Liveness)
│   │   └── stream.py            # Gestion des flux vidéo via WebSockets
│   ├── static/
│   │   ├── camera.js            # Logique front-end du scanner
│   │   └── style.css            # Styles de l'interface
│   ├── templates/
│   │   ├── dashboard.html       # Tableau de bord historique
│   │   ├── scanner.html         # Interface de scan vidéo
│   │   └── register.html        # Interface d'enrôlement multi-captures
│   ├── app.py                   # Point d'entrée de l'API FastAPI
│   ├── requirements.txt         # Dépendances Python
│   └── Dockerfile               # Configuration de l'image applicative
├── docker-compose.yml           # Fichier d'orchestration Docker
├── .gitignore                   # Exclusion des fichiers sensibles
└── README.md                    # Documentation


🚀 Guide d'Installation (Local)
1. Prérequis
    - Python 3.10+
  
    - Un compte Supabase actif (avec une table attendance_logs)

    - Une webcam fonctionnelle


2. Cloner le dépôt
  - git clone [https://github.com/votre-nom-utilisateur/face_recognize.git](https://github.com/votre-nom-utilisateur/face_recognize.git)
cd face_recognize

3. Configuration de l'environnement virtuel
    - python3 -m venv venv

    - source venv/bin/activate

    - pip install -r web/requirements.txt

4. Variables d'environnement
    - SUPABASE_URL=[https://votre-projet.supabase.co](https://votre-projet.supabase.co)

    - SUPABASE_KEY=votre-cle-api-publique-anon

5. Lancement du serveur de développement
  - uvicorn app:app --host 127.0.0.1 --port 8001 --reload
```
## 🐳 Déploiement en Production (Docker)

    1. Construire l'image depuis la racine du projet
    
        - docker build -t face-attendance-app:latest -f web/Dockerfile .
        
    2. Lancer le conteneur via Docker Compose

        - docker compose up -d
        
NB : Si vous utilisez Portainer, vous pouvez directement déployer le contenu du docker-compose.yml en tant que nouvelle "Stack".
