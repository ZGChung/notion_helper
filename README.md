# Notion Helper - Workflow Automation Tool

Automate your todo list workflow by integrating daily todos, Notion project tracking, weekly email reports, and calendar synchronization.

## Features

🔄 **Automated Weekly Workflow**
- Parse completed tasks from daily todo lists
- Update Notion project database with weekly summaries
- Generate professional weekly email reports
- Sync next week's calendar events to daily todos

📅 **Smart Calendar Integration**
- Import iCalendar events to daily todo lists
- Support for both timed and all-day events
- Automatic timezone conversion

📝 **Flexible Todo Parsing**
- Support multiple todo formats (checkboxes, strikethrough)
- Automatic project categorization
- Date-based file organization

🤖 **Full Automation**
- Cron job setup for Friday 16:00 China Time
- Manual commands for individual operations
- Comprehensive error handling and logging

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd notion_helper

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy and edit the configuration file:

```bash
cp config.yaml my_config.yaml
```

Edit `config.yaml` with your settings:

```yaml
# Notion API Configuration
notion:
  token: "YOUR_NOTION_INTEGRATION_TOKEN"
  project_database_id: "YOUR_PROJECT_DATABASE_ID"
  daily_log_page_id: "YOUR_DAILY_LOG_PAGE_ID"

# File paths
paths:
  daily_todos_dir: "~/Documents/DailyTodos"
  ical_file: "~/Documents/calendar.ics"
  email_template: "email_template.txt"

# Email configuration
email:
  boss_email: "boss@company.com"
  your_name: "Your Name"
  subject_template: "Weekly Update - {week_start} to {week_end}"

# Timezone
timezone: "Asia/Shanghai"  # China Time

# Daily todo file naming pattern
daily_todo_filename_pattern: "%Y-%m-%d.txt"
```

### 3. Setup Notion Integration

1. Create a Notion integration at https://www.notion.so/my-integrations
2. Copy the integration token to your config
3. Share your project database and daily log page with the integration
4. Copy the database/page IDs to your config

### 4. Test Configuration

```bash
python main.py test-config
```

## Usage

### Manual Commands

```bash
# Run full weekly automation (recommended)
python main.py weekly-automation

# Individual operations
python main.py sync-calendar       # Sync next week's calendar
python main.py generate-email      # Generate weekly email only
python main.py update-notion       # Update Notion only
python main.py test-config         # Test configuration
```

### Automated Setup

Set up automatic execution every Friday at 16:00 China Time:

```bash
# Using the built-in command
python main.py setup-cron

# Or using the shell script
./setup_cron.sh
```

## Supported Todo Formats

The tool supports multiple todo list formats:

### Checkbox Format
```
- [x] Completed task
- [ ] Pending task
- [x] [ProjectName] Task with project tag
```

### Strikethrough Format
```
- ~~Completed task~~
- Pending task
- ~~@ProjectName Task with project mention~~
```

### Project Categorization

Tasks are automatically categorized by project using these patterns:
- `[ProjectName]` - Square brackets
- `@ProjectName` - @ mentions
- `#ProjectName` - Hash tags
- `- ProjectName:` - Colon format

If no project is detected, tasks are categorized by keywords:
- **Meetings**: meeting, call, standup
- **Communication**: email, respond, reply
- **Development**: code, develop, implement, fix, bug
- **Documentation**: review, document, write
- **General**: everything else

## File Structure

```
notion_helper/
├── main.py                 # Main CLI application
├── config.yaml            # Configuration template
├── email_template.txt     # Email template
├── requirements.txt       # Python dependencies
├── setup_cron.sh          # Cron setup script
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── todo_parser.py     # Daily todo parsing
│   ├── notion_client.py   # Notion API integration
│   ├── email_generator.py # Email report generation
│   └── calendar_sync.py   # Calendar synchronization
└── README.md
```

## Workflow Overview

### Weekly Automation Process

1. **Parse Last Week's Todos** (Monday-Sunday)
   - Scan daily todo files for completed tasks
   - Extract and categorize by project
   - Group by completion date

2. **Update Notion Database**
   - Find or create project pages
   - Append weekly summaries to project pages
   - Update daily log page with consolidated view

3. **Generate Email Report**
   - Create professional weekly update email
   - Group tasks by project and date
   - Save draft for review and sending

4. **Sync Next Week's Calendar**
   - Parse iCalendar file for upcoming events
   - Convert events to todo items
   - Update daily todo files with calendar events

### Daily Todo File Example

```
# 2023-12-01.txt

## Work Tasks
- [x] [WebApp] Fix login bug
- [x] [WebApp] Update user dashboard
- [ ] [API] Implement new endpoint

## Meetings
- [x] 09:00-10:00: Team standup
- [ ] 14:00-15:00: Client review

# Calendar Events
- [ ] 10:00-11:00: Project planning meeting
- [ ] 15:30: Code review session
# End Calendar Events
```

## Troubleshooting

### Common Issues

1. **Notion Connection Failed**
   - Verify integration token is correct
   - Ensure database/page is shared with integration
   - Check database/page IDs in config

2. **No Todo Files Found**
   - Verify `daily_todos_dir` path in config
   - Check filename pattern matches your files
   - Ensure files exist for the target week

3. **Calendar Sync Issues**
   - Verify iCalendar file path and format
   - Check timezone settings
   - Ensure file is readable

4. **Cron Job Not Running**
   - Check cron service is running: `sudo service cron status`
   - Verify cron job: `crontab -l`
   - Check logs: `tail -f ~/.notion_helper/automation.log`

### Debug Mode

Add debug logging by setting environment variable:

```bash
export NOTION_HELPER_DEBUG=1
python main.py weekly-automation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
