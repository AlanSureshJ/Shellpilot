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
    "Clear-Cache": "del /q /s %LOCALAPPDATA%\\Temp\\* 2>nul" ,
    "Get-ChildItem DerivedData\\* -File | Remove-Item -Force": 'del /q /s %LOCALAPPDATA%\\Temp\\* 2>nul'
                   if subprocess.os.name == "nt" else "rm -rf ~/.cache/*",
}

def clean_shell_output(text):
    # Remove any kind of Markdown-style code block
    return re.sub(r"```(?:\w+)?\s*([\s\S]*?)\s*```", r"\1", text, flags=re.DOTALL).strip()

def ask_llm(prompt, category):
    full_prompt = (
        f"Convert the following into a real, working Windows PowerShell command.\n"
        f"Prompt: '{prompt}'\n"
        f"Only respond with the raw PowerShell command — no explanations, no formatting.\n"
        f"Task type: {category}\n"
        f"Instruction: Convert this into a valid PowerShell command:\n'{prompt}'\n"
        f"Requirements:\n"
        f"- The command must run successfully on real Windows PowerShell.\n"
        f"- DO NOT use imaginary commands like 'Clear-Cache'.\n"
        f"- Always wrap full -Path or -Destination values in double quotes, including environment variables. Example:\n"
        f'  New-Item -ItemType Directory -Path "$env:USERPROFILE\\Desktop\\resume"\n'
        f"- Output only the single-line PowerShell command. No explanations, no Markdown, no code blocks."
        f"- NEVER return imaginary commands like 'Clear-Cache' or 'Delete-Folder'. Only use real Windows PowerShell commands like 'Move-Item', 'Remove-Item', 'Get-ChildItem'.\n"

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

def categorize(prompt):
    prompt_lower = prompt.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in prompt_lower for keyword in keywords):
            return category
    return "❓ Unknown"

