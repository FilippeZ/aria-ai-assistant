"""Face-tracking sign calibration for Reachy Mini (Mock Mode).
"""

import sys
import time
from pathlib import Path
import numpy as np
from rich.console import Console

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Config
from app.camera import Camera
from app.face_detector import FaceDetector

# --- MOCK CLASS ΓΙΑ ΠΑΡΑΚΑΜΨΗ ΤΟΥ SDK ---
class MockReachy:
    def set_target(self, head=None, antennas=None, body_yaw=0.0):
        pass # Mock κίνηση

def create_head_pose(yaw=0.0, pitch=0.0, degrees=True):
    return {'yaw': yaw, 'pitch': pitch}

console = Console()
_NEUTRAL_ANT = np.array([0.0, 0.0], dtype=np.float64)

def hold(reachy, yaw=0.0, pitch=0.0, secs=1.5, hz=100):
    pose = create_head_pose(yaw=yaw, pitch=pitch, degrees=True)
    t0 = time.monotonic()
    while time.monotonic() - t0 < secs:
        reachy.set_target(head=pose, antennas=_NEUTRAL_ANT, body_yaw=0.0)
        time.sleep(1.0 / hz)

def measure_face(cam, detector, samples=12):
    xs, ys, ws, hs = [], [], [], []
    for _ in range(samples):
        frame = cam.read_raw_live()
        if frame is not None:
            box = detector.detect(frame)
            if box is not None:
                x1, y1, x2, y2 = box
                xs.append((x1 + x2) / 2.0)
                ys.append((y1 + y2) / 2.0)
                hh, ww = frame.shape[:2]
                ws.append(ww); hs.append(hh)
        time.sleep(0.05)
    if not xs: return None
    return (np.median(xs), np.median(ys), np.median(ws), np.median(hs))

def main():
    config = Config.load()
    reachy = MockReachy() # Χρήση Mock
    
    cam = Camera(
        device=config.vision.camera_device,
        width=config.vision.width, height=config.vision.height,
        jpeg_quality=config.vision.jpeg_quality, capture_fps=config.vision.capture_fps,
    )
    if not cam.start():
        console.print("[red]Camera failed to start.[/red]")
        return
    detector = FaceDetector()
    if not detector.load():
        console.print("[red]Face detector failed to load.[/red]")
        cam.close(); return

    console.print("\n[bold cyan]Tracking sign calibration (Mocked)[/bold cyan]")
    console.print("Keep your face centered. Starting in 3s...\n")
    hold(reachy, secs=3.0)

    base = measure_face(cam, detector)
    if base is None:
        console.print("[red]No face detected.[/red]")
        cam.close(); return
    console.print(f"  baseline face: cx={base[0]:.0f}, cy={base[1]:.0f}")

    yaw_probe = 12.0
    hold(reachy, yaw=yaw_probe, secs=1.5)
    yaw_meas = measure_face(cam, detector)
    hold(reachy, secs=1.2)

    pitch_probe = 12.0
    hold(reachy, pitch=pitch_probe, secs=1.5)
    pitch_meas = measure_face(cam, detector)
    hold(reachy, secs=1.5)

    cam.close()

    console.print("\n[bold]Results[/bold]")
    if yaw_meas:
        dcx = yaw_meas[0] - base[0]
        yaw_sign = -1.0 if dcx > 0 else 1.0
        console.print(f"  => correct yaw control: delta_yaw = {yaw_sign:+.0f} * gain * err_x")
    
    if pitch_meas:
        dcy = pitch_meas[1] - base[1]
        pitch_sign = -1.0 if dcy > 0 else 1.0
        console.print(f"  => correct pitch control: delta_pitch = {pitch_sign:+.0f} * gain * err_y")

if __name__ == "__main__":
    main()
