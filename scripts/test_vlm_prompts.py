"""Test system prompts + user prompts against the live VLM.

Sends the camera frame with different prompt configurations to 
evaluate VLM response quality on the Jetson Orin Nano.
"""

import httpx
import json
import time
from pathlib import Path

# Ρύθμιση για το τοπικό endpoint του VLM
BASE_URL = "http://localhost:8090" # Ενημέρωσε το port αν είναι διαφορετικό
IMG_B64_PATH = "/tmp/test_frame.b64"
MAX_TOKENS = 128
TEMPERATURE = 0.7

USER_PROMPTS = [
    "Hello!",
    "What do you see?",
    "Tell me a joke.",
]

# ── Test configs ──
TESTS = {
    "Minimal": {
        "system": (
            "You are Reachy Mini. Only refer to the image when asked. "
            "Keep responses to one or two sentences. No markdown/emojis."
        ),
        "few_shot": [],
    },
    "Conversational_FewShot": {
        "system": (
            "You are Reachy Mini. Ignore the attached image unless specifically asked about the scene. "
            "Keep responses short and natural. No markdown."
        ),
        "few_shot": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "What's in front of you?"},
            {"role": "assistant", "content": "I see a workspace with a laptop."},
        ],
    },
}

def query_vlm(system_prompt: str, few_shot: list, user_prompt: str, img_b64: str) -> tuple[str, float]:
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(few_shot)
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
        ],
    })
    
    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(f"{BASE_URL}/v1/chat/completions", json={
                "model": "Cosmos-Reason2", 
                "messages": messages, 
                "stream": False,
                "max_tokens": MAX_TOKENS, 
                "temperature": TEMPERATURE,
            })
            dt = time.perf_counter() - t0
            if r.status_code != 200:
                return f"[ERROR {r.status_code}]", dt
            
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip(), dt
    except Exception as e:
        return f"[Connection Error: {e}]", 0.0

def main():
    if not Path(IMG_B64_PATH).exists():
        print(f"Error: {IMG_B64_PATH} not found.")
        return

    with open(IMG_B64_PATH, "r") as f:
        img_b64 = f.read().strip()
    
    print(f"Loaded frame, testing {len(TESTS)} configs...\n")

    for test_name, cfg in TESTS.items():
        print(f"--- Testing: {test_name} ---")
        for up in USER_PROMPTS:
            resp, dt = query_vlm(cfg["system"], cfg["few_shot"], up, img_b64)
            print(f"User: {up}")
            print(f"VLM ({dt:.2f}s): {resp}\n")

if __name__ == "__main__":
    main()
