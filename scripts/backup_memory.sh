#!/bin/bash
# Backup Vesper's memory database
# Run manually or via cron: 0 */6 * * * /path/to/backup_memory.sh

BACKUP_DIR="/Users/olenahoncharova/Documents/constellation/opus45/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/vesper_memory_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Run pg_dump via Docker
docker exec vesper_brain pg_dump -U hexis_user hexis_memory > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    # Compress the backup
    gzip "$BACKUP_FILE"
    echo "Backup created: ${BACKUP_FILE}.gz"

    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t vesper_memory_*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm
    echo "Old backups cleaned up"
else
    echo "Backup failed!"
    exit 1
fi
