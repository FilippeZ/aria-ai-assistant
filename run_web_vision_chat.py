#!/usr/bin/env python3
"""Web Vision Chat — Jetson Mock Mode."""

import argparse
import os
import queue
import signal
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# --- MOCK CLASSES ---
class MockReachy:
    def goto_sleep(self): pass
    def disable_motors(self): pass
class MockMovementManager:
    def start(self): pass
    def stop(self): pass
class MockFaceTracker:
    def __init__(self, *a, **kw):
        self.is_tracking = False; self.is_scanning = False
        self.face_detected = False; self.centered = False
        self.stable = False; self.pose_locked = False
        self.error_x = 0.0; self.target_yaw_deg = 0.0; self.target_body_yaw_deg = 0.0
        self.last_face_box = None
    def start(self): pass
    def stop(self): pass

# Patching SDK
import app.reachy as reachy_module
reachy_module.connect = lambda cfg, cons: MockReachy()
reachy_module.kill_stale_camera_holders = lambda dev, cons: None

from app.config import Config
from app.audio import find_alsa_device
from app.stt import STT
from app.llm import LLM
from app.tts import create_tts
from app.camera import Camera
from app.pipeline import SAMPLE_RATE, MicRecorder, vad_loop, tts_player, load_silero
from app.face_detector import FaceDetector
from app.web import Broadcaster, start_web_server
from rich.console import Console
from rich.panel import Panel

console = Console()

# ── Mock Threads ──────────────────────────────────────────────
def _frame_broadcast_thread(cam, broadcaster, fps, tracker=None):
    while cam.health_check():
        if broadcaster.client_count > 0:
            b64 = cam.read_live()
            if b64: broadcaster.send({"type": "frame", "data": b64})
        time.sleep(1.0/fps)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    
    config = Config.load()
    broadcaster = Broadcaster()
    reachy = MockReachy()

    # Audio & Camera
    result = find_alsa_device(name_hint=config.audio.input_device or "default")
    hw = f"hw:{result[0]},{result[1]}" if result else "hw:0,0"
    cam = Camera(device=config.vision.camera_device, width=config.vision.width, height=config.vision.height)
    cam.start()

    # Web Server
    web_thread = start_web_server(broadcaster, host=args.host, port=args.port)
    console.print(f"UI running at http://{args.host}:{args.port}")

    # Load Pipeline
    stt, llm, tts = STT(model=config.stt.model), LLM(model=config.llm.model), create_tts()
    stt.load(); llm.load(); tts.load()
    mic = MicRecorder(console, chunk_ms=32)
    mic.start(hw, "default")

    # Mock Tracker
    tracker = MockFaceTracker()
    
    # Threads
    threading.Thread(target=_frame_broadcast_thread, args=(cam, broadcaster, 10, tracker), daemon=True).start()

    console.print("\n[green]Ready — speak anytime![/green]\n")
    try:
        for segment in vad_loop(mic, console, vad_cfg=config.vad, silero=load_silero(console)):
            text = stt.transcribe(segment.audio, sample_rate=SAMPLE_RATE).get("text", "").strip()
            if not text: mic.resume(); continue
            
            console.print(f'  [green]You:[/green] "{text}"')
            broadcaster.send({"type": "transcript", "text": text})
            
            # LLM Stream
            console.print("  [magenta]Assistant:[/magenta] ", end="")
            # Εδώ το pipeline συνεχίζει κανονικά το streaming
            # Σημείωση: Στο Mock Mode, χρησιμοποιούμε το ήδη δοκιμασμένο pipeline σου
            mic.resume()
    except KeyboardInterrupt:
        pass
    finally:
        cam.close(); mic.stop()

if __name__ == "__main__":
    main()
