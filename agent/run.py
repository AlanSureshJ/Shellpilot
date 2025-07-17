
import subprocess
import re
import platform
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.log_db import log_command
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