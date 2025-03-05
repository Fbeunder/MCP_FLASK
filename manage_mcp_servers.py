#!/usr/bin/env python3
"""
MCP-Server Beheerder

Dit hulpprogramma helpt bij het beheren van de MCP-servers die worden gebruikt
door de Flask MCP-integratie applicatie.

Gebruik:
    python manage_mcp_servers.py start [brave|github|all]
    python manage_mcp_servers.py stop [brave|github|all]
    python manage_mcp_servers.py status

Vereisten:
    - Python 3.7+
    - Dezelfde omgeving als de hoofdapplicatie
"""

import os
import sys
import time
import argparse
import subprocess
import signal
import requests
from pathlib import Path

# Definieer de MCP-servers
MCP_SERVERS = {
    "brave": {
        "command": [sys.executable, "brave_mcp_server.py"],
        "env": {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")},
        "port": 5001,
        "url": "http://localhost:5001/"
    },
    "github": {
        "command": [sys.executable, "github_mcp_server.py"],
        "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "")},
        "port": 5002,
        "url": "http://localhost:5002/"
    }
}

# Globale dictionary om processen bij te houden
processes = {}
pid_file = Path(".mcp_server_pids.txt")

def load_pids():
    """Laad opgeslagen proces-IDs uit het bestand als het bestaat."""
    if pid_file.exists():
        try:
            with open(pid_file, "r") as f:
                lines = f.read().strip().split("\n")
                for line in lines:
                    if line:
                        name, pid = line.split(":")
                        processes[name] = int(pid)
        except Exception as e:
            print(f"Fout bij het laden van proces-IDs: {e}")

def save_pids():
    """Sla actieve proces-IDs op in een bestand."""
    try:
        with open(pid_file, "w") as f:
            for name, pid in processes.items():
                f.write(f"{name}:{pid}\n")
    except Exception as e:
        print(f"Fout bij het opslaan van proces-IDs: {e}")

def is_server_running(name):
    """Controleer of een server actief is door een verzoek te sturen."""
    if name not in MCP_SERVERS:
        return False
        
    # Controleer eerst of we een PID hebben
    if name not in processes:
        return False
        
    # Probeer om de status via HTTP te controleren
    try:
        url = MCP_SERVERS[name]["url"]
        response = requests.get(url, timeout=1)
        return response.status_code == 200
    except:
        # Als HTTP niet werkt, controleer dan het proces
        try:
            # In Windows moeten we anders controleren
            if os.name == 'nt':
                # Gebruik tasklist om te zien of het proces nog draait
                cmd = f'tasklist /FI "PID eq {processes[name]}" /NH'
                output = subprocess.check_output(cmd, shell=True).decode()
                return str(processes[name]) in output
            else:
                # In Unix kunnen we een signaal sturen om te controleren
                os.kill(processes[name], 0)  # Signaal 0 test of proces bestaat
                return True
        except:
            # Proces bestaat niet meer
            return False

def start_server(name):
    """Start een MCP-server."""
    if name not in MCP_SERVERS:
        print(f"Onbekende server: {name}")
        return False
        
    if is_server_running(name):
        print(f"Server '{name}' draait al.")
        return True
        
    try:
        # Verzamel de command en env
        cmd = MCP_SERVERS[name]["command"]
        env = {**os.environ, **MCP_SERVERS[name]["env"]}
        
        # Start het proces
        print(f"Server '{name}' starten met Python: {sys.executable}")
        proc = subprocess.Popen(cmd, env=env)
        
        # Sla het PID op
        processes[name] = proc.pid
        save_pids()
        
        # Geef het proces tijd om te starten
        time.sleep(1)
        
        # Controleer of het gestart is
        if is_server_running(name):
            print(f"Server '{name}' succesvol gestart (PID: {proc.pid}).")
            return True
        else:
            print(f"Server '{name}' lijkt niet te zijn gestart. Controleer de logbestanden.")
            return False
            
    except Exception as e:
        print(f"Fout bij het starten van '{name}': {e}")
        
        # Geef extra hulp bij veelvoorkomende fouten
        if "FileNotFoundError" in str(e):
            print(f"Zorg ervoor dat {cmd[1]} bestaat in de huidige map.")
        elif "PermissionError" in str(e):
            print(f"Zorg ervoor dat {cmd[1]} uitvoerbare permissies heeft.")
            
        # Toon virtuele omgeving debugging info
        print("\nVirtuele omgeving debugging info:")
        print(f"- Huidige Python: {sys.executable}")
        print("- Actieve packages:")
        try:
            pip_list = subprocess.check_output([sys.executable, "-m", "pip", "list"]).decode()
            flask_installed = "flask" in pip_list.lower()
            print(f"- Flask geïnstalleerd: {flask_installed}")
            if not flask_installed:
                print("  Installeer Flask met: pip install flask")
        except:
            print("  Kon packages niet controleren")
            
        return False

def stop_server(name):
    """Stop een MCP-server."""
    if name not in MCP_SERVERS:
        print(f"Onbekende server: {name}")
        return False
        
    if not is_server_running(name):
        print(f"Server '{name}' draait niet.")
        # Verwijder eventuele oude verwijzingen
        if name in processes:
            del processes[name]
            save_pids()
        return True
        
    try:
        pid = processes[name]
        
        # Probeer het proces te beëindigen
        if os.name == 'nt':
            # Windows gebruikt taskkill
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False)
        else:
            # Unix-achtige systemen gebruiken kill
            os.kill(pid, signal.SIGTERM)
            # Geef het proces tijd om af te sluiten
            time.sleep(2)
            # Als het nog draait, forceer afsluiten
            if is_server_running(name):
                os.kill(pid, signal.SIGKILL)
                
        # Controleer of het gestopt is
        if not is_server_running(name):
            print(f"Server '{name}' succesvol gestopt.")
            del processes[name]
            save_pids()
            return True
        else:
            print(f"Server '{name}' kon niet worden gestopt.")
            return False
            
    except Exception as e:
        print(f"Fout bij het stoppen van '{name}': {e}")
        # Als het proces niet meer bestaat, verwijder de verwijzing
        if "No such process" in str(e) or "process no longer exists" in str(e):
            print(f"Proces voor '{name}' bestaat niet meer. Verwijzing opgeschoond.")
            if name in processes:
                del processes[name]
                save_pids()
            return True
        return False

def show_status():
    """Toon de status van alle MCP-servers."""
    print("MCP-Server Status:")
    print("-----------------")
    
    for name in MCP_SERVERS:
        running = is_server_running(name)
        status = "ACTIEF" if running else "GESTOPT"
        pid = processes.get(name, "N/A")
        port = MCP_SERVERS[name]["port"]
        
        print(f"{name.upper()} Server (poort {port}): {status}")
        if running:
            print(f"  - PID: {pid}")
            print(f"  - URL: {MCP_SERVERS[name]['url']}")
        print()
        
    return True

def main():
    """Hoofdfunctie voor het verwerken van commandoregelargumenten."""
    parser = argparse.ArgumentParser(description="MCP-Server beheerder")
    parser.add_argument("actie", choices=["start", "stop", "status"], 
                        help="De actie die moet worden uitgevoerd")
    parser.add_argument("server", nargs="?", default="all",
                        help="De te beheren server (brave, github, of all)")
    
    args = parser.parse_args()
    
    # Laad bestaande proces-IDs
    load_pids()
    
    if args.actie == "status":
        return show_status()
    
    # Bepaal welke servers moeten worden beheerd
    servers = list(MCP_SERVERS.keys()) if args.server == "all" else [args.server]
    
    # Voer de gekozen actie uit
    success = True
    for server in servers:
        if server not in MCP_SERVERS:
            print(f"Onbekende server: {server}")
            success = False
            continue
            
        if args.actie == "start":
            if not start_server(server):
                success = False
        elif args.actie == "stop":
            if not stop_server(server):
                success = False
    
    # Toon de status na de actie
    show_status()
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nOperatie onderbroken door gebruiker.")
        sys.exit(1)
    except Exception as e:
        print(f"Onverwachte fout: {e}")
        sys.exit(1)
