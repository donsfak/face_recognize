import base64
import time
import asyncio
import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from engine.recognition import FaceRecognitionEngine
from database.crud import log_attendance

# Instanciation globale du moteur IA (chargé une seule fois)
engine = FaceRecognitionEngine(gpu=False)

# Dictionnaire pour gérer le cooldown des pointages (évite le spam en BDD)
last_logged_times = {}
COOLDOWN_SECONDS = 10.0

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[INFO] Client WebSocket connecté pour l'analyse en direct.")
    
    try:
        while True:
            # Réception de la frame depuis le navigateur
            data = await websocket.receive_text()
            
            try:
                # 1. Validation et décodage sécurisés de l'image Base64
                if ',' not in data:
                    continue
                encoded_data = data.split(',')[1]
                nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue

                # 2. Analyse par le moteur IA
                results = engine.process_frame(frame)
                
                # 3. Gestion de l'enregistrement Supabase en arrière-plan (non bloquant)
                current_time = time.time()
                for res in results:
                    name = res["identity"]
                    sim = res["similarity"]
                    liveness = res["liveness"]
                    
                    if name not in ["Inconnu", "FRAUDE DETECTEE"]:
                        last_time = last_logged_times.get(name, 0.0)
                        if (current_time - last_time) >= COOLDOWN_SECONDS:
                            last_logged_times[name] = current_time
                            try:
                                await asyncio.to_thread(
                                    log_attendance, 
                                    user_name=name, 
                                    liveness_status=liveness, 
                                    confidence_score=sim
                                )
                                print(f"[DB] Pointage validé et enregistré pour : {name}")
                            except Exception as db_error:
                                print(f"[DB WARNING] Erreur Supabase ignorée : {db_error}")
                
                # 4. Envoi propre des résultats au Front-End
                await websocket.send_json({"faces": results})
                
            except Exception as frame_error:
                # Filet de sécurité : si une frame spécifique plante, on l'attrape 
                # MAIS on ne ferme pas le WebSocket ! Le flux vidéo continue.
                print(f"[WARNING] Erreur de traitement sur une frame (ignorée) : {frame_error}")
                await websocket.send_json({"faces": []})
                
    except WebSocketDisconnect:
        print("[INFO] Client déconnecté proprement.")
    except Exception as ws_error:
        print(f"[ERROR] Erreur critique WebSocket : {ws_error}")
