const videoElement = document.getElementById('videoElement');
const overlayCanvas = document.getElementById('overlayCanvas');
const ctxOverlay = overlayCanvas.getContext('2d');
const statusText = document.getElementById('status');

const captureCanvas = document.createElement('canvas');
const ctxCapture = captureCanvas.getContext('2d');

// Connexion WebSocket vers FastAPI
const ws = new WebSocket(`ws://${window.location.host}/ws/detect`);

let waitingForResponse = false;

// 1. Allumage de la webcam depuis le flux de navigation
navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
    .then(stream => {
        videoElement.srcObject = stream;
        videoElement.play();
        statusText.innerText = "Caméra active. Connexion au serveur IA...";
    })
    .catch(err => {
        statusText.innerText = "Erreur webcam : " + err.message;
        console.error("Erreur d'accès à la caméra :", err);
    });

// 2. Gestion des événements WebSocket et traçage des erreurs
ws.onopen = () => {
    statusText.innerText = "IA connectée et active.";
    statusText.style.color = "green";
    sendNextFrame();
};

ws.onerror = (error) => {
    console.error("Erreur critique sur le WebSocket :", error);
    statusText.innerText = "Erreur de liaison réseau avec l'IA.";
    statusText.style.color = "red";
};

ws.onclose = (event) => {
    // Affiche le code exact de fermeture dans la console du navigateur (F12)
    console.warn(`WebSocket fermé. Code: ${event.code}, Raison: ${event.reason}`);
    statusText.innerText = `Déconnecté du serveur IA (Code: ${event.code}).`;
    statusText.style.color = "red";
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

        let color = "#00FF00";
        if (face.identity === "FRAUDE DETECTEE") {
            color = "#FF0000";
        } else if (face.identity === "Inconnu") {
            color = "#FFA500";
        } else if (!face.is_real) {
            color = "#FFFF00";
        }

        ctxOverlay.strokeStyle = color;
        ctxOverlay.lineWidth = 3;
        ctxOverlay.strokeRect(x1, y1, width, height);

        ctxOverlay.fillStyle = color;
        ctxOverlay.fillRect(x1, y2, width, 25);

        ctxOverlay.fillStyle = (color === "#FFFF00" || color === "#00FF00") ? "#000000" : "#FFFFFF";
        ctxOverlay.font = "16px Arial";
        ctxOverlay.fillText(`${face.identity} (${face.similarity.toFixed(2)})`, x1 + 5, y2 + 18);
        
        ctxOverlay.fillStyle = color;
        ctxOverlay.font = "bold 14px Arial";
        ctxOverlay.fillText(face.liveness, x1, y1 - 10);
    });
}
