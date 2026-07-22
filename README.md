<div align="center">

  <img src="static/aria.png" alt="ARIA AI ASSISTANT Logo" width="220" style="border-radius: 24px; box-shadow: 0 8px 32px rgba(59, 130, 246, 0.4); margin-bottom: 20px;">

  # 🤖 ARIA AI ASSISTANT 🤖

  ### **Autonomous Multimodal Voice, Vision, RAG & Desktop Automation Agent for NVIDIA Jetson Orin Nano**

  [![NVIDIA Jetson](https://img.shields.io/badge/NVIDIA-Jetson%20Orin%20Nano-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/)
  [![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20Local%2BCloud-blue?style=for-the-badge)](#-system-architecture--workflow)
  [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![License](https://img.shields.io/badge/License-Apache%202.0-green?style=for-the-badge)](LICENSE)
  [![Creator](https://img.shields.io/badge/Creator-Philip%20%28FilippeZ%29-orange?style=for-the-badge&logo=github)](https://github.com/FilippeZ)

</div>

---

## 📌 Overview

**ARIA AI ASSISTANT** is a state-of-the-art autonomous, real-time, multimodal voice, vision, local RAG, and desktop automation assistant designed for edge robotics and high-productivity desktop environments on the **NVIDIA Jetson Orin Nano (8GB / 67 TOPS)**.

ARIA combines local on-device neural processing with cloud agentic intelligence in an **Advanced Dual-Core Hybrid Architecture**:

1. **Local Core (`LOCAL`)**: 
   - Real-time voice interaction with GPU-accelerated STT (`faster-whisper`) and CPU-optimized TTS (`Kokoro-ONNX`).
   - Optical vision perception & YuNet facial detection/recognition to identify the owner (**Philip**).
   - Desktop screenshot inspection via local VLM (`Cosmos-Reason2-2B-Q4_K_M`).
   - Real-time system telemetry diagnostics (CPU, RAM, GPU load, thermals).
   - Local Vector RAG using `ChromaDB` for domain-specific knowledge base retrieval.
   - Rolling short-term conversation context deque.

2. **Cloud Core (`CLOUD`)**:
   - Multi-step agentic execution via **OpenClaw Agent Gateway**.
   - Autonomous desktop cursor navigation & PyAutoGUI control (mouse movements, clicks, scrolling, playback).
   - Local GUI Application Generator (`app_generator.py`) creating `.desktop` launchers on-the-fly.
   - NotebookLM deep research querying & structured markdown synthesis.
   - Autonomous web search & browsing agent.
   - Live Python code runner and terminal command execution (`x-terminal-emulator`).

---

## 🖥️ Live Assistant Interface in Action

Here is ARIA AI Assistant running in real-time on desktop with live voice interaction, system status monitoring, and agent execution:

<div align="center">
  <img src="static/aria_live_usage.png" alt="ARIA AI Assistant Live Desktop Interface" width="900" style="border-radius: 14px; box-shadow: 0 8px 32px rgba(0,0,0,0.35); margin-top: 10px; margin-bottom: 20px;">
</div>

---

## 🖼️ Feature Highlights & Capabilities

### 🎬 1. Desktop GUI & Media Voice Automation
ARIA parses voice commands to control desktop GUI elements via `PyAutoGUI` and `python-xlib`. It can open media platforms (e.g., YouTube), locate UI targets, click buttons, type, and control playback seamlessly.

### ⚡ 2. Autonomous Local Desktop App Generator
Using the built-in `app_generator.py` tool, ARIA can automatically generate local custom GUI applications, shell scripts, and Linux `.desktop` desktop shortcuts on demand for instant executable access.

### 👁️ 3. Optical VLM Camera Perception & Face Recognition
Connects to USB camera devices (`/dev/video0`) to perform real-time YuNet face detection & feature matching (recognizing Philip) alongside local `Cosmos-Reason2-2B` VLM visual scene understanding and live screenshot analysis.

### 📚 4. Cloud Agent NotebookLM & Deep Web Research
Routes complex multi-turn reasoning and research queries through the OpenClaw Cloud Gateway, retrieving notebook knowledge from NotebookLM, performing live web searches, and rendering comparison tables.

### 🧠 5. Local RAG & Jetson Telemetry Monitoring
Performs high-speed vector search against an embedded `ChromaDB` vector store (`./knowledge_base/`) and provides real-time voice updates on CPU, RAM, GPU utilization, and Orin Nano thermals.

---

## 🌟 Technical Stack & Architecture Division

| Layer | System / Tool | Technology Stack | Functional Capabilities |
| :--- | :--- | :--- | :--- |
| **Local VLM Core** | Voice & Vision Engine | `Cosmos-Reason2-2B-Q4_K_M` (`llama-server`) | Voice conversations, live camera perception (`/dev/video0`), desktop screenshot VLM inspection. |
| **Local RAG** | Vector Memory | `ChromaDB` / `app/rag.py` | Local domain knowledge base querying markdown documentation in `./knowledge_base/`. |
| **System Telemetry**| Diagnostics Engine | `psutil` / `app/tools/cursor_control.py` | Real-time monitoring of CPU, RAM, GPU load, and Jetson Orin Nano thermals. |
| **Face Recognition**| Optical Perception | `YuNet` ONNX + OpenCV | Face tracking and biometric identification for Philip. |
| **Short-Term Memory**| Rolling History Buffer | Python Deque Buffer (`assistant.py`) | Preserves multi-turn conversation state across local & cloud turns. |
| **Long-Term Memory**| Permanent Profile | `user_profile.md` + ChromaDB | Stores permanent user background, preferences, and project details. |
| **Cloud Agent** | OpenClaw Gateway | OpenClaw / Groq LLMs | Multi-step agentic execution, NotebookLM queries, and cloud tasks. |
| **Desktop Automation**| GUI Cursor Agent | `PyAutoGUI` / `python-xlib` | Mouse cursor navigation, YouTube video thumbnail clicking, scrolling, typing. |
| **App Generator** | Desktop Creator Tool | `app/tools/app_generator.py` | Spawns custom Tkinter/Python apps and generates `.desktop` shortcuts. |
| **Code & Shell Runner**| Code Execution | `x-terminal-emulator` / Subprocess | Autonomous creation and execution of Python scripts and terminal commands. |
| **Voice Pipeline** | STT & TTS | `faster-whisper` + `Kokoro-ONNX` | Ultra-fast GPU transcription + natural CPU speech synthesis with WebRTC AEC. |

---

## 📊 System Workflow Architecture

```mermaid
graph TD
    %% Inputs
    Mic((🎙️ USB Microphone)) --> VAD[Silero VAD\nCPU]
    Cam((📷 USB Camera /dev/video0)) --> FaceRec[YuNet Face Recognition\nCPU]
    
    %% Audio & Vision Pipeline
    VAD -- Speech Detected --> STT[faster-whisper\nGPU CUDA]
    STT -- Transcript --> App{assistant.py\nMain Orchestrator}
    FaceRec -- "Recognized User (Philip)" --> App
    Cam -- Live Frame --> App
    
    %% Memory Layer
    App <--> ShortMem[(Short-Term Memory\nRolling Chat Deque)]
    App <--> LongMem[(Long-Term Memory\nLocal RAG ChromaDB)]
    
    %% Semantic Router
    App -- Query + Context --> Router{Semantic Router\napp/llm.py}
    
    %% Routing Paths
    Router -- "Voice / Vision / RAG / Telemetry" --> LocalVLM[Local VLM & Telemetry\nCosmos-Reason2-2B]
    Router -- "Complex / NotebookLM / Automation" --> CloudAgent[OpenClaw Cloud Gateway\nGroq / Node.js 24]
    
    %% Cloud Agent Tools
    CloudAgent -- NotebookLM Queries --> NotebookLM[NotebookLM API / Integration]
    CloudAgent -- GUI Cursor Automation --> Cursor[Desktop Cursor Agent\napp/tools/cursor_control.py]
    CloudAgent -- App Generator --> AppGen[App Generator Agent\napp/tools/app_generator.py]
    CloudAgent -- Code & Terminal Exec --> Term[Python & Shell Agent\nx-terminal-emulator]
    CloudAgent -- Web Research --> Web[Web Search Agent\nxdg-open / Web Search]
    
    %% Outputs
    LocalVLM -- Speech Response --> TTS[Kokoro TTS\nCPU ONNX]
    CloudAgent -- Action Response --> TTS
    Cursor -- Action Completed --> TTS
    AppGen -- Shortcut Created --> TTS
    
    TTS -- Audio Stream --> Speaker((🔊 Speaker / AEC WebRTC))
```

---

## ⚡ Hardware Architecture & AI Models Symphony

### 1. 🧠 NVIDIA Jetson Orin Nano Architecture (Edge AI Hardware)
The **NVIDIA Jetson Orin Nano (8GB / 67 TOPS)** is a pocket supercomputer engineered specifically for **Physical & Edge AI**. Rather than relying on cloud latency, ARIA processes real-time multimodal workloads directly on the hardware:

* **Unified Memory Architecture (UMA):** Unlike desktop PCs with separate CPU & GPU VRAM pools, the Jetson shares **8GB LPDDR5 RAM** directly between the CPU and GPU with a fast **102 GB/s bandwidth**. This eliminates data transfer overhead over PCIe buses.
* **Dynamic Power Efficiency (`nvpmodel`):** Hardware power draw can be dynamically scaled using `nvpmodel` from maximum performance (25W) down to battery-friendly modes (7W or 15W).
* **Memory Optimization Stack:** Utilizes headless Linux execution paired with a **16GB NVMe SSD Swap file** to ensure memory stability under heavy multimodal workloads.

---

### 2. 🔀 CPU & GPU Functional Processing Division

| Processing Unit | Hardware Cores | Primary AI & System Responsibilities |
| :--- | :--- | :--- |
| **CPU (Central Processing Unit)** | **6-core ARM Cortex-A78AE** | Runs Ubuntu OS, network pipelines, **Silero VAD** (32ms audio chunking), **YuNet** face detection, and **Kokoro-ONNX** text-to-speech synthesis (CPU-offloaded to preserve VRAM). |
| **GPU (Graphics Processing Unit)** | **1024-core Ampere GPU + 32 Tensor Cores** | Handles massive parallel matrix multiplications, **`faster-whisper`** GPU CUDA STT (via CTranslate2 INT8), and **`Cosmos-Reason2-2B`** VLM scene perception & spatial reasoning. |

---

### 3. 🌌 The Cosmos Vision-Language Models (Physical AI)
NVIDIA's **Cosmos-Reason2** family provides intuitive spatial reasoning for Physical AI:
* **Deep Physical Reasoning:** Beyond simple image tagging, Cosmos understands temporal and physical relations between objects in physical space.
* **4-bit Quantization (`Q4_K_M`):** Originally requiring 5GB RAM, Cosmos is compressed via INT4 quantization down to **~1.2GB VRAM**, running smoothly alongside the OS and STT pipeline inside Jetson's 8GB Unified Memory.
* **Multimodal Transformer (`mmproj`):** Uses visual projection embeddings to translate camera frames (`/dev/video0`) into token streams for immediate local inference.
* **Massive Context Window:** Capable of handling context windows up to **256,000 tokens**.

---

### 4. 🎭 Multimodal AI Model Symphony
To deliver instant voice and vision feedback, ARIA orchestrates a synchronized ensemble of specialized models:

```
                  ┌─────────────────────────────────────────┐
                  │ 🎙️ Microphone Audio Input                │
                  └────────────────────┬────────────────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         │   Silero VAD (CPU 32ms)   │
                         └─────────────┬─────────────┘
                                       │ Speech Detected
                         ┌─────────────┴─────────────┐
                         │ faster-whisper INT8 (GPU) │
                         └─────────────┬─────────────┘
                                       │ Transcript
   ┌───────────────────────────────────┼───────────────────────────────────┐
   │                                   │                                   │
┌──┴──────────────────────┐ ┌──────────┴───────────┐ ┌─────────────────────┴──┐
│  YuNet Face Rec (CPU)   │ │ Cosmos-Reason2 (GPU) │ │ OpenClaw Gateway (Cloud)│
│  Biometric Identity     │ │ Physical Perception │ │ Agent & Cursor Tools    │
└──┬──────────────────────┘ └──────────┬───────────┘ └─────────────────────┬──┘
   │                                   │                                   │
   └───────────────────────────────────┼───────────────────────────────────┘
                                       │ Response Text
                         ┌─────────────┴─────────────┐
                         │  Kokoro-ONNX TTS (CPU)    │
                         └─────────────┬─────────────┘
                                       │ Audio Stream
                  ┌────────────────────┴────────────────────┐
                  │ 🔊 Speaker Output (WebRTC AEC)           │
                  └─────────────────────────────────────────┘
```

* **`faster-whisper` (GPU STT):** Operates on CUDA GPU using INT8 CTranslate2 quantization, achieving up to **4x speedup** over standard Whisper.
* **`Kokoro-ONNX` (CPU TTS):** High-quality voice synthesis offloaded to CPU to save GPU VRAM. Employs 8-word chunk buffering for seamless, non-stuttering speech output.
* **`Silero VAD` (CPU Attention):** Constantly analyzes audio chunks every 32ms to gate STT processing and eliminate idle CPU/GPU load.
* **`YuNet` (CPU Optical Tracker):** Lightweight computer vision model running on CPU to detect human faces without consuming GPU resources.

---

### 5. 🤖 OpenClaw: 24/7 Agentic Execution Layer
**OpenClaw** operates as a continuous background daemon (Node.js Gateway) providing autonomous agentic capabilities:
* **24/7 Background Agency:** Continuously runs as a system daemon executing background tasks, tool calls, and scheduled Cron jobs.
* **Autonomous Skillset & Tools:** Connects the LLM to local shell execution, desktop GUI cursor navigation, web search engines, Python code execution, and NotebookLM deep research.
* **Messaging Integration:** Supports remote messaging bridges (e.g., Telegram / WhatsApp) to query your Jetson assistant remotely.
* **Hybrid Load Balancing:** Delegates heavy agent reasoning (16k+ prompt tokens) to cloud gateways (e.g., Groq / Llama 3 70B) while keeping voice and vision processing local, ensuring zero latency degradation on the Jetson Orin Nano.

---

## 📂 Repository Structure

```
aria-ai-assistant/
├── app/
│   ├── audio.py                # PyAudio recording & WebRTC AEC processing
│   ├── camera.py               # OpenCV camera capturing & image encoding
│   ├── cli.py                  # CLI user interface & interactive chat
│   ├── config.py               # System environment variables & settings
│   ├── face_detector.py        # YuNet face detector wrapper
│   ├── face_recognition.py     # Biometric face identification & model downloader
│   ├── llm.py                  # Hybrid local/cloud LLM routing & API handling
│   ├── monitor.py              # System load & thermal diagnostics engine
│   ├── pipeline.py             # Audio/Video execution pipeline
│   ├── rag.py                  # ChromaDB vector RAG implementation
│   ├── stt.py                  # GPU faster-whisper speech transcription
│   ├── tts.py                  # Kokoro-ONNX speech synthesizer
│   ├── tts_worker.py           # Async worker for audio playback queue
│   ├── vision_capture.py       # Live screen & webcam image capture
│   ├── web.py                  # Web dashboard UI server (FastAPI/Flask)
│   └── tools/
│       ├── app_generator.py    # Desktop GUI app & .desktop shortcut generator
│       └── cursor_control.py   # PyAutoGUI mouse navigation & screen automation
├── config/
│   └── settings.yaml           # Core system prompts, thresholds & model paths
├── knowledge_base/
│   ├── jetson_orin_nano.md     # Jetson hardware documentation for RAG
│   └── user_profile.md         # Permanent user profile for Philip
├── static/                     # Web dashboard assets, images, & logos
│   ├── aria.png
│   └── index.html              # Modern web control panel UI
├── assistant.py                # Main orchestrator loop
├── launch_aria.sh              # Master launch script for all services
├── create_desktop_shortcut.sh  # Generator for Linux desktop entry
├── run_llama_cpp.sh            # GGUF model runner wrapper
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## ⚙️ Installation & Quick Start

### 1. Prerequisites
- **Hardware:** NVIDIA Jetson Orin Nano (8GB / 67 TOPS) or Linux x86_64 system with CUDA support.
- **OS:** Ubuntu 22.04 LTS / JetPack 6.x.
- **Environment:** Python 3.10+, Node.js 24+, CUDA 12.x, `llama-server`.

### 2. Quick Start
Clone the repository and launch the full ARIA assistant stack:

```bash
# Clone the repository
git clone https://github.com/FilippeZ/aria-ai-assistant.git
cd aria-ai-assistant

# Make scripts executable and launch ARIA
chmod +x launch_aria.sh run_llama_cpp.sh start.sh
./launch_aria.sh
```

### 3. Active Endpoints & Services
When running, ARIA exposes the following local interfaces:

| Service | Address / Port | Description |
| :--- | :--- | :--- |
| **Web Dashboard** | `http://localhost:8090` | Interactive web control panel & status view |
| **OpenClaw Gateway** | `http://localhost:19000` | Cloud agent bridge server |
| **Local LLM API** | `http://localhost:8080` | Local `llama-server` GGUF endpoint |

---

## 🗣️ Voice Commands & Example Prompting

### 🔹 Local Diagnostic & Vision Queries
- *"Aria, system status"* → Returns real-time CPU/GPU load, RAM usage, and temperatures.
- *"Aria, what is on my screen right now?"* → Takes desktop screenshot and analyzes contents with VLM.
- *"Aria, who am I?"* → Recognizes Philip via face perception and local user profile RAG.

### 🔹 Cloud Agent & Desktop Automation
- *"Aria, open YouTube and search for Jetson Orin Nano tutorials"* → Controls browser and mouse cursor autonomously.
- *"Aria, create a desktop app for calculating fast Fourier transforms"* → Generates Python GUI app and desktop launcher icon.
- *"Aria, use NotebookLM to analyze my research notes on neural interfaces"* → Queries NotebookLM and returns a structured comparison table.

## 🇬🇷 Σύνδεση με τη Θεωρία του AI Engineering & Hardware Setup

### 1.0 Σύνδεση με τη θεωρία του AI Engineering
Το project Aria δεν αποτελεί απλώς μια πρακτική κατασκευή, αλλά εφαρμόζει βασικές αρχές της θεωρίας του AI Engineering. Η ανάπτυξή του ακολουθεί τη λογική **Product → Data → Model**: πρώτα δημιουργείται ένα λειτουργικό πρωτότυπο που λύνει ένα πραγματικό πρόβλημα αλληλεπίδρασης ανθρώπου-μηχανής και στη συνέχεια γίνονται επιλογές μοντέλων, βελτιστοποιήσεις και τεχνικές προσαρμογές ανάλογα με τους περιορισμούς του συστήματος.

Η θεωρία του **AI Stack** εμφανίζεται ξεκάθαρα στην αρχιτεκτονική της Aria. Στο επίπεδο της υποδομής υπάρχουν το Jetson Orin Nano, η GPU, η CPU, η ενιαία μνήμη και ο NVMe SSD. Στο επίπεδο ανάπτυξης μοντέλων εφαρμόζονται τεχνικές όπως ο κβαντισμός, η επιλογή μικρών μοντέλων και η κατανομή φόρτου μεταξύ CPU και GPU. Στο επίπεδο ανάπτυξης εφαρμογής εντάσσονται η διεπαφή χρήστη, το Web UI, το voice pipeline, η αναγνώριση προσώπων και η αλληλεπίδραση σε πραγματικό χρόνο.

Ιδιαίτερα σημαντική είναι η σύνδεση με τη θεωρία της **βελτιστοποίησης inference**. Επειδή τα edge devices έχουν περιορισμένη μνήμη και υπολογιστικούς πόρους, η Aria εφαρμόζει πρακτικές όπως 4-bit quantization, χρήση int8 στο Speech-to-Text, GPU offloading μέσω llama.cpp, CPU execution για το TTS, χρήση swap σε NVMe και προθέρμανση μοντέλων. Αυτές οι επιλογές συνδέονται άμεσα με τη θεωρητική ανάγκη για χαμηλό latency, χαμηλή κατανάλωση πόρων και αξιόπιστη τοπική εκτέλεση σε συσκευές edge.

Τέλος, η Aria εφαρμόζει στην πράξη την έννοια των **multimodal foundation models**, καθώς συνδυάζει ομιλία, κείμενο, εικόνα και αναγνώριση προσώπου σε ένα ενιαίο σύστημα. Με αυτόν τον τρόπο, το project λειτουργεί ως case study που δείχνει πώς η θεωρία των foundation models, του AI Stack, της βελτιστοποίησης inference και του edge deployment μετατρέπεται σε πραγματικό AI προϊόν.

### 1.1 Hardware Platform: NVIDIA Jetson Orin Nano
Το Jetson Orin Nano είναι ένας υπερυπολογιστής "edge AI", κατασκευασμένος για να εκτελεί τοπικά βαριά μοντέλα μηχανικής μάθησης, χωρίς να απαιτείται εξάρτηση από το cloud.

#### 1.1.1 Βασικά χαρακτηριστικά υλικού
* **Επεξεργαστής (CPU):** Διαθέτει έναν 6-πύρηνο επεξεργαστή Arm Cortex-A78AE v8.2 64-bit. Η CPU είναι ο κεντρικός "εγκέφαλος" του υπολογιστή που αναλαμβάνει τις γενικές και πολύπλοκες διεργασίες. Το γεγονός ότι διαθέτει 6 πυρήνες, σημαίνει ότι μπορεί να εκτελεί ταυτόχρονα 6 διαφορετικές, "βαριές" εντολές χωρίς να κολλάει. *(Αναλογία: Φαντάσου την CPU σαν ένα επιβατικό jumbo jet. Ευέλικτη και ταχύτατη.)*
* **Κάρτα Γραφικών (GPU):** Βασίζεται στην αρχιτεκτονική NVIDIA Ampere, με 1024-core GPU και 32 Tensor Cores. Ενώ η CPU έχει λίγους αλλά "έξυπνους" πυρήνες, η GPU διαθέτει χιλιάδες σχεδιασμένους για παράλληλη επεξεργασία (parallel processing). Οι **Tensor Cores** είναι απόλυτα εξειδικευμένοι σχεδιασμένοι αποκλειστικά για τον πολλαπλασιασμό πινάκων (matrices), δίνοντας τη δυνατότητα για inference σε πραγματικό χρόνο. *(Αναλογία: Η GPU είναι ένα τεράστιο cargo ship μεταφοράς εμπορευματοκιβωτίων.)*
* **Μνήμη (RAM):** 8GB LPDDR5 (128-bit) με πολύ υψηλό εύρος ζώνης στα 102 GB/s. Αυτή η τεράστια ταχύτητα αποτρέπει το "μποτιλιάρισμα" δεδομένων.
* **Επιδόσεις AI:** Η πλακέτα αποδίδει έως και 67 TOPS (Tera Operations Per Second), εξασφαλίζοντας ότι τα AI μοντέλα ανταποκρίνονται σε πραγματικό χρόνο.

### 1.2 Αγορά και εγκατάσταση υλικού
Το Jetson Orin Nano δεν διαθέτει ενσωματωμένο αποθηκευτικό χώρο (eMMC), αλλά επεκτείνεται μέσω εξωτερικών μέσων για μέγιστη ταχύτητα.

<div align="center">
  <img src="static/hardware_setup_1.jpg" alt="Hardware Setup of ARIA" width="400" style="border-radius: 10px; margin: 10px;">
  <img src="static/hardware_setup_2.jpg" alt="Hardware Components of ARIA" width="400" style="border-radius: 10px; margin: 10px;">
</div>

1. **Αρχική Εγκατάσταση (MicroSD):** 
   * **SANDISK 256GB Extreme microSDXC & UGREEN SD Card Reader (USB 3.0):** Για την πρώτη εκκίνηση, το "image" του OS φλασαρίστηκε εδώ.
2. **Κύριος Αποθηκευτικός Χώρος (NVMe SSD):** 
   * **SK hynix Platinum P41 1TB PCIe NVMe Gen4:** Το πρωτόκολλο NVMe επιτρέπει στον δίσκο να επικοινωνεί απευθείας με τον επεξεργαστή. Σε αυτόν τον δίσκο εγκαταστάθηκε το Ubuntu, το NVIDIA JetPack SDK και τα Docker containers, και το σύστημα κάνει boot από εδώ.
3. **Προβολή και Συνδεσιμότητα:** 
   * **Καλώδιο SWITCHFLUX DisplayPort 1.4 σε HDMI 2.1:** Η πλακέτα παράγει εικόνα αποκλειστικά μέσω θύρας DisplayPort. Το καλώδιο τη μετατρέπει σε HDMI για τη σύνδεση σε συμβατικές οθόνες.

### 1.3 Πρόκληση ενιαίας μνήμης και διαχείριση πόρων
Το Jetson Orin Nano αξιοποιεί μια αρχιτεκτονική Ενιαίας Μνήμης (Unified Memory). Αυτό σημαίνει ότι οι 6 πυρήνες της CPU και οι 1024 πυρήνες της GPU μοιράζονται την ίδια «δεξαμενή» των 8GB RAM. Το Ubuntu δεσμεύει μέρος της, αφήνοντας ~3,5GB με 4GB για τα AI μοντέλα. Η ταυτόχρονη εκτέλεση LLM, STT, TTS, και Face Rec μπορεί να οδηγήσει σε Out-Of-Memory (OOM) Killer.

**Πώς η "Aria" λύνει το πρόβλημα αξιοποιώντας το Hardware:**
1. **NVMe SSD & 16GB Swap:** Η Aria δημιουργεί 16GB εικονικής μνήμης (Swap) πάνω στον υπερ-γρήγορο NVMe Gen4 SSD της SK hynix. Η μεταφορά δεδομένων μεταξύ της RAM και του δίσκου γίνεται αστραπιαία.
2. **Αυστηρός Διαχωρισμός (Load Balancing) CPU και GPU:** Τα πιο ελαφριά μοντέλα —όπως το TTS (Kokoro) ή ο YuNet— ανατίθενται αποκλειστικά στην CPU, αφήνοντας την GPU να διαχειριστεί το πιο βαρύ έργο (LLM και STT).

### 1.4 Αρχιτεκτονική λογισμικού της Aria

* **1.4.1 Εγκέφαλος (Vision & Reasoning):** 
  * **Μοντέλο:** Cosmos-Reason2-2B-Q4_K_M (GPU)
  * **Βελτιστοποίηση:** 4-bit Quantization (K-quants). Το μέγεθος μειώνεται από ~5GB σε 1,2GB. Το llama.cpp (NGL=999) τρέχει αποκλειστικά στην Ampere GPU για Time-To-First-Token 0.3s. Με χρήση multimodal projector (mmproj) αναλύει pixels της κάμερας σε tokens.
* **1.4.2 Ακοή (Speech-to-Text):** 
  * **Μοντέλο:** faster-whisper small (GPU)
  * **Βελτιστοποίηση:** Τρέχει αναγκαστικά στην GPU, επειδή το CTranslate2 έχει ένα γνωστό SGEMM bug με τους ARM64 Cortex-A78AE (CPU), που θα οδηγούσε σε σιωπηλή αποτυχία πολλαπλασιασμού πινάκων.
* **1.4.3 Φωνή (Text-to-Speech):** 
  * **Μοντέλο:** Kokoro ONNX - af_sarah (CPU)
  * **Βελτιστοποίηση:** Σώζει 1.5GB VRAM. Απομονώνεται σε ξεχωριστό subprocess (worker) λόγω GPL Isolation. Χρησιμοποιεί buffering (8 λέξεις) για ομαλή ροή (αποφυγή stuttering).
* **1.4.4 Προσοχή (Voice Activity Detection):** 
  * **Μοντέλο:** Silero VAD (CPU)
  * **Βελτιστοποίηση:** Αναλύει τον ήχο σε chunks των 32ms σε 1ms χρόνο. Συνδυάζεται με WebRTC AEC για ακύρωση της ηχούς.

### 1.5 Ανάλυση εξαρτημάτων λογισμικού
Η δομή του φακέλου `app/` πετυχαίνει απόλυτη εξισορρόπηση φορτίου (load balancing):
* **`assistant.py`:** Ο κεντρικός μαέστρος που τρέχει τηλεμετρία (`_stats_thread`), διαχείριση κάμερας (`_frame_thread`), και προληπτικό χαιρετισμό (`_face_monitor_thread`).
* **`app/pipeline.py`:** Διαχείριση ακύρωσης ηχούς (AEC / WebRTC) και ομαλής ροής (`stream_and_speak`).
* **`app/stt.py`:** Τρέχει προθέρμανση (Warmup) στέλνοντας ένα άδειο αρχείο ήχου στους CUDA cores για να αποφευχθεί το initial lag.
* **`app/tts_worker.py`:** Ανεξάρτητη διεργασία (GPL Isolation) που χρησιμοποιεί CPUExecutionProvider.
* **`app/llm.py` & `run_llama_cpp.sh`:** Απόλυτη χρήση GPU (NGL=999) και Multimodal Streaming.
* **`app/face_recognition.py`:** Χρησιμοποιεί Downscaling (640 pixels πλάτος) για να "τεντώνει" αστραπιαία τα αποτελέσματα του YuNet στην CPU χωρίς να φρενάρει το σύστημα.
* **`app/web.py`:** WebSocket Broadcaster σε FastAPI (port 8090) για ζωντανά δεδομένα χωρίς refresh.

---

## 📄 License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for full details.

---

<div align="center">

**Developed with ❤️ by [Philip (FilippeZ)](https://github.com/FilippeZ)**

</div>
