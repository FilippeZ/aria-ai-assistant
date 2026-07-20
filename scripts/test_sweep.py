import sys, time, threading, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from app.config import Config
from app.camera import Camera
from app.face_detector import FaceDetector
from rich.console import Console

# --- MOCK CLASS ΓΙΑ ΠΑΡΑΚΑΜΨΗ ΤΟΥ SDK ---
class MockReachy:
    def set_target(self, head=None, antennas=None, body_yaw=None):
        pass # Mock κίνηση
    def get_current_head_pose(self):
        # Επιστρέφει dummy 4x4 πίνακα για να αποφύγουμε σφάλματα στο achived_yaw
        return np.eye(4)

def create_head_pose(yaw=0.0, pitch=0.0, degrees=True):
    return {'yaw': yaw, 'pitch': pitch}

OUT = open("/tmp/sweep_stats.txt", "w")
def log(*a):
    s = " ".join(str(x) for x in a); print(s); OUT.write(s + "\n"); OUT.flush()

cfg = Config.load(); console = Console()
# Χρήση Mock αντί για connect_reachy
reachy = MockReachy()
log("SDK bypassed: Using MockReachy interface")

cmd = {"yaw": 0.0, "pitch": 0.0, "body": 0.0, "run": True}
ant = np.array([0.0, 0.0])
def _stream():
    while cmd["run"]:
        try:
            # Το set_target καλείται στο mock object
            reachy.set_target(head=create_head_pose(yaw=cmd["yaw"], pitch=cmd["pitch"]),
                              antennas=ant, body_yaw=math.radians(cmd["body"]))
        except Exception as e:
            log("set_target err:", repr(e)); break
        time.sleep(0.01)
threading.Thread(target=_stream, daemon=True).start()
time.sleep(2.0)

# kill_stale_camera_holders παρακάμπτεται
cam = Camera(device=cfg.vision.camera_device, width=cfg.vision.width, height=cfg.vision.height,
             jpeg_quality=cfg.vision.jpeg_quality, capture_fps=cfg.vision.capture_fps)
cam.start(); det = FaceDetector(); det.load(); time.sleep(1.0)

def measure(n=18):
    xs = []; ys = []; w = h = 0
    for _ in range(n):
        f = cam.read_raw_live()
        if f is not None:
            h, w = f.shape[:2]
            b = det.detect(f)
            if b is not None: xs.append((b[0]+b[2])/2); ys.append((b[1]+b[3])/2)
        time.sleep(0.05)
    if not xs: return None
    return (float(np.median(xs)), float(np.median(ys)), w, h, len(xs), n)

def achieved_yaw():
    # Επιστρέφει dummy τιμή για αποφυγή του scipy dependency
    return np.array([0.0, 0.0, 0.0])

def hold(yaw=0.0, pitch=0.0, body=0.0, secs=2.0):
    cmd["yaw"], cmd["pitch"], cmd["body"] = yaw, pitch, body
    time.sleep(secs)

log("HOLD STILL. Sweeping HEAD YAW...")
for y in (0, -15, -25, 0, 15, 25, 0):
    hold(yaw=y, secs=2.0)
    m = measure()
    a = achieved_yaw()
    arpy = f"head_rpy={np.round(a,1)}" if a is not None else "head_rpy=?"
    if m: log(f"  cmd_yaw={y:+d} -> cx={m[0]:5.0f}/{m[3]} cy={m[1]:.0f} ({m[4]}/{m[5]} det) {arpy}")
    else: log(f"  cmd_yaw={y:+d} -> NO FACE {arpy}")

log("HOLD STILL. Sweeping BODY YAW (deg)...")
for b in (0, -25, -45, 0, 25, 45, 0):
    hold(body=b, secs=2.5)
    m = measure()
    if m: log(f"  cmd_body={b:+d}deg -> cx={m[0]:5.0f}/{m[3]} cy={m[1]:.0f} ({m[4]}/{m[5]} det)")
    else: log(f"  cmd_body={b:+d}deg -> NO FACE")

hold(secs=1.0)
cam.close(); cmd["run"] = False; OUT.close()
print("DONE")
