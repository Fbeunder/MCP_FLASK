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
- Flask
- Requests
- OpenAI Python package (optioneel, voor GPT-toegang)
- Anthropic Python package (optioneel, voor Claude-toegang)

### Stappen

1. **Clone de repository**

   ```bash
   git clone https://github.com/Fbeunder/MCP_FLASK.git
   cd MCP_FLASK
   ```

2. **Installeer de vereiste pakketten**

   ```bash
   pip install flask requests
   
   # Voor OpenAI model-toegang
   pip install openai
   
   # Voor Anthropic model-toegang
   pip install anthropic
   ```

3. **Configureer de API-sleutels**

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
