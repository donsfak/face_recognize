import os
import cv2
import numpy as np
from fastapi import FastAPI, Request, WebSocket, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from engine.stream import websocket_endpoint, engine
from database.crud import get_recent_logs
from typing import List

app = FastAPI(title="Face Attendance API")

# Montage des fichiers statiques et des templates HTML
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    """Route principale : Tableau de bord affichant les derniers logs de Supabase."""
    logs = get_recent_logs(limit=20)
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"logs": logs})

@app.get("/scanner", response_class=HTMLResponse)
async def read_scanner(request: Request):
    """Route du flux vidéo en direct de la caméra."""
    return templates.TemplateResponse(request=request, name="scanner.html")

@app.get("/register", response_class=HTMLResponse)
async def read_register(request: Request):
    """Route du formulaire d'enrôlement d'une nouvelle personne."""
    return templates.TemplateResponse(request=request, name="register.html")

@app.post("/register-user")
async def register_user(name: str = Form(...), files: List[UploadFile] = File(...)):
    """API d'enrôlement multi-photos : Extrait et moyenne les embeddings de plusieurs captures."""
    try:
        embeddings = []
        
        for file in files:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                faces = engine.app.get(frame)
                if len(faces) > 0:
                    embeddings.append(faces[0].normed_embedding)
        
        if len(embeddings) == 0:
            raise HTTPException(status_code=400, detail="Aucun visage valide détecté sur les photos. Veuillez recommencer.")
        
        # Calcul du vecteur moyen pour une robustesse maximale (Moyenne + Normalisation L2)
        mean_embedding = np.mean(embeddings, axis=0)
        mean_embedding = mean_embedding / np.linalg.norm(mean_embedding)

        # Chemin vers le fichier .npz (compatible Docker ou local)
        npz_path = "/models/encodings_arcface.npz"
        if not os.path.exists(npz_path):
            npz_path = "../models/encodings_arcface.npz"

        # Chargement et mise à jour de la base de données vectorielle
        data = np.load(npz_path)
        existing_encodings = data["encodings"]
        existing_names = data["names"]

        updated_encodings = np.vstack([existing_encodings, mean_embedding])
        updated_names = np.append(existing_names, name)

        np.savez(npz_path, encodings=updated_encodings, names=updated_names)
        
        # Actualisation instantanée du moteur FAISS en mémoire
        engine.reload_encodings(npz_path)

        return {"status": "success", "message": f"Utilisateur {name} enrôlé avec succès ({len(embeddings)} captures validées) !"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/detect")
async def detect_faces(websocket: WebSocket):
    """Flux WebSocket pour le traitement vidéo en temps réel."""
    await websocket_endpoint(websocket)


@app.get("/register", response_class=HTMLResponse)
async def read_register(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")
