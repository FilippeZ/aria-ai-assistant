#!/usr/bin/env python3
"""
Cursor Control & GUI Automation Tool for OpenClaw Agent.
Allows mouse cursor movement, clicking, YouTube playback, terminal execution, and typing.
"""

import time
import subprocess
import pyautogui

pyautogui.FAILSAFE = False

def get_screen_size():
    return pyautogui.size()

def move_cursor(x: int, y: int):
    pyautogui.moveTo(x, y, duration=0.5)
    return f"Cursor moved to ({x}, {y})"

def click_cursor(x: int = None, y: int = None):
    if x is not None and y is not None:
        pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click()
    return "Mouse clicked."

def open_youtube_and_click_play(search_query: str) -> str:
    """Open YouTube, search query, move cursor to the first video, and click play."""
    import urllib.parse
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
    subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3.0)
    
    w, h = pyautogui.size()
    # Target top video result thumbnail location on 1080p / standard display
    target_x = int(w * 0.45)
    target_y = int(h * 0.35)
    
    pyautogui.moveTo(target_x, target_y, duration=0.6)
    pyautogui.click()
    return f"Opened YouTube for '{search_query}', moved cursor to ({target_x}, {target_y}) and clicked to play."

def open_terminal_and_run(cmd: str) -> str:
    """Open terminal emulator and execute bash command."""
    subprocess.Popen(["x-terminal-emulator", "-e", f"bash -c '{cmd}; exec bash'"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"Opened terminal window and ran command: '{cmd}'"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "play_youtube" and len(sys.argv) > 2:
            print(open_youtube_and_click_play(" ".join(sys.argv[2:])))
        elif action == "run_term" and len(sys.argv) > 2:
            print(open_terminal_and_run(" ".join(sys.argv[2:])))
        elif action == "click":
            print(click_cursor())
        else:
            print(f"Unknown action: {action}")
