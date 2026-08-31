const videoElement = document.getElementById('videoElement');
const overlayCanvas = document.getElementById('overlayCanvas');
const ctxOverlay = overlayCanvas.getContext('2d');
const statusText = document.getElementById('status');

const captureCanvas = document.createElement('canvas');
const ctxCapture = captureCanvas.getContext('2d');

// Palette FaceGuard (dupliquée ici car un <canvas> ne peut pas lire les variables CSS)
const COLOR_ACCENT = "#2DD4BF";   // identité reconnue, visage réel
const COLOR_WARN = "#F59E0B";     // visage détecté mais Inconnu
const COLOR_DANGER = "#EF4444";   // fraude détectée (anti-spoofing)
const COLOR_ANALYSIS = "#60A5FA"; // vivacité en cours d'analyse (pas encore tranché)
const COLOR_KEYPOINT = "#5EEAD4"; // points clés du visage (yeux, nez, bouche)

// Connexion WebSocket vers FastAPI
const ws = new WebSocket(`ws://${window.location.host}/ws/detect`);

let waitingForResponse = false;
let cameraReady = false;
let wsOpen = false;

// Centralise l'affichage du statut pour éviter que la résolution de la caméra
// et l'ouverture du WebSocket ne s'écrasent mutuellement selon leur ordre d'arrivée.
function updateStatus() {
    if (wsOpen) {
        statusText.innerText = "IA connectée et active.";
        statusText.style.color = COLOR_ACCENT;
    } else if (cameraReady) {
        statusText.innerText = "Caméra active. Connexion au serveur IA...";
        statusText.style.color = COLOR_ANALYSIS;
    } else {
        statusText.innerText = "Initialisation de la caméra...";
        statusText.style.color = COLOR_ANALYSIS;
    }
}

// 1. Allumage de la webcam depuis le flux de navigation
navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
    .then(stream => {
        videoElement.srcObject = stream;
        videoElement.play();
        cameraReady = true;
        updateStatus();
    })
    .catch(err => {
        statusText.innerText = "Erreur webcam : " + err.message;
        statusText.style.color = COLOR_DANGER;
        console.error("Erreur d'accès à la caméra :", err);
    });

// 2. Gestion des événements WebSocket et traçage des erreurs
ws.onopen = () => {
    wsOpen = true;
    updateStatus();
    sendNextFrame();
};

ws.onerror = (error) => {
    console.error("Erreur critique sur le WebSocket :", error);
    statusText.innerText = "Erreur de liaison réseau avec l'IA.";
    statusText.style.color = COLOR_DANGER;
};

ws.onclose = (event) => {
    console.warn(`WebSocket fermé. Code: ${event.code}, Raison: ${event.reason}`);
    wsOpen = false;
    statusText.innerText = `Déconnecté du serveur IA (Code: ${event.code}).`;
    statusText.style.color = COLOR_DANGER;
};

ws.onmessage = (event) => {
    try {
        const response = JSON.parse(event.data);
        drawBoundingBoxes(response.faces);

        waitingForResponse = false;
        setTimeout(sendNextFrame, 100);
    } catch (parseError) {
        console.error("Erreur de décodage JSON de la réponse IA :", parseError);
        waitingForResponse = false;
    }
};

function sendNextFrame() {
    if (ws.readyState === WebSocket.OPEN && !waitingForResponse && videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
        waitingForResponse = true;

        captureCanvas.width = videoElement.videoWidth;
        captureCanvas.height = videoElement.videoHeight;
        ctxCapture.drawImage(videoElement, 0, 0, captureCanvas.width, captureCanvas.height);

        const dataURL = captureCanvas.toDataURL('image/jpeg', 0.6);
        ws.send(dataURL);
    } else {
        setTimeout(sendNextFrame, 200);
    }
}

function drawBoundingBoxes(faces) {
    ctxOverlay.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

    if (!faces) return;

    faces.forEach(face => {
        const [x1, y1, x2, y2] = face.box;
        const width = x2 - x1;
        const height = y2 - y1;

        // --- Choix de couleur selon le statut (identité + vivacité) ---
        let color = COLOR_ACCENT;
        if (face.identity === "FRAUDE DETECTEE") {
            color = COLOR_DANGER;
        } else if (face.identity === "Inconnu") {
            color = COLOR_WARN;
        } else if (!face.is_real) {
            color = COLOR_ANALYSIS;
        }

        // --- Cadre de détection ---
        ctxOverlay.strokeStyle = color;
        ctxOverlay.lineWidth = 3;
        ctxOverlay.strokeRect(x1, y1, width, height);

        // --- Étiquette identité + score ---
        ctxOverlay.fillStyle = color;
        ctxOverlay.fillRect(x1, y2, width, 25);

        const textColor = (color === COLOR_DANGER) ? "#FFFFFF" : "#06251F";
        ctxOverlay.fillStyle = textColor;
        ctxOverlay.font = "16px 'Inter', Arial, sans-serif";
        ctxOverlay.fillText(`${face.identity} (${face.similarity.toFixed(2)})`, x1 + 5, y2 + 18);

        // --- Statut de vivacité au-dessus du cadre ---
        ctxOverlay.fillStyle = color;
        ctxOverlay.font = "bold 14px 'JetBrains Mono', monospace";
        ctxOverlay.fillText(face.liveness, x1, y1 - 10);

        // --- Points clés du visage (yeux, nez, coins de bouche) ---
        // Nécessite que le backend inclue "kps" dans la réponse JSON par visage
        // (liste de 5 paires [x, y]). Si absent, ce bloc ne dessine simplement rien.
        if (face.kps && Array.isArray(face.kps)) {
            face.kps.forEach(([kx, ky]) => {
                ctxOverlay.beginPath();
                ctxOverlay.arc(kx, ky, 3, 0, 2 * Math.PI);
                ctxOverlay.fillStyle = COLOR_KEYPOINT;
                ctxOverlay.fill();
                ctxOverlay.lineWidth = 1;
                ctxOverlay.strokeStyle = "#06251F";
                ctxOverlay.stroke();
            });
        }
    });
}
