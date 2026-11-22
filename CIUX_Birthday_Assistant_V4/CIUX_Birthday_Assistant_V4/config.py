"""
Configuration Module for CIUX Birthday Assistant V4
Centralizes all environment, directory, Flask, LLM, and dataset configurations.
"""

import os
from datetime import timedelta
from pathlib import Path

# Base Paths (Using pathlib for robust cross-platform / Windows compatibility)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATASET_PATH = DATA_DIR / "people.xlsx"
ENV_PATH = BASE_DIR / ".env"

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH)
except ImportError:
    # Graceful manual fallback if python-dotenv is not installed
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))

# Flask Configuration
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "ciux-birthday-assistant-v4-secret-key-2026")
SESSION_COOKIE_NAME = "ciux_session_v4"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# Server Configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() in ("true", "1", "yes")

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

# Business Logic Configuration
DEFAULT_UPCOMING_DAYS = int(os.getenv("DEFAULT_UPCOMING_DAYS", "30"))
DEFAULT_PAGE_SIZE = 50
