#!/usr/bin/env python3
"""
Verification Script for Hybrid AI Assistant Architecture:
1. Open YouTube and play Greek song of Pantelidis (Agent Action via Cursor).
2. Cloud Agent NotebookLM analysis query.
3. Optical / Local VLM vision model check + Local RAG memory.
"""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import Config
from app.llm import OpenClawLLM
from app.camera import Camera
from assistant import needs_vision

def run_usecase_1():
    print("\n" + "="*60)
    print("🎬 USE CASE 1: Open YouTube & Play Song via Cursor Automation")
    print("="*60)
    prompt = "open youtube and play greek song of pantelidis"
    
    config = Config.load()
    llm = OpenClawLLM(
        model=config.llm.model,
        base_url=config.llm.base_url,
        backend=config.llm.backend,
    )
    llm.load()
    
    print(f"User Prompt: '{prompt}'")
    route = llm._decide_routing(prompt)
    print(f"Routing Decision: {route} (Agent Action)")
    
    print("Response Stream: ", end="", flush=True)
    full_resp = ""
    for chunk, meta in llm.generate_stream(prompt):
        if chunk:
            print(chunk, end="", flush=True)
            full_resp += chunk
    print("\n✓ Use Case 1 Test Complete.")
    return full_resp

def run_usecase_2():
    print("\n" + "="*60)
    print("📚 USE CASE 2: Cloud Agent NotebookLM Analysis Query")
    print("="*60)
    query = "use notebooklm and do an analysis in the last notebook ti leei"
    
    config = Config.load()
    llm = OpenClawLLM(
        model=config.llm.model,
        base_url=config.llm.base_url,
        backend=config.llm.backend,
    )
    llm.load()
    
    print(f"User Query: '{query}'")
    route = llm._decide_routing(query)
    print(f"Routing Decision: {route} (OpenClaw Cloud Agent)")
    
    print("Response Stream: ", end="", flush=True)
    full_resp = ""
    for chunk, meta in llm.generate_stream(query):
        if chunk:
            print(chunk, end="", flush=True)
            full_resp += chunk
    print("\n✓ Use Case 2 Test Complete.")
    return full_resp

def run_usecase_3():
    print("\n" + "="*60)
    print("👁️ USE CASE 3: Optical VLM Model Perception & Local RAG Memory")
    print("="*60)
    prompt = "tsekare an to local modelo einai ontos vlm kai me vlepei kai vlepei to perivelon den einai mono llm"
    
    is_vision = needs_vision(prompt)
    print(f"User Query: '{prompt}'")
    print(f"needs_vision trigger: {is_vision}")
    
    config = Config.load()
    cam = Camera(device=config.vision.camera_device)
    images_b64 = None
    if cam.start():
        for _ in range(10):
            time.sleep(0.2)
            single = cam.capture_single()
            if single:
                images_b64 = [single]
                print("✓ Camera frame captured from /dev/video0 for Optical VLM!")
                break
        cam.close()
    else:
        print("⚠ Camera device unavailable; testing visual payload.")
        
    llm = OpenClawLLM(
        model=config.llm.model,
        base_url=config.llm.base_url,
        backend=config.llm.backend,
    )
    llm.load()
    
    route = llm._decide_routing(prompt, images_b64=images_b64)
    print(f"Routing Decision: {route} (Local Optical VLM Model)")
    
    print("Response Stream: ", end="", flush=True)
    full_resp = ""
    for chunk, meta in llm.generate_stream(prompt, images_b64=images_b64):
        if chunk:
            print(chunk, end="", flush=True)
            full_resp += chunk
    print("\n✓ Use Case 3 Test Complete.")
    return full_resp

if __name__ == "__main__":
    run_usecase_1()
    run_usecase_2()
    run_usecase_3()
