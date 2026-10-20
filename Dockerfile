FROM python:3.11-slim

WORKDIR /site

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código al directorio /site/
COPY . /site/

# --- LO NUEVO PARA LAS MIGRACIONES ---
# Dar permisos de ejecución al script de arranque
RUN sed -i '1s/^\xEF\xBB\xBF//' /site/entrypoint.sh \
    && sed -i 's/\r$//' /site/entrypoint.sh \
    && chmod +x /site/entrypoint.sh
# EXPOSE es documentación: indica qué puerto pretende usar la aplicación
EXPOSE 8000

# Definir el script como el punto de entrada oficial que siempre se ejecuta primero
ENTRYPOINT ["sh", "/site/entrypoint.sh"]

# El comando principal de tu aplicación (Este pasa a ser el "$@" del entrypoint)
CMD ["gunicorn", "--config", "gunicorn.conf.py", "--bind", "0.0.0.0:8000", "wsgi:app"]