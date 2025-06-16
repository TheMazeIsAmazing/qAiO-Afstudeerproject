# qAiO

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1+-green)
![ChromaDB](https://img.shields.io/badge/ChromaDB-1.0.12+-orange)
![OpenAI](https://img.shields.io/badge/OpenAI-API-red)

Een AI-gestuurde tool om Quality Assurance medewerkers van iO te ondersteunen in hun dagelijkse werkzaamheden door intelligente opslag en generatie van testcases.

## 📝 Beschrijving

qAiO is ontwikkeld als afstudeerproject en biedt QA-professionals de mogelijkheid om:
- **Testcases opslaan** in een vectordatabase voor eenvoudige toegang en hergebruik
- **Intelligente zoekfunctionaliteit** om relevante testcases terug te vinden
- **Geautomatiseerde testcases genereren** inclusief Cypress test opzetten
- **AI-ondersteuning** voor het optimaliseren van QA-workflows

## 🚀 Features

- **Vectordatabase integratie** met ChromaDB voor semantische zoekfunctionaliteit
- **Flask web interface** voor gebruiksvriendelijke interactie
- **OpenAI integratie** voor intelligente testcase generatie
- **Cypress test generatie** voor geautomatiseerde testing
- **Contextbewust zoeken** door testcases en documentatie

## 🛠️ Installatie

### Vereisten

- Python 3.8+
- pip (Python package installer)
- OpenAI API key (of interne iO tooling toegang)

### Stappen

1. **Clone de repository**
   ```bash
   git clone https://github.com/TheMazeIsAmazing/qAiO-Afstudeerproject.git
   cd qAiO-Afstudeerproject

2. **Installeer dependencies**
   ```bash
   pip install -r requirements.txt

3. **Configureer API keys**

De applicatie haalt de API key op via os.getenv('AIO_API_KEY'). Zorg ervoor dat deze environment variabele is ingesteld voordat je de applicatie start.

4. **Start de applicatie**
   ```bash
    python app.py

## 💡 Gebruik

- Testcases opslaan
- Upload of voer testcases in via de web interface. Deze worden automatisch geïndexeerd in de vectordatabase voor semantische zoekopdrachten.
- Testcases zoeken
- Geautomatiseerde tests genereren op basis van de opgeslagen documentatie

## 🏗️ Technische architectuur
- Backend: Flask (Python)
- Database: ChromaDB voor vector opslag
- AI: OpenAI GPT voor natuurlijke taal verwerking
- Frontend: HTML/CSS/JavaScript templates

## 📁 Project structuur
qAiO/ <br>
├── app.py                 # Hoofdapplicatie <br>
├── requirements.txt       # Python dependencies <br>
├── templates/            # HTML templates <br> 
└──static/              # CSS/JS bestanden <br>
