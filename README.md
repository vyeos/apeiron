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
* **Hardware:** Mac.
* **System Python:** Python 3.11
* **Package Manager:** Poetry.

### Step 1: Install System Dependencies
```bash
brew install python@3.11
brew install poetry
brew install ollama
ollama serve &  # Run in background
```

### Step 2: pull the required models:
```bash
ollama run llama3
ollama run llava
```

### Step 3: Setup the Python Environment
```bash
cd apeiron
poetry env use python3.11
poetry install
```

## 4. Operational Workflow (The Daily Loop)

You have two ways to run the system: Automated Loop or Manual Control.

### Option A: The Automated Loop (Recommended)
We have a shell script that handles the Wake/Sleep cycle automatically.

1. Run the script:
    ```bash

    ./run.sh
    ```
2. Interact: Work, code, and chat.

3. Finish: Type exit. The script will automatically trigger the Sleep Phase and consolidate your memories.

### Option B: Manual Control

1. Morning: Wake the System

```bash
poetry run python core/wake_phase.py
```

Connect Eyes: Type watch: and drag your working folder into the terminal.

2. During the Day: Collaboration

- Ask: "Explain the authentication logic in auth.py."
- Edit: The system sees every save instantly.
- Recall: "recall: What did we decide about the database schema?"

3. Evening: Sleep & Consolidate

- Type sleep to shut down the agent gracefully.
- Run the consolidation script:

```bash
poetry run python core/sleep_phase.py
```

## 5. Command Reference

Interactive Commands (Inside Wake Phase)
- watch:[path] --- The Optic Nerve. Connects the AI to a local folder. Watches for real-time file changes. --- watch: /Users/me/Projects/Apeiron

- recall:[query] --- The Hippocampus. Searches Long-Term Memory (ChromaDB) for past chats or code. --- recall: python preference

- img:[path] --- The Retina. Switches to the Vision Model to analyze an image. --- img: /Users/me/Desktop/diagram.png

- sleep --- Shutdown. Saves logs and exits. --- sleep, exit, or quit


### System Commands (Terminal)

- poetry run python [script] - Runs a specific phase inside the environment.
- poetry shell - Spawns a shell inside the virtual environment (persistently).
- poetry add [package] - Installs a new library (replacing pip install).
- ollama serve - Starts the local LLM server (Background).

## 6. Project Configuration (pyproject.toml)

Your configuration file currently looks like this:

```toml
[project]
name = "apeiron"
version = "0.1.0"
description = "McNS-OS Local Implementation"
authors = [{name = "The World Runner"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "ollama",
    "chromadb",
    "watchdog"
]

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
```

## 7. Project Structure

```text
apeiron/
├── pyproject.toml       # Project Configuration & Dependencies
├── poetry.lock          # Dependency Lockfile
├── run_apeiron.sh       # Automation Script (Loop)
├── memory_db/           # ChromaDB (Long-Term Memory Storage)
├── session_logs.jsonl   # Raw Daily Logs (Episodic Memory)
├── core/
│   ├── wake_phase_v4.py # SYSTEM 1: Interaction & Reflexes
│   └── sleep_phase.py   # SYSTEM 2: Memory & Indexing
└── README.md            # This Manual
```
