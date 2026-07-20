import sys
import time
import cv2
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from app.face_recognition import FaceRecognizer

def main():
    print("=== Δοκιμή Αναγνώρισης Προσώπου ===")
    
    recognizer = FaceRecognizer()
    if recognizer.detector is None or recognizer.embedder is None:
        print("Σφάλμα φόρτωσης μοντέλων OpenCV.")
        sys.exit(1)
        
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Σφάλμα: Δεν βρέθηκε κάμερα.")
        sys.exit(1)

    print("\nΚοίταξε την κάμερα. Το σύστημα αναλύει...")
    time.sleep(2)  # Give camera time to warm up
    
    for i in range(5):
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            continue
            
        detected_names = recognizer.recognize_in_image(frame)
        
        if len(detected_names) == 0:
            print(f"[{i+1}/5] Δεν βρέθηκε πρόσωπο στην εικόνα.")
        else:
            names_str = ", ".join(detected_names)
            if "philip" in detected_names:
                print(f"[{i+1}/5] ✅ Αναγνωρίστηκε επιτυχώς: {names_str}")
            else:
                print(f"[{i+1}/5] 👤 Βρέθηκε πρόσωπο, αλλά δεν είναι ο Philip: {names_str}")
                
        time.sleep(0.5)
        
    cap.release()
    print("\nΟλοκληρώθηκε το τεστ.")

if __name__ == "__main__":
    main()
