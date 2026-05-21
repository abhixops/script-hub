#!/bin/bash

set -euo pipefail

LOG_FILE="/tmp/pg_backup.log"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "Starting PostgreSQL backup process."

# Backup Immich PostgreSQL database and tar.bz it
cd /tmp
log "Dumping PostgreSQL database..."
if docker exec -it immich_postgres pg_dump -U postgres immich > /tmp/immich_backup.sql; then
  log "Database dump successful."
else
  log "Database dump failed."
  exit 1
fi

log "Compressing database dump..."
if tar -cjvf immich_backup.tar.bz2 immich_backup.sql; then
  log "Compression successful."
else
  log "Compression failed."
  exit 1
fi

# Upload backup to remote storage with rclone
log "Uploading backup to remote storage..."
if rclone copy /tmp/immich_backup.tar.bz2 garage:immichpg/$(date +%d-%m-%Y) --progress; then
  log "Upload successful."
else
  log "Upload failed."
  exit 1
fi

# Clean up local backup file
log "Cleaning up local backup files..."
rm /tmp/immich_backup.sql
rm /tmp/immich_backup.tar.bz2
log "Cleanup complete."

log "PostgreSQL backup process completed successfully."
