import json
import subprocess
import os
import re
from langchain_ollama import OllamaLLM

# Initialize LLM
llm = OllamaLLM(model="llama3")


# -------------------- UTIL --------------------

def safe_path(path):
    """Ensure path is always relative"""
    if not path:
        return "output.txt"
    if path.startswith("/"):
        path = "." + path
    return path


# -------------------- TOOLS --------------------

def run_command(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode()
    except subprocess.CalledProcessError as e:
        return e.output.decode()


def read_file(path):
    try:
        path = safe_path(path)
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path, content):
    try:
        path = safe_path(path)

        dir_name = os.path.dirname(path)

        # Fix: only create directory if it exists
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(path, "w") as f:
            f.write(content)

        return f"File written successfully at {os.path.abspath(path)}"
    except Exception as e:
        return f"Error writing file: {e}"


# -------------------- JSON CLEANER --------------------

def clean_json(response):
    """Attempt to fix common LLM JSON mistakes"""
    cleaned = response.strip()

    # Remove triple quotes
    cleaned = re.sub(r'"""', '"', cleaned)

    # Remove trailing commas
    cleaned = re.sub(r',\s*}', '}', cleaned)

    # Replace smart quotes if any
    cleaned = cleaned.replace("“", '"').replace("”", '"')

    return cleaned


# -------------------- AGENT --------------------

def agent(prompt):
    system_prompt = f"""
You are a coding agent.

Respond ONLY in valid JSON.

STRICT RULES:
- Do NOT use triple quotes
- Escape newlines with \\n
- Always use relative paths (no leading /)
- If no folder is needed, just use filename (e.g., hello.c)
- Do NOT include explanations

FORMAT:
{{
 "action": "run|read|write|none",
 "command": "",
 "path": "",
 "content": ""
}}

User request: {prompt}
"""

    response = llm.invoke(system_prompt)

    print("\nLLM RAW OUTPUT:\n", response)

    # -------------------- PARSE JSON --------------------

    try:
        data = json.loads(response)
    except:
        print("❌ JSON parse failed, attempting fix...")
        try:
            cleaned = clean_json(response)
            data = json.loads(cleaned)
        except:
            print("❌ Still failed to parse JSON")
            print("RAW OUTPUT:\n", response)
            return

    # -------------------- EXECUTE --------------------

    action = data.get("action")

    if action == "run":
        print(run_command(data.get("command", "")))

    elif action == "write":
        print(write_file(data.get("path", ""), data.get("content", "")))

    elif action == "read":
        print(read_file(data.get("path", "")))

    else:
        print("No action taken")


# -------------------- LOOP --------------------

if __name__ == "__main__":
    while True:
        user_input = input("\n>>> ")
        agent(user_input)
