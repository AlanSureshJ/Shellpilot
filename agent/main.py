import requests
import subprocess
import re
import platform
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.log_db import log_command



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


def run_shell(command, prompt="", category=""):
    try:
        if platform.system() == "Windows":
            if category == "📁 File/Folder Ops" and "move" in prompt.lower():
                move_match = re.search(r"move\s+(.*?)\s+(?:from\s+(\w+)\s+)?to\s+(\w+)", prompt.lower())
                if move_match:
                    file_name = move_match.group(1).strip().strip('"')
                    dest_folder = move_match.group(3)
                else:
                    file_name = dest_folder = None

                if file_name and dest_folder:
                    folder_map = {
                        "downloads": "$env:USERPROFILE\\Downloads",
                        "documents": "$env:USERPROFILE\\Documents",
                        "desktop": "[Environment]::GetFolderPath('Desktop')"
                    }

                    # ✅ Inject this directly into PowerShell code
                    destination_expr = folder_map.get(dest_folder.lower(), "[Environment]::GetFolderPath('Desktop')")

                    # 🧠 Inline destination directly
                    ps_script = f'''
$filename = "{file_name}"
$found = $null
$folders = @(
    "$env:USERPROFILE\\Downloads",
    "$env:USERPROFILE\\Documents",
    [Environment]::GetFolderPath("Desktop")
)
foreach ($folder in $folders) {{
    $match = Get-ChildItem -Path $folder -Recurse -Filter $filename -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($match) {{
        $found = $match.FullName
        break
    }}
}}
if ($found) {{
    Write-Output "✅ Moving: $found"
    Move-Item -Path $found -Destination $({destination_expr})
}} else {{
    Write-Output "❌ File not found."
}}
'''
                    import base64
                    encoded = base64.b64encode(ps_script.encode("utf-16le")).decode()
                    command = f"powershell -NoLogo -NoProfile -EncodedCommand {encoded}"

            else:
                if not command.strip().lower().startswith("powershell"):
                    command = f'powershell -Command "{command}"'

        output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True, shell=True)
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
            result = run_shell(shell_cmd, prompt=prompt, category=category)
            print(result)
            log_command(
                prompt=prompt,
                category=category,
                suggested_command=shell_cmd,
                was_run=True,
                output=result
            )
        else:
            log_command(
                prompt=prompt,
                category=category,
                suggested_command=shell_cmd,
                was_run=False,
                output=None
            )


if __name__ == "__main__":
    main()