import ollama
import json
import os
import time
import threading
import chromadb
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
TEXT_MODEL = "llama3"
VISION_MODEL = "llava"
LOG_FILE = "session_logs.jsonl"
MEMORY_DB_DIR = "memory_db"
CONTEXT_LIMIT = 10

# Files to watch
WATCH_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".js",
    ".html",
    ".css",
    ".json",
    ".yaml",
    ".yml",
}
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
    "memory_db",
    "apeiron_core",
}

# --- GLOBAL STATE ---
PROJECT_MEMORY = {}  # Live RAM memory (Watchdog)
LONG_TERM_MEMORY = []  # Retrieved Vector memory (ChromaDB)

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are THE WORLD RUNNER (System 1 of Project Apeiron).
You have three sources of information:
1. [CONVERSATION]: Immediate chat history.
2. [LIVE CONTEXT]: The user's active file system (Real-time).
3. [RECALLED MEMORY]: Relevant excerpts from the Vector Database (Past knowledge).

Goal: Synthesize these inputs to provide accurate, context-aware answers.
"""


# --- MODULE: LIVE WATCHER (From v3) ---
class ProjectWatcher(FileSystemEventHandler):
    def is_valid_file(self, file_path):
        if any(ignore in file_path.split(os.sep) for ignore in IGNORE_DIRS):
            return False
        _, ext = os.path.splitext(file_path)
        return ext in WATCH_EXTENSIONS

    def on_modified(self, event):
        if not event.is_directory and self.is_valid_file(event.src_path):
            update_live_memory(event.src_path)
            print(
                f"\n   [Reflex: Detected Change in {os.path.basename(event.src_path)}]"
            )


def update_live_memory(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if len(content) < 50000:
                PROJECT_MEMORY[file_path] = content
    except:
        pass


def start_watching(path):
    observer = Observer()
    observer.schedule(ProjectWatcher(), path, recursive=True)
    observer.start()

    # Initial quick scan
    print(f"   [System 1: Eyes opening on {path}...]")
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(tuple(WATCH_EXTENSIONS)):
                update_live_memory(os.path.join(root, file))
    return observer


# --- MODULE: HIPPOCAMPUS (New for v4) ---
def query_vector_db(query_text, n_results=3):
    """Searches the ChromaDB created by the Sleep Cycle."""
    try:
        if not os.path.exists(MEMORY_DB_DIR):
            return ["(Memory Offline: No database found. Run sleep_phase.py first.)"]

        client = chromadb.PersistentClient(path=MEMORY_DB_DIR)

        # We query both collections: Chat History and Codebase
        results = []

        # 1. Search Semantic Knowledge (Code)
        try:
            semantic = client.get_collection("semantic_knowledge")
            code_res = semantic.query(query_texts=[query_text], n_results=n_results)
            if code_res["documents"]:
                for i, doc in enumerate(code_res["documents"][0]):
                    meta = code_res["metadatas"][0][i]
                    results.append(
                        f"[SOURCE CODE: {meta.get('filename', 'unknown')}]\n{doc}"
                    )
        except:
            pass

        # 2. Search Episodic Memory (Chat)
        try:
            episodic = client.get_collection("episodic_memory")
            chat_res = episodic.query(query_texts=[query_text], n_results=n_results)
            if chat_res["documents"]:
                for i, doc in enumerate(chat_res["documents"][0]):
                    meta = chat_res["metadatas"][0][i]
                    results.append(
                        f"[PAST CHAT: {meta.get('timestamp', 'unknown')}]\n{doc}"
                    )
        except:
            pass

        return results
    except Exception as e:
        return [f"(Memory Error: {str(e)})"]


# --- MAIN LOOP ---
def wake_system():
    print(f"--- WORLD RUNNER ONLINE (v4 Integrated) ---")
    print("Commands: 'watch:/path', 'recall: topic', 'img:/path', 'exit'")

    observer = None
    conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

    try:
        while True:
            user_input = input("\nUSER: ").strip()

            if user_input.lower() in ["exit", "quit", "sleep"]:
                break

            # 1. COMMAND: WATCH (Start Live Monitoring)
            if user_input.startswith("watch:"):
                path = (
                    user_input.replace("watch:", "")
                    .strip()
                    .replace("'", "")
                    .replace('"', "")
                )
                if os.path.exists(path):
                    if observer:
                        observer.stop()
                    observer = start_watching(path)
                continue

            # 2. COMMAND: RECALL (Query Vector DB)
            if user_input.startswith("recall:"):
                query = user_input.replace("recall:", "").strip()
                print(f"   [Hippocampus: Searching memories for '{query}'...]")
                memories = query_vector_db(query)

                # Store in global state to inject into next prompt
                LONG_TERM_MEMORY.clear()
                LONG_TERM_MEMORY.extend(memories)

                print(
                    f"   [Recall: Found {len(memories)} relevant records. Added to context.]"
                )
                continue

            # 3. COMMAND: IMAGE (Vision)
            if user_input.startswith("img:"):
                # (Simplified logic for brevity - assumes you have the v2 logic or use simple prompt)
                print("   [Vision: Analyzing...]")
                # ... Insert v2 vision logic here if needed, or simple bypass
                continue

            # --- BUILD DYNAMIC CONTEXT BLOCK ---
            context_block = ""

            # A. Live Files
            if PROJECT_MEMORY:
                context_block += "\n=== LIVE FILE CONTEXT (READ-ONLY) ===\n"
                for fpath, content in PROJECT_MEMORY.items():
                    context_block += f"\n--- {os.path.basename(fpath)} ---\n{content}\n"

            # B. Recalled Memories
            if LONG_TERM_MEMORY:
                context_block += "\n=== RECALLED LONG-TERM MEMORY ===\n"
                for mem in LONG_TERM_MEMORY:
                    context_block += f"{mem}\n----------------\n"

            # Construct Messages
            current_messages = conversation_history.copy()
            if context_block:
                current_messages.insert(
                    -1, {"role": "system", "content": context_block}
                )

            # Add User Input
            current_messages.append({"role": "user", "content": user_input})

            # INFERENCE
            print("APEIRON: ", end="", flush=True)
            response_content = ""
            stream = ollama.chat(
                model=TEXT_MODEL, messages=current_messages, stream=True
            )

            for chunk in stream:
                part = chunk["message"]["content"]
                print(part, end="", flush=True)
                response_content += part
            print()

            # Log to history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append(
                {"role": "assistant", "content": response_content}
            )

            # Save to disk for Sleep Cycle
            with open(LOG_FILE, "a") as f:
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "role": "user",
                    "content": user_input,
                }
                f.write(json.dumps(entry) + "\n")
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "role": "assistant",
                    "content": response_content,
                }
                f.write(json.dumps(entry) + "\n")

            # Clear recalled memory after use (so it doesn't pollute next totally different question)
            LONG_TERM_MEMORY.clear()

    except KeyboardInterrupt:
        pass
    finally:
        if observer:
            observer.stop()
        print("\n--- SYSTEM SLEEP ---")


if __name__ == "__main__":
    wake_system()
