import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import Config
from app.tts import create_tts
import time
import os

print("Φόρτωση Config...")
config = Config.load()

print(f"Φόρτωση Kokoro TTS (voice: {config.tts.voice})...")
tts = create_tts(voice=config.tts.voice, speed=config.tts.speed, lang=config.tts.lang)
if not tts.load():
    print("Error loading TTS")
    sys.exit(1)

print("Synthesizing: Welcome back...")
success = tts.synthesize_to_file("Welcome back, I am Aria, your personal assistant.", "welcome.wav")
if success:
    print("Playing audio...")
    os.system("paplay welcome.wav")
else:
    print("Failed to synthesize")
