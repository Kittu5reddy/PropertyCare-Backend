#!/bin/bash

# ============================================================
# ⚠️ PostgreSQL Database Deletion Script for PropertyCare
# Author: Palvai Kaushik Reddy
# Date: $(date)
# ============================================================

# === Configuration ===
DB_NAME="Propcare"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"

LOG_DIR="/opt/PropertyCare-Backend/logs/cron"
LOG_FILE="$LOG_DIR/delete_db_$(date +'%Y-%m-%d_%H-%M').log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# === Logging function ===
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" | tee -a "$LOG_FILE"
}

# === Safety warning ===
echo "⚠️  WARNING: You are about to permanently delete the PostgreSQL database: $DB_NAME"
read -p "Type 'DELETE' to confirm: " CONFIRM

if [ "$CONFIRM" != "DELETE" ]; then
  log "❌ Operation cancelled by user."
  exit 1
fi

# === Drop the database ===
log "🗑️  Dropping database $DB_NAME..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -c "DROP DATABASE IF EXISTS \"$DB_NAME\";" 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
  log "✅ Database $DB_NAME deleted successfully."
else
  log "❌ Failed to delete database $DB_NAME."
  exit 1
fi

log "🧹 Database deletion completed at $(date)"
log "============================================================"
