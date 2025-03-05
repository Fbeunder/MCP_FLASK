from flask import Flask, render_template, request, redirect, url_for
import requests, subprocess, os
import json

# API keys importeren (in productie via os.getenv)
# Gebruik deze variabelen om je API-sleutels in te stellen of stel ze in als omgevingsvariabelen
# openai.api_key = os.getenv("OPENAI_API_KEY")
# anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

try:
    import openai
    openai_available = True
    openai.api_key = os.getenv("OPENAI_API_KEY")
except ImportError:
    openai_available = False
    print("OpenAI package not installed. OpenAI model will not be available.")

try:
    import anthropic
    anthropic_available = True
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    claude_client = anthropic.Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None
except ImportError:
    anthropic_available = False
    print("Anthropic package not installed. Claude model will not be available.")

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
        "command": ["python", "brave_mcp_server.py"],
        "env": {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")}
    },
    "github": {
        "command": ["python", "github_mcp_server.py"],
        "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "")}
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
        proc = subprocess.Popen(cfg["command"], env={**os.environ, **cfg["env"]})
        processes[name] = proc
        return True
    except Exception as e:
        print(f"Failed to start {name}: {e}")
        return False

def stop_mcp_server(name):
    """Stop een draaiend MCP-server proces."""
    proc = processes.get(name)
    if not proc:
        return False
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()
    processes.pop(name, None)
    return True

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
            except Exception as e:
                print(f"Error querying Brave Search: {e}")
    
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
        except Exception as e:
            print(f"Error querying GitHub: {e}")
    
    # Combineer alle contextdelen
    context = "\n\n".join(context_parts)
    if context:
        context = "## Aanvullende informatie via MCP-tools\n\n" + context
    return context

def query_llm(model_choice, prompt_text):
    """Stuurt de prompt naar het gekozen LLM-model en geeft het antwoord terug."""
    if model_choice == "openai" and openai_available:
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt_text}]
            )
            return resp["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Fout bij OpenAI API aanroep: {str(e)}"
    
    elif model_choice == "anthropic" and anthropic_available:
        if not claude_client:
            return "Anthropic API key niet geconfigureerd."
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
                return f"Fout bij Anthropic API aanroep (oudere SDK): {str(e)}"
        except Exception as e:
            return f"Fout bij Anthropic API aanroep: {str(e)}"
    
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
    app.run(debug=True)
