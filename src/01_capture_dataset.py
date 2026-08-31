"""
Étape 2 — Capture du dataset via webcam.

Ce script ouvre la webcam et enregistre des photos du visage d'une personne
dans dataset/<nom_personne>/. On ne fait volontairement AUCUN traitement
(pas de détection, pas de crop) ici : on garde les images brutes, c'est
l'étape suivante (encodage) qui s'occupera de localiser le visage dedans.

Usage :
    python 01_capture_dataset.py --name cedric --count 20
"""

import argparse
import os
import time
import cv2


def parse_args():
    parser = argparse.ArgumentParser(description="Capture d'un dataset de visages via webcam")
    parser.add_argument("--name", required=True, help="Nom de la personne (utilisé comme nom de dossier)")
    parser.add_argument("--count", type=int, default=20, help="Nombre de photos à capturer")
    parser.add_argument("--dataset_dir", default="../dataset", help="Dossier racine du dataset")
    parser.add_argument("--interval", type=float, default=0.6, help="Secondes entre deux captures automatiques")
    return parser.parse_args()


def main():
    args = parse_args()

    person_dir = os.path.join(args.dataset_dir, args.name)
    os.makedirs(person_dir, exist_ok=True)

    existing = [f for f in os.listdir(person_dir) if f.endswith(".jpg")]
    start_index = len(existing)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Impossible d'ouvrir la webcam (index 0). Vérifiez qu'aucune autre appli ne l'utilise.")

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    print(f"[INFO] Capture pour '{args.name}'. Objectif : {args.count} photos.")
    print("[INFO] Bougez légèrement la tête (face, 3/4 gauche, 3/4 droite, sourire/neutre) entre les prises.")
    print("[INFO] Appuyez sur 'q' pour arrêter avant la fin. Appuyez sur ESPACE pour forcer une capture immédiate.")

    captured = 0
    last_capture_time = 0

    while captured < args.count:
        ret, frame = cap.read()
        if not ret:
            print("[ERREUR] Lecture webcam échouée.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

        display = frame.copy()
        for (x, y, w, h) in faces:
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(display, f"{args.name}: {captured}/{args.count}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Capture dataset - appuyez sur 'q' pour quitter", display)

        key = cv2.waitKey(1) & 0xFF
        now = time.time()

        should_capture = (
            len(faces) > 0
            and (now - last_capture_time) >= args.interval
        ) or key == ord(" ")

        if should_capture and len(faces) > 0:
            filename = os.path.join(person_dir, f"{args.name}_{start_index + captured:03d}.jpg")
            cv2.imwrite(filename, frame)
            captured += 1
            last_capture_time = now
            print(f"[CAPTURE] {filename}")

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"[TERMINÉ] {captured} photos enregistrées dans {person_dir}")


if __name__ == "__main__":
    main()
