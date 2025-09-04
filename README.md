# Notion Helper - Workflow Automation Tool

Automate your workflow by integrating Notion todos, iCloud calendar, and email reporting.

## Features

🔄 **Automated Weekly Workflow**
- Fetch completed tasks from Notion
- Update Notion project database with weekly summaries
- Generate professional weekly email reports
- Sync iCloud calendar events to Notion

📅 **Smart Calendar Integration**
- Import iCloud calendar events to Notion
- Support for both timed and all-day events
- Automatic timezone conversion

📝 **Notion Integration**
- Fetch todos directly from Notion
- Automatic project categorization
- Date-based organization

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

Edit `my_config.yaml` with your settings:

```yaml
# Notion API Configuration
notion:
  token: "YOUR_NOTION_INTEGRATION_TOKEN"
  project_database_id: "YOUR_PROJECT_DATABASE_ID"
  daily_log_page_id: "YOUR_DAILY_LOG_PAGE_ID"

# iCloud configuration
icloud:
  username: "your.email@icloud.com"       # Your iCloud email
  password: "xxxx-xxxx-xxxx-xxxx"        # App-specific password

# Email configuration
email:
  to_list:
    - "recipient1@example.com"
    - "recipient2@example.com"
  cc_list:
    - "cc1@example.com"
    - "cc2@example.com"
  your_name: "Your Name"
  subject_template: "Weekly Update - {week_start} to {week_end}"

# Timezone
timezone: "Asia/Shanghai"  # Your timezone
```

### 3. Setup Notion Integration

1. Create a Notion integration at https://www.notion.so/my-integrations
2. Copy the integration token to your config
3. Share your project database and daily log page with the integration
4. Copy the database/page IDs to your config

### 4. Setup iCloud Access

1. Go to https://appleid.apple.com
2. Sign in with your Apple ID
3. Under "Security", click "Generate Password" for app-specific passwords
4. Enter a name (e.g., "Notion Helper") and copy the generated password
5. Add the password to your config file

### 5. Test Configuration

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

## Project Structure

```
notion_helper/
├── main.py                 # Main CLI application
├── config.yaml            # Configuration template
├── email_template.txt     # Email template
├── requirements.txt       # Python dependencies
├── setup_cron.sh         # Cron setup script
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── notion_api.py      # Notion API integration
│   ├── email_generator.py # Email report generation
│   └── calendar_sync.py   # Calendar synchronization
└── README.md
```

## Troubleshooting

### Common Issues

1. **Notion Connection Failed**
   - Verify integration token is correct
   - Ensure database/page is shared with integration
   - Check database/page IDs in config

2. **iCloud Calendar Sync Issues**
   - Verify iCloud credentials
   - Check app-specific password
   - Ensure calendar access is enabled

3. **Cron Job Not Running**
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