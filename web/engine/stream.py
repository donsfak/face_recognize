import base64
import time
import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from engine.recognition import FaceRecognitionEngine
from database.crud import log_attendance

# Instanciation globale du moteur IA
engine = FaceRecognitionEngine(gpu=False)

# Dictionnaire pour gérer le cooldown des pointages (évite le spam en BDD)
last_logged_times = {}
COOLDOWN_SECONDS = 10.0

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[INFO] Client WebSocket connecté pour l'analyse en direct.")
    
    try:
        while True:
            data = await websocket.receive_text()
            encoded_data = data.split(',')[1]
            nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Analyse par le moteur IA
            results = engine.process_frame(frame)
            
            # Gestion de l'enregistrement Supabase
            current_time = time.time()
            for res in results:
                name = res["identity"]
                is_real = res["is_real"]
                sim = res["similarity"]
                liveness = res["liveness"]
                
                # On logue si c'est un vrai visage reconnu (hors Inconnu / Fraude, ou même les fraudes pour la sécurité !)
                if name not in ["Inconnu"]:
                    last_time = last_logged_times.get(name, 0.0)
                    if (current_time - last_time) >= COOLDOWN_SECONDS:
                        # Enregistrement en base de données
                        log_attendance(user_name=name, liveness_status=liveness, confidence_score=sim)
                        last_logged_times[name] = current_time
                        print(f"[DB] Pointage enregistré pour : {name} ({liveness})")
            
            await websocket.send_json({"faces": results})
            
    except WebSocketDisconnect:
        print("[INFO] WebSocket déconnecté.")
