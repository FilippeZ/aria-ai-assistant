import sys, time, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import cv2
from app.config import Config
from app.camera import Camera
from app.face_detector import FaceDetector
from rich.console import Console

# --- MOCK CLASS ΓΙΑ ΠΑΡΑΚΑΜΨΗ ΤΟΥ SDK ---
class MockReachy:
    def set_target(self, head=None, antennas=None, body_yaw=None):
        pass # Mock κίνηση

OUT = open("/tmp/detect_stats.txt", "w")
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s); OUT.write(s + "\n"); OUT.flush()

console = Console()
cfg = Config.load()

# Χρήση του Mock interface αντί για σύνδεση στο SDK
reachy = MockReachy()
log("SDK bypassed: Using MockReachy interface")

hold = {"run": True}
# Ο κώδικας του stream τρέχει πλέον κανονικά με το mock object
def _stream():
    while hold["run"]:
        try: reachy.set_target()
        except Exception: pass
        time.sleep(0.01)
threading.Thread(target=_stream, daemon=True).start()
time.sleep(2.0)
log("system ready (mock mode), head neutral")

# Αφαίρεση του kill_stale_camera_holders που εξαρτάται από το SDK
cam = Camera(device=cfg.vision.camera_device, width=cfg.vision.width,
             height=cfg.vision.height, jpeg_quality=cfg.vision.jpeg_quality,
             capture_fps=cfg.vision.capture_fps)
cam.start()
det = FaceDetector(); det.load()
time.sleep(1.0)

log("Sampling 60 frames (~9s). Face the robot...")
N = 60; hits = 0; seq = ""; brights = []; boxes = []
fw = fh = 0
for i in range(N):
    frame = cam.read_raw_live()
    if frame is None:
        seq += "_"; time.sleep(0.15); continue
    fh, fw = frame.shape[:2]
    brights.append(frame.mean())
    box = det.detect(frame)
    if box is not None:
        hits += 1; seq += "#"
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        boxes.append((cx,cy,box[2]-box[0]))
    else:
        seq += "."
    time.sleep(0.15)

log(f"FRAME {fw}x{fh}  mean_brightness={np.mean(brights):.0f}")
log(f"detected {100*hits/N:.0f}% ({hits}/{N})")
log("timeline (#=face, .=none):", seq)
if boxes:
    cxs=[b[0] for b in boxes]; cys=[b[1] for b in boxes]; ws=[b[2] for b in boxes]
    log(f"face cx range [{min(cxs)}-{max(cxs)}] of {fw}, cy [{min(cys)}-{max(cys)}] of {fh}, facew~{sum(ws)//len(ws)}")
cam.close()
hold["run"] = False
OUT.close()
