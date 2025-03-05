# Flask Webapplicatie met LLM-integratie en MCP-tools

Deze Flask-webapplicatie stelt gebruikers in staat om:

- LLM-modellen (OpenAI en Anthropic) te benaderen via een eenvoudige webinterface
- Prompts in te voeren en antwoorden te ontvangen
- MCP-servers (Model Context Protocol) voor GitHub en Brave Search te starten en stoppen
- De prompt automatisch te verrijken met context uit deze tools voordat deze naar het LLM wordt gestuurd

## Functionaliteiten

- **LLM-model selectie**: Kies tussen OpenAI GPT-3.5 en Anthropic Claude 2
- **Prompt invoer**: Voer een vraag of prompt in om door het gekozen model te laten beantwoorden
- **MCP-tools beheer**: Start en stop externe tools (Brave Search en GitHub) vanuit de webinterface
- **Contextverrijking**: De applicatie verrijkt je prompt automatisch met relevante informatie uit actieve tools
- **Volledige prompt weergave**: Bekijk de volledige prompt inclusief toegevoegde context

## Installatie

### Vereisten

- Python 3.7 of hoger

### Stappen

1. **Clone de repository**

   ```bash
   git clone https://github.com/Fbeunder/MCP_FLASK.git
   cd MCP_FLASK
   ```

2. **Maak een virtuele omgeving aan (aanbevolen)**

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Installeer de vereiste pakketten**

   ```bash
   # Aanbevolen: installeer alle afhankelijkheden via requirements.txt
   pip install -r requirements.txt
   
   # Alternatief: installeer alleen de specifieke pakketten die je nodig hebt
   pip install flask requests
   
   # Voor OpenAI model-toegang
   pip install openai
   
   # Voor Anthropic model-toegang
   pip install anthropic
   
   # Voor .env bestandsondersteuning
   pip install python-dotenv
   ```

4. **Configureer de API-sleutels**

   Je kunt API-sleutels configureren via omgevingsvariabelen of een .env bestand.

   **Optie 1: Maak een .env bestand**
   
   Kopieer het .env.example bestand en pas het aan:
   
   ```bash
   # Windows
   copy .env.example .env
   
   # macOS/Linux
   cp .env.example .env
   ```
   
   Bewerk vervolgens het .env bestand en vul je API-sleutels in.

   **Optie 2: Stel omgevingsvariabelen in**
   
   Stel de volgende omgevingsvariabelen in:

   - `OPENAI_API_KEY`: Je OpenAI API-sleutel (voor GPT-modellen)
   - `ANTHROPIC_API_KEY`: Je Anthropic API-sleutel (voor Claude-modellen)
   - `BRAVE_API_KEY`: Je Brave Search API-sleutel (voor Brave Search MCP-server)
   - `GITHUB_TOKEN`: Je GitHub Personal Access Token (optioneel, voor hogere limieten)

   Bijvoorbeeld in Linux/macOS:

   ```bash
   export OPENAI_API_KEY="jouw-openai-api-sleutel"
   export ANTHROPIC_API_KEY="jouw-anthropic-api-sleutel"
   export BRAVE_API_KEY="jouw-brave-api-sleutel"
   export GITHUB_TOKEN="jouw-github-token"
   ```

   Of in Windows:

   ```cmd
   set OPENAI_API_KEY=jouw-openai-api-sleutel
   set ANTHROPIC_API_KEY=jouw-anthropic-api-sleutel
   set BRAVE_API_KEY=jouw-brave-api-sleutel
   set GITHUB_TOKEN=jouw-github-token
   ```

## Gebruik

### De applicatie starten

Start de Flask-app:

```bash
python app.py
```

De applicatie zal standaard draaien op `http://localhost:5000`.

### Werken met de webinterface

1. **Open de webinterface** in je browser: `http://localhost:5000`

2. **Start MCP-tools** (optioneel):
   - Klik op "Start Brave Search" om de Brave Search-tool te starten
   - Klik op "Start GitHub" om de GitHub-tool te starten

3. **Voer een prompt in**:
   - Selecteer het gewenste LLM-model uit de keuzelijst
   - Typ je vraag of prompt in het tekstvak
   - Klik op "Verstuur naar AI"

4. **Bekijk het antwoord**:
   - Het antwoord van het AI-model wordt getoond
   - Je kunt optioneel op "Toon volledige prompt met context" klikken om te zien hoe de extra context is toegevoegd

### MCP-servers

De applicatie gebruikt twee MCP-servers die automatisch gestart kunnen worden vanuit de interface:

- **Brave Search MCP-server**: Draait op poort 5001 en biedt webzoekfunctionaliteit
- **GitHub MCP-server**: Draait op poort 5002 en biedt GitHub-zoekfunctionaliteit

Wanneer deze servers actief zijn, wordt de context van deze tools automatisch toegevoegd aan je prompts.

## Problemen oplossen

### Virtuele omgeving problemen

Als je een foutmelding krijgt over ontbrekende modules (zoals Flask) terwijl je zeker weet dat deze zijn geïnstalleerd, kan dit te maken hebben met problemen met virtuele omgevingen. Hier zijn enkele stappen om dit op te lossen:

#### Windows virtuele omgeving problemen

1. **Controleer of de virtuele omgeving is geactiveerd**:
   
   Je moet de virtuele omgeving activeren in elke nieuwe terminal-sessie:
   ```bash
   venv\Scripts\activate
   ```
   
   Je zou `(venv)` aan het begin van je command prompt moeten zien.

2. **Controleer welke Python-executable wordt gebruikt**:
   
   ```bash
   where python
   ```
   
   Het eerste pad moet wijzen naar de python.exe in je virtuele omgeving (bijv. `\path\to\project\venv\Scripts\python.exe`).

3. **Problemen met subprocess in Windows**:
   
   De laatste versie van de applicatie gebruikt nu automatisch dezelfde Python-executable voor het starten van MCP-servers als de hoofdapplicatie, wat problemen met virtuele omgevingen voorkomt.

#### Linux/macOS virtuele omgeving problemen

1. **Controleer of de virtuele omgeving is geactiveerd**:
   
   ```bash
   source venv/bin/activate
   ```
   
   Je zou `(venv)` aan het begin van je command prompt moeten zien.

2. **Controleer welke Python-executable wordt gebruikt**:
   
   ```bash
   which python
   ```
   
   Het pad moet wijzen naar de python in je virtuele omgeving (bijv. `/path/to/project/venv/bin/python`).

### ModuleNotFoundError: No module named 'flask'

Als je deze fout nog steeds ziet wanneer je de applicatie of MCP-servers probeert te starten, probeer dan het volgende:

1. **Controleer de installatie**:
   ```bash
   pip list | grep flask
   ```
   
   Je zou Flask in de lijst moeten zien.

2. **Herinstalleer Flask**:
   ```bash
   pip uninstall flask
   pip install flask
   ```

3. **Gebruik absolute paden voor het uitvoeren**:
   ```bash
   # Vind het volledige pad naar Python in je virtuele omgeving
   # Windows
   echo %VIRTUAL_ENV%\Scripts\python.exe
   
   # Linux/macOS
   echo $VIRTUAL_ENV/bin/python
   
   # Gebruik dit pad om de applicatie te starten
   /volledig/pad/naar/venv/bin/python app.py
   ```

4. **Controleer PYTHONPATH**:
   
   In sommige gevallen kan de PYTHONPATH omgevingsvariabele verstoord raken:
   ```bash
   # Windows
   echo %PYTHONPATH%
   
   # Linux/macOS
   echo $PYTHONPATH
   ```
   
   Als het een waarde heeft die niet zinvol is voor je project, overweeg om het tijdelijk te wissen:
   ```bash
   # Windows
   set PYTHONPATH=
   
   # Linux/macOS
   unset PYTHONPATH
   ```

### Andere package-gerelateerde fouten

Als je andere ModuleNotFoundError-meldingen ziet, controleer dan of:
- Alle packages zijn geïnstalleerd via `pip install -r requirements.txt`
- Je Python-omgeving correct is ingesteld
- Je geen oudere of incompatibele versies van packages hebt geïnstalleerd

## Model Context Protocol (MCP)

MCP (Model Context Protocol) is een open protocol dat AI-modellen in staat stelt om via gestandaardiseerde serverinterfaces veilig met externe bronnen te interageren. In deze applicatie worden MCP-servers gebruikt om:

1. Extra context te verzamelen op basis van de gebruikersprompt
2. Deze context toe te voegen aan de prompt voordat deze naar het LLM wordt gestuurd
3. Zo het antwoord te verrijken met actuele of specifieke informatie

## Opmerkingen

- De MCP-serverimplementaties zijn vereenvoudigd voor demonstratiedoeleinden
- Voor productiegerbruik is een betere foutafhandeling en beveiliging aanbevolen
- De applicatie heeft API-sleutels nodig voor elke dienst (OpenAI, Anthropic, Brave Search)

## Licentie

MIT
