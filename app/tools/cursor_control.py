#!/usr/bin/env python3
"""
Advanced Desktop Automation & Agent Control Suite for Aria Hybrid Assistant.
Supports:
- Desktop GUI Cursor Movement, Clicking & Dragging
- YouTube Search & Media Playback Automation
- Terminal Command Execution & Python Script Runner
- Screen Capture & Screenshot Helper
- Mouse Wheel Scrolling & Text Typing
- System Telemetry & Thermal Diagnostics
"""

import time
import subprocess
import os
from pathlib import Path
import pyautogui

pyautogui.FAILSAFE = False

def get_screen_size():
    w, h = pyautogui.size()
    return {"width": w, "height": h}

def move_cursor(x: int, y: int):
    pyautogui.moveTo(x, y, duration=0.5)
    return f"Cursor moved to ({x}, {y})"

def click_cursor(x: int = None, y: int = None, double_click: bool = False):
    if x is not None and y is not None:
        pyautogui.moveTo(x, y, duration=0.3)
    if double_click:
        pyautogui.doubleClick()
        return f"Double-clicked mouse at ({x}, {y})"
    pyautogui.click()
    return "Mouse clicked."

def scroll_screen(clicks: int = 5, direction: str = "down"):
    amount = -clicks if direction == "down" else clicks
    pyautogui.scroll(amount)
    return f"Scrolled screen {direction} by {clicks} units."

def type_text(text: str, interval: float = 0.03):
    pyautogui.write(text, interval=interval)
    return f"Typed text: '{text}'"

def take_screenshot(filename: str = "/tmp/aria_screenshot.png") -> str:
    img = pyautogui.screenshot()
    img.save(filename)
    return filename

def extract_youtube_query(text: str) -> str:
    import re
    if "Question:" in text:
        text = text.split("Question:", 1)[-1].strip()
    text = re.sub(r"User Identity Profile.*?(?:Question:|\n\n|$)", "", text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r"Answer concisely using the following information:.*?(?:Question:|\n\n|$)", "", text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r"Question:", "", text, flags=re.IGNORECASE).strip()
    
    # Remove prefix action phrases
    text = re.sub(r"^(?:oh!|oh|hey|aria|please|can you|could you)?\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^(?:open\s+youtube\s+and\s+search\s+for|open\s+youtube\s+and\s+play|open\s+youtube\s+and|open\s+youtube|search\s+and\s+play|find\s+and\s+play|search\s+for|find|look\s+up|play\s+me|play\s+a|play\s+some|play|click\s+it\s+to\s+hear\s+it|click|βρες\s+και\s+παίξε|βρες\s+και\s+παιξε|παίξε\s+μου|παιξε\s+μου|παίξε|παιξε|βρες|vres\s+kai\s+paixe|paixe\s+mou|paixe|vres)\s*", "", text, flags=re.IGNORECASE).strip()

    # Remove filler suffix/words if specific artist/song title remains
    cleaned_suffix = re.sub(r"\b(?:song|music|video|track|tragoudi|mousiki|on youtube|youtube)\b", "", text, flags=re.IGNORECASE).strip()
    cleaned_suffix = re.sub(r"\bPhilip\b", "", cleaned_suffix, flags=re.IGNORECASE).strip(". ,:-")

    if cleaned_suffix and len(cleaned_suffix) >= 2 and cleaned_suffix.lower() not in ["a", "some", "the", "me", "ena", "kanena"]:
        return cleaned_suffix

    text = re.sub(r"\bPhilip\b", "", text, flags=re.IGNORECASE).strip(". ,:-")
    if not text or text.lower() in ["a", "some", "the", "me", "ena", "kanena", "a song", "music", "song", "tragoudi", "mousiki"]:
        return "popular music top hits"
    return text

def _clean_query(text: str) -> str:
    return extract_youtube_query(text)

def open_youtube_and_click_play(search_query: str) -> str:
    """Open YouTube, search query, move cursor to top video thumbnail, and click play."""
    search_query = _clean_query(search_query)
    import urllib.parse
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
    subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3.0)
    
    w, h = pyautogui.size()
    target_x = int(w * 0.45)
    target_y = int(h * 0.35)
    
    pyautogui.moveTo(target_x, target_y, duration=0.6)
    pyautogui.click()
    return f"Opened YouTube for '{search_query}', moved cursor to ({target_x}, {target_y}) and clicked to play."

def open_browser_search(query: str) -> str:
    """Open web browser search query."""
    query = _clean_query(query)
    import urllib.parse
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"Opened web search for '{query}' in browser."

def open_terminal_and_run(cmd: str) -> str:
    """Open terminal emulator and execute bash command."""
    subprocess.Popen(["x-terminal-emulator", "-e", f"bash -c '{cmd}; exec bash'"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"Opened terminal window and ran command: '{cmd}'"

def execute_python_code(code: str, filename: str = "/tmp/aria_agent_script.py") -> str:
    """Write python code to file and execute it."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)
    
    proc = subprocess.run(["python3", filename], capture_output=True, text=True, timeout=30)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    return f"Python Script Output:\n{stdout}\n{stderr}" if stderr else f"Python Script Output:\n{stdout}"

def get_system_telemetry() -> dict:
    """Gather live Jetson Orin Nano telemetry (CPU, RAM, GPU, Thermals)."""
    import psutil
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    
    gpu_load = 0.0
    try:
        if os.path.exists("/sys/devices/gpu.0/load"):
            with open("/sys/devices/gpu.0/load", "r") as f:
                gpu_load = float(f.read().strip()) / 10.0
    except Exception:
        pass
        
    return {
        "cpu_percent": cpu_percent,
        "ram_used_gb": round(ram.used / (1024**3), 2),
        "ram_total_gb": round(ram.total / (1024**3), 2),
        "gpu_percent": gpu_load,
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "play_youtube" and len(sys.argv) > 2:
            print(open_youtube_and_click_play(" ".join(sys.argv[2:])))
        elif action == "run_term" and len(sys.argv) > 2:
            print(open_terminal_and_run(" ".join(sys.argv[2:])))
        elif action == "search" and len(sys.argv) > 2:
            print(open_browser_search(" ".join(sys.argv[2:])))
        elif action == "click":
            print(click_cursor())
        elif action == "telemetry":
            print(get_system_telemetry())
        else:
            print(f"Unknown action: {action}")
