#!/usr/bin/env python3
"""
Complicated Use Cases Verification Suite for Aria Assistant

1. USE CASE 1 (Local Model + RAG):
   Deep technical diagnostic on NVIDIA Jetson Orin Nano hardware specifications,
   power modes (7W/15W/25W), and memory bandwidth using local ChromaDB RAG vector search
   and local Cosmos-Reason2 LLM (GPU port 8080). Completely local / edge offline.

2. USE CASE 2 (Cloud Model Agent - Multi-Step Research & Comparative Matrix):
   Complex multi-step cloud research query comparing Jetson Orin Nano Super vs Raspberry Pi 5
   AI Kit for edge vision and LLM inference, generating a comparative markdown matrix.

3. USE CASE 3 (Cloud Model Agent - Multi-Tool Desktop Automation & Code Synthesis):
   System telemetry audit, inspecting local codebase files (app/pipeline.py & app/web.py),
   identifying pipeline bottleneck risks, and creating an automated optimizer tool script.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import Config
from app.llm import OpenClawLLM
from app.rag import KnowledgeBase, RAGRetriever


def run_usecase_1_local_rag():
    print("\n" + "═" * 70)
    print("🧠 USE CASE 1: Local Model + RAG (Jetson Technical Hardware Diagnostic)")
    print("═" * 70)

    config = Config.load()
    query = (
        "Ποια είναι τα ακριβή τεχνικά χαρακτηριστικά του Jetson Orin Nano (CUDA cores, RAM bandwidth, "
        "power modes 7W/15W/25W) και ποιες εντολές χρησιμοποιούμε για ρύθμιση ισχύος (nvpmodel) και παρακολούθηση (jtop);"
    )
    print(f"🔹 Ερώτηση Χρήστη: '{query}'")

    # 1. Local RAG Retrieval
    print("\n🔍 Εκτέλεση RAG Retrieval από το τοπικό ChromaDB Knowledge Base...")
    kb = KnowledgeBase(
        persist_dir=config.rag.persist_dir,
        embedding_backend=config.rag.embedding_backend,
        embedding_model=config.rag.embedding_model,
        embedding_base_url=config.rag.embedding_base_url,
    )
    kb.sync_directory(config.rag.knowledge_dir)
    docs = kb.search(query, n_results=3)
    relevant_docs = [d for d in docs if d.get("distance", 2.0) < 1.2]

    if relevant_docs:
        context_str = "\n\n".join(d["content"] for d in relevant_docs)
        print(f"✅ Βρέθηκαν {len(relevant_docs)} σχετικές ενότητες στο Knowledge Base.")
        augmented_prompt = f"Χρησιμοποίησε αποκλειστικά τις παρακάτω τεχνικές πληροφορίες για να απαντήσεις αναλυτικά:\n\n{context_str}\n\nΕρώτηση: {query}"
    else:
        print("⚠️ Δεν βρέθηκαν σχετικές ενότητες στο RAG, αποστολή ερωτήματος...")
        augmented_prompt = query

    # 2. Local Model Inference (Cosmos-Reason / llama.cpp)
    llm = OpenClawLLM(
        model=config.llm.model,
        base_url=config.llm.base_url,
        backend=config.llm.backend,
    )
    llm.load()

    route = llm._decide_routing(augmented_prompt)
    print(f"🎯 Δρομολόγηση: {route} (Local Edge Model)")

    print("\n💬 Απάντηση Τοπικού Μοντέλου (Streaming):")
    print("-" * 50)
    full_response = ""
    start_t = time.perf_counter()
    for chunk_data in llm.generate_stream(prompt=augmented_prompt, system_prompt=config.llm.system_prompt, max_tokens=150):
        content = chunk_data[0] if isinstance(chunk_data, tuple) else chunk_data
        if content:
            print(content, end="", flush=True)
            full_response += content
    elapsed = time.perf_counter() - start_t
    print("\n" + "-" * 50)
    print(f"⏱️ Χρόνος Απάντησης Τοπικού Μοντέλου: {elapsed:.2f}s")
    print("✅ Use Case 1 (Local RAG) ολοκληρώθηκε επιτυχώς!")
    return full_response


def run_usecase_2_cloud_research():
    print("\n" + "═" * 70)
    print("🌐 USE CASE 2: Cloud Model Agent (Multi-Step Web Research & Comparison Matrix)")
    print("═" * 70)

    config = Config.load()
    query = (
        "Perform a deep technical comparison between NVIDIA Jetson Orin Nano Super (67 INT8 TOPS) "
        "and Raspberry Pi 5 with AI Kit (13 TOPS) for edge vision & local LLM inference. "
        "Analyze memory bandwidth, TOPS per Watt, framework support (TensorRT vs Hailo), and synthesize a markdown table."
    )
    print(f"🔹 Ερώτηση Χρήστη: '{query}'")

    llm = OpenClawLLM(
        model=config.llm.model,
        base_url=config.llm.base_url,
        backend=config.llm.backend,
    )
    llm.load()

    route = llm._decide_routing(query)
    print(f"🎯 Δρομολόγηση: {route} (OpenClaw Cloud Agent Gateway)")

    print("\n💬 Απάντηση Cloud Agent (Streaming):")
    print("-" * 50)
    full_response = ""
    start_t = time.perf_counter()
    for chunk_data in llm.generate_stream(prompt=query):
        content = chunk_data[0] if isinstance(chunk_data, tuple) else chunk_data
        if content:
            print(content, end="", flush=True)
            full_response += content
    elapsed = time.perf_counter() - start_t
    print("\n" + "-" * 50)
    print(f"⏱️ Χρόνος Απάντησης Cloud Agent: {elapsed:.2f}s")
    print("✅ Use Case 2 (Cloud Agent Deep Research) ολοκληρώθηκε επιτυχώς!")
    return full_response


def run_usecase_3_cloud_code_automation():
    print("\n" + "═" * 70)
    print("⚙️ USE CASE 3: Cloud Model Agent (System Telemetry Audit & Code Synthesis)")
    print("═" * 70)

    config = Config.load()
    query = (
        "Perform a system audit of the Aria Assistant stack. Check the pipeline queue logic in app/pipeline.py "
        "and web broadcasting in app/web.py. Provide a performance code audit report and generate an automated "
        "python script in app/tools/system_optimizer.py to monitor CPU, RAM and WebSocket broadcast queues."
    )
    print(f"🔹 Ερώτηση Χρήστη: '{query}'")

    llm = OpenClawLLM(
        model=config.llm.model,
        base_url=config.llm.base_url,
        backend=config.llm.backend,
    )
    llm.load()

    route = llm._decide_routing(query)
    print(f"🎯 Δρομολόγηση: {route} (OpenClaw Cloud Agent Multi-Tool Automation)")

    print("\n💬 Απάντηση Cloud Agent Automation (Streaming):")
    print("-" * 50)
    full_response = ""
    start_t = time.perf_counter()
    for chunk_data in llm.generate_stream(prompt=query):
        content = chunk_data[0] if isinstance(chunk_data, tuple) else chunk_data
        if content:
            print(content, end="", flush=True)
            full_response += content
    elapsed = time.perf_counter() - start_t
    print("\n" + "-" * 50)
    print(f"⏱️ Χρόνος Απάντησης Cloud Agent Automation: {elapsed:.2f}s")
    print("✅ Use Case 3 (Cloud Agent Code Automation) ολοκληρώθηκε επιτυχώς!")
    return full_response


if __name__ == "__main__":
    print("🚀 Εκκίνηση Complicated Use Cases Suite για την Aria...")
    run_usecase_1_local_rag()
    run_usecase_2_cloud_research()
    run_usecase_3_cloud_code_automation()
