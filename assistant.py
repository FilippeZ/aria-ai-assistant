#!/usr/bin/env python3
"""
Personal AI Assistant — Jetson Edition
Mic → Silero VAD → STT → LLM/VLM → TTS → Speaker
Optional: USB Camera + Web UI broadcaster

Usage:
    python assistant.py                     # φωνή + κάμερα + web UI
    python assistant.py --no-camera         # χωρίς κάμερα
    python assistant.py --no-web            # χωρίς web UI
    python assistant.py --no-tts            # χωρίς TTS (text-only)
    python assistant.py --no-rag            # χωρίς knowledge base
"""

import argparse
import sys
import threading
import time
import queue
import cv2
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import Config
from app.audio import find_alsa_device
from app.stt import STT
from app.llm import LLM, OpenClawLLM
from app.tts import create_tts
from app.pipeline import (
    SAMPLE_RATE, MicRecorder, vad_loop, load_silero,
    stream_and_speak, tts_player, play_audio
)
from app.monitor import get_system_stats, format_stats, get_jetson_model
from app.face_recognition import FaceRecognizer
from rich.console import Console
from rich.panel import Panel


console = Console()

# Global state for bounding boxes
last_detected_faces = []

# ── Vision keyword detection ──────────────────────────────────────────────

VISION_KEYWORDS_EL = [
    "τι βλέπεις", "τι βλέπεσαι", "τι υπάρχει", "τι έχει",
    "περίγραψε", "περιγράψτε", "κοίτα", "κοίτα γύρω", "κοίταξε", "δες",
    "μπροστά σου", "μπροστά", "γύρω σου", "το δωμάτιο", "περιβάλλον",
    "η εικόνα", "την εικόνα", "χρώμα", "χρώματα", "πόσα",
    "βλέπω", "βλέπεις", "με βλέπεις", "τι είναι", "ποιος", "ποια", "κάμερα", "vlm",
]
VISION_KEYWORDS_EN = [
    "what do you see", "can you see", "see me", "see", "describe", "look at", "look", "camera",
    "in front", "what's there", "show me", "what color",
    "how many", "what is", "who is", "environment", "vlm",
]

def needs_vision(text: str) -> bool:
    """Return True if the user's question requires visual context."""
    t = text.lower()
    return any(kw in t for kw in VISION_KEYWORDS_EL + VISION_KEYWORDS_EN)


# ── Stats broadcast loop ──────────────────────────────────────────────────

def _stats_thread(broadcaster, config, models_info: dict):
    """Background thread: broadcasts system stats every 5 seconds."""
    platform = get_jetson_model()
    broadcaster.send({"type": "info", "platform": platform, "models": models_info})

    while True:
        time.sleep(5)
        stats = get_system_stats()
        broadcaster.send({"type": "info", "platform": platform, "models": models_info})
        # Check service status (Ollama & OpenClaw)
        try:
            import subprocess
            ollama_ok = subprocess.run(["systemctl", "--user", "is-active", "--quiet", "ollama"], capture_output=True).returncode == 0
            if not ollama_ok:
                ollama_ok = subprocess.run(["systemctl", "is-active", "--quiet", "ollama"], capture_output=True).returncode == 0
            openclaw_ok = subprocess.run(["systemctl", "--user", "is-active", "--quiet", "openclaw-gateway"], capture_output=True).returncode == 0
            if not openclaw_ok:
                openclaw_ok = subprocess.run(["pgrep", "-f", "openclaw gateway"], capture_output=True).returncode == 0
        except Exception:
            ollama_ok = False
            openclaw_ok = False

        broadcaster.send({
            "type": "stats",
            "cpu": stats.cpu_percent,
            "ram_used": stats.ram_used_mb / 1024,
            "ram_total": stats.ram_total_mb / 1024,
            "gpu": stats.gpu_percent,
            "platform": platform,
            "ollama_active": ollama_ok,
            "openclaw_active": openclaw_ok,
        })


# ── Camera frame broadcast loop ───────────────────────────────────────────

def _frame_thread(cam, broadcaster, fps: float):
    """Background thread: streams camera frames to web clients."""
    global last_detected_faces
    interval = 1.0 / fps
    while cam.health_check():
        if broadcaster.client_count > 0:
            frame = cam.latest_raw(copy=True)
            if frame is not None:
                for name, conf, box in last_detected_faces:
                    color = (0, 255, 0) if name.lower() == "philip" else (255, 165, 0)
                    cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                    label = f"{name}: {conf:.1f}%" if name.lower() != "unknown" else "Face"
                    cv2.putText(frame, label, (box[0], max(0, box[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    b64 = base64.b64encode(jpg.tobytes()).decode("ascii")
                    broadcaster.send({"type": "frame", "data": b64})
        time.sleep(interval)


# ── Proactive Face Greeting loop ──────────────────────────────────────────

def _face_monitor_thread(cam, face_recognizer, tts, mic, assistant_active, broadcaster):
    """Background thread: proactively greets known faces and activates assistant."""
    global last_detected_faces
    last_greeted = {}
    greeting_cooldown = 36000  # seconds (10 hours cooldown)

    while cam.health_check():
        # Sleep longer if already active to save CPU for VAD/STT
        sleep_time = 2.0 if assistant_active.is_set() else 0.3
        time.sleep(sleep_time)
        
        # Skip if the mic is paused (meaning assistant is already talking)
        if not mic.listening.is_set():
            continue
            
        frame = cam.latest_raw()
        if frame is not None and face_recognizer and tts:
            detected = face_recognizer.recognize_in_image(frame)
            last_detected_faces = detected
            now = time.time()
            
            best_name = None
            best_conf = 0.0
            
            for name, conf, box in detected:
                if name.lower() != "unknown" and conf > best_conf:
                    best_name = name
                    best_conf = conf
                    
            if broadcaster:
                broadcaster.send({"type": "face_rec", "name": best_name, "confidence": best_conf})
                
            if best_name and best_name.lower() == "philip":
                if best_conf > 60.0: # high confidence threshold for activation
                    if not assistant_active.is_set():
                        assistant_active.set()
                        console.print(f"\n[bold green]🌟 Αναγνώριση Προσώπου ({best_conf:.1f}%): Ο Assistant ΕΝΕΡΓΟΠΟΙΗΘΗΚΕ![/bold green]")
                    
                    # Check cooldown
                    if best_name not in last_greeted or (now - last_greeted[best_name]) > greeting_cooldown:
                        last_greeted[best_name] = now
                        console.print(f"\n[bold green]👋 Χαιρετισμός: Welcome back, {best_name.capitalize()}![/bold green]")
                        
                        r = tts.synthesize(f"Welcome back {best_name.capitalize()}. How can I help you?")
                        if r and r.get("audio") is not None:
                            mic.pause()
                            play_audio(r["audio"], r["sample_rate"], sink=mic.get_pa_sink())
                            mic.resume()


# ── Main assistant loop ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Personal AI Assistant")
    parser.add_argument("--no-camera", action="store_true", help="Disable camera")
    parser.add_argument("--no-web", action="store_true", help="Disable web UI")
    parser.add_argument("--no-tts", action="store_true", help="Disable TTS (text-only)")
    parser.add_argument("--no-rag", action="store_true", help="Disable RAG knowledge base")
    parser.add_argument("--host", default=None, help="Web server host (default from config)")
    parser.add_argument("--port", type=int, default=None, help="Web server port (default from config)")
    parser.add_argument("--run-usecases", action="store_true", help="Run the 3 complicated use cases test suite")
    args = parser.parse_args()

    if args.run_usecases:
        from test_complicated_usecases import (
            run_usecase_1_local_rag,
            run_usecase_2_cloud_research,
            run_usecase_3_cloud_code_automation,
        )
        print("🚀 Running 3 Complicated Use Cases Suite...")
        run_usecase_1_local_rag()
        run_usecase_2_cloud_research()
        run_usecase_3_cloud_code_automation()
        return

    config = Config.load()
    assistant_name = config.assistant.name

    use_rag = not args.no_rag and config.rag.enabled
    use_camera = not args.no_camera
    use_web = not args.no_web
    use_tts = not args.no_tts

    active_system_prompt = (
        config.llm.system_prompt if use_rag else config.llm.system_prompt_no_rag
    )

    console.print(Panel.fit(
        f"[bold cyan]{assistant_name} — Personal AI Assistant[/bold cyan]\n"
        f"Μίλα οποτεδήποτε — auto-detects speech\n"
        f"[dim]"
        + ("📷 Camera  " if use_camera else "")
        + ("🌐 Web UI  " if use_web else "")
        + ("🔊 TTS  " if use_tts else "📝 Text-only  ")
        + ("📚 RAG  " if use_rag else "")
        + "  |  Ctrl-C για έξοδο[/dim]",
        border_style="cyan",
    ))

    # ── Broadcaster (Web UI) ──────────────────────────────────
    broadcaster = None
    if use_web:
        from app.web import Broadcaster, start_web_server
        broadcaster = Broadcaster()
        host = args.host or config.web.host
        port = args.port or config.web.port
        start_web_server(broadcaster, host=host, port=port)
        console.print(f"  🌐 Web UI: [link]http://{host}:{port}[/link]")

    # ── Camera ────────────────────────────────────────────────
    cam = None
    if use_camera:
        try:
            from app.camera import Camera
            cam = Camera(
                device=config.vision.camera_device,
                width=config.vision.width,
                height=config.vision.height,
                jpeg_quality=config.vision.jpeg_quality,
                capture_fps=config.vision.capture_fps,
            )
            if cam.start():
                console.print(f"  📷 Camera: [green]✓ /dev/video{config.vision.camera_device}[/green]")
                if broadcaster:
                    threading.Thread(
                        target=_frame_thread,
                        args=(cam, broadcaster, config.web.ui_fps),
                        daemon=True,
                        name="frame-broadcaster",
                    ).start()
            else:
                console.print("  [yellow]⚠ Camera not available — vision disabled[/yellow]")
                cam = None
        except Exception as exc:
            console.print(f"  [yellow]⚠ Camera error: {exc}[/yellow]")
            cam = None

    # ── Audio device ──────────────────────────────────────────
    console.print("\n[bold]Φόρτωση μοντέλων...[/bold]")
    result = find_alsa_device(name_hint=config.audio.input_device or "USB Audio")
    if result:
        card, dev, mic_name = result
        hw = f"hw:{card},{dev}"
    else:
        # Fallback: use plughw: if input_device looks like one
        hint = config.audio.input_device or ""
        if hint.startswith("plughw:") or hint.startswith("hw:"):
            hw = hint
            mic_name = hint
        else:
            hw = "hw:0,0"
            mic_name = "default"
        console.print(f"  [yellow]Mic not found by name, using {hw}[/yellow]")

    # ── Load models ───────────────────────────────────────────
    stt = STT(
        model=config.stt.model,
        device=config.stt.device,
        compute_type=config.stt.compute_type,
        language=config.stt.language or config.assistant.language,
        beam_size=config.stt.beam_size,
    )
    stt.load()
    console.print(f"  ✓ STT: faster-whisper [{config.stt.model}]")

    silero_model = load_silero(console)

    llm = OpenClawLLM(
        model=config.llm.model,
        base_url=config.llm.base_url,
        backend=config.llm.backend,
        max_tokens=config.llm.max_tokens,
        temperature=config.llm.temperature,
        system_prompt=active_system_prompt,
        timeout=config.llm.timeout,
    )
    llm.load()
    llm.warmup()
    console.print(f"  ✓ Agent: OpenClaw @ {llm.base_url}")

    tts = None
    if use_tts:
        tts = create_tts(voice=config.tts.voice, speed=config.tts.speed, lang=config.tts.lang)
        if tts.load():
            console.print(f"  ✓ TTS: Kokoro [{config.tts.voice}]")
        else:
            console.print("  [yellow]⚠ TTS unavailable — text-only mode[/yellow]")
            tts = None

    # ── RAG ───────────────────────────────────────────────────
    rag = None
    if use_rag:
        try:
            from app.rag import KnowledgeBase, RAGRetriever
            kb = KnowledgeBase(persist_dir=config.rag.persist_dir)
            kb.sync_directory(config.rag.knowledge_dir)
            rag = RAGRetriever(kb, config.rag.n_results, config.rag.min_relevance)
            console.print("  ✓ RAG: knowledge base ready")
        except Exception as exc:
            console.print(f"  [yellow]⚠ RAG error: {exc}[/yellow]")

    # ── Face Recognition ──────────────────────────────────────
    face_recognizer = None
    if use_camera:
        try:
            face_recognizer = FaceRecognizer()
            console.print("  ✓ Face Recognition: ready")
        except Exception as exc:
            console.print(f"  [yellow]⚠ Face recognition error: {exc}[/yellow]")


    # ── Models info for Web UI ────────────────────────────────
    models_info = {
        "stt": f"whisper/{config.stt.model}",
        "vlm": llm.model or "cosmos",
        "tts": f"kokoro/{config.tts.voice}" if tts else "off",
        "vad": "silero",
    }

    if broadcaster:
        threading.Thread(
            target=_stats_thread,
            args=(broadcaster, config, models_info),
            daemon=True,
            name="stats-broadcaster",
        ).start()

    mic = MicRecorder(console, chunk_ms=config.vad.chunk_ms)
    mic_ready = mic.start(
        hw,
        config.audio.input_device or "USB Audio",
        speaker_hint=config.audio.output_device,
        echo_cancellation=config.audio.echo_cancellation,
    )
    if not mic_ready:
        console.print("  [yellow]⚠ Microphone unavailable — running Web UI server[/yellow]")
        if broadcaster:
            console.print("  [green]✅ Web UI online at http://0.0.0.0:8090[/green]")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                return
        else:
            return

    # ── Proactive Greeting Thread ─────────────────────────────
    assistant_active = threading.Event()

    def _on_ptt(active: bool):
        if active:
            assistant_active.set()
            if broadcaster:
                broadcaster.send({"type": "status", "stage": "listening"})
            console.print("  [green]🎤 Microphone Active (Unmuted)[/green]")
        else:
            assistant_active.clear()
            if broadcaster:
                broadcaster.send({"type": "status", "stage": "muted"})
            console.print("  [yellow]🔇 Microphone Muted[/yellow]")

    if broadcaster:
        broadcaster.configure_speakers(
            getter=mic.speaker_state,
            setter=mic.select_speaker,
        )
        broadcaster.on_ptt_toggle = _on_ptt

    if cam and face_recognizer and use_tts:
        threading.Thread(
            target=_face_monitor_thread,
            args=(cam, face_recognizer, tts, mic, assistant_active, broadcaster),
            daemon=True,
            name="face-monitor",
        ).start()
    else:
        # If no camera or face rec, just activate immediately
        assistant_active.set()

    if assistant_active.is_set():
        console.print(f"\n[green bold]✅ Ready — speak anytime![/green bold]\n")
    else:
        console.print(f"\n[yellow bold]😴 Dormant. Waiting to recognize Philip on camera to activate...[/yellow bold]\n")

    if broadcaster:
        broadcaster.send({"type": "status", "stage": "listening" if broadcaster.ptt_active else "muted"})

    chat_history = []

    # ── Main conversation loop ────────────────────────────────
    try:
        for segment in vad_loop(mic, console, vad_cfg=config.vad, silero=silero_model):

            if not assistant_active.is_set() or (broadcaster and not broadcaster.ptt_active):
                # Ignore audio if muted or not activated yet
                mic.resume()
                continue

            # Pipeline stage: transcribing
            if broadcaster:
                broadcaster.send({"type": "status", "stage": "transcribing"})

            result = stt.transcribe(segment.audio, sample_rate=SAMPLE_RATE)
            text = result.get("text", "").strip()
            if not text:
                mic.resume()
                if broadcaster:
                    broadcaster.send({"type": "status", "stage": "listening"})
                continue

            console.print(f'  [green]You:[/green] "{text}"')

            if broadcaster:
                broadcaster.send({
                    "type": "transcript",
                    "text": text,
                    "stt_time": result.get("duration"),
                    "duration": segment.duration,
                })

            # ── RAG context & User Identity injection ─────────
            user_identity_context = (
                "User Identity Profile (Philip):\n"
                "- Name: Philip (Φίλιππος)\n"
                "- Hometown: Lamia, Greece\n"
                "- Education: Computer & Software Engineer (University of Patras)\n"
                "- Profession & Role: AI Engineer & Creator of the Aria AI Assistant"
            )
            prompt = text
            rag_context = ""
            if rag:
                docs = rag.kb.search(text, n_results=rag.n_results)
                relevant = [d for d in docs if d.get("distance", 2) < 1.5]
                if relevant:
                    rag_context = "Retrieved Knowledge Base Context:\n" + "\n\n".join(d["content"] for d in relevant)
                    console.print(f"  [cyan]🧠 RAG Retrieval: Found {len(relevant)} relevant chunks in Knowledge Base[/cyan]")

            # ── Vision: capture frames if question needs it ───
            images_b64 = None
            system_prompt = f"{active_system_prompt}\n\n{user_identity_context}"
            if rag_context:
                system_prompt += f"\n\n{rag_context}"
            detected_names = []
            
            if cam:
                latest_frame = cam.latest_raw()
                if latest_frame is not None and face_recognizer:
                    detected = face_recognizer.recognize_in_image(latest_frame)
                    if detected:
                        names_str = ", ".join([f"{n} ({c:.1f}%)" for n, c, _ in detected])
                        system_prompt += f"\n\nContext: You can currently see {names_str}."
                        console.print(f"  [dim]👤 Recognized: {names_str}[/dim]")

                if needs_vision(text):
                    if broadcaster:
                        broadcaster.send({"type": "status", "stage": "thinking"})
                    images_b64 = cam.get_speech_frames(
                        segment.start_time,
                        segment.end_time,
                        max_frames=config.vision.frames,
                    )
                    if not images_b64:
                        single = cam.capture_single()
                        if single:
                            images_b64 = [single]
                    system_prompt = config.vision.system_prompt
                    if detected_names:
                        names_str = ", ".join(detected_names)
                        system_prompt += f"\n\nContext: The person in the image is {names_str}."
                    console.print("  [dim]📷 Vision query — attaching camera frame[/dim]")

            # ── LLM generation + TTS ──────────────────────────
            console.print(f"  [magenta]{assistant_name}:[/magenta] ", end="")

            if broadcaster:
                broadcaster.send({"type": "status", "stage": "thinking"})

            pa_sink = mic.get_pa_sink()
            
            # Combine vision few_shot and chat history
            current_few_shot = list(chat_history)
            if images_b64 and config.vision.few_shot:
                current_few_shot.extend(config.vision.few_shot)

            # Stream LLM and simultaneously speak
            full_response, elapsed, ttft = stream_and_speak(
                llm,
                tts,
                prompt,
                system_prompt,
                pa_sink=pa_sink,
                images_b64=images_b64,
                few_shot=current_few_shot if current_few_shot else None,
                first_chunk_words=config.tts.first_chunk_words,
                max_chunk_words=config.tts.max_chunk_words,
                broadcaster=broadcaster,
            )
            console.print()
            
            if full_response:
                chat_history.append({"role": "user", "content": prompt})
                chat_history.append({"role": "assistant", "content": full_response})
                if len(chat_history) > 20: # keep last 10 exchanges
                    chat_history = chat_history[-20:]

            if broadcaster:
                broadcaster.send({
                    "type": "done",
                    "ttft": ttft,
                    "vlm_time": elapsed if images_b64 else None,
                })
                broadcaster.send({"type": "status", "stage": "listening"})

            mic.resume()

    except KeyboardInterrupt:
        console.print(f"\n[yellow]Αντίο! Ο {assistant_name} σταματάει...[/yellow]")
    finally:
        mic.stop()
        if cam:
            cam.close()


if __name__ == "__main__":
    main()
