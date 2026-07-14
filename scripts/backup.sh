#!/usr/bin/env bash
#
# Backup diario del Sistema RA UNIMET (§9):
#   - Dump de PostgreSQL (comprimido)
#   - Copia de los archivos xlsx originales (fuente de verdad)
#
# Uso (desde la raíz del proyecto, con docker compose de producción activo):
#   ./scripts/backup.sh
#
# Programar en cron (diario a las 02:00):
#   0 2 * * * cd /ruta/al/proyecto && ./scripts/backup.sh >> /var/log/sistema_ra_backup.log 2>&1
#
set -euo pipefail

FECHA="$(date +%Y%m%d_%H%M%S)"
DESTINO="${BACKUP_DIR:-./backups}"
RETENCION_DIAS="${BACKUP_RETENCION_DIAS:-30}"
COMPOSE="${COMPOSE_CMD:-docker compose -f docker-compose.prod.yml}"

mkdir -p "$DESTINO"

echo "[$(date)] Iniciando backup…"

# 1. Dump de PostgreSQL
DB_USER="${POSTGRES_USER:-sistema_ra}"
DB_NAME="${POSTGRES_DB:-sistema_ra}"
ARCHIVO_DB="$DESTINO/db_${FECHA}.sql.gz"
$COMPOSE exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$ARCHIVO_DB"
echo "  Base de datos -> $ARCHIVO_DB"

# 2. Copia de los archivos originales (volumen media)
ARCHIVO_MEDIA="$DESTINO/media_${FECHA}.tar.gz"
$COMPOSE run --rm -T -v "$(pwd)/$DESTINO:/backup" web \
  tar czf "/backup/media_${FECHA}.tar.gz" -C /app media
echo "  Archivos originales -> $ARCHIVO_MEDIA"

# 3. Rotación: borrar backups más viejos que RETENCION_DIAS
find "$DESTINO" -name "db_*.sql.gz" -mtime +"$RETENCION_DIAS" -delete
find "$DESTINO" -name "media_*.tar.gz" -mtime +"$RETENCION_DIAS" -delete

echo "[$(date)] Backup completado. Retención: ${RETENCION_DIAS} días."
