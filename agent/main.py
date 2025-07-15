import requests
import subprocess
import re



OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:latest"

BLOCKED = ["rm -rf", "mkfs", "shutdown", "reboot", ":(){", "dd if="]
CATEGORIES = {
    "🧼 Cache/Temp Cleaner": ["cache", "temp", "clean", "clear", "wipe"],
    "📁 File/Folder Ops": ["delete", "move", "copy", "rename", "mkdir", "rmdir"],
    "🔍 Search/Filter": ["find", "grep", "search", "locate", "where"],
    "⚙️ System Info": ["cpu", "memory", "uptime", "disk", "os", "version"],
    "📦 Package Install": ["install", "apt", "yum", "choco", "pip", "brew"],
}
SAFE_REPLACEMENTS = {
    "rm -rf ~/.cache/*": (
        "del /q /s %LOCALAPPDATA%\\Temp\\* 2>nul" 
        if subprocess.os.name == "nt" else "rm -rf ~/.cache/*"
    )
}

def clean_shell_output(text):
    return re.sub(r"```(?:bash)?\n(.*?)```", r"\1", text, flags=re.DOTALL).strip()

def ask_llm(prompt, category):
    full_prompt = (
        f"This is a {category.lower()} task.\n"
        f"Convert this into a safe shell command:\n'{prompt}'\n"
        f"Output only the command. No explanation or markdown."
    )
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": full_prompt,
            "stream": False
        })
        json_data = response.json()

        if "response" not in json_data:
            print("⚠️ Full LLM response:\n", json_data)
            return ""

        return clean_shell_output(json_data["response"])

    except Exception as e:
        print(f"⚠️ Error querying model: {e}")
        return ""

def is_safe(command):
    return not any(term in command for term in BLOCKED)

def run_shell(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        return output
    except subprocess.CalledProcessError as e:
        return e.output
    
def categorize(prompt):
    prompt_lower = prompt.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in prompt_lower for keyword in keywords):
            return category
    return "❓ Unknown"

def main():
    print("🧠 ShellPilot is ready. Type natural language commands.")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        prompt = input("\n🧠 ShellPilot > ").strip()
        category = categorize(prompt)
        print(f"🗂️ Category: {category}")
        if prompt.lower() in ["exit", "quit"]:
            break

        shell_cmd = ask_llm(prompt, category)


        if not shell_cmd:
            print("⚠️ No command returned by the model.")
            continue

        if shell_cmd in SAFE_REPLACEMENTS:
            print("⚠️ Replacing LLM output with a verified safe version.")
            shell_cmd = SAFE_REPLACEMENTS[shell_cmd]

        print(f"\n🤖 Suggested command:\n{shell_cmd}")

        if not is_safe(shell_cmd):
            print("⚠️  Warning: This command is considered dangerous!")
            confirm_danger = input("Are you sure you want to run it? (y/n): ")
            if confirm_danger.lower() != "y":
                continue

        confirm = input("Run this? (y/n): ")
        if confirm.lower() == "y":
            print("\n💻 Output:")
            print(run_shell(shell_cmd))

if __name__ == "__main__":
    main()
