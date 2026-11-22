# CIUX Birthday Assistant V3

An intelligent, conversational Birthday Assistant web application built with Python, Flask, Pandas, and Rule-Based Natural Language Understanding (NLU).

The application allows users to ask questions about birthdays, locations, and relationships in natural language. All factual information is retrieved strictly from the Excel dataset (`data/people.xlsx`). **The assistant never hallucinates or invents personal details, dates, or relationships.**

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [V3 Features](#2-v3-features)
3. [Architecture](#3-architecture)
4. [Technologies Used](#4-technologies-used)
5. [Folder Structure](#5-folder-structure)
6. [Installation (Windows PowerShell)](#6-installation-windows-powershell)
7. [Python Setup & Compatibility](#7-python-setup--compatibility)
8. [VS Code Setup](#8-vs-code-setup)
9. [Virtual Environment Setup](#9-virtual-environment-setup)
10. [Dataset Setup](#10-dataset-setup)
11. [How to Run the Application](#11-how-to-run-the-application)
12. [How to Use the Chatbot](#12-how-to-use-the-chatbot)
13. [Example Queries](#13-example-queries)
14. [How to Run Tests](#14-how-to-run-tests)
15. [Troubleshooting & FAQs](#15-troubleshooting--faqs)

---

## 1. Project Overview

The **CIUX Birthday Assistant V3** is designed to provide immediate, factual answers to birthday queries while retaining conversational context across multi-turn dialogues. 

- **100% Fact-Grounded**: All answers come directly from `data/people.xlsx`.
- **Zero External API Dependency**: Operates completely offline without requiring third-party API keys.
- **Session-Isolated Dialogue Memory**: Supports continuous conversational follow-ups such as *"Show my nephews' birthdays in September"*, followed by *"What about October?"*, *"How many?"*, and *"Where does Rahul live?"*.

---

## 2. V3 Features

1. **Birthday Search**: Search birthdays across months, relationships, and names.
2. **Search by Month**: Full month name or numeric filtering (January–December).
3. **Search by Relationship**: Plural/singular normalization for nephew, niece, friend, brother, sister, cousin, spouse, etc.
4. **Search by Name**: Lookup by full name, first name, or nickname.
5. **Search by Person ID**: Direct ID lookup (e.g., `P001`, `P004`).
6. **Count Birthdays**: Count birthdays matching any criteria or count previous filtered results (*"How many?"*).
7. **Upcoming Birthdays**: 30-day rolling birthday projection handling past birthdays in the current year, leap years (Feb 29), and next-year transitions.
8. **Tomorrow's Birthdays**: Instant identification of birthdays occurring tomorrow.
9. **Next Month's Birthdays**: Automatic calculation and search for next month's celebrations.
10. **Person Location**: Look up residential place of stay (`Place_of_Stay`) for any individual.
11. **Person Birthday**: Exact date of birth lookup with formatted dates.
12. **Rule-Based NLU**: 7 core intents and 6 entity extractors returning a consistent JSON structure.
13. **Conversational Memory**: Maintains previous intent, person, relationship, month, query, and results.
14. **Context-Aware Follow-Up Queries**: Automatically reuses previous context.
15. **Ambiguity Clarification**: Prompts user when multiple individuals match a surname or partial name.
16. **Session Reset**: One-click and endpoint-based memory reset (`POST /reset`).
17. **Live Debug Panel**: Real-time inspector displaying detected intent, extracted entities, and session state.
18. **Modern Responsive UI**: Clean light-theme interface with blue accents and suggested questions.

---

## 3. Architecture

```
[ User Browser Interface ]
          │
          │ HTTP / JSON (POST /chat, POST /reset, GET /)
          ▼
┌────────────────────────────────────────────────────────┐
│ Flask Web Server (app.py)                              │
│ - Session management (cookie-signed session state)     │
│ - JSON validation and HTTP error handling              │
│ - Serves static CSS, JavaScript, and HTML templates    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Dialogue Manager (dialogue.py)                         │
│ - Multi-turn conversation state (DialogueState)        │
│ - Resolves contextual follow-ups ("What about Oct?")   │
│ - Handles pronoun & bare count queries ("How many?")   │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
                ▼                        ▼
┌────────────────────────┐      ┌────────────────────────┐
│ NLU Engine (nlu.py)    │      │ Birthday Service       │
│ - Rule-based intent    │      │ (service.py)           │
│   recognition          │      │ - Dynamic column map   │
│ - Entity extraction    │      │ - Upcoming rolling calc│
│ - Standard structure   │      │ - Pandas queries       │
└────────────────────────┘      └───────────┬────────────┘
                                            │
                                            ▼
                                  [ data/people.xlsx ]
```

---

## 4. Technologies Used

- **Python 3.10 - 3.14**: Backend programming language.
- **Flask 3.1+**: Web framework and session management.
- **Pandas 2.2+**: High-performance Excel ingestion, data cleaning, and query engine.
- **OpenPyXL 3.1+**: Excel file format engine.
- **Pytest 8.0+ & Unittest**: Automated testing frameworks.
- **HTML5, CSS3, Modern JavaScript**: Lightweight, responsive frontend with zero external dependencies.

---

## 5. Folder Structure

```
CIUX_Birthday_Assistant_V3/
│
├── app.py                  # Flask web application & API routes
├── nlu.py                  # Rule-based intent recognition & entity extraction
├── service.py              # Data processing, search, upcoming calculations
├── dialogue.py             # Conversation memory & follow-up dialogue resolution
├── config.py               # Centralized configuration (pathlib, cross-platform)
├── requirements.txt        # Pinned dependencies
├── README.md               # Beginner-friendly documentation
├── .gitignore              # Git ignore configuration
│
├── data/
│   └── people.xlsx         # Factual dataset (100 verified entries)
│
├── templates/
│   └── index.html          # Chatbot interface with Version 3 badge
│
├── static/
│   ├── style.css           # Professional light-theme styles with blue accents
│   └── chat.js             # Client controller, markdown renderer, debug inspector
│
└── tests/
    ├── test_nlu.py         # NLU intent & entity extraction unit tests
    ├── test_service.py     # Data service & query unit tests
    └── test_dialogue.py    # Conversation state & follow-up unit tests
```

---

## 6. Installation (Windows PowerShell)

Open **Windows PowerShell** and run:

### Step 1: Navigate to Project Directory
```powershell
cd CIUX_Birthday_Assistant_V3
```

### Step 2: Create Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate Virtual Environment
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

## 7. Python Setup & Compatibility

- Compatible with Python **3.10, 3.11, 3.12, 3.13, and 3.14**.
- Uses `pathlib.Path` for cross-platform path handling.
- To check your Python version:
  ```powershell
  python --version
  ```

---

## 8. VS Code Setup

1. Open VS Code:
   ```powershell
   code .
   ```
2. Press `Ctrl + Shift + P` and search for **Python: Select Interpreter**.
3. Choose `.\venv\Scripts\python.exe`.
4. Open the terminal inside VS Code (`Ctrl + ~`) to run commands directly.

---

## 9. Virtual Environment Setup

Verify that the virtual environment is active:
```powershell
Get-Command python | Select-Object -ExpandProperty Source
```
The output should point to `...\CIUX_Birthday_Assistant_V3\venv\Scripts\python.exe`.

---

## 10. Dataset Setup

- The dataset is located at `data/people.xlsx`.
- Columns are dynamically recognized:
  - `Person_ID`
  - `Name`
  - `DOB`
  - `Relationship`
  - `Place_of_Stay`
  - `Nickname`, `Relationship_Group`, `Notes` (optional)
- Missing dates, duplicate entries, and inconsistent casing are cleaned automatically during loading.

---

## 11. How to Run the Application

Start the Flask server:

```powershell
python app.py
```

Expected terminal output:
```text
[INFO] CIUX_V3_App: Initializing BirthdayService...
[INFO] service: Loaded 100 records from ...\data\people.xlsx
[INFO] CIUX_V3_App: Initializing DialogueManager...
[INFO] CIUX_V3_App: CIUX Birthday Assistant V3 backend initialized successfully.
[INFO] CIUX_V3_App: Starting CIUX Birthday Assistant V3 on http://127.0.0.1:5000
```

---

## 12. How to Use the Chatbot

1. Open your browser and go to `http://127.0.0.1:5000`.
2. Type a query in the input box or click any of the suggested question buttons.
3. Use the **Debug** button in the header to view detected intent, entities, and conversation state.
4. Use the **Reset Chat** button to clear conversational memory.

---

## 13. Example Queries

### A. Single-Turn Inquiries
- `"Show birthdays in September"`
- `"Show my nephews' birthdays"`
- `"How many people have birthdays in January?"`
- `"When is Rahul's birthday?"`
- `"Where does Rahul live?"`
- `"Show upcoming birthdays"`
- `"Show birthdays tomorrow"`
- `"Show next month's birthdays"`

### B. Multi-Turn Follow-Up Dialogue (Conversational Memory)
- **User**: `"Show my nephews' birthdays in September."`
  - *Assistant shows Bharath Rao, Rahul Patil, and Nikhil Bhat.*
- **User**: `"What about October?"`
  - *Assistant remembers relationship = nephew and displays Nikhil Hegde!*
- **User**: `"How many?"`
  - *Assistant counts the previous filtered results: 1 birthday.*
- **User**: `"Where does Rahul live?"`
  - *Assistant looks up Rahul Patil and returns Bengaluru.*

---

## 14. How to Run Tests

Run the full automated test suite using either `unittest` or `pytest`:

### Run with Python unittest:
```powershell
python -m unittest discover tests
```

### Run with pytest:
```powershell
python -m pytest tests -v
```

All 24 automated tests pass, testing:
- Rule-based intent recognition and entity extraction across all 7 intents.
- Combined filtering, count, person birthday, location, upcoming calculation, and leap year handling.
- Dialogue memory, follow-up resolution, bare count (*"How many?"*), pronoun tracking, and reset.

---

## 15. Troubleshooting & FAQs

### Q: Why do I see an execution policy error when activating venv?
**A**: Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in PowerShell, then re-run `.\venv\Scripts\Activate.ps1`.

### Q: How do I change the upcoming birthday window?
**A**: Update `DEFAULT_UPCOMING_DAYS` in `config.py` (default is 30 days).

### Q: Does V3 require an OpenAI API key or internet access?
**A**: No! V3 is designed with a 100% self-contained Rule-Based NLU engine that operates completely offline.
