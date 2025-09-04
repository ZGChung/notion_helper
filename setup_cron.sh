#!/bin/bash
# Setup script for automated cron job

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"

echo "🔧 Setting up Notion Helper cron job..."
echo "Script location: $MAIN_SCRIPT"

# Check if main.py exists
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "❌ Error: main.py not found at $MAIN_SCRIPT"
    exit 1
fi

# Make sure main.py is executable
chmod +x "$MAIN_SCRIPT"

# Create log directory
LOG_DIR="$HOME/.notion_helper"
mkdir -p "$LOG_DIR"

# Cron job for Friday 16:00 China Time (08:00 UTC)
CRON_COMMAND="0 8 * * 5 cd $SCRIPT_DIR && /usr/bin/python3 $MAIN_SCRIPT weekly-automation >> $LOG_DIR/automation.log 2>&1"

echo "Cron command to be added:"
echo "$CRON_COMMAND"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "notion_helper\|weekly-automation"; then
    echo "⚠️  A Notion Helper cron job already exists."
    echo "Current crontab:"
    crontab -l | grep -E "notion_helper|weekly-automation"
    echo ""
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Remove existing job
    crontab -l | grep -v -E "notion_helper|weekly-automation" | crontab -
    echo "Removed existing cron job."
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
    echo "📅 Will run every Friday at 16:00 China Time (08:00 UTC)"
    echo "📝 Logs will be saved to: $LOG_DIR/automation.log"
    echo ""
    echo "Current crontab:"
    crontab -l
else
    echo "❌ Failed to add cron job"
    exit 1
fi