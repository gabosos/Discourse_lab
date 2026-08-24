# Discourse Lab

Discourse Lab es una plataforma educativa gamificada orientada a contenido de lingüística y discurso organizacional.

## Requisitos

- Python 3.9+
- Node.js 20+
- npm

## Instalación backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Instalación frontend

```bash
cd frontend
npm install
```

## Ejecución

```bash
python3 app.py
cd frontend && npm run dev
```

## Estructura

- app/: backend Flask modular
- frontend/: frontend React + Vite
- data/: base de datos y recursos
- scripts/: scripts de instalación y ejecución
