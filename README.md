# Notion Helper - Workflow Automation Tool

Automate your workflow by integrating Notion todos, iCloud calendar, and email reporting.

## Features

🔄 **Automated 3-Step Workflow**

1. **Calendar Sync**: Import iCloud calendar events to Notion daily todo lists
2. **Todo Organization**: Copy todos with prefixes to their corresponding project pages
3. **Weekly Reporting**: Generate professional email reports based on completed tasks

📅 **Smart Calendar Integration**

-   Import iCloud calendar events to Notion
-   Support for both timed and all-day events
-   Automatic timezone conversion
-   Selective calendar sync (choose which calendars to sync)

📝 **Notion Integration**

-   Fetch todos directly from Notion pages
-   Prefix-based project matching (e.g., `[adr] Task` → ADR project page)
-   Hierarchical todo structure preservation
-   Duplicate detection and prevention

🤖 **Full Automation**

-   Cron job setup for Friday 16:00 China Time
-   Manual commands for individual operations
-   Comprehensive error handling and logging

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
    username: "your.email@icloud.com" # Your iCloud email
    password: "xxxx-xxxx-xxxx-xxxx" # App-specific password
    calendars: # List of calendars to sync
        - "Calendar" # Leave empty to sync all calendars
        - "Work"
        - "Personal"

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
timezone: "Asia/Shanghai" # Your timezone
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
6. List the calendars you want to sync in the config file
    - Open Calendar.app to see your calendar names
    - Add them to the `calendars` list in your config
    - Leave the list empty to sync all calendars

### 5. Test Configuration

```bash
python main.py test-config
```

## How It Works

### Todo Organization with Prefixes

The system automatically organizes your todos based on prefixes in square brackets:

1. **Daily Todo Format**: Add prefixes to your todos in Notion
   ```
   - [x] [adr] Improve the json converter
       - [x] Align the items in order
       - [ ] Add validation
   - [ ] [ch] Flight to Chengdu
   - [x] [proj] Update documentation
   ```

2. **Project Database**: Create projects with matching prefixes
   - Project name: `[adr] Architecture Decision Records`
   - Project name: `[proj] Main Project`
   - Project name: `[ch] Personal Chores`

3. **Automatic Sync**: When you run `sync-todos`, the system:
   - Finds todos with prefixes (e.g., `[adr]`)
   - Matches them to projects with the same prefix
   - Copies the entire todo hierarchy to the project page
   - Preserves sub-items and completion status
   - Avoids duplicates

### Calendar Integration

Calendar events are automatically imported as toggle lists by date:
```
> Sep 8 Mon
  - [ ] [Apple] Meeting at 10:00
  - [ ] [Personal] Gym at 18:00

> Sep 9 Tue  
  - [ ] [Work] Project Review at 14:00
```

## Usage

### Manual Commands

```bash
# Run full 3-step automation (recommended)
python main.py weekly-automation

# Individual operations
python main.py sync-calendar       # Step 1: Sync next week's calendar events
python main.py sync-todos          # Step 2: Copy todos to project pages
python main.py generate-email      # Step 3: Generate weekly email report

# Utility commands
python main.py test-config         # Test configuration and connections
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
├── my_config.yaml         # Your personal configuration (not tracked)
├── email_template.txt     # Email template
├── requirements.txt       # Python dependencies
├── setup_cron.sh         # Cron setup script
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── todo_parser.py     # Todo parsing and project sync
│   ├── notion_api.py      # Notion API integration
│   ├── email_generator.py # Email report generation
│   └── calendar_sync.py   # Calendar synchronization
├── test/                  # Test scripts for debugging
└── README.md
```

## Troubleshooting

### Common Issues

1. **Notion Connection Failed**

    - Verify integration token is correct
    - Ensure database/page is shared with integration
    - Check database/page IDs in config

2. **Todo Sync Issues**

    - Ensure project database has projects with prefixes (e.g., `[adr] Project Name`)
    - Verify todos have matching prefixes (e.g., `[adr] Task`)
    - Check that project pages are accessible by the integration
    - Run `python main.py sync-todos` to see available projects and prefixes

3. **iCloud Calendar Sync Issues**

    - Verify iCloud credentials
    - Check app-specific password
    - Ensure calendar access is enabled
    - Verify calendar names match exactly with Calendar.app
    - Check if selected calendars are accessible
    - Grant Calendar access to Terminal/Python in macOS System Settings

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
