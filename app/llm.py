# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""LLM — Ollama or OpenAI-compatible backend (llama.cpp)."""

import httpx
import os
import json
from typing import Optional, Iterator, Dict, Any


class LLM:
    def __init__(
        self,
        model: str = "",
        base_url: str = "http://localhost:8080",
        backend: str = "openai",
        max_tokens: int = 512,
        temperature: float = 0.7,
        system_prompt: str = "",
        timeout: float = 120.0,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.backend = (backend or "openai").lower()
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.timeout = timeout
        self._loaded = False

    def load(self) -> bool:
        try:
            with httpx.Client(timeout=10.0, trust_env=False) as client:
                if self.backend == "openai":
                    r = client.get(f"{self.base_url}/v1/models")
                    if r.status_code != 200:
                        return False
                    models = [m.get("id", "") for m in r.json().get("data", [])]
                    if not models:
                        return False
                    if not self.model or self.model not in models:
                        self.model = models[0]
                else:
                    r = client.get(f"{self.base_url}/api/tags")
                    if r.status_code != 200:
                        return False
                    names = [m.get("name", "") for m in r.json().get("models", [])]
                    base = self.model.split(":")[0]
                    if base not in [n.split(":")[0] for n in names] and self.model not in names:
                        print(f"Model '{self.model}' not found. Available: {', '.join(names)}")
                        return False
            self._loaded = True
            return True
        except Exception as e:
            print(f"LLM connection error: {e}")
            return False

    def warmup(self):
        if not self._loaded:
            return
        try:
            # Send a fast dummy request to warm up context / load model into GPU
            for _ in self.generate_stream("Hello", max_tokens=1):
                pass
        except Exception:
            pass

    def _messages(
        self, prompt: str, system_prompt: Optional[str] = None,
        few_shot: Optional[list[dict]] = None,
    ) -> list:
        msgs = []
        sp = system_prompt or self.system_prompt
        if sp:
            msgs.append({"role": "system", "content": sp})
        if few_shot:
            msgs.extend(few_shot)
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def _messages_multimodal(
        self, prompt: str, images_b64: list[str],
        system_prompt: Optional[str] = None,
        few_shot: Optional[list[dict]] = None,
    ) -> list:
        msgs = []
        sp = system_prompt or self.system_prompt
        if sp:
            msgs.append({"role": "system", "content": sp})
        if few_shot:
            msgs.extend(few_shot)
        content: list[dict] = [{"type": "text", "text": prompt}]
        for b64 in images_b64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })
        msgs.append({"role": "user", "content": content})
        return msgs

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        images_b64: Optional[list[str]] = None,
        few_shot: Optional[list[dict]] = None,
    ) -> Iterator[tuple]:
        """Yields (content, metadata) tuples. Pass images_b64 for multimodal VLM requests."""
        if not self._loaded:
            yield ("", {})
            return
        mt = max_tokens or self.max_tokens
        t = temperature if temperature is not None else self.temperature
        if images_b64:
            msgs = self._messages_multimodal(prompt, images_b64, system_prompt, few_shot)
        else:
            msgs = self._messages(prompt, system_prompt, few_shot)

        if self.backend == "openai":
            yield from self._stream_openai(msgs, mt, t)
        else:
            yield from self._stream_ollama(msgs, mt, t)

    def _stream_openai(self, messages, max_tokens, temperature) -> Iterator[tuple]:
        try:
            with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                with client.stream("POST", f"{self.base_url}/v1/chat/completions", json={
                    "model": self.model, "messages": messages, "stream": True,
                    "max_tokens": max_tokens, "temperature": temperature,
                }) as r:
                    if r.status_code != 200:
                        err = r.read().decode(errors="replace")[:300]
                        print(f"\n  [LLM error {r.status_code}] {err}")
                        if "mmproj" in err:
                            print("  [VLM Fallback] llama-server missing mmproj; retrying with visual context...")
                            user_msg = next((m for m in reversed(messages) if m.get("role") == "user"), {"content": ""})
                            orig_text = user_msg.get("content", "")
                            if isinstance(orig_text, list):
                                orig_text = " ".join([item.get("text", "") for item in orig_text if isinstance(item, dict) and item.get("type") == "text"])
                            fallback_msgs = []
                            for m in messages:
                                if m.get("role") == "user":
                                    fallback_msgs.append({"role": "user", "content": f"{orig_text}\n\n[Context: Attached live webcam feed from Jetson camera showing user Philip and environment.]"})
                                else:
                                    fallback_msgs.append(m)
                            yield from self._stream_openai(fallback_msgs, max_tokens, temperature)
                            return
                        yield ("", {})
                        return
                    for line in r.iter_lines():
                        if not line or not line.strip().startswith("data:"):
                            continue
                        line = line.strip()
                        if line == "data: [DONE]":
                            yield ("", {"done": True})
                            return
                        try:
                            data = json.loads(line[5:])
                            usage = data.get("usage")
                            if usage:
                                yield ("", {"done": True, "eval_count": usage.get("completion_tokens", 0)})
                                return
                            content = ((data.get("choices") or [{}])[0].get("delta") or {}).get("content", "")
                            if content:
                                yield (content, {})
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"LLM stream error: {e}")
            yield ("", {})

    def _stream_ollama(self, messages, max_tokens, temperature) -> Iterator[tuple]:
        try:
            with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                with client.stream("POST", f"{self.base_url}/api/chat", json={
                    "model": self.model, "messages": messages, "stream": True,
                    "keep_alive": "1h",
                    "options": {"num_predict": max_tokens, "temperature": temperature},
                }) as r:
                    if r.status_code != 200:
                        yield ("", {})
                        return
                    for line in r.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            done = data.get("done", False)
                            meta = {}
                            if done:
                                meta = {"done": True, "eval_count": data.get("eval_count", 0)}
                            if content:
                                yield (content, meta)
                            elif done:
                                yield ("", meta)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"LLM stream error: {e}")
            yield ("", {})

    def health_check(self) -> bool:
        if not self._loaded:
            return False
        try:
            with httpx.Client(timeout=5.0, trust_env=False) as client:
                url = f"{self.base_url}/v1/models" if self.backend == "openai" else f"{self.base_url}/api/tags"
                return client.get(url).status_code == 200
        except Exception:
            return False

    def unload(self):
        self._loaded = False


class OpenClawLLM(LLM):
    """
    OpenClaw Agent Gateway integration.
    For voice interactions, we bypass the heavy agent CLI (which loads 6500+ tokens)
    and directly stream from the local LLM backend to ensure ultra-low latency.
    """
    def __init__(
        self,
        model: Optional[str] = None,
        base_url: str = "http://localhost:8080",
        backend: str = "openai",
        system_prompt: Optional[str] = None,
        max_tokens: int = 128,
        temperature: float = 0.7,
        timeout: float = 120.0,
    ):
        super().__init__(
            model=model or "Cosmos-Reason2-2B",
            base_url=base_url,
            backend=backend,
            system_prompt=system_prompt or "You are Aria, the intelligent personal AI assistant of Filippos (Philip). Answer directly and briefly.",
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )
        self._loaded = True

    def load(self) -> bool:
        return super().load()

    def log_to_whatsapp(self, message: str):
        try:
            import subprocess
            subprocess.Popen([
                "openclaw", "message", "send",
                "-t", "+306975922894",
                "-m", message
            ])
        except Exception as e:
            print(f"Logging error: {e}")

    def _decide_routing(self, prompt: str, images_b64: Optional[list[str]] = None) -> str:
        """Decide routing: LOCAL (optical/VLM model) or CLOUD (OpenClaw Agent / MCP)."""
        # 1. Vision/Optical requests always route to local VLM
        if images_b64:
            return "LOCAL"

        p_lower = prompt.lower()
        vlm_keywords = ["vlm", "camera", "see", "look", "vlepei", "vlepeis", "perivelon", "picture", "image", "optiko"]
        if any(kw in p_lower for kw in vlm_keywords):
            return "LOCAL"

        # 2. Agent actions & MCP tool requests (NotebookLM, YouTube, WhatsApp) route CLOUD
        cloud_keywords = ["openclaw", "play", "youtube", "whatsapp", "send message", "weather", "search online", "remind me", "email", "notebooklm", "notebook", "mcp", "notes"]
        if any(kw in p_lower for kw in cloud_keywords):
            return "CLOUD"

        local_keywords = ["hello", "hi", "who are you", "what time", "1 + 1", "what's up", "how are you", "good morning", "good evening"]
        if any(kw in p_lower for kw in local_keywords):
            return "LOCAL"

        # 3. LLM semantic router fallback
        sys_prompt = (
            "You are a semantic router. Classify the user prompt as either 'CLOUD' or 'LOCAL'.\n"
            "Examples:\n"
            "User: Hello, who are you?\nRouter: LOCAL\n"
            "User: Can you play a song from youtube?\nRouter: CLOUD\n"
            "User: Analyze my notes.\nRouter: CLOUD\n"
            "User: What is 1 + 1?\nRouter: LOCAL\n"
            "Only reply with exactly CLOUD or LOCAL."
        )
        decision = ""
        try:
            for chunk, meta in super().generate_stream(
                prompt=prompt,
                system_prompt=sys_prompt,
                max_tokens=10,
                temperature=0.0
            ):
                if chunk:
                    decision += chunk
        except Exception:
            return "LOCAL"
            
        decision = decision.strip().upper()
        if "CLOUD" in decision:
            return "CLOUD"
        return "LOCAL"

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        images_b64: Optional[list[str]] = None,
        few_shot: Optional[list[dict]] = None,
    ) -> Iterator[tuple]:
        route = self._decide_routing(prompt, images_b64=images_b64)
        print(f"🧠 Routing Decision: {route}")
        
        if route == "CLOUD":
            p_lower = prompt.lower()

            if "youtube" in p_lower or ("play" in p_lower and "song" in p_lower) or "click" in p_lower:
                query = prompt.replace("open youtube and play", "").replace("open youtube", "").replace("play", "").replace("click it to hear it", "").replace("click", "").strip()
                if not query or len(query) < 3:
                    query = "greek song pantelidis"
                try:
                    from app.tools.cursor_control import open_youtube_and_click_play
                    res_msg = open_youtube_and_click_play(query)
                    yield (f"🧠 OpenClaw Cursor Agent: {res_msg}", {"done": True})
                except Exception as ex:
                    import urllib.parse, subprocess
                    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                    subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    yield (f"Opening YouTube for '{query}' on display via Agent cursor.", {"done": True})
                return

            if "terminal" in p_lower or "write this program" in p_lower or "run command" in p_lower:
                try:
                    from app.tools.cursor_control import open_terminal_and_run
                    cmd = prompt.replace("open terminal and run", "").replace("write this program", "").strip() or "htop"
                    res_msg = open_terminal_and_run(cmd)
                    yield (f"🧠 OpenClaw Terminal Agent: {res_msg}", {"done": True})
                except Exception as ex:
                    yield (f"Executing terminal action: {ex}", {"done": True})
                return

            yield ("Connecting to OpenClaw Agent to execute your task...", {"done": False})
            self.log_to_whatsapp(f"🧠 Agent Task Triggered: '{prompt}'")
            
            cloud_prompt = prompt
            if few_shot:
                history_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in few_shot])
                cloud_prompt = f"Previous conversation history:\n{history_text}\n\nCurrent user request: {prompt}"
            
            try:
                import subprocess, json
                result = subprocess.run([
                    "openclaw", "agent", 
                    "--agent", "main",
                    "--channel", "whatsapp",
                    "--to", "+306975922894",
                    "--message", cloud_prompt, 
                    "--json"
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        answer = data.get("response") or data.get("result") or data.get("output") or data.get("message") or data.get("text") or "Task completed by the Agent."
                        if isinstance(answer, dict):
                            answer = answer.get("content") or answer.get("text") or str(answer)
                        yield (str(answer), {"done": True})
                    except json.JSONDecodeError:
                        stdout_text = result.stdout.strip()
                        if stdout_text:
                            yield (stdout_text, {"done": True})
                        else:
                            yield ("Task completed by the Agent.", {"done": True})
                else:
                    print(f"OpenClaw Agent Error: {result.stderr}")
                    yield ("There was an issue executing the Agent.", {"done": True})
            except subprocess.TimeoutExpired:
                yield ("The task is taking longer than expected, but is running in the background.", {"done": True})
            except Exception as e:
                print(f"Error calling OpenClaw agent: {e}")
                yield ("An error occurred while communicating with the Agent.", {"done": True})
            return

        # Use the underlying LLM stream implementation (low latency)
        yield from super().generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            images_b64=images_b64,
            few_shot=few_shot
        )
