# CIUX Birthday Assistant V4

An intelligent, conversational Birthday Assistant web application built with Python, Flask, Pandas, and a Hybrid Natural Language Understanding (LLM + Rule-Based NLU) engine. 

The assistant allows users to query birthday, relationship, and residential information using natural language. All factual data is strictly retrieved from the Excel dataset (`data/people.xlsx`). **The AI never hallucinates or invents personal information, dates, or relationships.**

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [V4 Architecture](#2-v4-architecture)
3. [Key Features](#3-key-features)
4. [Technologies Used](#4-technologies-used)
5. [Folder Structure](#5-folder-structure)
6. [Installation Guide (Windows PowerShell)](#6-installation-guide-windows-powershell)
7. [VS Code Setup](#7-vs-code-setup)
8. [Python Setup & Compatibility](#8-python-setup--compatibility)
9. [Virtual Environment Setup](#9-virtual-environment-setup)
10. [Dependency Installation](#10-dependency-installation)
11. [Excel Dataset Setup](#11-excel-dataset-setup)
12. [API Key Configuration](#12-api-key-configuration)
13. [How to Run the Application](#13-how-to-run-the-application)
14. [How to Access the Website](#14-how-to-access-the-website)
15. [Automated Testing](#15-automated-testing)
16. [Example Queries to Test](#16-example-queries-to-test)
17. [Troubleshooting & FAQs](#17-troubleshooting--faqs)

---

## 1. Project Overview

The **CIUX Birthday Assistant V4** is a conversational AI system designed to answer questions about birthdays, age milestones, upcoming events, and personal locations. It enforces **strict factual grounding**:
- The Excel file (`data/people.xlsx`) is the **sole source of truth**.
- Natural language queries are processed to extract *intents* and *entities*.
- When an OpenAI API key is supplied, OpenAI LLM (`gpt-4o-mini`) handles semantic parsing into structured JSON.
- If no API key is provided, or if the API is unreachable, the system automatically falls back to an internal **Rule-based NLU engine** without any disruption to the user experience.
- Dialogue memory supports multi-turn conversations (e.g. asking *"Show my nephews' birthdays in September"* followed by *"What about October?"* and *"Where does Rahul live?"*).

---

## 2. V4 Architecture

The application is structured into decoupled, single-responsibility layers:

```
[ User in Browser ]
        │  (HTTP / JSON)
        ▼
┌────────────────────────────────────────────────────────┐
│ Flask Web Server (app.py)                              │
│ - Serves Index UI                                      │
│ - /chat (Processes messages & tracks Flask sessions)   │
│ - /reset (Clears conversational memory)                │
│ - /api/health (Service & Dataset monitoring)           │
└───────────────┬────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────┐
│ Dialogue Manager (dialogue.py)                         │
│ - Session memory (DialogueState)                       │
│ - Follow-up query context merging                      │
│ - Disambiguation & clarification triggers              │
└───────────────┬────────────────────────────────────────┘
                │
        ┌───────┴────────────────────────┐
        ▼                                ▼
┌────────────────────────┐      ┌────────────────────────┐
│ Hybrid NLU Engine      │      │ Birthday Service       │
│ (llm_nlu.py & nlu.py)  │      │ (service.py)           │
│ - OpenAI JSON mode     │      │ - Dynamic column map   │
│ - Rule-based fallback  │      │ - Upcoming window calc │
│ - Entity normalization │      │ - Pandas queries       │
└────────────────────────┘      └───────────┬────────────┘
                                            │
                                            ▼
                                  [ data/people.xlsx ]
```

---

## 3. Key Features

1. **Birthday Search**: Find birthdays across months, relationships, and names.
2. **Search Birthdays by Month**: Filter birthdays for any calendar month (January to December).
3. **Search by Relationship**: Query friends, nephews, nieces, colleagues, cousins, spouse, etc., with automatic plural-to-singular normalization.
4. **Search by Person Name**: Search by full name, first name, or nickname.
5. **Search by Person ID**: Direct lookup by ID (e.g., `P001`, `P004`).
6. **Count Birthdays**: Count birthdays matching specific criteria (e.g., *"How many nephews have birthdays in October?"*).
7. **Upcoming Birthdays**: Predict upcoming birthdays within a rolling 30-day window, handling birthdays that already passed this year, leap year births, and next-year transitions.
8. **Tomorrow's Birthdays**: Instant lookup of birthdays happening tomorrow.
9. **Next Month's Birthdays**: Filter birthdays occurring in the subsequent calendar month.
10. **Person Location Search**: Look up residential place of stay (`Place_of_Stay`) for any individual.
11. **Rule-Based Intent Recognition**: Pattern and regex-driven intent classifier.
12. **Entity Extraction**: Extracts `person_name`, `person_id`, `month`, `relationship`, `relative_date`, and `relative_month`.
13. **LLM-Powered NLU**: Uses OpenAI Python SDK with structured JSON mode for intent/entity parsing.
14. **Rule-Based NLU Fallback**: Seamless zero-config fallback when OpenAI API key is unavailable or offline.
15. **Conversation Context Management**: Per-session conversational state tracking.
16. **Context-Aware Follow-Ups**: Remembers previous relationships, people, and months for chained queries.
17. **Clarification for Ambiguous Queries**: Prompts user when multiple individuals match a surname or token.
18. **Chat Reset**: One-click and endpoint-based memory reset.
19. **Live Debug Panel**: Real-time inspection of detected intent, entities, active NLU engine, and session state.
20. **Error Handling**: Graceful handling of missing files, invalid dates, malformed inputs, and network errors.
21. **Modern Responsive UI**: Clean light-theme interface with blue accents, suggested prompt chips, and mobile responsiveness.

---

## 4. Technologies Used

- **Python 3.10 - 3.14**: Backend programming language.
- **Flask 3.1+**: Lightweight WSGI web framework and session management.
- **Pandas & OpenPyXL**: High-performance Excel ingestion, data cleaning, and query engine.
- **OpenAI Python SDK (v1.0+)**: Optional LLM natural language understanding.
- **Python-Dotenv**: Environment variable configuration.
- **Pytest & Unittest**: Automated unit and integration testing.
- **HTML5, CSS3, Modern JavaScript (ES6+)**: Responsive frontend without external framework overhead.

---

## 5. Folder Structure

```
CIUX_Birthday_Assistant_V4/
│
├── app.py                  # Flask web server and API endpoints
├── nlu.py                  # Rule-based intent recognition and entity extraction
├── llm_nlu.py              # OpenAI LLM integration with automatic rule-based fallback
├── service.py              # Pandas data processing, search, upcoming calculations
├── dialogue.py             # Conversation memory and follow-up dialogue resolution
├── config.py               # Centralized configuration using pathlib
├── requirements.txt        # Pinned project dependencies
├── README.md               # Detailed documentation
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
│
├── data/
│   └── people.xlsx         # Ground-truth Excel dataset
│
├── templates/
│   └── index.html          # Modern light-theme chatbot interface
│
├── static/
│   ├── style.css           # Responsive styles and blue-accent theme
│   └── chat.js             # Client-side chat controller and debug inspector
│
└── tests/
    ├── test_nlu.py         # NLU intent & entity extraction unit tests
    ├── test_service.py     # Data service & query unit tests
    └── test_dialogue.py    # Conversation state & follow-up unit tests
```

---

## 6. Installation Guide (Windows PowerShell)

Open **Windows PowerShell** and follow these steps:

### Step 1: Navigate to the Project Directory
```powershell
cd CIUX_Birthday_Assistant_V4
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(If you see an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once).*

### Step 4: Install Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 7. VS Code Setup

1. Open VS Code:
   ```powershell
   code .
   ```
2. Open the Command Palette (`Ctrl + Shift + P`).
3. Select **Python: Select Interpreter**.
4. Choose the virtual environment: `.\venv\Scripts\python.exe`.
5. Open an integrated terminal in VS Code (`Ctrl + ~`) which will automatically activate `venv`.

---

## 8. Python Setup & Compatibility

- Compatible with **Python 3.10, 3.11, 3.12, 3.13, and 3.14**.
- Uses native `pathlib.Path` objects for 100% Windows and POSIX path compatibility.
- Uses `openpyxl` as the Excel reading engine for Pandas.

---

## 9. Virtual Environment Setup

Always ensure you run inside an isolated virtual environment:

```powershell
# Create venv
python -m venv venv

# Activate venv on Windows PowerShell
.\venv\Scripts\Activate.ps1

# Verify the active Python path
Get-Command python | Select-Object -ExpandProperty Source
```

---

## 10. Dependency Installation

The `requirements.txt` file specifies all required libraries:

```powershell
python -m pip install -r requirements.txt
```

To verify the installation:
```powershell
python -c "import flask, pandas, openpyxl, openai; print('All core libraries imported successfully!')"
```

---

## 11. Excel Dataset Setup

- The factual dataset is located at `data/people.xlsx`.
- Columns supported dynamically:
  - `Person_ID` (or `ID`)
  - `Name` (or `Full_Name`)
  - `DOB` (or `DateOfBirth`)
  - `Relationship` (or `Relation`)
  - `Place_of_Stay` (or `Location`, `City`, `Place`)
  - `Nickname`, `Relationship_Group`, `Notes` (optional)
- The service automatically handles:
  - Missing values (filled cleanly)
  - Duplicate rows (deduplicated by `Person_ID`)
  - Invalid date entries (coerced safely)
  - Whitespace trimming and case-insensitive normalization.

---

## 12. API Key Configuration

The application includes **Hybrid NLU**:
1. **Without API Key (Default)**: The application works **100% out of the box** using the built-in Rule-Based NLU.
2. **With OpenAI API Key**:
   - Copy `.env.example` to `.env`:
     ```powershell
     Copy-Item .env.example .env
     ```
   - Open `.env` and enter your OpenAI key:
     ```ini
     OPENAI_API_KEY=sk-proj-your-actual-api-key-here
     OPENAI_MODEL=gpt-4o-mini
     FLASK_SECRET_KEY=your-custom-secret-key
     DEBUG_MODE=true
     DEFAULT_UPCOMING_DAYS=30
     ```

> **Security Note**: Never commit `.env` containing live API keys. The repository `.gitignore` automatically prevents `.env` from being checked in.

---

## 13. How to Run the Application

Start the Flask development server:

```powershell
python app.py
```

Expected terminal output:
```text
[INFO] CIUX_V4_App: Initializing BirthdayService...
[INFO] service: Loaded 100 valid records from ...\data\people.xlsx
[INFO] CIUX_V4_App: Initializing DialogueManager with Hybrid NLU...
[INFO] CIUX_V4_App: Hybrid NLU ready.
[INFO] CIUX_V4_App: Starting CIUX Birthday Assistant V4 on http://127.0.0.1:5000
```

---

## 14. How to Access the Website

Open your web browser and navigate to:

```
http://127.0.0.1:5000
```

You will see the responsive UI featuring:
- App branding and dataset connection badge.
- Quick prompt buttons for instant questions.
- Chat message history with formatted results.
- Collapsible NLU Debug Inspector panel on the right.

---

## 15. Automated Testing

Run the full automated test suite using either `unittest` or `pytest`:

### Run with Python unittest:
```powershell
python -m unittest discover tests
```

### Run with pytest:
```powershell
python -m pytest tests -v
```

All 25 automated unit and integration tests test:
- Intent recognition across all intents
- Entity extraction (`person_name`, `person_id`, `month`, `relationship`, `relative_date`, `relative_month`)
- Data filtering, upcoming birthday calculations, year transition
- Multi-turn conversation state retention, follow-up queries, pronoun resolution, and chat reset.

---

## 16. Example Queries to Test

Try these natural language questions in the chatbot UI:

### A. Birthday Search
- `"Show birthdays in September"`
- `"Show birthdays of nephews"`
- `"List all friends"`
- `"Birthdays next month"`

### B. Birthday Count
- `"How many nephews have birthdays in October?"`
- `"Count birthdays in September"`
- `"How many friends do I have in the dataset?"`

### C. Upcoming & Relative Dates
- `"Show upcoming birthdays"`
- `"Tomorrow's birthdays"`
- `"Who has birthdays coming up in the next 30 days?"`

### D. Specific Person & Location Lookup
- `"Where does Rahul live?"`
- `"When is Rahul's birthday?"`
- `"Where is Lakshmi Rao located?"`
- `"What is the birthday of P004?"`

### E. Multi-Turn Follow-Up Queries
- **User**: `"Show my nephews' birthdays in September."`
  - *Assistant shows Rahul Patil, Bharath Rao, Nikhil Bhat.*
- **User**: `"What about October?"`
  - *Assistant automatically retains relationship = nephew and displays Nikhil Hegde!*
- **User**: `"Where does Rahul live?"`
  - *Assistant responds that Rahul Patil resides in Bengaluru.*
- **User**: `"When is his birthday?"`
  - *Assistant retains Rahul Patil from context and shows 18 September 2004!*

---

## 17. Troubleshooting & FAQs

### Q: Does the app work without an OpenAI API key?
**A**: Yes! The Hybrid NLU automatically detects when no API key is present and runs using the rule-based NLU engine with 100% functionality.

### Q: How do I change the upcoming birthday window?
**A**: Set `DEFAULT_UPCOMING_DAYS=60` (or your preferred number of days) in `.env` or in `config.py`.

### Q: How do I reset the conversation memory?
**A**: Click the **Reset Chat** button in the top right header, or send a `POST /reset` request.

### Q: Why do I see a warning about PowerShell script execution?
**A**: If `.\venv\Scripts\Activate.ps1` gives an execution policy error, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
This enables virtual environment activation for your current PowerShell session only.
