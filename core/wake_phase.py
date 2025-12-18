import ollama
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
TEXT_MODEL = "llama3"
VISION_MODEL = "llava"
LOG_FILE = "session_logs.jsonl"
CONTEXT_LIMIT = 10  # Keep last 10 exchanges to save memory

# --- THE APEIRON SYSTEM PROMPT ---
# This defines the "Intuition Engine" persona.
SYSTEM_PROMPT = """
You are SYSTEM 1 (NEURAL INTUITION) of Project Apeiron.
Your goal is to generate hypotheses, patterns, and raw content.
You are NOT the final decision maker. You provide options.
1. Be concise and high-entropy (creative).
2. If asked for a plan, provide it in steps.
3. Do not adhere to social pleasantries; focus on the data.
"""

def log_interaction(role, content, image_path=None):
    """Saves to episodic memory."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "content": content,
        "image_context": image_path
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def analyze_image(image_path, prompt):
    """Switches to the Vision Model (Llava) for image tasks."""
    print(f"   [Eye Opening: Analyzing {os.path.basename(image_path)}...]")
    res = ollama.generate(model=VISION_MODEL, prompt=prompt, images=[image_path])
    return res['response']

def wake_system():
    print(f"--- PROJECT APEIRON: SYSTEM 1 ONLINE ---")
    print(f"--- Text: {TEXT_MODEL} | Vision: {VISION_MODEL} ---")
    print("Commands: Type 'exit' to sleep. Type 'img:[path]' to see.")

    # Initialize Context with the System Prompt
    conversation_history = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    while True:
        user_input = input("\nUSER: ").strip()
        
        # Shutdown Command
        if user_input.lower() in ["exit", "quit", "sleep"]:
            print("--- MEMORY DUMPING TO LOGS... SLEEPING ---")
            break
        
        image_path = None
        current_response = ""

        # Vision Handling
        if user_input.startswith("img:"):
            # Format: img:/path/to/image.png Explain this chart
            parts = user_input.split(" ", 1)
            image_path = parts[0].replace("img:", "").strip()
            # Remove quotes if drag-and-drop added them
            image_path = image_path.replace("'", "").replace('"', "")
            
            prompt_text = parts[1] if len(parts) > 1 else "Describe this image."
            
            if os.path.exists(image_path):
                # Switch to Vision Model
                response_content = analyze_image(image_path, prompt_text)
                print(f"APEIRON (Vision): {response_content}")
                
                # Log the vision event
                log_interaction("user", f"[Image: {image_path}] {prompt_text}", image_path)
                log_interaction("assistant", response_content, image_path)
                
                # Add vision insight to text history so Llama 3 knows what was seen
                conversation_history.append({'role': 'user', 'content': f"I just showed you an image. Analysis: {response_content}"})
                continue
            else:
                print("   [System Error: Image path not found]")
                continue

        # Text Handling (Llama 3)
        log_interaction("user", user_input)
        conversation_history.append({'role': 'user', 'content': user_input})
        
        # Sliding Window Context (Keep System Prompt + Last N messages)
        if len(conversation_history) > CONTEXT_LIMIT:
            # Keep index 0 (System) and slice the end
            active_context = [conversation_history[0]] + conversation_history[-(CONTEXT_LIMIT-1):]
        else:
            active_context = conversation_history

        print("APEIRON: ", end="", flush=True)
        stream = ollama.chat(model=TEXT_MODEL, messages=active_context, stream=True)

        for chunk in stream:
            part = chunk['message']['content']
            print(part, end="", flush=True)
            current_response += part
        print()

        log_interaction("assistant", current_response)
        conversation_history.append({'role': 'assistant', 'content': current_response})

if __name__ == "__main__":
    wake_system()
