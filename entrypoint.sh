#!/bin/sh
set -e
# Las migraciones pertenecen exclusivamente al servicio Django migrate.
exec "$@"
