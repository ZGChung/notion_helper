# Installation and Setup Guide

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure the Application
1. Edit `config.yaml` with your settings:
   - Add your Notion integration token
   - Set your project database and daily log page IDs
   - Configure file paths for your daily todos and calendar
   - Set email preferences

### 3. Set Up Notion Integration
1. Go to https://www.notion.so/my-integrations
2. Create a new integration
3. Copy the integration token to your config
4. Share your project database and daily log page with the integration
5. Copy the database/page IDs to your config

### 4. Test Configuration
```bash
python main.py test-config
```

### 5. Set Up Automation (Optional)
```bash
# Set up cron job for Friday 16:00 China Time
python main.py setup-cron

# Or use the shell script
./setup_cron.sh
```

## Manual Usage

### Run Full Weekly Automation
```bash
python main.py weekly-automation
```
This will:
1. Parse last week's completed todos
2. Update Notion project database
3. Generate weekly email report
4. Sync next week's calendar events

### Individual Commands
```bash
# Sync calendar only
python main.py sync-calendar

# Generate email only
python main.py generate-email

# Update Notion only
python main.py update-notion

# Test configuration
python main.py test-config
```

## File Structure Requirements

### Daily Todo Files
- Location: Set in `config.yaml` under `paths.daily_todos_dir`
- Naming: Use pattern in `config.yaml` (default: `%Y-%m-%d.txt`)
- Format: Support both checkbox and strikethrough formats

Example file `2023-12-04.txt`:
```
## Work Tasks
- [x] [WebApp] Fix login bug
- [x] [Documentation] Update API docs
- [ ] [API] Implement new endpoint

## Meetings
- [x] 09:00-10:00: Team standup
- [ ] 14:00-15:00: Client review
```

### iCalendar File
- Location: Set in `config.yaml` under `paths.ical_file`
- Format: Standard .ics format
- Export from your calendar application

## Configuration Details

### Required Notion Setup
1. **Project Database**: A database with at least a "Name" property (title)
2. **Daily Log Page**: A page where weekly summaries will be appended
3. **Integration**: Must have access to both the database and page

### File Paths
- Use absolute paths or paths relative to your home directory (`~`)
- Ensure directories exist and are writable
- Calendar file should be regularly updated/synced

### Email Template
- Customize `email_template.txt` for your email format
- Use variables: `{week_start}`, `{week_end}`, `{project_summaries}`, `{total_tasks}`, `{project_count}`, `{your_name}`

## Troubleshooting

### Common Issues
1. **Module not found**: Run `pip install -r requirements.txt`
2. **Notion connection failed**: Check token and database/page IDs
3. **No todo files found**: Verify paths and filename patterns
4. **Calendar sync issues**: Check iCalendar file format and path

### Debug Mode
Set environment variable for detailed logging:
```bash
export NOTION_HELPER_DEBUG=1
python main.py weekly-automation
```

### Log Files
- Cron job logs: `~/.notion_helper/automation.log`
- Manual run output: Console output

## Advanced Configuration

### Custom Project Categorization
Modify `todo_parser.py` to add custom project detection patterns:
```python
# In TodoItem._extract_project() method
patterns = [
    r'\[([^\]]+)\]',  # [ProjectName]
    r'@(\w+)',        # @ProjectName
    r'#(\w+)',        # #ProjectName
    r'- (\w+):',      # - ProjectName:
    r'your_pattern',  # Add your custom pattern
]
```

### Email Customization
1. Edit `email_template.txt` for basic customization
2. Modify `email_generator.py` for advanced formatting
3. Add custom variables in the template system

### Calendar Event Filtering
Modify `calendar_sync.py` to filter specific event types:
```python
# In CalendarSync._parse_event() method
# Add filtering logic based on event properties
if 'skip' in summary.lower():
    return None  # Skip this event
```