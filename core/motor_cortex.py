import os
import subprocess

# --- SAFETY CONFIGURATION ---
ALLOWED_EXTENSIONS = {".py", ".md", ".txt", ".js", ".ts", ".html", ".css", ".json"}
FORBIDDEN_COMMANDS = ["rm", "sudo", "mv", "chmod", "wget", "curl", "ssh", "ftp"]


def is_safe_path(path):
    """Prevents the AI from writing outside the project folder."""
    # Simple check: must not contain '..' and must have valid extension
    if ".." in path:
        return False
    _, ext = os.path.splitext(path)
    return ext in ALLOWED_EXTENSIONS


def write_file_action(path, content):
    """
    ACTION: Writes code to a file.
    Returns: (Success: bool, Message: str)
    """
    if not is_safe_path(path):
        return (
            False,
            f"SAFETY BLOCK: Cannot write to {path} (Invalid extension or path traversal).",
        )

    try:
        # Fix: Only create directories if the path actually has one
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Successfully wrote {len(content)} chars to {path}."
    except Exception as e:
        return False, f"Write Error: {str(e)}"


def run_shell_action(command):
    """
    ACTION: Runs a terminal command (e.g., to run a test).
    Returns: (Success: bool, Output: str)
    """
    # 1. Safety Filter
    cmd_parts = command.split()
    if not cmd_parts:
        return False, "Empty command."

    base_cmd = cmd_parts[0]
    if base_cmd in FORBIDDEN_COMMANDS or any(";" in p or "|" in p for p in cmd_parts):
        return (
            False,
            f"SAFETY BLOCK: Command '{base_cmd}' or chaining operators forbidden.",
        )

    # 2. Execute
    try:
        # We set a timeout so the AI doesn't hang your computer
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr
        return (result.returncode == 0), output.strip()
    except subprocess.TimeoutExpired:
        return False, "Execution Timed Out (10s limit)."
    except Exception as e:
        return False, f"Shell Error: {str(e)}"


# --- TEST HARNESS ---
if __name__ == "__main__":
    print(write_file_action("test_apeiron.txt", "Hello World"))
    print(run_shell_action("echo 'Motor Cortex Online'"))
    print(run_shell_action("rm -rf /"))  # Should be blocked
