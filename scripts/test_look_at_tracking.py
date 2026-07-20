import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import Config
from app.camera import Camera
from app.face_detector import FaceDetector
from rich.console import Console

# --- MOCK CLASSES ΓΙΑ ΠΑΡΑΚΑΜΨΗ ΤΟΥ SDK ---
class MockReachy:
    pass

class MockMovementManager:
    def start(self): pass
    def stop(self): pass
    _c_body = 0.0

class MockFaceTracker:
    def __init__(self, *a, **kw):
        self.last_face_box = None
        self.face_detected = False
        self.centered = False
        self.stable = False
        self._body = 0.0
        self._pitch = 0.0
    def start(self): pass
    def stop(self): pass

OUT = open("/tmp/lookat_stats.txt", "w")
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    try: OUT.write(s + "\n"); OUT.flush()
    except Exception: pass

cfg = Config.load(); console = Console()
# Χρήση Mock Objects
reachy = MockReachy()
log("SDK bypassed: Using Mock interfaces")

cam = Camera(device=cfg.vision.camera_device, width=cfg.vision.width, height=cfg.vision.height,
             jpeg_quality=cfg.vision.jpeg_quality, capture_fps=cfg.vision.capture_fps)
cam.start()
det = FaceDetector(); det.load()
time.sleep(1.0)

mgr = MockMovementManager(); mgr.start()
trk = MockFaceTracker(cam, det, mgr, reachy)
trk.start()

log("INSTRUMENTED tracking (Mock Mode).")
log("Columns: t det centered stable err_x err_y -> body_target pitch_target | current_body")

t0 = time.time()
while time.time() - t0 < 30.0:
    box = trk.last_face_box
    det_f = trk.face_detected
    cen = trk.centered
    stable = trk.stable
    body_t = trk._body
    pitch_t = trk._pitch
    cur_body = mgr._c_body
    
    if box is not None:
        f = cam.read_raw_live()
        if f is not None:
            h, w = f.shape[:2]
            cx = (box[0] + box[2]) / 2; cy = (box[1] + box[3]) / 2
            ex = (cx - w/2)/(w/2); ey = (cy - h/2)/(h/2)
            log(f"t={time.time()-t0:4.1f} det={det_f} cen={cen} stable={stable} err_x={ex:+.2f} err_y={ey:+.2f} "
                f"-> body={body_t:+6.1f} pitch={pitch_t:+5.1f} | cur_body={cur_body:+6.1f}")
    else:
        log(f"t={time.time()-t0:4.1f} det=False (no face)         "
            f"-> body={body_t:+6.1f} pitch={pitch_t:+5.1f} | cur_body={cur_body:+6.1f}")
    time.sleep(0.4)

log("resetting + stopping")
trk.stop(); time.sleep(1.0); mgr.stop(); cam.close()
try: OUT.close()
except Exception: pass
print("DONE")
