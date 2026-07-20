import os
import sys
import cv2
import numpy as np
from pathlib import Path
import urllib.request

MODELS_DIR = Path(__file__).resolve().parent.parent / "models" / "face"
FACES_DIR = Path(__file__).resolve().parent.parent / "faces"

YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"

def download_yunet(path: Path):
    if path.exists():
        return
    print(f"Downloading YuNet model to {path}...")
    path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(YUNET_URL, str(path))
    print("Download complete.")

class FaceRecognizer:
    def __init__(self, threshold=0.65):
        self.threshold = threshold
        self.known_faces = {}
        
        # Paths to OpenCV DNN models
        model_path = str(MODELS_DIR / "face_detection_yunet_2023mar.onnx")
        embedder_path = str(MODELS_DIR / "openface_nn4.small2.v1.t7")
        
        download_yunet(Path(model_path))
        
        # Load models
        try:
            self.detector = cv2.FaceDetectorYN.create(
                model_path, "", (320, 320),
                score_threshold=0.6, nms_threshold=0.3, top_k=5000
            )
            self.embedder = cv2.dnn.readNet(embedder_path)
            print("  ✓ Face models loaded (YuNet + OpenFace)")
        except Exception as e:
            print(f"Error loading face models: {e}")
            self.detector = None
            self.embedder = None
            
        self.load_known_faces()

    def load_known_faces(self):
        """Loads reference embeddings from the faces/ directory."""
        if not FACES_DIR.exists():
            FACES_DIR.mkdir(parents=True, exist_ok=True)
            return

        self.known_faces.clear()
        for filepath in FACES_DIR.glob("*.npy"):
            name = filepath.stem
            embedding = np.load(str(filepath))
            self.known_faces[name] = embedding
            print(f"  ✓ Loaded known face: {name}")

    def save_known_face(self, name: str, embedding: np.ndarray):
        """Saves a reference embedding."""
        if not FACES_DIR.exists():
            FACES_DIR.mkdir(parents=True, exist_ok=True)
        path = FACES_DIR / f"{name}.npy"
        np.save(str(path), embedding)
        self.known_faces[name] = embedding

    def detect_faces(self, image, conf_threshold=0.6):
        """Detect faces in an image using YuNet."""
        if self.detector is None or image is None:
            return []
            
        h, w = image.shape[:2]
        self.detector.setInputSize((w, h))
        
        _, faces = self.detector.detect(image)
        
        boxes = []
        if faces is not None:
            for face in faces:
                box = face[:4].astype(int)
                conf = face[-1]
                if conf > conf_threshold:
                    startX, startY, width, height = box
                    endX = startX + width
                    endY = startY + height
                    
                    startX = max(0, startX)
                    startY = max(0, startY)
                    endX = min(w - 1, endX)
                    endY = min(h - 1, endY)
                    
                    if endX - startX > 20 and endY - startY > 20:
                        boxes.append((startX, startY, endX, endY))
        return boxes

    def get_embedding(self, face_image):
        """Extract 128D embedding from a cropped face image."""
        if self.embedder is None or face_image is None or face_image.size == 0:
            return None
            
        faceBlob = cv2.dnn.blobFromImage(face_image, 1.0 / 255, (96, 96),
                                         (0, 0, 0), swapRB=True, crop=False)
        self.embedder.setInput(faceBlob)
        vec = self.embedder.forward()
        return vec.flatten()

    def identify(self, embedding):
        """Compare embedding to known faces."""
        best_name = "Unknown"
        best_dist = float('inf')
        
        for name, known_emb in self.known_faces.items():
            dist = np.linalg.norm(known_emb - embedding)
            if dist < best_dist:
                best_dist = dist
                best_name = name
                
        if best_dist <= self.threshold:
            # Convert distance to confidence percentage (heuristic mapping)
            # Distance 0 -> 100%, threshold -> approx 50-60%
            confidence = max(0.0, min(100.0, (1.0 - (best_dist / 1.5)) * 100.0))
            return best_name, best_dist, confidence
        return "Unknown", best_dist, 0.0

    def recognize_in_image(self, image):
        """Finds faces and identifies them. Returns list of tuples: (name, confidence)."""
        detected = {}
        faces = self.detect_faces(image)
        for (startX, startY, endX, endY) in faces:
            face_roi = image[startY:endY, startX:endX]
            embedding = self.get_embedding(face_roi)
            if embedding is not None:
                name, dist, conf = self.identify(embedding)
                if name != "Unknown":
                    if name not in detected or conf > detected[name]:
                        detected[name] = conf
        return list(detected.items())
