"""
config.py - Centralized Configuration for CIUX Birthday Assistant V2.
Uses pathlib for robust cross-platform path handling on Windows.
"""

from pathlib import Path

# Base directory: absolute path to project root
BASE_DIR = Path(__file__).resolve().parent

# Dataset path: single source of truth
DATA_DIR = BASE_DIR / "data"
EXCEL_PATH = DATA_DIR / "people.xlsx"

# Flask Server Configuration - MUST use port 5002 (Do not use 5000)
HOST = "127.0.0.1"
PORT = 5002
DEBUG = True
SECRET_KEY = "ciux_birthday_assistant_v2_secret_key"

# Service parameters
DEFAULT_UPCOMING_DAYS = 30
