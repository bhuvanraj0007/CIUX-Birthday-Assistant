"""
Configuration Module for CIUX Birthday Assistant V3
Centralizes all paths, Flask settings, session parameters, and business logic defaults.
Uses pathlib for robust cross-platform / Windows path resolution.
"""

import os
from datetime import timedelta
from pathlib import Path

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATASET_PATH = DATA_DIR / "people.xlsx"

# Flask Application Settings
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "ciux-birthday-assistant-v3-secret-key-2026")
SESSION_COOKIE_NAME = "ciux_session_v3"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# Server Configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

# Business Logic Defaults
DEFAULT_UPCOMING_DAYS = int(os.getenv("DEFAULT_UPCOMING_DAYS", "30"))
