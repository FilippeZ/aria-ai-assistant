import sys
import os
import time

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.llm import OpenClawLLM

def test_usecase(prompt):
    print(f"\n--- USE CASE: {prompt} ---")
    start_time = time.time()
    
    llm = OpenClawLLM()
    llm.load()
    
    print("Response: ", end="", flush=True)
    full_response = ""
    
    for chunk, meta in llm.generate_stream(prompt):
        if chunk:
            print(chunk, end="", flush=True)
            full_response += chunk
        if meta.get("done"):
            break
            
        if time.time() - start_time > 120:
            print("\n[Timeout reached]")
            break
            
    print(f"\n\n[Time elapsed: {time.time() - start_time:.2f}s]")
    return full_response

if __name__ == "__main__":
    # Case 1: Simple Chat -> Should route LOCAL
    test_usecase("Hello, who are you?")
    
    # Case 2: Tool usage -> Should route CLOUD
    test_usecase("Can you play a song from youtube?")
    
    # Case 3: Complex Analysis -> Should route CLOUD
    test_usecase("Analyze my notes for the current project.")
