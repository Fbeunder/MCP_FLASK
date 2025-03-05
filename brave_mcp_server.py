#!/usr/bin/env python3
"""
Brave Search MCP Server - Eenvoudige implementatie

Deze server biedt een MCP (Model Context Protocol) interface voor Brave Search.
Het implementeert een eenvoudige HTTP-server die verzoeken ontvangt en doorgeeft 
aan de Brave Search API.

Vereisten:
- Een Brave Search API-sleutel in de omgevingsvariabele BRAVE_API_KEY
- Python 3.7+ met Flask en requests

Gebruik:
- Start de server met 'python brave_mcp_server.py'
- De server draait standaard op http://localhost:5001
"""

import os
import sys
import traceback

# Controleer op vereiste modules voor een betere foutmelding
try:
    import json
    import requests
    from flask import Flask, request, jsonify
except ImportError as e:
    module_name = str(e).split("'")[-2]
    print(f"ERROR: De benodigde module '{module_name}' is niet geïnstalleerd.")
    print("\nInstalleer de vereiste pakketten met:")
    print("    pip install -r requirements.txt")
    print("\nOf installeer specifiek de ontbrekende module:")
    print(f"    pip install {module_name}")
    print("\nZie README.md voor gedetailleerde installatie-instructies.")
    sys.exit(1)

# Laad .env bestand indien beschikbaar
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Instellingen geladen vanuit .env bestand")
except ImportError:
    print("OPMERKING: python-dotenv niet geïnstalleerd, .env bestand wordt niet geladen.")
    print("Gebruik 'pip install python-dotenv' om .env bestandsondersteuning toe te voegen.")

app = Flask(__name__)

# Configuratie
PORT = 5001
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/search"

if not BRAVE_API_KEY:
    print("WAARSCHUWING: BRAVE_API_KEY is niet ingesteld. De server zal niet correct werken.")
    print("Voeg BRAVE_API_KEY toe aan je omgevingsvariabelen of .env bestand.")

def log_error(message, exception=None):
    """Centraal punt voor foutregistratie."""
    print(f"ERROR: {message}")
    if exception:
        print(f"Details: {str(exception)}")
        traceback.print_exc()

@app.route("/", methods=["GET"])
def home():
    """Eenvoudige startpagina om te controleren of de server draait."""
    return jsonify({
        "service": "Brave Search MCP Server",
        "status": "running",
        "api_key_present": bool(BRAVE_API_KEY)
    })

@app.route("/search", methods=["POST"])
def search():
    """MCP-compatibele zoekfunctie die Brave Search aanroept."""
    try:
        data = request.json
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Invalid request format"}), 400
        
        # Haal de zoekopdracht uit het MCP-verzoek
        query = data.get("query")
        if not query:
            return jsonify({"error": "Missing query parameter"}), 400
        
        # Controleer of de API-sleutel aanwezig is
        if not BRAVE_API_KEY:
            return jsonify({
                "error": "BRAVE_API_KEY is not set. Please configure the environment variable."
            }), 500
        
        # Roep de Brave Search API aan
        try:
            headers = {"X-Subscription-Token": BRAVE_API_KEY}
            params = {
                "q": query,
                "source": "web",
                "count": 3  # Aantal resultaten
            }
            
            response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params)
            
            if response.status_code != 200:
                error_message = f"Brave Search API returned status code {response.status_code}"
                log_error(error_message)
                return jsonify({
                    "error": error_message,
                    "message": response.text
                }), response.status_code
            
            search_results = response.json()
            
            # Formateer de resultaten in een MCP-compatibel antwoord
            mcp_response = {
                "results": []
            }
            
            # Verwerk web resultaten
            if search_results.get("web", {}).get("results"):
                for result in search_results["web"]["results"][:3]:  # Beperk tot 3 resultaten
                    mcp_response["results"].append({
                        "title": result.get("title", ""),
                        "description": result.get("description") or result.get("text", ""),
                        "url": result.get("url", ""),
                        "source": "brave_search"
                    })
            
            return jsonify(mcp_response)
            
        except requests.exceptions.ConnectionError as e:
            log_error("Verbindingsfout bij het aanroepen van Brave Search API", e)
            return jsonify({
                "error": "Connection error when calling Brave Search API",
                "message": "Controleer uw internetverbinding"
            }), 503
        except requests.exceptions.Timeout as e:
            log_error("Time-out bij het aanroepen van Brave Search API", e)
            return jsonify({
                "error": "Timeout when calling Brave Search API",
                "message": "De Brave Search API reageert traag of is niet beschikbaar"
            }), 504
        except Exception as e:
            log_error("Onverwachte fout bij het aanroepen van Brave Search API", e)
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        log_error("Algemene fout in search endpoint", e)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/mcp/query", methods=["POST"])
def mcp_query():
    """Standaard MCP query endpoint."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request"}), 400
        
        if data.get("type") == "search":
            return search()
        
        return jsonify({"error": "Unsupported query type"}), 400
    except Exception as e:
        log_error("Algemene fout in mcp_query endpoint", e)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    print(f"Starting Brave Search MCP Server on port {PORT}")
    print(f"API Key present: {bool(BRAVE_API_KEY)}")
    try:
        # Gebruik threaded=False om socket gerelateerde problemen te voorkomen
        # vooral op Windows-systemen met WinError 10038
        app.run(host="127.0.0.1", port=PORT, threaded=False)
    except OSError as e:
        if "10038" in str(e):
            # Specifieke afhandeling voor socket error 10038 (WinError)
            log_error("Socket error 10038 detected. Probeer af te sluiten en opnieuw te starten.", e)
            print("\nVoor Windows-gebruikers: Controleer of er geen andere processen draaien op poort 5001.")
            print("Gebruik 'netstat -ano | findstr 5001' om actieve processen te vinden.")
            print("Gebruik daarna 'taskkill /F /PID <pid>' om ze te beëindigen.")
        else:
            log_error(f"OSError bij het starten van de server", e)
        sys.exit(1)
    except Exception as e:
        log_error(f"Onverwachte fout bij het starten van de server", e)
        print("\nZie README.md voor installatie- en troubleshooting-instructies.")
        sys.exit(1)
