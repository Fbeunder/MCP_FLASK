#!/usr/bin/env python3
"""
Flask MCP-integratie Applicatie

Deze Flask-applicatie integreert LLM-modellen (OpenAI en Anthropic) met MCP-servers
voor het verrijken van prompts met context uit externe bronnen.
"""

import os
import sys
import json
import subprocess

# Haal het huidige Python executable path op voor subprocessen
PYTHON_EXECUTABLE = sys.executable

# Probeer .env bestand te laden indien beschikbaar
try:
    from dotenv import load_dotenv
    load_dotenv()  # Laad .env bestand als het bestaat
    env_loaded = True
except ImportError:
    env_loaded = False
    print("OPMERKING: python-dotenv niet geïnstalleerd. .env bestand zal niet worden geladen.")
    print("Gebruik 'pip install python-dotenv' om .env bestandsondersteuning toe te voegen.")

# Controleer Flask-afhankelijkheid
try:
    from flask import Flask, render_template, request, redirect, url_for
except ImportError:
    print("ERROR: Flask is niet geïnstalleerd. Dit is een vereiste afhankelijkheid.")
    print("\nInstalleer met:")
    print("    pip install -r requirements.txt")
    print("\nOf installeer Flask afzonderlijk:")
    print("    pip install flask\n")
    print("Zie README.md voor gedetailleerde installatie-instructies.")
    sys.exit(1)

# Controleer requests-afhankelijkheid
try:
    import requests
except ImportError:
    print("ERROR: requests is niet geïnstalleerd. Dit is een vereiste afhankelijkheid.")
    print("\nInstalleer met:")
    print("    pip install -r requirements.txt")
    print("\nOf installeer requests afzonderlijk:")
    print("    pip install requests\n")
    print("Zie README.md voor gedetailleerde installatie-instructies.")
    sys.exit(1)

# Probeer OpenAI te importeren
try:
    import openai
    openai_available = True
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        print("WAARSCHUWING: OPENAI_API_KEY is niet ingesteld. OpenAI-model zal niet correct werken.")
        if not env_loaded:
            print("Overweeg om een .env bestand te maken of gebruik omgevingsvariabelen.")
except ImportError:
    openai_available = False
    print("OpenAI package is niet geïnstalleerd. OpenAI-model zal niet beschikbaar zijn.")
    print("Installeer met: pip install openai")

# Probeer Anthropic te importeren
try:
    import anthropic
    anthropic_available = True
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        print("WAARSCHUWING: ANTHROPIC_API_KEY is niet ingesteld. Claude-model zal niet correct werken.")
        if not env_loaded:
            print("Overweeg om een .env bestand te maken of gebruik omgevingsvariabelen.")
    else:
        # Probeer de Anthropic client aan te maken
        try:
            claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
        except Exception as e:
            print(f"Fout bij het aanmaken van Anthropic client: {e}")
            claude_client = None
            anthropic_available = False
except ImportError:
    anthropic_available = False
    print("Anthropic package is niet geïnstalleerd. Claude-model zal niet beschikbaar zijn.")
    print("Installeer met: pip install anthropic")

app = Flask(__name__)

# Model opties en API keys vanuit omgeving
MODEL_OPTIONS = {}
if openai_available:
    MODEL_OPTIONS["openai"] = "OpenAI GPT-3.5"
if anthropic_available:
    MODEL_OPTIONS["anthropic"] = "Anthropic Claude 2"

# Globale dict om subprocessen bij te houden
processes = {}
MCP_SERVERS = {
    "brave": {
        "command": [PYTHON_EXECUTABLE, "brave_mcp_server.py"],
        "env": {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")},
        "port": 5001
    },
    "github": {
        "command": [PYTHON_EXECUTABLE, "github_mcp_server.py"],
        "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "")},
        "port": 5002
    }
}

def start_mcp_server(name):
    """Start een MCP-server proces als deze nog niet draait."""
    if name in processes:
        return False
    cfg = MCP_SERVERS.get(name)
    if not cfg:
        return False
    try:
        # Zorg ervoor dat we hetzelfde Python-executable gebruiken
        # en kopieer de huidige PYTHONPATH om site-packages te vinden
        env = {**os.environ, **cfg["env"]}
        
        # Geef informatie over het gestarte proces
        python_path = cfg["command"][0]
        print(f"MCP server '{name}' starten met Python: {python_path}")
        
        proc = subprocess.Popen(cfg["command"], env=env)
        processes[name] = proc
        return True
    except Exception as e:
        error_message = str(e)
        print(f"Fout bij het starten van {name}: {error_message}")
        
        # Controleer op veelvoorkomende fouten en geef duidelijke meldingen
        if "No such file or directory" in error_message:
            print(f"Zorg ervoor dat {cfg['command'][1]} bestaat in de huidige map.")
        elif "Permission denied" in error_message:
            print(f"Zorg ervoor dat {cfg['command'][1]} uitvoerbare permissies heeft.")
        
        # Voeg virtuele omgeving troubleshooting toe
        print("\nTroubleshooting voor virtuele omgevingen:")
        print(f"- Huidige Python: {sys.executable}")
        print(f"- Gebruikt voor MCP server: {cfg['command'][0]}")
        print("- Controleer of Flask correct is geïnstalleerd in de actieve Python-omgeving")
        print("- Als u een virtuele omgeving gebruikt, zorg dat deze is geactiveerd")
        print("- Voer 'pip install -r requirements.txt' uit om alle vereiste packages te installeren")
        return False

def stop_mcp_server(name):
    """Stop een draaiend MCP-server proces."""
    proc = processes.get(name)
    if not proc:
        return False
    try:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
        processes.pop(name, None)
        return True
    except Exception as e:
        print(f"Fout bij het stoppen van {name}: {e}")
        return False

def get_tool_context(user_prompt):
    """Maakt gebruik van actieve MCP-tools om extra context te vergaren voor de prompt."""
    context_parts = []
    
    # Brave Search context
    if "brave" in processes:
        api_key = os.getenv("BRAVE_API_KEY")
        if api_key:
            headers = {"X-Subscription-Token": api_key}
            params = {"q": user_prompt, "source": "web"}
            try:
                res = requests.get("https://api.search.brave.com/res/v1/search", headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("web", {}).get("results"):
                        top = data["web"]["results"][0]
                        desc = top.get("description") or top.get("text") or ""
                        url = top.get("url", "")
                        context_parts.append(f"Brave zoekresultaat: {top.get('title')}. {desc} [Bron: {url}]")
                else:
                    print(f"Brave Search API fout: {res.status_code} - {res.text}")
            except Exception as e:
                print(f"Fout bij het bevragen van Brave Search: {e}")
    
    # GitHub context
    if "github" in processes:
        query = " ".join(user_prompt.split()[:5])
        try:
            headers = {}
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"
                
            res = requests.get(
                "https://api.github.com/search/repositories", 
                headers=headers,
                params={"q": query}
            )
            
            if res.status_code == 200:
                data = res.json()
                if data.get("items"):
                    repo = data["items"][0]
                    context_parts.append(
                        f"GitHub repo: {repo.get('full_name')} - {repo.get('description')}\n"
                        f"URL: {repo.get('html_url')}\n"
                        f"Stars: {repo.get('stargazers_count')}, Forks: {repo.get('forks_count')}"
                    )
            else:
                print(f"GitHub API fout: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Fout bij het bevragen van GitHub: {e}")
    
    # Combineer alle contextdelen
    context = "\n\n".join(context_parts)
    if context:
        context = "## Aanvullende informatie via MCP-tools\n\n" + context
    return context

def query_llm(model_choice, prompt_text):
    """Stuurt de prompt naar het gekozen LLM-model en geeft het antwoord terug."""
    if model_choice == "openai" and openai_available:
        if not openai.api_key:
            return "OpenAI API-sleutel niet geconfigureerd. Stel de OPENAI_API_KEY omgevingsvariabele in."
        
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt_text}]
            )
            return resp["choices"][0]["message"]["content"]
        except Exception as e:
            error_msg = f"Fout bij OpenAI API aanroep: {str(e)}"
            print(error_msg)
            return error_msg
    
    elif model_choice == "anthropic" and anthropic_available:
        if not anthropic_api_key:
            return "Anthropic API-sleutel niet geconfigureerd. Stel de ANTHROPIC_API_KEY omgevingsvariabele in."
        
        if not claude_client:
            return "Claude client kon niet worden geïnitialiseerd."
        
        try:
            # Update voor nieuwere versies van de Anthropic SDK
            message = claude_client.messages.create(
                model="claude-2",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt_text}
                ]
            )
            return message.content[0].text
        except AttributeError:
            # Fallback voor oudere versies van de Anthropic SDK
            try:
                resp = claude_client.completions.create(
                    prompt=f"{anthropic.HUMAN_PROMPT} {prompt_text} {anthropic.AI_PROMPT}",
                    model="claude-2",
                    max_tokens_to_sample=1000
                )
                return resp.completion
            except Exception as e:
                error_msg = f"Fout bij Anthropic API aanroep (oudere SDK): {str(e)}"
                print(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Fout bij Anthropic API aanroep: {str(e)}"
            print(error_msg)
            return error_msg
    
    else:
        return "Ongeldig model of API client niet beschikbaar."

@app.route("/", methods=["GET", "POST"])
def index():
    """Hoofdroute voor de webinterface."""
    answer = None
    selected_model = None
    user_prompt = None
    full_prompt = None
    
    if request.method == "POST" and "prompt" in request.form:
        # Prompt verwerken via tools en model
        selected_model = request.form.get("model")
        user_prompt = request.form.get("prompt", "")
        
        # Haal context op via actieve tools
        context = get_tool_context(user_prompt)
        
        # Combineer context en prompt
        full_prompt = f"{context}\n\nVraag: {user_prompt}" if context else user_prompt
        
        # Vraag het LLM om antwoord
        answer = query_llm(selected_model, full_prompt)
    
    # Geeft de indexpagina weer
    running_tools = list(processes.keys())
    return render_template(
        "index.html", 
        models=MODEL_OPTIONS, 
        running=running_tools,
        selected_model=selected_model, 
        prompt=user_prompt, 
        answer=answer,
        full_prompt=full_prompt
    )

@app.route("/start/<tool>", methods=["POST"])
def start_tool(tool):
    """Start een MCP-server via de webinterface."""
    start_mcp_server(tool)
    return redirect(url_for("index"))

@app.route("/stop/<tool>", methods=["POST"])
def stop_tool(tool):
    """Stop een MCP-server via de webinterface."""
    stop_mcp_server(tool)
    return redirect(url_for("index"))

if __name__ == "__main__":
    if not MODEL_OPTIONS:
        print("\nWAARSCHUWING: Geen LLM-modellen beschikbaar. Installeer openai en/of anthropic packages.")
        print("Gebruik 'pip install openai anthropic' om beide te installeren.\n")
    
    if not os.getenv("BRAVE_API_KEY"):
        print("OPMERKING: BRAVE_API_KEY is niet ingesteld. Brave Search MCP-server zal niet correct werken.")
    
    print("Flask MCP-integratie Applicatie wordt gestart...")
    print(f"Actieve Python omgeving: {sys.executable}")
    print(f"Beschikbare modellen: {', '.join(MODEL_OPTIONS.values()) if MODEL_OPTIONS else 'Geen'}")
    print("Open http://localhost:5000 in je browser om de interface te gebruiken.")
    app.run(debug=True)
