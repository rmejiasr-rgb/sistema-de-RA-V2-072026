#!/usr/bin/env bash
#
# Restauración de un backup del Sistema RA UNIMET.
#
# Uso:
#   ./scripts/restore.sh backups/db_20260714_020000.sql.gz [backups/media_20260714_020000.tar.gz]
#
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Uso: $0 <dump_db.sql.gz> [media.tar.gz]"
  exit 1
fi

DUMP_DB="$1"
DUMP_MEDIA="${2:-}"
COMPOSE="${COMPOSE_CMD:-docker compose -f docker-compose.prod.yml}"
DB_USER="${POSTGRES_USER:-sistema_ra}"
DB_NAME="${POSTGRES_DB:-sistema_ra}"

echo "ADVERTENCIA: esto sobrescribe la base de datos actual."
read -r -p "¿Continuar? (escriba 'si'): " CONFIRMA
[ "$CONFIRMA" = "si" ] || { echo "Cancelado."; exit 1; }

echo "Restaurando base de datos desde $DUMP_DB…"
gunzip -c "$DUMP_DB" | $COMPOSE exec -T db psql -U "$DB_USER" -d "$DB_NAME"

if [ -n "$DUMP_MEDIA" ]; then
  echo "Restaurando archivos originales desde $DUMP_MEDIA…"
  $COMPOSE run --rm -T -v "$(pwd)/$(dirname "$DUMP_MEDIA"):/backup" web \
    tar xzf "/backup/$(basename "$DUMP_MEDIA")" -C /app
fi

echo "Restauración completada."
