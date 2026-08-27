from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ENV_DB_PATH = os.getenv("DB_PATH")
# SQLite remains convenient for local development. Production should provide a
# postgresql:// (or postgres://) URL through the hosting provider's secrets.
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DATA_DIR / 'educational_platform.db'}"

if ENV_DB_PATH:
    DB_PATH = Path(ENV_DB_PATH)
elif DATABASE_URL.startswith("sqlite:///"):
    # ``sqlite:///relative.db`` and ``sqlite:////absolute/path.db`` are both
    # valid URLs. Keep the leading slash for an absolute path.
    DB_PATH = Path(DATABASE_URL.removeprefix("sqlite:///"))
else:
    # PostgreSQL is not a filesystem path. This value is only kept for legacy
    # callers; the database adapter uses DATABASE_URL directly.
    DB_PATH = DATA_DIR / "educational_platform.db"

if DATABASE_URL.startswith("sqlite:///"):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

LEVELS = [
    {"id": 1, "title": "Fonética y Fonología", "activities": ["Detective Fonético", "Arrastra la Prosodia", "Reconstruye el Discurso"]},
    {"id": 2, "title": "Morfología", "activities": ["Arquitecto de Palabras", "Máquina Léxica", "Clasificador Morfológico"]},
    {"id": 3, "title": "Sintaxis", "activities": ["Construye Oraciones", "Detective del Error", "Gramática en Contexto"]},
    {"id": 4, "title": "Semántica", "activities": ["Mapa Conceptual", "Lenguaje Figurado", "Análisis de Texto"]},
    {"id": 5, "title": "Pragmática", "activities": ["Lee entre Líneas", "Cliente Difícil", "Auditor Organizacional"]},
    {"id": 6, "title": "Discurso Organizacional", "activities": ["CSI Discurso", "Simulador Profesional"]},
]

ACTIVITY_TYPES = [
    "Drag & Drop",
    "Escape Room",
    "Matching",
    "Hotspot",
    "Puzzles",
    "Clasificación",
    "Líneas de tiempo",
    "Videos interactivos",
    "Audios interactivos",
    "Simuladores",
    "Casos",
    "Misiones",
    "Retos colaborativos",
]
