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

## Publicación en producción

La aplicación que se publica es Flask (`app.py` y `app/templates`). La carpeta
`frontend/` contiene un prototipo React independiente y **no debe desplegarse
como una segunda página** hasta que se integre con las rutas y la API de Flask.

1. Crea una base PostgreSQL administrada (por ejemplo, Supabase) y copia su
   cadena de conexión en `DATABASE_URL`.
2. En Render crea un servicio web Python con:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
3. Configura estas variables privadas en Render (nunca en Git):

   ```text
   APP_ENV=production
   DATABASE_URL=postgresql://...
   SECRET_KEY=<clave larga y aleatoria>
   INITIAL_TEACHER_NAME=Nombre docente
   INITIAL_TEACHER_EMAIL=docente@ejemplo.com
   INITIAL_TEACHER_PASSWORD=<contraseña inicial fuerte>
   ```

   Las tres variables `INITIAL_TEACHER_*` crean el primer docente una única
   vez. Después del primer despliegue elimina `INITIAL_TEACHER_PASSWORD` del
   panel de Render. No existe una cuenta docente ni una contraseña escrita en
   el repositorio.

4. Registra una cuenta de prueba y confirma que puedes iniciar sesión,
   guardar avance, abrir el panel docente y crear una observación.

SQLite se mantiene solo para desarrollo local. PostgreSQL es la opción que
conserva datos de usuarios en la nube entre despliegues y permite crecer.

## Estructura

- app/: backend Flask modular
- frontend/: frontend React + Vite
- data/: base de datos y recursos
- scripts/: scripts de instalación y ejecución
