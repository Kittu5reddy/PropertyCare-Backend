#!/bin/bash

# =========================================================
# 🚀 PropertyCare Cron Setup Script
# Removes old cron jobs, adds new ones, and logs all actions
# =========================================================

PROJECT_DIR="/opt/PropertyCare-Backend"
VENV_PYTHON="$PROJECT_DIR/myenv/bin/python"
LOG_DIR="$PROJECT_DIR/logs/cron"
LOG_FILE="$LOG_DIR/cron_setup.log"




# === Prepare log directory ===
mkdir -p "$LOG_DIR"

# === Logging function ===
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" | tee -a "$LOG_FILE"
}

log_error() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" | tee -a "$LOG_FILE" >&2
}

log "=============================================="
log "🕓 Starting cron setup process..."
log "Project directory: $PROJECT_DIR"
log "Logs: $LOG_FILE"

# === Step 1: Remove ALL existing cron jobs ===
log "🧹 Removing all existing cron jobs..."
crontab -r 2>/dev/null
if [ $? -eq 0 ]; then
  log "✅ All existing cron jobs removed."
else
  log "⚠️ No existing cron jobs found or removal failed (may be empty)."
fi

# === Step 2: Define new cron jobs ===
log "🛠️ Creating new cron jobs..."

CRON_TEMP_FILE=$(mktemp)

cat <<EOL > "$CRON_TEMP_FILE"
# ============================================================
# 🕒 PropertyCare-Backend Automated Cron Jobs
# Installed on $(date)
# ============================================================

# 🗄️ Daily database backup at 2 AM
0 2 * * * $VENV_PYTHON $PROJECT_DIR/scripts/backup_to_s3.py >> $LOG_DIR/backup.log 2>&1

# ❤️ Health check every 10 minutes
# */10 * * * * $VENV_PYTHON $PROJECT_DIR/scripts/health_check.py >> $LOG_DIR/health.log 2>&1
EOL

# === Step 3: Apply the cron jobs ===
crontab "$CRON_TEMP_FILE"
if [ $? -eq 0 ]; then
  log "✅ New cron jobs installed successfully."
else
  log_error "❌ Failed to install new cron jobs!"
  exit 1
fi

# === Step 4: Verify installed jobs ===
log "🔍 Verifying installed cron jobs..."
crontab -l | tee -a "$LOG_FILE"

# === Step 5: Cleanup ===
rm "$CRON_TEMP_FILE"

log "🎉 Cron setup completed successfully."
log "=============================================="
