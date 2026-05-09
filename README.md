# Feliz Día de la Madre - Aplicación Flask

Esta es una aplicación web simple creada con Flask para celebrar el Día de la Madre.

## Instalación

1. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

2. Ejecuta la aplicación:
   ```
   python main.py
   ```

3. Abre tu navegador y ve a `http://127.0.0.1:5000/`

## Características

- Página de inicio con mensaje de Feliz Día de la Madre
- Base de datos SQLite con mensajes de amor
- Estilo rosa con efectos hover en botones
- Botón para cambiar el color de fondo aleatoriamente
- Navegación simple con botones en el header

## Estructura del Proyecto

- `main.py`: Aplicación Flask principal
- `db.py`: Configuración de la base de datos
- `templates/index.html`: Plantilla HTML
- `static/css/style.css`: Estilos CSS
- `static/js/script.js`: JavaScript para interactividad
- `requirements.txt`: Dependencias de Python

## Solución de Problemas

- Si hay errores al ejecutar, asegúrate de tener Flask instalado.
- La base de datos se crea automáticamente al ejecutar la aplicación.