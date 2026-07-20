#!/usr/bin/env python3
"""Vision Chat — Optimized for Jetson (Mock SDK Mode)."""

import os
import signal
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# --- MOCK CLASSES ΓΙΑ ΠΑΡΑΚΑΜΨΗ ΤΟΥ SDK ---
class MockReachy:
    def goto_sleep(self): pass
    def disable_motors(self): pass
class MockMovementManager:
    def start(self): pass
    def stop(self): pass
class MockFaceTracker:
    def start(self): pass
    def stop(self): pass

# Patching για να μην σκάει το import
import app.reachy as reachy_module
reachy_module.connect = lambda cfg, cons: MockReachy()
reachy_module.kill_stale_camera_holders = lambda dev, cons: None

from app.config import Config
from app.audio import find_alsa_device
from app.stt import STT
from app.llm import LLM
from app.tts import create_tts
from app.camera import Camera
from app.pipeline import (
    SAMPLE_RATE, MicRecorder, warmup_stt, vad_loop, stream_and_speak, load_silero,
)
from app.face_detector import FaceDetector
# Εδώ χρησιμοποιούμε τα Mocks που ορίσαμε
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    config = Config.load()
    console.print(Panel.fit("[bold cyan]Vision Chat (Mock Mode)[/bold cyan]"))

    reachy = MockReachy() # Χρήση Mock

    # ── Audio setup ──────────
    result = find_alsa_device(name_hint=config.audio.input_device or "default")
    if not result:
        console.print("[red]No mic found![/red]"); return
    card, dev, mic_name = result
    hw = f"hw:{card},{dev}"

    # ── Camera setup ─────────
    cam = Camera(device=config.vision.camera_device, width=config.vision.width,
                 height=config.vision.height, jpeg_quality=config.vision.jpeg_quality,
                 capture_fps=config.vision.capture_fps)
    if cam.start(): console.print("  ✓ Camera active")
    else: console.print("[red]  ✗ Camera failed[/red]"); return

    # ── Cleanup ──────────────
    def _do_cleanup():
        console.print("\n[yellow]Shutting down...[/yellow]")
        cam.close()
        reachy.goto_sleep()
        reachy.disable_motors()

    signal.signal(signal.SIGINT, lambda s, f: _do_cleanup() or sys.exit(0))

    # ── Load models ──────────
    stt = STT(model=config.stt.model, device=config.stt.device)
    stt.load()
    silero_model = load_silero(console)
    llm = LLM(model=config.llm.model, base_url=config.llm.base_url, system_prompt=config.vision.system_prompt)
    llm.load()
    tts = create_tts(voice=config.tts.voice)
    tts = tts if tts.load() else None

    # ── Mock Face Tracking ──
    face_detector = FaceDetector()
    movement_manager = MockMovementManager()
    face_tracker = MockFaceTracker()

    # ── Main loop ────────────
    mic = MicRecorder(console, chunk_ms=32)
    mic.start(hw, config.audio.input_device or "default")
    
    console.print("\n[green bold]Ready — speak anytime![/green bold]\n")

    try:
        for segment in vad_loop(mic, console, vad_cfg=config.vad, silero=silero_model):
            result = stt.transcribe(segment.audio, sample_rate=SAMPLE_RATE)
            text = result.get("text", "").strip()
            
            if not text:
                mic.resume(); continue

            console.print(f'  [green]You:[/green] "{text}"')
            
            # Mock capture_frames_for_vlm (δεν χρειάζεται tracking για να στείλει frame)
            captured_frames = [cam.read_raw_live()] 
            
            console.print("  [magenta]Assistant:[/magenta] ", end="")
            stream_and_speak(llm, tts, text, config.vision.system_prompt, mic.pa_sink, 
                             images_b64=captured_frames)
            mic.resume()
    except KeyboardInterrupt:
        _do_cleanup()

if __name__ == "__main__":
    main()
