from fastapi import FastAPI, HTTPException
import sys
import os
from pydantic import BaseModel
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from agent.run import run_shell
from shared.log_db import log_command
from agent.logic import ask_llm, categorize, is_safe, SAFE_REPLACEMENTS

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CommandRequest(BaseModel):
    prompt: str

class CommandResponse(BaseModel):
    category: str
    shell_command: str
    output: str

@app.get("/")
def root():
    return {"message": "ShellPilot API is running."}

@app.post("/run", response_model=CommandResponse)
def run_command(request: CommandRequest):
    prompt = request.prompt.strip()
    print("Received prompt:", prompt)

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    print("Categorizing...")
    category = categorize(prompt)
    print("Category:", category)

    print("Asking LLM...")
    shell_cmd = ask_llm(prompt, category)
    print("Shell command:", shell_cmd)

    if not shell_cmd:
        raise HTTPException(status_code=500, detail="Model failed to generate a command.")

    if shell_cmd in SAFE_REPLACEMENTS:
        shell_cmd = SAFE_REPLACEMENTS[shell_cmd]

    print("Checking safety...")
    if not is_safe(shell_cmd):
        raise HTTPException(status_code=400, detail="Command deemed unsafe and blocked.")

    print("Running shell...")
    output = run_shell(shell_cmd, prompt=prompt, category=category)
    print("Output:", output)

    print("Logging command...")
    log_command(
        prompt=prompt,
        category=category,
        suggested_command=shell_cmd,
        was_run=True,
        output=output
    )

    print("Returning response...")
    return CommandResponse(
        category=category,
        shell_command=shell_cmd,
        output=output
    )