
FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances système pour OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements depuis le dossier web
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le code source de l'application web
COPY web/ .

# Copie des modèles d'IA situés à la racine du projet
COPY models /models

# Exposition du port 8001
EXPOSE 8001

# Lancement d'Uvicorn sur le port 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]x
