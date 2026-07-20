#!/usr/import/env python3
import sys
import time
import cv2
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from app.face_recognition import FaceRecognizer

def main():
    if len(sys.argv) < 2:
        print("Usage: python enroll_face.py <name>")
        print("Example: python enroll_face.py philip")
        sys.exit(1)
        
    name = sys.argv[1].lower()
    print(f"=== Enroll Face: {name} ===")
    
    recognizer = FaceRecognizer()
    if recognizer.detector is None or recognizer.embedder is None:
        print("Σφάλμα φόρτωσης μοντέλων OpenCV. Βεβαιώσου ότι εκτέλεσες το script λήψης των μοντέλων.")
        sys.exit(1)
        
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Σφάλμα: Δεν βρέθηκε κάμερα.")
        sys.exit(1)

    print("\n[ΟΔΗΓΙΕΣ] Κοίταξε την κάμερα. Το σύστημα θα τραβήξει 15 φωτογραφίες.")
    print("Θα ξεκινήσει σε 3 δευτερόλεπτα...")
    time.sleep(3)
    
    embeddings = []
    required_shots = 15
    
    while len(embeddings) < required_shots:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
            
        faces = recognizer.detect_faces(frame)
        if len(faces) == 0:
            print("Δεν βρέθηκε πρόσωπο. Κοίταξε την κάμερα...", end="\r")
            time.sleep(0.5)
            continue
            
        if len(faces) > 1:
            print("Προσοχή: Βρέθηκαν παραπάνω από 1 πρόσωπα. Παρακαλώ να είσαι μόνο εσύ στο πλάνο.")
            time.sleep(0.5)
            continue
            
        (startX, startY, endX, endY) = faces[0]
        face_roi = frame[startY:endY, startX:endX]
        emb = recognizer.get_embedding(face_roi)
        
        if emb is not None:
            embeddings.append(emb)
            print(f"✓ Φωτογραφία {len(embeddings)}/{required_shots} λήφθηκε επιτυχώς!")
            time.sleep(0.2)  # Μικρή παύση για να πάρει διαφορετικές γωνίες
            
    cap.release()
    
    if len(embeddings) == required_shots:
        print("\nΟλοκληρώθηκε η λήψη! Εκπαίδευση μοντέλου...")
        # Average the embeddings for a robust reference
        avg_embedding = np.mean(embeddings, axis=0)
        recognizer.save_known_face(name, avg_embedding)
        print(f"✅ Επιτυχία! Το σύστημα πλέον αναγνωρίζει τον '{name}'.")
    else:
        print("\n❌ Η διαδικασία ακυρώθηκε.")

if __name__ == "__main__":
    main()
