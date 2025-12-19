# Project Apeiron: The McNS-OS Indie Implementation

> **Version:** 1.0 (Local-First Architecture)  
> **Date:** December 18, 2025  
> **Hardware Target:** Apple Silicon (M1 Pro)  
> **Operator:** The World Runner

---

## 1. Executive Summary

### The Problem
Artificial Intelligence in 2025 has hit a plateau. Standard Large Language Models (LLMs) suffer from:
* **Passivity:** They wait for input rather than acting on goals.
* **Hallucination:** They invent facts due to probabilistic guessing.
* **Digital Amnesia:** They reset their state after every session, preventing long-term learning.

### The Solution
Project Apeiron implements a **Meta-Cognitive Neuro-Symbolic Operating System (McNS-OS)**. Unlike standard chatbots, this system separates "Intuition" (Neural Networks) from "Memory & Logic" (Symbolic Databases), allowing for a grounded, persistent, and active agent that runs locally on consumer hardware.

---

## 2. System Architecture

The system is bifurcated into two distinct phases, mimicking the biological cognitive rhythm:

### Phase 1: The Wake Cycle (System 1)
* **Role:** Intuition, Perception, & Interaction.
* **Engine:** `wake_phase_v4.py`
* **Core Models:**
    * *Text:* Llama 3 (8B) via Ollama.
    * *Vision:* Llava via Ollama.
* **Capabilities:**
    * **Live Reflexes:** Uses watchdog to monitor file system changes in real-time.
    * **Context Injection:** Loads relevant project files into Working Memory dynamically.

### Phase 2: The Sleep Cycle (System 2)
* **Role:** Memory Consolidation & Semantic Indexing.
* **Engine:** `sleep_phase.py`
* **Core Technology:**
    * *Vector Database:* ChromaDB (Local).
* **Capabilities:**
    * **Episodic Memory:** Reads chat logs and stores them for future recall.
    * **Semantic Indexing:** Scans the entire codebase, converting code into vectors to allow the AI to "know" the whole project without loading it all into RAM.

---

## 3. Installation & Setup

### Prerequisites
* **Hardware:** Mac with Apple Silicon (M1/M2/M3).
* **Software:** Python 3.10+, Homebrew.

### Step 1: Install the Neural Engine
```bash
brew install ollama
ollama serve  # (Run in a separate background terminal)
```

### Then, pull the required models:
```bash
ollama run llama3
ollama run llava
```

### Step 2: Setup the Python Environment
```bash
mkdir apeiron
cd apeiron
python3 -m venv venv
source venv/bin/activate
```
### Step 3: Install Dependencies
```bash
pip install ollama chromadb watchdog
pip freeze > requirements.txt
```
## 4. Operational Workflow (The Daily Loop)

Morning: Wake the System

Open your terminal and activate the environment:
```bash
source venv/bin/activate
```

Launch the World Runner agent:
```bash
python3 core/wake_phase_v4.py
```

Connect Eyes: Type watch: and drag your working folder into the terminal.

During the Day: Collaboration
- Ask Questions: "Explain the authentication logic in auth.py."
- Edit Code: The system sees every save instantly.
- Recall History: "recall: What did we decide about the database schema?"

Evening: Sleep & Consolidate

Type sleep to shut down the agent gracefully. Then, run the consolidation script to store memories:
```bash
python3 core/sleep_phase.py
```

Output: 
```text
[Sleep: Stored X chat interactions. Indexed Y source code files.]
```

## 5. Command Reference

Interactive Commands (Inside Wake Phase)
- watch:[path] --- The Optic Nerve. Connects the AI to a local folder. Watches for real-time file changes. --- watch: /Users/me/Projects/Apeiron

- recall:[query] --- The Hippocampus. Searches Long-Term Memory (ChromaDB) for past chats or code. --- recall: python preference

- img:[path] --- The Retina. Switches to the Vision Model to analyze an image. --- img: /Users/me/Desktop/diagram.png

- sleep --- Shutdown. Saves logs and exits. --- sleep, exit, or quit


### System Commands (Terminal)

- ollama serve - Starts the local LLM server (Background).
- source venv/bin/activate - Activates the Python sandbox.
- python3 core/wake_phase_v4.py - Starts the Interactive Agent.
- python3 core/sleep_phase.py - Runs Memory Consolidation.

## 6. Project Structure

```text
apeiron/
├── venv/                   # Python Virtual Environment
├── memory_db/              # ChromaDB (Long-Term Memory Storage)
├── session_logs.jsonl      # Raw Daily Logs (Episodic Memory)
├── requirements.txt        # Package List
├── core/
│   ├── wake_phase_v4.py    # SYSTEM 1: Interaction & Reflexes
│   └── sleep_phase.py      # SYSTEM 2: Memory & Indexing
└── README.md               # This Manual
```
