# 🎂 CIUX Birthday Assistant V2

A complete, production-ready, full-stack Natural Language Birthday Assistant powered by **Python**, **Flask**, **Pandas**, and modern web standards.

Version 2 brings robust rule-based Natural Language Understanding (NLU), real-time debug visualization, high-performance dataset filtering, comprehensive automated test suites, and strict execution on **Port 5002**.

---

## 📌 Table of Contents

1. [Key Features](#-key-features)
2. [What's New in Version 2 (V1 vs V2)](#-whats-new-in-version-2-v1-vs-v2)
3. [Important Port Rule](#-important-port-rule)
4. [Technology Stack](#-technology-stack)
5. [Project Folder Structure](#-project-folder-structure)
6. [Windows Setup & Installation](#-windows-setup--installation)
7. [Running the Application](#-running-the-application)
8. [Example Queries & How to Use](#-example-queries--how-to-use)
9. [Dataset Structure](#-dataset-structure)
10. [Automated Testing](#-automated-testing)
11. [Troubleshooting Guide](#-troubleshooting-guide)

---

## ✨ Key Features

- **Single Source of Truth**: Answers are computed directly from `data/people.xlsx`. No names, dates, relationships, or locations are ever invented.
- **Rule-Based NLU Engine (`nlu.py`)**: Accurately recognizes intents (`birthday_search`, `count_birthdays`, `person_place`, `person_birthday`, `upcoming_birthdays`, `tomorrow_birthdays`, `unknown`) and extracts key entities (`person_name`, `person_id`, `month`, `relationship`, `relative_date`).
- **High-Performance Service Logic (`service.py`)**: Computes leap-year-safe upcoming birthdays, tomorrow's birthdays, combined filters (e.g. *nephews born in October*), and counts.
- **Modern Responsive Chat Interface (`templates/` & `static/`)**:
  - Light theme with blue/indigo accents.
  - User and Assistant message bubbles with timestamps.
  - Interactive suggested prompts (one-click query chips).
  - Collapsible real-time **NLU Debug Inspector** showing extracted intents and entities.
  - Reset conversation and keyboard navigation (Enter key).
- **Automated Test Suite (`tests/`)**: 33 unit and integration tests covering NLU parsing, service logic, and API endpoints.

---

## ⚡ What's New in Version 2 (V1 vs V2)

| Feature | Version 1 | Version 2 (Current) |
| :--- | :--- | :--- |
| **Server Port** | Port 5000 | **Port 5002** (Strictly configured) |
| **NLU Architecture** | Basic keyword matching | **Structured Rule-Based NLU (`nlu.py`)** with normalized entity extraction |
| **Debug Visibility** | None | **Live NLU Debug Panel** displaying parsed intents & entities in real time |
| **Combined Queries** | Single condition only | **Multi-condition filtering** (e.g., relationship + month + count) |
| **Upcoming Logic** | Simple calendar lookup | **Smart nearest-birthday calculation** rolling over to next year |
| **Testing** | Manual testing | **Full automated Pytest suite** (33 unit & integration tests) |
| **Configuration** | Hardcoded variables | **Centralized `config.py`** using `pathlib` for Windows path safety |

---

## ⚠️ Important Port Rule

- **Version 1** uses port `5000`.
- **Version 2 MUST use port `5002`**.
- Do not use port `5000`.
- Flask is configured to bind directly to:
  ```
  http://127.0.0.1:5002
  ```

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ / Python 3.14+, Flask
- **Data Engine**: Pandas, OpenPyXL
- **Frontend**: HTML5, CSS3 (Modern Flexbox/Grid), Vanilla JavaScript (ES6+ Fetch API)
- **Testing**: Pytest

---

## 📂 Project Folder Structure

```
CIUX_Birthday_Assistant_V2/
├── app.py                     # Flask backend application & routing (Port 5002)
├── nlu.py                     # Rule-based Natural Language Understanding engine
├── service.py                 # Birthday business logic, filtering & date arithmetic
├── config.py                  # Centralized configuration (pathlib, Port 5002)
├── requirements.txt           # Minimal pinned dependencies
├── README.md                  # Comprehensive documentation
├── .gitignore                 # Excludes venv, pycache, temporary files, etc.
│
├── data/
│   └── people.xlsx            # Primary Excel dataset (100 sample records)
│
├── templates/
│   └── index.html             # Main chatbot user interface
│
├── static/
│   ├── style.css              # Modern light-theme styling with blue accents
│   └── chat.js                # Chat interactions, debug panel updater & async fetch
│
└── tests/
    ├── test_app.py            # Integration tests for Flask endpoints
    ├── test_nlu.py            # Unit tests for intents & entity extraction
    └── test_service.py        # Unit tests for filtering, date calculation & formatting
```

---

## 💻 Windows Setup & Installation

Follow these steps using **Windows PowerShell**:

### 1. Open Windows PowerShell and navigate to the project directory:

```powershell
cd "C:\Users\Bhuvanraj S\.gemini\antigravity\scratch\CIUX_Birthday_Assistant_V2"
```

### 2. Create a Python Virtual Environment:

```powershell
python -m venv venv
```

### 3. Activate the Virtual Environment:

```powershell
.\venv\Scripts\Activate.ps1
```

> *Tip: If you encounter an execution policy restriction in PowerShell, run:*
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

### 4. Install Dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Start the Flask server:

```powershell
python app.py
```

You will see output confirming the server has started on **Port 5002**:

```
==================================================
 CIUX Birthday Assistant V2
 Server running at: http://127.0.0.1:5002
 Note: Port 5002 is active (Port 5000 is NOT used).
==================================================
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5002
```

Open your browser and navigate to:

👉 **[http://127.0.0.1:5002](http://127.0.0.1:5002)**

---

## 💬 Example Queries & How to Use

Click any suggestion chip or type your own question into the chat box:

| Question / Query | Detected Intent | Extracted Entities | Result |
| :--- | :--- | :--- | :--- |
| `Show birthdays in September.` | `birthday_search` | `month: September` | Lists all individuals born in September |
| `How many nephews have birthdays in October?` | `count_birthdays` | `relationship: nephew`, `month: October` | Returns exact count from dataset |
| `Where does Rahul live?` | `person_place` | `person_name: Rahul` | Returns Rahul Patil's place of stay (`Bengaluru`) |
| `When is Rahul's birthday?` | `person_birthday` | `person_name: Rahul` | Returns Rahul's DOB (`2004-09-18`) and relationship |
| `Show upcoming birthdays.` | `upcoming_birthdays` | `relative_date: upcoming` | Returns next birthdays within 30 days sorted by days left |
| `Who has a birthday tomorrow?` | `tomorrow_birthdays` | `relative_date: tomorrow` | Returns records whose birthday falls tomorrow |
| `Find birthday for P004.` | `person_birthday` | `person_id: P004` | Looks up person directly by Person_ID |
| `Count birthdays.` | `count_birthdays` | none | Returns total count of all records in dataset |

---

## 📊 Dataset Structure (`data/people.xlsx`)

The dataset is loaded and cleaned by `service.py`. It inspects:

| Column | Type | Description |
| :--- | :--- | :--- |
| `Person_ID` | String | Unique identifier (e.g., `P001`, `P004`) |
| `Name` | String | Full name (e.g., `Rahul Patil`, `Lakshmi Rao`) |
| `Nickname` | String | Optional short name used for quick matching |
| `DOB` | Date/String | Date of birth (parsed safely into datetime) |
| `Place_of_Stay`| String | City or location (e.g., `Bengaluru`, `Davanagere`) |
| `Relationship` | String | Relationship category (`Nephew`, `Cousin`, `Sister`, etc.) |

---

## 🧪 Automated Testing

Run the complete test suite with **Pytest**:

```powershell
python -m pytest tests -v
```

All 33 test cases will execute:
- **`test_nlu.py`**: Intent recognition, month extraction, relationship normalizations, Person_ID regex, relative date detection, unknown query handling.
- **`test_service.py`**: Dataset loading, month search, relationship search, name lookup, Person_ID lookup, count calculations, leap year upcoming logic, tomorrow's birthdays.
- **`test_app.py`**: Flask endpoints (`/`, `/health`, `/chat`), input validation, and Port 5002 validation.

---

## 🔍 Troubleshooting Guide

### 1. Port 5002 is already in use
If another application is using port 5002, find and stop it in PowerShell:
```powershell
Get-NetTCPConnection -LocalPort 5002 | Select-Object OwningProcess
Stop-Process -Id <ProcessId> -Force
```

### 2. Dataset not found error
Ensure `data/people.xlsx` is present. `config.py` uses `pathlib.Path(__file__).resolve().parent` to reliably locate `data/people.xlsx` regardless of your current terminal directory.

### 3. Missing dependencies
If an import error occurs, ensure your virtual environment is activated and reinstall:
```powershell
pip install -r requirements.txt
```

---

© 2026 CIUX Birthday Assistant V2 Team. Built for speed, clarity, and reliability.
