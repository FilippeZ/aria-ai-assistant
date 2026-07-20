#!/usr/bin/env python3
"""
Personal AI Assistant — Jetson Edition

Usage:
    python assistant.py                 # πλήρης λειτουργία (φωνή + κάμερα + web)
    python assistant.py --no-camera     # χωρίς κάμερα
    python assistant.py --no-web        # χωρίς web UI
    python assistant.py --no-tts        # text-only (χωρίς TTS)
    python assistant.py --no-rag        # χωρίς knowledge base

    python main.py                      # ισοδύναμο του assistant.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from assistant import main

if __name__ == "__main__":
    main()
