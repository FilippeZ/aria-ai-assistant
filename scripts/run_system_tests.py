import sys
import time
import base64
import numpy as np
import cv2
from pathlib import Path
from rich.console import Console

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Config
from app.stt import STT
from app.llm import LLM
from app.tts import create_tts
from app.face_recognition import FaceRecognizer

console = Console()

def run_tests():
    config = Config.load()
    console.print("\n[bold cyan]🚀 Starting System Integration Tests (5 Use Cases)[/bold cyan]")
    
    # ── Use Case 1: STT ──────────────────────────────────────────────────
    console.print("\n[bold yellow]--- Use Case 1: Speech-To-Text (STT) ---[/bold yellow]")
    try:
        stt = STT(
            model=config.stt.model,
            device=config.stt.device,
            compute_type=config.stt.compute_type,
            language=config.stt.language or "el",
            beam_size=config.stt.beam_size,
        )
        stt.load()
        console.print("✓ STT model loaded successfully.")
        
        # Use a synthetic audio array (1 second of silence) to test processing
        dummy_audio = np.zeros(16000, dtype=np.float32)
        result = stt.transcribe(dummy_audio, sample_rate=16000)
        text = result.get("text", "").strip()
        console.print(f"✓ STT Transcription processed dummy audio. Text: '{text}'")
        
        # Free memory
        stt.unload()
        console.print("✓ STT memory freed.")
    except Exception as e:
        console.print(f"[red]❌ STT Test Failed: {e}[/red]")
        
    # ── Use Case 2: LLM Text Generation ──────────────────────────────────
    console.print("\n[bold yellow]--- Use Case 2: LLM Text Generation ---[/bold yellow]")
    try:
        llm = LLM(
            model=config.llm.model,
            base_url=config.llm.base_url,
            backend=config.llm.backend,
        )
        llm.load()
        console.print("✓ LLM model loaded successfully.")
        
        prompt = "Πες μου ένα γρήγορο γεια."
        response_chunks = []
        start_time = time.time()
        for chunk_data in llm.generate_stream(prompt, system_prompt="You are a helpful assistant.", max_tokens=20):
            chunk, meta = chunk_data if isinstance(chunk_data, tuple) else (chunk_data, {})
            if chunk:
                response_chunks.append(chunk)
        elapsed = time.time() - start_time
        full_response = "".join(response_chunks).strip()
        console.print(f"✓ LLM Response: '{full_response}' (took {elapsed:.2f}s)")
    except Exception as e:
        console.print(f"[red]❌ LLM Test Failed: {e}[/red]")

    # ── Use Case 3: VLM Vision Analysis ──────────────────────────────────
    console.print("\n[bold yellow]--- Use Case 3: VLM Vision Analysis ---[/bold yellow]")
    try:
        # Create a dummy image
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', dummy_img)
        dummy_b64 = base64.b64encode(buffer).decode('utf-8')
        
        prompt = "Describe this image in 5 words."
        response_chunks = []
        for chunk_data in llm.generate_stream(prompt, system_prompt="You are a helpful assistant.", images_b64=[dummy_b64], max_tokens=15):
            chunk, meta = chunk_data if isinstance(chunk_data, tuple) else (chunk_data, {})
            if chunk:
                response_chunks.append(chunk)
        full_response = "".join(response_chunks).strip()
        console.print(f"✓ VLM Response to dummy image: '{full_response}'")
    except Exception as e:
        console.print(f"[red]❌ VLM Test Failed: {e}[/red]")

    # ── Use Case 4: TTS Generation ───────────────────────────────────────
    console.print("\n[bold yellow]--- Use Case 4: Text-To-Speech (TTS) ---[/bold yellow]")
    try:
        tts = create_tts(voice=config.tts.voice, speed=config.tts.speed, lang=config.tts.lang)
        if tts.load():
            console.print("✓ TTS model loaded successfully.")
            r = tts.synthesize("Αυτή είναι μια δοκιμή.")
            if r and r.get("audio") is not None:
                audio_len = len(r["audio"])
                console.print(f"✓ TTS generated audio array of size: {audio_len}")
            else:
                console.print("[red]❌ TTS returned no audio data.[/red]")
            
            # Free memory
            tts.unload()
            console.print("✓ TTS memory freed.")
        else:
            console.print("[red]❌ TTS could not be loaded.[/red]")
    except Exception as e:
        console.print(f"[red]❌ TTS Test Failed: {e}[/red]")

    # ── Use Case 5: Face Recognition ─────────────────────────────────────
    console.print("\n[bold yellow]--- Use Case 5: Face Recognition ---[/bold yellow]")
    try:
        face_recognizer = FaceRecognizer()
        console.print("✓ Face recognition initialized successfully.")
        
        # Test on dummy frame (should return no faces but shouldn't crash)
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detected = face_recognizer.recognize_in_image(dummy_frame)
        console.print(f"✓ Face recognition processed dummy frame. Detected: {detected}")
    except Exception as e:
        console.print(f"[red]❌ Face Recognition Test Failed: {e}[/red]")

    console.print("\n[bold green]✅ System Integration Tests Complete.[/bold green]")

if __name__ == "__main__":
    run_tests()
