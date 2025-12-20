import ollama
import json
import os
import chromadb
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- IMPORTS FROM MODULES ---
try:
    from core.logic_gate import validate_schedule_logic
    from core.motor_cortex import write_file_action, run_shell_action
except ImportError:
    from logic_gate import validate_schedule_logic
    from motor_cortex import write_file_action, run_shell_action

# --- CONFIGURATION ---
TEXT_MODEL = "llama3"
LOG_FILE = "session_logs.jsonl"
MEMORY_DB_DIR = "memory_db"

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
    ".toml",
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
# We use an Ephemeral Chroma Client for live, fast, RAM-only search
LIVE_VECTOR_DB = chromadb.Client()
LIVE_COLLECTION = None

# We keep a simple list of paths so the AI knows the folder structure
PROJECT_FILE_TREE = set()

# Long term memory buffer
LONG_TERM_MEMORY = []

# --- PROMPTS ---
STANDARD_PROMPT = """
You are THE WORLD RUNNER (System 1 of Project Apeiron).
You have access to:
1. [PROJECT STRUCTURE]: The full list of files in the folder.
2. [RELEVANT FILES]: The specific file contents most relevant to the user's last query.
Goal: Provide accurate, technical, and context-aware answers.
"""

PLANNER_PROMPT = """
You are the LOGIC ARCHITECT.
Format: {"task": "string", "start_time": int (0-2400), "end_time": int (0-2400)}
Example: {"task": "Coding", "start_time": 900, "end_time": 1700}
DO NOT write markdown or explanations. Just the JSON object.
"""

AGENT_PROMPT = """
You are an AUTONOMOUS AGENT.
Format:
[
  {"action": "write", "path": "filename.py", "content": "print('hello')"},
  {"action": "run", "command": "python filename.py"}
]
IMPORTANT: Output ONLY the JSON list. No markdown.
"""


# --- MODULE: LIVE WATCHER (SMART RAG) ---
class ProjectWatcher(FileSystemEventHandler):
    def __init__(self, target_path):
        self.target_path = target_path
        self.is_dir_watch = os.path.isdir(target_path)
        self.abs_target = (
            os.path.abspath(target_path) if not self.is_dir_watch else None
        )

    def is_valid_file(self, file_path):
        if any(ignore in file_path.split(os.sep) for ignore in IGNORE_DIRS):
            return False
        _, ext = os.path.splitext(file_path)
        return ext in WATCH_EXTENSIONS

    def on_modified(self, event):
        if event.is_directory:
            return
        if not self.is_dir_watch and os.path.abspath(event.src_path) != self.abs_target:
            return

        if self.is_valid_file(event.src_path):
            update_live_memory(event.src_path)
            print(f"\n   [Reflex: Re-indexed {os.path.basename(event.src_path)}]")

    def on_created(self, event):
        if (
            not event.is_directory
            and self.is_dir_watch
            and self.is_valid_file(event.src_path)
        ):
            update_live_memory(event.src_path)
            print(f"\n   [Reflex: New File Indexed {os.path.basename(event.src_path)}]")


def update_live_memory(file_path):
    """Reads file and upserts to In-Memory Vector DB."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if len(content) < 100000:  # Increase limit slightly
            # Add to Tree
            PROJECT_FILE_TREE.add(file_path)

            # Add to Vector DB (Upsert handles updates)
            if LIVE_COLLECTION:
                LIVE_COLLECTION.upsert(
                    ids=[file_path],
                    documents=[content],
                    metadatas=[{"filename": os.path.basename(file_path)}],
                )
    except:
        pass


def start_watching(path):
    global LIVE_COLLECTION

    # 1. Reset the Live Collection
    try:
        LIVE_VECTOR_DB.delete_collection("live_working_memory")
    except:
        pass
    LIVE_COLLECTION = LIVE_VECTOR_DB.create_collection("live_working_memory")
    PROJECT_FILE_TREE.clear()

    observer = Observer()

    if os.path.isfile(path):
        print(f"   [System 1: Focused on single file: {os.path.basename(path)}]")
        update_live_memory(path)
        parent_dir = os.path.dirname(path)
        handler = ProjectWatcher(target_path=path)
        observer.schedule(handler, parent_dir, recursive=False)

    elif os.path.isdir(path):
        print(f"   [System 1: Embedding directory: {path} (This may take a moment)...]")

        count = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if file.endswith(tuple(WATCH_EXTENSIONS)):
                    update_live_memory(os.path.join(root, file))
                    count += 1

        print(f"   [System 1: Active Memory Ready. Indexed {count} files.]")
        handler = ProjectWatcher(target_path=path)
        observer.schedule(handler, path, recursive=True)
    else:
        print(f"   [Error: Invalid path: {path}]")
        return None

    observer.start()
    return observer


# --- HELPER: CONTEXT BUILDER (THE OPTIMIZER) ---
def build_smart_context(user_query):
    """
    Selects only the most relevant files from RAM to send to the LLM.
    This fixes the 'slow response' issue by keeping prompts small.
    """
    context = ""

    # 1. Always show the File Tree (Cheap tokens, high situational awareness)
    if PROJECT_FILE_TREE:
        context += "\n=== PROJECT STRUCTURE ===\n"
        # Only show relative paths to save tokens
        cwd = os.getcwd()
        for f in sorted(PROJECT_FILE_TREE):
            try:
                rel = os.path.relpath(f, cwd)
            except:
                rel = os.path.basename(f)
            context += f"- {rel}\n"

    # 2. Retrieve ONLY relevant file contents (Vector Search)
    if LIVE_COLLECTION and PROJECT_FILE_TREE:
        results = LIVE_COLLECTION.query(
            query_texts=[user_query],
            n_results=3,  # Only pick Top 3 files. Adjust if needed.
        )

        if results["documents"]:
            context += "\n=== RELEVANT FILE CONTENTS ===\n"
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                fname = meta["filename"]
                context += f"\n--- {fname} ---\n{doc}\n"

    # 3. Add Long Term Memory if recalled
    if LONG_TERM_MEMORY:
        context += "\n=== RECALLED HISTORY ===\n" + "\n".join(LONG_TERM_MEMORY)

    return context


# --- MODULE: HIPPOCAMPUS (LONG TERM MEMORY) ---
def query_vector_db(query_text, n_results=3):
    try:
        if not os.path.exists(MEMORY_DB_DIR):
            return []
        client = chromadb.PersistentClient(path=MEMORY_DB_DIR)
        results = []
        # Query semantic and episodic collections (same as v6)
        try:
            semantic = client.get_collection("semantic_knowledge")
            res = semantic.query(query_texts=[query_text], n_results=n_results)
            if res["documents"]:
                for i, doc in enumerate(res["documents"][0]):
                    meta = res["metadatas"][0][i]
                    results.append(f"[ARCHIVE: {meta.get('filename')}]\n{doc}")
        except:
            pass
        return results
    except Exception as e:
        return [f"(Memory Error: {str(e)})"]


def extract_json_content(text):
    text = text.strip()
    start = text.find("[")
    end = text.rfind("]") + 1
    if start != -1 and end != -1:
        return text[start:end]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end != -1:
        return text[start:end]
    return text


# --- MAIN EVENT LOOP ---
def wake_system():
    print(f"--- WORLD RUNNER ONLINE (v7 Smart Context) ---")
    print("Commands: watch, recall, plan, achieve, exit")

    observer = None
    conversation_history = [{"role": "system", "content": STANDARD_PROMPT}]

    try:
        while True:
            user_input = input("\nUSER: ").strip()
            if user_input.lower() in ["exit", "quit", "sleep"]:
                break

            # --- ACHIEVE MODE ---
            if user_input.startswith("achieve:"):
                goal = user_input.replace("achieve:", "").strip()
                print(f"   [System 1: Agent Active for '{goal}']")
                agent_msgs = [
                    {"role": "system", "content": AGENT_PROMPT},
                    {"role": "user", "content": f"Goal: {goal}. Generate JSON list."},
                ]

                # We inject smart context here too so the agent knows the code
                smart_context = build_smart_context(goal)
                if smart_context:
                    agent_msgs.insert(1, {"role": "system", "content": smart_context})

                print("   [Thinking...]")
                response = ollama.chat(model=TEXT_MODEL, messages=agent_msgs)
                raw_action_text = extract_json_content(response["message"]["content"])
                try:
                    cleaned_json = (
                        raw_action_text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                    )
                    actions = json.loads(cleaned_json)
                    if isinstance(actions, dict):
                        actions = [actions]
                    for action_data in actions:
                        if action_data["action"] == "write":
                            print(f"   [Write: {action_data['path']}]")
                            success, msg = write_file_action(
                                action_data["path"], action_data["content"]
                            )
                            print(f"   -> {msg}")
                        elif action_data["action"] == "run":
                            print(f"   [Run: {action_data['command']}]")
                            success, msg = run_shell_action(action_data["command"])
                            print(f"   -> Output:\n{msg}")
                except Exception as e:
                    print(f"   [Agent Error: {e}]")
                continue

            # --- PLAN MODE ---
            if user_input.startswith("plan:"):
                task = user_input.replace("plan:", "").strip()
                print(f"   [System 2: Planning '{task}']")
                planner_messages = [
                    {"role": "system", "content": PLANNER_PROMPT},
                    {"role": "user", "content": f"Schedule: {task}"},
                ]
                print("   [Drafting...]")
                response = ollama.chat(model=TEXT_MODEL, messages=planner_messages)
                raw_plan = extract_json_content(response["message"]["content"])
                is_valid, message = validate_schedule_logic(raw_plan)
                if is_valid:
                    print(f"APPROVED: {raw_plan}")
                else:
                    print(f"REJECTED: {message}. Correcting...")
                    # logic correction loop omitted for brevity, same as v6
                continue

            # --- WATCH MODE ---
            if user_input.startswith("watch:"):
                path = (
                    user_input.replace("watch:", "")
                    .strip()
                    .replace("'", "")
                    .replace('"', "")
                )
                if not os.path.exists(path):
                    print(f"   [Error: Path not found]")
                    continue
                if observer:
                    observer.stop()
                observer = start_watching(path)
                continue

            # --- RECALL MODE ---
            if user_input.startswith("recall:"):
                query = user_input.replace("recall:", "").strip()
                memories = query_vector_db(query)
                LONG_TERM_MEMORY.clear()
                LONG_TERM_MEMORY.extend(memories)
                print(f"   [Recall: {len(memories)} records loaded]")
                continue

            # --- STANDARD CHAT ---
            # 1. Build Smart Context based on the CURRENT Query
            smart_context = build_smart_context(user_input)

            msgs = conversation_history.copy()
            if smart_context:
                msgs.insert(-1, {"role": "system", "content": smart_context})
            msgs.append({"role": "user", "content": user_input})

            print("APEIRON: ", end="", flush=True)
            resp = ""
            stream = ollama.chat(model=TEXT_MODEL, messages=msgs, stream=True)
            for chunk in stream:
                part = chunk["message"]["content"]
                print(part, end="", flush=True)
                resp += part
            print()

            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": resp})

            with open(LOG_FILE, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "role": "user",
                            "content": user_input,
                        }
                    )
                    + "\n"
                )
                f.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "role": "assistant",
                            "content": resp,
                        }
                    )
                    + "\n"
                )

            LONG_TERM_MEMORY.clear()

    except KeyboardInterrupt:
        pass
    finally:
        if observer:
            observer.stop()
        print("\n--- SYSTEM SLEEP ---")


if __name__ == "__main__":
    wake_system()
