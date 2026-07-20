#!/usr/bin/env python3
"""
Voice Chat — speak anytime, dynamic recording.
Mic -> Silero VAD -> STT -> (RAG) -> LLM stream -> TTS stream -> Speaker
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import Config
from app.audio import find_alsa_device
from app.stt import STT
from app.llm import LLM
from app.tts import create_tts
from app.pipeline import (
    SAMPLE_RATE, MicRecorder, warmup_stt, vad_loop, stream_and_speak, load_silero,
)
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    use_rag = "--no-rag" not in sys.argv
    config = Config.load()
    active_system_prompt = config.llm.system_prompt if use_rag else config.llm.system_prompt_no_rag

    console.print(Panel.fit(
        "[bold cyan]Voice Chat (Jetson Optimized)[/bold cyan]\n"
        "Speak anytime — auto-detects speech\n"
        f"[dim]{'RAG on' if use_rag else 'RAG off'}  |  Ctrl-C to quit[/dim]",
        border_style="cyan",
    ))

    # ── Audio setup ──────────
    result = find_alsa_device(name_hint=config.audio.input_device or "default")
    if not result:
        console.print("[red]No mic found![/red]"); return
    card, dev, mic_name = result
    hw = f"hw:{card},{dev}"

    # ── Load models ──────────
    console.print("\n[bold]Loading models...[/bold]")
    stt = STT(model=config.stt.model, device=config.stt.device, compute_type=config.stt.compute_type)
    stt.load()
    silero_model = load_silero(console)

    llm = LLM(model=config.llm.model, base_url=config.llm.base_url, 
              system_prompt=active_system_prompt, timeout=config.llm.timeout)
    llm.load()
    
    tts = create_tts(voice=config.tts.voice)
    tts = tts if tts.load() else None

    # ── RAG setup ────────────
    rag = None
    if use_rag and config.rag.enabled:
        try:
            from app.rag import KnowledgeBase, RAGRetriever
            kb = KnowledgeBase(persist_dir=config.rag.persist_dir)
            kb.sync_directory(config.rag.knowledge_dir)
            rag = RAGRetriever(kb, config.rag.n_results, config.rag.min_relevance)
            console.print("  ✓ RAG ready")
        except Exception as e:
            console.print(f"  ⚠ RAG error: {e}")

    # ── Start Mic ────────────
    mic = MicRecorder(console, chunk_ms=32)
    if not mic.start(hw, config.audio.input_device or "default"):
        console.print("[red]Cannot start mic![/red]"); return

    console.print("\n[green bold]Ready — speak anytime![/green bold]\n")

    # ── Main Loop ────────────
    try:
        for segment in vad_loop(mic, console, vad_cfg=config.vad, silero=silero_model):
            # STT
            result = stt.transcribe(segment.audio, sample_rate=SAMPLE_RATE)
            text = result.get("text", "").strip()
            if not text: mic.resume(); continue

            console.print(f'  [green]You:[/green] "{text}"')

            # RAG handling
            prompt = text
            if rag:
                docs = rag.kb.search(text, n_results=rag.n_results)
                relevant = [d for d in docs if d.get("distance", 2) < 1.0]
                if relevant:
                    ctx = "\n\n".join(d["content"] for d in relevant)
                    prompt = f"Answer using these facts:\n\n{ctx}\n\nQuestion: {text}"

            # LLM & TTS
            console.print("  [magenta]Assistant:[/magenta] ", end="")
            stream_and_speak(llm, tts, prompt, active_system_prompt, mic.pa_sink)
            console.print()
            mic.resume()

    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    finally:
        mic.stop()

if __name__ == "__main__":
    main()
