# ShellPilot

ShellPilot is a natural language shell agent. It lets users describe what they want to do in plain English and translates that into safe shell commands using a local LLM. You stay in control by reviewing and approving each command before execution. All activity can be logged to a PostgreSQL database for audit, debugging or future training.

## Features

Converts natural language into terminal commands  
Categorizes each prompt by intent  
Supports Windows and Linux command equivalents  
Warns before executing dangerous commands  
Allows manual override of blocked operations  
Logs prompts, outputs and decisions into a database  
Runs completely offline using Ollama and open models  
Modular and ready for web or daemon integration

## Tech Stack

Python for the core agent logic  
PostgreSQL for persistent command logging  
Ollama for running local large language models like Gemma  
Planned frontend in React with Tailwind  
Planned daemon in Go or Rust

## Getting Started

1. Install Ollama from ollama.com  
2. Run a supported model locally  
    ollama run gemma3
3. Set up PostgreSQL  
- Default port is 5432  
- Create a user and database  
- Store credentials in a .env file

4. Install Python dependencies  
    pip install -r requirements.txt

5. Start the agent
    cd agent

6. python main.py

