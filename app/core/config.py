from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ENV_DB_PATH = os.getenv("DB_PATH")
DATABASE_URL = os.getenv("DATABASE_URL", str(DATA_DIR / "educational_platform.db"))

if ENV_DB_PATH:
    DB_PATH = Path(ENV_DB_PATH)
elif DATABASE_URL.startswith("sqlite:///"):
    DB_PATH = Path(DATABASE_URL.replace("sqlite://///", "", 1))
else:
    DB_PATH = Path(DATABASE_URL)

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
