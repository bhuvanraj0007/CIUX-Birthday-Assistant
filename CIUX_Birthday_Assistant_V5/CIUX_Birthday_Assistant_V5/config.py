"""
config.py - Configuration settings for CIUX Birthday Assistant V5.
Uses pathlib for robust cross-platform path handling on Windows and Linux.
"""

import os
from pathlib import Path

# Base directory: absolute path to project root
BASE_DIR = Path(__file__).resolve().parent

# Attempt to load environment variables from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# Flask settings
SECRET_KEY = os.environ.get("SECRET_KEY", "ciux_birthday_assistant_v5_secret_default_key_2026")
DEBUG_MODE = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

# Dataset settings
DATA_DIR = BASE_DIR / "data"
EXCEL_PATH = DATA_DIR / "people.xlsx"

# Service settings
DEFAULT_UPCOMING_DAYS = int(os.environ.get("UPCOMING_DAYS", "30"))

# LLM NLU settings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()

# Server settings
HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
PORT = int(os.environ.get("FLASK_PORT", "5005"))
