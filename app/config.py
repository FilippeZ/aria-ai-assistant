"""Configuration — loads settings.yaml into typed dataclasses."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import yaml


@dataclass
class AssistantConfig:
    name: str = "Aria"
    language: str = "el"  # STT language: "el" Greek, "en" English, "" auto-detect


@dataclass
class LLMConfig:
    model: str = ""
    base_url: str = "http://localhost:8080"
    backend: str = "openai"
    max_tokens: int = 512
    temperature: float = 0.7
    timeout: float = 120.0
    system_prompt: str = "Είσαι η Aria, η έξυπνη προσωπική βοηθός του Φίλιππου (Philip). Απάντα σύντομα και άμεσα."
    system_prompt_no_rag: str = "Είσαι η Aria, η έξυπνη προσωπική βοηθός του Φίλιππου (Philip). Απάντα από τις γνώσεις σου."


@dataclass
class STTConfig:
    model: str = "base"
    device: str = "cuda"
    compute_type: str = "int8"
    language: str = "el"
    beam_size: int = 1


@dataclass
class TTSConfig:
    voice: str = "af_sarah"
    speed: float = 1.0
    lang: str = "en-us"
    first_chunk_words: int = 12
    max_chunk_words: int = 30


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    input_device: Optional[str] = "USB Audio"
    output_device: Optional[str] = None
    echo_cancellation: bool = True


@dataclass
class VADConfig:
    speech_threshold: float = 0.008
    silence_duration_ms: int = 500
    lookback_ms: int = 250
    max_speech_secs: int = 15
    chunk_ms: int = 32
    min_utterance_secs: float = 0.3
    min_utterance_rms: float = 0.001
    silero_threshold: float = 0.5


@dataclass
class VisionConfig:
    camera_device: int = 0
    width: int = 640
    height: int = 480
    jpeg_quality: int = 80
    frames: int = 1
    capture_fps: float = 10.0
    system_prompt: str = (
        "Είσαι ένας έξυπνος προσωπικός βοηθός με πρόσβαση σε κάμερα. "
        "Όταν σε ρωτούν για το τι βλέπεις, περίγραψε την εικόνα σύντομα. "
        "Μια με δύο προτάσεις. Χωρίς markdown."
    )
    few_shot: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class RAGConfig:
    enabled: bool = True
    knowledge_dir: str = "./knowledge_base"
    persist_dir: str = "./data/chromadb"
    embedding_backend: str = "llamacpp"
    embedding_model: str = "bge-small-en-v1.5"
    embedding_base_url: str = "http://localhost:8081"
    n_results: int = 3
    min_relevance: float = 0.5
    chunk_size: int = 200
    chunk_overlap: int = 20


@dataclass
class WebConfig:
    ui_fps: float = 10.0
    host: str = "0.0.0.0"
    port: int = 8090


_SECTIONS = [
    ("assistant", "assistant", AssistantConfig),
    ("llm", "llm", LLMConfig),
    ("stt", "stt", STTConfig),
    ("tts", "tts", TTSConfig),
    ("audio", "audio", AudioConfig),
    ("vad", "vad", VADConfig),
    ("vision", "vision", VisionConfig),
    ("rag", "rag", RAGConfig),
    ("web", "web", WebConfig),
]


@dataclass
class Config:
    assistant: AssistantConfig = field(default_factory=AssistantConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    web: WebConfig = field(default_factory=WebConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        config = cls()
        if not os.path.exists(config_path):
            return config
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
            for yaml_key, attr_name, _ in _SECTIONS:
                section_obj = getattr(config, attr_name)
                for k, v in data.get(yaml_key, {}).items():
                    if hasattr(section_obj, k):
                        setattr(section_obj, k, v)
        except Exception as e:
            print(f"Error loading config: {e}")
        return config
