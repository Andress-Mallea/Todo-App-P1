FROM python:3.11-slim

WORKDIR /site

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código al directorio /site/
COPY . /site/

# --- LO NUEVO PARA LAS MIGRACIONES ---
# Dar permisos de ejecución al script de arranque
RUN chmod +x /site/entrypoint.sh

# EXPOSE es documentación: indica qué puerto pretende usar la aplicación
EXPOSE 8000

# Definir el script como el punto de entrada oficial que siempre se ejecuta primero
ENTRYPOINT ["/site/entrypoint.sh"]

# El comando principal de tu aplicación (Este pasa a ser el "$@" del entrypoint)
CMD ["python", "app.py"]