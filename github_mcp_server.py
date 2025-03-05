"""
GitHub MCP Server - Eenvoudige implementatie

Deze server biedt een MCP (Model Context Protocol) interface voor GitHub API.
Het implementeert een eenvoudige HTTP-server die verzoeken ontvangt en doorgeeft 
aan de GitHub API.

Vereisten:
- Optioneel: een GitHub API-token in de omgevingsvariabele GITHUB_TOKEN
  (zonder token zijn API-limieten lager)
- Python 3.7+ met Flask en requests

Gebruik:
- Start de server met 'python github_mcp_server.py'
- De server draait standaard op http://localhost:5002
"""

import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuratie
PORT = 5002
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Optioneel maar aanbevolen
GITHUB_API_URL = "https://api.github.com"

@app.route("/", methods=["GET"])
def home():
    """Eenvoudige startpagina om te controleren of de server draait."""
    return jsonify({
        "service": "GitHub MCP Server",
        "status": "running",
        "token_present": bool(GITHUB_TOKEN)
    })

def get_github_headers():
    """Stel de juiste headers in voor GitHub API-verzoeken."""
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers

@app.route("/search/repositories", methods=["POST"])
def search_repositories():
    """Zoek naar repositories op GitHub."""
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid request format"}), 400
    
    # Haal de zoekopdracht uit het MCP-verzoek
    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    
    # Stel het aantal resultaten in (maximum 5)
    count = min(int(data.get("count", 3)), 5)
    
    # Roep de GitHub API aan
    try:
        headers = get_github_headers()
        params = {
            "q": query,
            "sort": "stars",
            "per_page": count
        }
        
        response = requests.get(
            f"{GITHUB_API_URL}/search/repositories", 
            headers=headers, 
            params=params
        )
        
        if response.status_code != 200:
            return jsonify({
                "error": f"GitHub API returned status code {response.status_code}",
                "message": response.text
            }), response.status_code
        
        search_results = response.json()
        
        # Formateer de resultaten in een MCP-compatibel antwoord
        mcp_response = {
            "results": []
        }
        
        if search_results.get("items"):
            for repo in search_results["items"]:
                mcp_response["results"].append({
                    "name": repo.get("full_name", ""),
                    "description": repo.get("description", ""),
                    "url": repo.get("html_url", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language", ""),
                    "source": "github_repo"
                })
        
        return jsonify(mcp_response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/search/code", methods=["POST"])
def search_code():
    """Zoek naar code op GitHub."""
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid request format"}), 400
    
    # Haal de zoekopdracht uit het MCP-verzoek
    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    
    # Stel het aantal resultaten in (maximum 5)
    count = min(int(data.get("count", 3)), 5)
    
    # Roep de GitHub API aan
    try:
        headers = get_github_headers()
        params = {
            "q": query,
            "per_page": count
        }
        
        response = requests.get(
            f"{GITHUB_API_URL}/search/code", 
            headers=headers, 
            params=params
        )
        
        if response.status_code != 200:
            return jsonify({
                "error": f"GitHub API returned status code {response.status_code}",
                "message": response.text
            }), response.status_code
        
        search_results = response.json()
        
        # Formateer de resultaten in een MCP-compatibel antwoord
        mcp_response = {
            "results": []
        }
        
        if search_results.get("items"):
            for item in search_results["items"]:
                mcp_response["results"].append({
                    "name": item.get("name", ""),
                    "path": item.get("path", ""),
                    "repository": item.get("repository", {}).get("full_name", ""),
                    "url": item.get("html_url", ""),
                    "source": "github_code"
                })
        
        return jsonify(mcp_response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/mcp/query", methods=["POST"])
def mcp_query():
    """Standaard MCP query endpoint."""
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    
    query_type = data.get("type", "")
    
    if query_type == "repository_search":
        return search_repositories()
    elif query_type == "code_search":
        return search_code()
    
    return jsonify({"error": "Unsupported query type"}), 400

if __name__ == "__main__":
    print(f"Starting GitHub MCP Server on port {PORT}")
    print(f"GitHub Token present: {bool(GITHUB_TOKEN)}")
    app.run(host="0.0.0.0", port=PORT)
