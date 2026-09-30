#!/bin/sh
# aborta el script si algún comando falla
set -e 

if [ -d migrations ]; then
  echo "Applying database migrations..."
  flask db upgrade
fi

# Reemplaza el proceso actual con el comando principal (ej. gunicorn)
exec "$@"