set -e

# Si no existe la carpeta de migraciones, la inicializa
if [ ! -f migrations/env.py ]; then
  echo "Inicializando Flask-Migrate..."
  flask db init
fi

# Si no hay ninguna migración, genera la inicial a partir de los modelos
if ! ls migrations/versions/*.py >/dev/null 2>&1; then
  echo "Generando migración inicial..."
  flask db migrate -m "initial"
fi

echo "Aplicando migraciones..."
flask db upgrade

echo "Creando usuarios por defecto..."
python seed.py

echo "Poblando datos del restaurante..."
python seed_restaurant.py

exec "$@"