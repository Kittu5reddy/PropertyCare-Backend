#!/bin/bash

# ============================================================
# ♻️ PostgreSQL Database Restore Script for PropertyCare
# Author: Palvai Kaushik Reddy
# ============================================================

# === Configuration ===
PROJECT_DIR="/opt/PropertyCare-Backend"
BACKUP_DIR="$PROJECT_DIR/Backups"
LOG_DIR="$PROJECT_DIR/logs/cron"
LOG_FILE="$LOG_DIR/restore_$(date +'%Y-%m-%d_%H-%M').log"

DB_NAME="Propcare"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"

# === Ensure log directory exists ===
mkdir -p "$LOG_DIR"

# === Logging function ===
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" | tee -a "$LOG_FILE"
}

# === Require admin privileges ===
if [ "$EUID" -ne 0 ]; then
  echo "🚫 This script requires admin (sudo) privileges."
  echo "👉 Please run it as: sudo $0"
  exit 1
fi

# === Begin restore ===
log "🔁 Starting PostgreSQL restore process..."
log "============================================"

# === Step 1: Find the latest backup file ===
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.backup 2>/dev/null | head -n 1)

if [ -z "$LATEST_BACKUP" ]; then
  log "❌ No backup file found in $BACKUP_DIR."
  exit 1
fi

log "📦 Latest backup file found: $LATEST_BACKUP"

# === Step 2: Confirm restore ===
echo "⚠️  This will overwrite the existing database: $DB_NAME"
read -p "Type 'RESTORE' to continue: " CONFIRM

if [ "$CONFIRM" != "RESTORE" ]; then
  log "❌ Operation cancelled by user."
  exit 1
fi

# === Step 3: Drop existing database ===
log "⚙️ Dropping existing database (if exists)..."
sudo -u postgres psql -h "$DB_HOST" -p "$DB_PORT" -c "DROP DATABASE IF EXISTS \"$DB_NAME\";" 2>&1 | tee -a "$LOG_FILE"

# === Step 4: Create a new empty database ===
log "🆕 Creating new database..."
sudo -u postgres psql -h "$DB_HOST" -p "$DB_PORT" -c "CREATE DATABASE \"$DB_NAME\";" 2>&1 | tee -a "$LOG_FILE"

# === Step 5: Restore from backup ===
log "📂 Restoring database from backup..."
sudo -u postgres pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v "$LATEST_BACKUP" 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
  log "✅ Restore completed successfully from: $LATEST_BACKUP"
else
  log "❌ Restore failed. Check the log for details: $LOG_FILE"
  exit 1
fi

log "🎉 Database restore finished at $(date)"
log "============================================================"
