import chromadb
import json
import os
import hashlib
from datetime import datetime

# --- CONFIGURATION ---
PERSIST_DIR = "memory_db"  # Where the database lives on your hard drive
LOG_FILE = "session_logs.jsonl"
PROJECT_ROOT = "../"  # Scan the root of your project

# Files to Index (Codebase Knowledge)
WATCH_EXTENSIONS = {".py", ".md", ".txt", ".js", ".html", ".css", ".json"}
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


def get_file_hash(content):
    """Creates a unique ID for a file based on its content."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def setup_database():
    """Initializes the Vector Database."""
    client = chromadb.PersistentClient(path=PERSIST_DIR)

    # Collection 1: Episodic Memory (Chat History)
    episodic = client.get_or_create_collection(name="episodic_memory")

    # Collection 2: Semantic Knowledge (Codebase)
    semantic = client.get_or_create_collection(name="semantic_knowledge")

    return episodic, semantic


def consolidate_chat_logs(collection):
    """Reads session_logs.jsonl and stores them in vector DB."""
    if not os.path.exists(LOG_FILE):
        print("   [Sleep: No session logs found. Skipping.]")
        return

    print("   [Sleep: Consolidating Episodic Memories...]")

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = [json.loads(line) for line in f]

    # Batch process
    ids = []
    documents = []
    metadatas = []

    for i, entry in enumerate(logs):
        # Create a unique ID for this specific chat line
        doc_id = f"log_{entry['timestamp']}_{i}"

        # Check if already exists (naive check, usually DB handles duplicates but this saves processing)
        # For simplicity in this v1, we just try to add everything. Chroma handles dupes by ID.

        ids.append(doc_id)
        documents.append(f"{entry['role']}: {entry['content']}")
        metadatas.append(
            {"timestamp": entry["timestamp"], "role": entry["role"], "type": "chat_log"}
        )

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"   [Sleep: Stored {len(ids)} chat interactions.]")


def index_project_files(collection, root_path):
    """Scans the codebase and indexes it for Long Term Knowledge."""
    print(f"   [Sleep: Indexing Project Files in {root_path}...]")

    ids = []
    documents = []
    metadatas = []

    count = 0
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            _, ext = os.path.splitext(file)
            if ext in WATCH_EXTENSIONS:
                file_path = os.path.join(root, file)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Skip empty or massive files
                    if not content.strip() or len(content) > 50000:
                        continue

                    # ID is the file path
                    doc_id = file_path

                    ids.append(doc_id)
                    documents.append(content)
                    metadatas.append(
                        {"source": "file_system", "path": file_path, "filename": file}
                    )
                    count += 1
                except Exception:
                    continue

    if ids:
        # Upsert: Updates if exists, Inserts if new
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"   [Sleep: Indexed {count} source code files.]")


def run_sleep_cycle():
    print("--- INITIATING SLEEP CYCLE (SYSTEM 2) ---")

    episodic_db, semantic_db = setup_database()

    # 1. Process Chat Logs
    consolidate_chat_logs(episodic_db)

    # 2. Process Codebase
    # We navigate up one level from 'core' to 'apeiron' root
    project_root = os.path.abspath(os.path.join(os.getcwd(), PROJECT_ROOT))
    index_project_files(semantic_db, project_root)

    print("--- SLEEP CYCLE COMPLETE. MEMORY CONSOLIDATED. ---")


if __name__ == "__main__":
    run_sleep_cycle()
