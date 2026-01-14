#!/bin/bash

# ===========================================
# Poker MTT Helper - Database Backup Script
# ===========================================
# This script creates backups of the PostgreSQL database
# Usage: ./scripts/backup.sh [backup_dir]
# 
# Can be run manually or via cron:
# 0 2 * * * /path/to/pokerhelper/scripts/backup.sh

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${1:-/var/backups/pokerhelper}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pokerhelper_${TIMESTAMP}.sql.gz"

# Load environment variables
if [ -f "$PROJECT_DIR/.env.production" ]; then
    source "$PROJECT_DIR/.env.production"
fi

echo "🗄️ Poker MTT Helper - Database Backup"
echo "====================================="
echo "Timestamp: $TIMESTAMP"
echo "Backup dir: $BACKUP_DIR"
echo ""

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# ===========================================
# Create backup
# ===========================================
echo "📦 Creating backup..."

cd "$PROJECT_DIR"

# Check if docker compose is available
if docker compose version &> /dev/null; then
    COMPOSE="docker compose"
else
    COMPOSE="docker-compose"
fi

# Get database container name
DB_CONTAINER=$($COMPOSE -f docker-compose.prod.yml ps -q db 2>/dev/null || echo "")

if [ -z "$DB_CONTAINER" ]; then
    # Try development compose
    DB_CONTAINER=$($COMPOSE ps -q db 2>/dev/null || echo "")
fi

if [ -z "$DB_CONTAINER" ]; then
    echo "❌ Database container not found. Is the application running?"
    exit 1
fi

# Create backup using pg_dump
docker exec "$DB_CONTAINER" pg_dump -U ${DB_USER:-postgres} ${DB_NAME:-pokerhelper} | gzip > "$BACKUP_DIR/$BACKUP_FILE"

# Get backup size
BACKUP_SIZE=$(ls -lh "$BACKUP_DIR/$BACKUP_FILE" | awk '{print $5}')
echo "✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# ===========================================
# Backup additional data
# ===========================================
echo "📁 Backing up additional data..."

# Backup training dataset metadata
DATASET_BACKUP="dataset_${TIMESTAMP}.tar.gz"
if [ -d "$PROJECT_DIR/backend/data/training_dataset" ]; then
    tar -czf "$BACKUP_DIR/$DATASET_BACKUP" \
        -C "$PROJECT_DIR/backend/data/training_dataset" \
        metadata.json 2>/dev/null || true
    echo "✅ Dataset metadata backed up"
fi

# ===========================================
# Cleanup old backups
# ===========================================
echo "🧹 Cleaning up old backups (older than $RETENTION_DAYS days)..."

find "$BACKUP_DIR" -name "pokerhelper_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "dataset_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Count remaining backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/pokerhelper_*.sql.gz 2>/dev/null | wc -l)
echo "✅ $BACKUP_COUNT backup(s) remaining"

# ===========================================
# Summary
# ===========================================
echo ""
echo "====================================="
echo "✅ Backup Complete!"
echo "====================================="
echo ""
echo "Backup file: $BACKUP_DIR/$BACKUP_FILE"
echo "Backup size: $BACKUP_SIZE"
echo ""

# List recent backups
echo "Recent backups:"
ls -lht "$BACKUP_DIR"/pokerhelper_*.sql.gz 2>/dev/null | head -5
