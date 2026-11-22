# CIUX Birthday Assistant – Version 5 (V5)

An intelligent, multimodal Birthday Assistant chatbot that allows users to ask questions about birthdays, people, relationships, locations, upcoming birthdays, and birthday counts using natural language, voice input, and optional speech synthesis.

The chatbot is **strictly grounded** in the provided Excel dataset (`data/people.xlsx`) as its single source of truth. It never hallucinates or fabricates birthdays, names, locations, relationships, or dates.

---

## 🌟 Version Evolution (V1 to V5)

| Version | Focus | Core Capabilities | Limitations / Motivation |
|---|---|---|---|
| **V1** | Keyword-Based Lookup | Basic substring and token matching on Excel rows. | Strict phrasing requirements; unable to handle variations or missing fields. |
| **V2** | Intent & Entity Architecture | Regex and pattern-based NLU pipeline; structured intents and entity slots. | Single-turn only; queries had to contain all information every time. |
| **V3** | Multi-Turn Dialogue Context | Dialogue state manager tracking previous entities (relationships, months, people). | Inability to resolve nuanced natural language phrasing without strict rules. |
| **V4** | LLM-Assisted NLU | Hybrid architecture: LLM parses complex intent/entities with rule-based fallback. | Text-only interface. |
| **V5 (Current)** | **Multimodal Voice & UI** | **Voice input (SpeechRecognition `en-IN`), Voice output (Text-to-Speech `SpeechSynthesisUtterance`), Live diagnostic debug drawer, and full offline resilience.** | **Complete, production-ready conversational system.** |

---

## 🚀 Key Features in V5

1. **Birthday Search:** Look up birthdays by month, date, or person name.
2. **Search by Month:** Filter birthdays occurring in any calendar month (January to December, plus abbreviations).
3. **Search by Relationship:** Filter birthdays across relationships (Nephew, Niece, Uncle, Aunt, Colleague, Friend, etc.).
4. **Search by Person Name & ID:** Case-insensitive search supporting full names, first names, nicknames, and Person IDs (`P001`, `P004`).
5. **Birthday Counting:** Accurate counts matching complex conditions (e.g., *"How many nephews have birthdays in October?"*).
6. **Upcoming Celebrations:** Calculates exact days remaining until next birthday, upcoming age, and chronologically sorts upcoming birthdays within a 30-day window (configurable).
7. **Tomorrow's Birthdays:** Instantly identifies celebrations happening tomorrow.
8. **Next Month's Celebrations:** Automatically calculates next month's calendar window and rolls over December to January.
9. **Person Location Lookup:** Queries residential locations (`Place_of_Stay`) (e.g., *"Where does Rahul live?"*).
10. **Context-Aware Dialogue Management:** Retains conversation memory across turns. Follow up seamlessly with *"What about October?"* or *"Where does he live?"*.
11. **Rule-Based NLU:** Comprehensive pattern-matching engine for offline and deterministic query parsing.
12. **LLM-Assisted NLU:** Structured JSON output via OpenAI API for conversational understanding.
13. **Zero-Crash Graceful Fallback:** If the OpenAI API key is missing, network drops, or rate limit occurs, the assistant immediately falls back to rule-based NLU without crashing.
14. **Voice Input (Speech-to-Text):** Integrated Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) configured for Indian English (`en-IN`).
15. **Voice Output (Text-to-Speech):** Clean speech synthesis via `SpeechSynthesisUtterance` with markdown stripping and audio queue management.
16. **Live Debug Panel:** Collapsible side drawer displaying real-time NLU intent, extracted entities, execution engine, and session context.
17. **Conversation Reset:** Clears conversation memory both on the client and within the secure Flask session.
18. **Prompt Suggestions:** Interactive chips for one-click common inquiries.
19. **Complete Error Handling:** Validates malformed requests, handles empty queries, and tolerates corrupt/missing Excel dates.
20. **Responsive UI:** Clean card layout styled with blue accents, custom avatars, and mobile responsiveness.

---

## 📁 Project Directory Structure

```text
CIUX_Birthday_Assistant_V5/
│
├── app.py                  # Flask web backend and REST endpoints (/chat, /reset)
├── nlu.py                  # Rule-based Natural Language Understanding (Regex & entity matcher)
├── llm_nlu.py              # LLM-assisted NLU with automatic rule-based fallback
├── service.py              # Factual Excel data service & query resolution engine
├── dialogue.py             # Multi-turn conversational context manager
├── config.py               # Cross-platform application settings using pathlib
├── requirements.txt        # Python package dependencies
├── README.md               # Comprehensive project documentation
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules for virtual environments and cache
│
├── data/
│   └── people.xlsx         # Primary Excel dataset (Single Source of Truth)
│
├── templates/
│   └── index.html          # Semantic HTML5 chat interface with Voice UI controls
│
├── static/
│   ├── style.css           # Modern, responsive styling with animations and CSS variables
│   └── chat.js             # Client-side chat logic, Web Speech API & SpeechSynthesis
│
└── tests/
    ├── test_nlu.py         # Unit tests for intent classification and entity extraction
    ├── test_service.py     # Unit tests for dataset filtering, counts, and corrupt DOBs
    └── test_dialogue.py    # Unit tests for multi-turn context carryover and resets
```

---

## 🛠️ Technologies Used

- **Backend:** Python 3.10 – 3.14, Flask 3.x
- **Data Grounding & Analysis:** Pandas, OpenPyXL
- **Natural Language Understanding:** Regular Expressions (Rule-Based) + OpenAI Python SDK (Structured JSON Output)
- **Frontend:** HTML5, CSS3 (Flexbox/Grid, CSS Variables, Animations), Vanilla JavaScript (ES6+)
- **Voice APIs:** Web Speech API (`SpeechRecognition`, `webkitSpeechRecognition`, `speechSynthesis`)
- **Testing:** Python `unittest` framework (fully compatible with `pytest`)

---

## 💻 Prerequisites & Setup (Windows & VS Code)

### 1. Python Installation
- Ensure **Python 3.10 or higher** (Python 3.11, 3.12, 3.13, or 3.14) is installed.
- Verify in PowerShell:
  ```powershell
  python --version
  ```

### 2. Open Project in VS Code
1. Launch **Visual Studio Code**.
2. Go to **File** > **Open Folder...**
3. Select `CIUX_Birthday_Assistant_V5`.

### 3. Create and Activate Virtual Environment
Open the built-in VS Code Terminal (`Ctrl + ~`) in PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> **Note for Windows Execution Policy:** If PowerShell reports script execution is disabled, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Install Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## ⚙️ Configuration & Environment (.env)

1. Create a `.env` file from the provided `.env.example`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Open `.env` and configure settings:
   ```env
   # Flask Session Security
   SECRET_KEY=ciux_v5_secret_key_change_in_production
   FLASK_DEBUG=True

   # Optional OpenAI API Key for LLM-Assisted NLU
   # If left blank, the system automatically uses Rule-Based NLU.
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini

   # Days for upcoming birthday calculation
   UPCOMING_DAYS=30
   ```

---

## 📊 Dataset Placement & Column Adaptation

The Excel file is located at:
```text
data/people.xlsx
```

The service dynamically detects and maps standard column header variants:
- **ID:** `Person_ID`, `ID`, `Pid`
- **Name:** `Name`, `Full_Name`, `Person_Name`
- **Date of Birth:** `DOB`, `DateOfBirth`, `BirthDate`
- **Relationship:** `Relationship`, `Relation`
- **Location:** `Place_of_Stay`, `Place`, `Location`, `City`
- **Optional Details:** `Nickname`, `Relationship_Group`, `Relationship_Detail`, `Notes`

---

## ▶️ Running the Application

In your activated virtual environment, execute:

```powershell
python app.py
```

You will see output indicating the dataset is loaded:
```text
INFO [CIUX_App]: Initializing BirthdayService with dataset: ...\data\people.xlsx
INFO [CIUX_App]: Dataset loaded successfully with 146 registered persons.
INFO [CIUX_App]: Starting CIUX Birthday Assistant V5 on http://127.0.0.1:5005
```

Open your web browser and navigate to:
```text
http://127.0.0.1:5005
```

---

## 🎙️ Using Voice Features

### 1. Voice Input (Speech-to-Text)
- Click the **Microphone** button next to the message input.
- Allow browser microphone permission when prompted.
- The button glows red and displays **"Listening... Speak now"**.
- Speak your query (e.g., *"Show birthdays in September"* or *"Where does Rahul live?"*).
- The recognized text automatically populates the input field and sends the query.

### 2. Voice Output (Text-to-Speech)
- Toggle the **Voice Response** switch in the top header.
- When enabled, the assistant reads out the factual results aloud using an English (India) `en-IN` synthesized voice.
- Markdown tags, bullet symbols, and emojis are automatically stripped before speaking so it sounds natural.
- Pressing **Reset** or speaking a new query immediately cancels any ongoing speech.

### 3. Browser Compatibility for Voice
- **Google Chrome** (Recommended): Full support for SpeechRecognition and SpeechSynthesis.
- **Microsoft Edge**: Full support for SpeechRecognition and SpeechSynthesis.
- **Firefox / Safari**: Supports SpeechSynthesis (Voice Output). If SpeechRecognition is unavailable, standard keyboard input functions seamlessly.

---

## 🧪 Running the Test Suite

Run all unit tests using Python's standard `unittest` discovery:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Or using `pytest`:
```powershell
pytest -v
```

All 23 unit tests cover:
- **`test_nlu.py`:** Intent classification (`birthday_search`, `count_birthdays`, `upcoming_birthdays`, `person_place`, `person_birthday`, `tomorrow_birthdays`), entity extraction (months, relationships, IDs, names, relative dates).
- **`test_service.py`:** Month filtering, relationship filtering, countdown math, person birthday, person location, empty results, corrupt DOB handling with temporary test datasets.
- **`test_dialogue.py`:** Context tracking, session isolation, ellipsis resolution (*"What about October?"*), pronoun resolution (*"Where does he live?"*), entity overriding, and context resets.

---

## 💬 Benchmark Test Questions

Try asking the assistant these queries in order to experience context-awareness:

| Step | Query | Intent Recognized | Expected Factual Behavior |
|---|---|---|---|
| 1 | *"Show my nephews' birthdays in September"* | `birthday_search` | Lists Bharath Rao (02 Sep), Rahul Patil (18 Sep), and Nikhil Bhat (25 Sep). |
| 2 | *"What about October?"* | `birthday_search` (Contextual) | Automatically carries over **Nephew** as relationship and shows Nikhil Hegde (03 Oct). |
| 3 | *"Where does Rahul live?"* | `person_place` | Identifies Rahul Patil and responds: *"Rahul Patil lives in Bengaluru."* |
| 4 | *"When is his birthday?"* | `person_birthday` (Contextual) | Resolves pronoun *"his"* to Rahul and outputs: *"Rahul Patil's birthday is on 18 September 2004."* |
| 5 | *"How many nephews have birthdays in October?"* | `count_birthdays` | Returns: *"There is 1 birthday for Nephew(s) in October: Nikhil Hegde on 03 October 2001."* |
| 6 | *"Show upcoming birthdays"* | `upcoming_birthdays` | Calculates days remaining from today and lists upcoming birthdays chronologically. |
| 7 | *"Who has a birthday tomorrow?"* | `tomorrow_birthdays` | Checks exact calendar day + 1. |
| 8 | *"Find person P001"* | `birthday_search` / `person_id` | Displays Lakshmi Rao's details. |

---

## 🔍 Diagnostics & Debug Panel

- Turn on the **Debug Info** toggle switch in the header.
- The right side panel opens to reveal real-time JSON diagnostics:
  ```json
  {
    "intent": "birthday_search",
    "entities": {
      "person_name": null,
      "person_id": null,
      "month": 10,
      "relationship": "Nephew",
      "relative_date": null,
      "relative_month": null
    },
    "engine": "rule_based",
    "query_type": "birthday_search",
    "records_found": 1,
    "context": {
      "last_person": "Rahul",
      "last_relationship": "Nephew",
      "last_month": 10,
      "last_intent": "birthday_search"
    }
  }
  ```

---

## ❓ Troubleshooting

1. **`ModuleNotFoundError: No module named 'flask'`**
   - Ensure your virtual environment is activated (`.\venv\Scripts\Activate.ps1`).
   - Run `python -m pip install -r requirements.txt`.

2. **Microphone permission denied:**
   - In Chrome/Edge, click the tune/lock icon in the address bar next to `127.0.0.1:5005` and set **Microphone** to **Allow**.

3. **OpenAI API Key errors:**
   - If you do not have an OpenAI API key, leave `OPENAI_API_KEY=` blank in `.env`. The chatbot will automatically run in Rule-Based NLU mode with zero downtime or errors.

4. **Port in use:**
   - Modify `FLASK_PORT=5006` in your `.env` file and re-run `python app.py`.
