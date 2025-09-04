#!/usr/bin/env python3
"""
Notion Helper - Workflow Automation Tool

This script automates your todo list workflow by:
1. Parsing daily todo lists to extract completed tasks
2. Updating Notion project database with weekly summaries
3. Generating weekly email reports
4. Syncing calendar events to daily todo lists

Usage:
    python main.py weekly-automation    # Run full weekly automation (steps 1-3)
    python main.py sync-calendar       # Sync next week's calendar events
    python main.py sync-todos          # Sync todos with prefixes to project pages
    python main.py generate-email      # Generate weekly email only
    python main.py update-notion       # Update Notion only
    python main.py test-config         # Test configuration and connections
    python main.py setup-cron          # Set up automated cron job
"""

import sys
import click
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import get_config
from src.todo_parser import TodoParser
from src.notion_api import NotionClient
from src.email_generator import EmailGenerator
from src.calendar_sync import CalendarSync


@click.group()
def cli():
    """Notion Helper - Workflow Automation Tool"""
    pass


@cli.command()
def weekly_automation():
    """Run full weekly automation: parse todos, update Notion, generate email, sync calendar."""
    click.echo("🚀 Starting weekly automation...")

    try:
        # Step 1: Parse last week's completed todos
        click.echo("📋 Parsing last week's todo lists...")
        parser = TodoParser()
        week_start, week_end = parser.get_last_week_range()

        click.echo(
            f"   Week range: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
        )

        todos = parser.parse_week_files(week_start)
        completed_by_project = parser.get_completed_tasks_by_project(todos)

        total_completed = sum(len(tasks) for tasks in completed_by_project.values())
        click.echo(
            f"   Found {total_completed} completed tasks across {len(completed_by_project)} projects"
        )

        if total_completed == 0:
            click.echo(
                "   No completed tasks found. Skipping Notion and email updates."
            )
        else:
            # Step 2: Update Notion
            click.echo("📝 Updating Notion database...")
            notion_client = NotionClient()
            notion_client.update_project_database(completed_by_project)
            notion_client.update_daily_log(completed_by_project, week_start, week_end)
            click.echo("   ✅ Notion updated successfully")

            # Step 3: Generate email
            click.echo("📧 Generating weekly email...")
            email_gen = EmailGenerator()
            email_content = email_gen.generate_weekly_email(
                completed_by_project, week_start, week_end
            )

            email_file = email_gen.save_email_draft(email_content)
            click.echo(f"   ✅ Email draft saved to: {email_file}")

        # Step 4: Sync next week's calendar
        click.echo("📅 Syncing next week's calendar events...")
        calendar_sync = CalendarSync()
        calendar_sync.sync_next_week()
        click.echo("   ✅ Calendar sync completed")

        click.echo("🎉 Weekly automation completed successfully!")

    except Exception as e:
        click.echo(f"❌ Error during weekly automation: {e}")
        sys.exit(1)


@cli.command()
def sync_calendar():
    """Sync next week's calendar events to daily todo lists."""
    click.echo("📅 Syncing calendar events...")

    try:
        calendar_sync = CalendarSync()

        # Get next week range and fetch events once
        parser = TodoParser()
        next_week_start, next_week_end = parser.get_next_week_range()

        # Fetch events once
        events = calendar_sync.fetch_calendar_events(next_week_start, next_week_end)

        # Preview the events
        preview = calendar_sync.preview_sync(next_week_start, next_week_end, events)

        if not preview:
            click.echo("   No calendar events found for next week.")
            return

        click.echo(
            f"   Preview for {next_week_start.strftime('%Y-%m-%d')} to {next_week_end.strftime('%Y-%m-%d')}:"
        )
        for filename, event_list in preview.items():
            click.echo(f"   📄 {filename}: {len(event_list)} events")
            for event in event_list[:3]:  # Show first 3 events
                click.echo(f"      {event}")
            if len(event_list) > 3:
                click.echo(f"      ... and {len(event_list) - 3} more")

        # Sync to Notion using the same events
        calendar_sync.sync_to_notion(next_week_start, next_week_end, events)
        click.echo("   ✅ Calendar sync completed")

    except Exception as e:
        click.echo(f"❌ Error syncing calendar: {e}")
        sys.exit(1)


@cli.command()
def generate_email():
    """Generate weekly email report only."""
    click.echo("📧 Generating weekly email...")

    try:
        # Parse last week's todos
        parser = TodoParser()
        week_start, week_end = parser.get_last_week_range()

        todos = parser.parse_week_files(week_start)
        completed_by_project = parser.get_completed_tasks_by_project(todos)

        total_completed = sum(len(tasks) for tasks in completed_by_project.values())

        if total_completed == 0:
            click.echo("   No completed tasks found for last week.")
            return

        # Generate email
        email_gen = EmailGenerator()
        email_content = email_gen.generate_weekly_email(
            completed_by_project, week_start, week_end
        )

        email_file = email_gen.save_email_draft(email_content)

        click.echo(f"   ✅ Email draft saved to: {email_file}")
        click.echo(
            f"   📊 Summary: {total_completed} tasks across {len(completed_by_project)} projects"
        )

    except Exception as e:
        click.echo(f"❌ Error generating email: {e}")
        sys.exit(1)


@cli.command()
def update_notion():
    """Update Notion database only."""
    click.echo("📝 Updating Notion database...")

    try:
        # Parse last week's todos
        parser = TodoParser()
        week_start, week_end = parser.get_last_week_range()

        todos = parser.parse_week_files(week_start)
        completed_by_project = parser.get_completed_tasks_by_project(todos)

        total_completed = sum(len(tasks) for tasks in completed_by_project.values())

        if total_completed == 0:
            click.echo("   No completed tasks found for last week.")
            return

        # Update Notion
        notion_client = NotionClient()
        notion_client.update_project_database(completed_by_project)
        notion_client.update_daily_log(completed_by_project, week_start, week_end)

        click.echo(f"   ✅ Notion updated successfully")
        click.echo(
            f"   📊 Summary: {total_completed} tasks across {len(completed_by_project)} projects"
        )

    except Exception as e:
        click.echo(f"❌ Error updating Notion: {e}")
        sys.exit(1)


@cli.command()
def sync_todos():
    """Sync todos with prefixes to their corresponding project pages."""
    click.echo("🔄 Syncing todos to project pages...")

    try:
        parser = TodoParser()
        
        # Get projects first to show available prefixes
        projects = parser.get_projects()
        if not projects:
            click.echo("   ⚠️  No projects found in database")
            return
        
        click.echo(f"   📋 Found {len(projects)} projects with prefixes:")
        for prefix, project in projects.items():
            click.echo(f"      [{prefix}] -> {project['name']}")
        
        # Sync todos to projects
        sync_results = parser.sync_todos_to_projects()
        
        if not sync_results:
            click.echo("   ℹ️  No todos with matching prefixes found")
            return
        
        total_synced = sum(sync_results.values())
        click.echo(f"   ✅ Successfully synced {total_synced} todos to {len(sync_results)} projects")
        
        for project_name, count in sync_results.items():
            if count > 0:
                click.echo(f"      {project_name}: {count} todos")
        
    except Exception as e:
        click.echo(f"   ❌ Error syncing todos: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def test_config():
    """Test configuration and connections."""
    click.echo("🔧 Testing configuration...")

    try:
        config = get_config()

        # Test config loading
        click.echo("   ✅ Configuration loaded successfully")

        # Test email configuration
        click.echo("   📧 Testing email configuration...")
        if config.email_to_list() and config.email_cc_list():
            click.echo("      ✅ Email lists configured")

        # Test Notion connection
        click.echo("   🔗 Testing Notion connection...")
        notion_client = NotionClient()
        try:
            # Test basic connection
            user = notion_client.client.users.me()
            click.echo(f"      ✅ Connected as: {user.get('name', 'Unknown')}")

            # Test database access
            db = notion_client.client.databases.retrieve(
                database_id=notion_client.config.project_database_id
            )
            click.echo(
                f"      ✅ Database access successful: {db.get('title', [{}])[0].get('text', {}).get('content', 'Untitled')}"
            )

            # Test page access
            page = notion_client.client.pages.retrieve(
                page_id=notion_client.config.daily_log_page_id
            )
            click.echo("      ✅ Page access successful")

        except Exception as e:
            click.echo(f"      ❌ Notion connection failed: {str(e)}")
            raise e

        # Test iCloud configuration
        click.echo("   ☁️  Testing iCloud configuration...")
        if config.icloud_username and config.icloud_password:
            click.echo("      ✅ iCloud credentials configured")
            if hasattr(config, "icloud_calendars"):
                calendars = config.icloud_calendars
                if calendars:
                    click.echo(f"      ✅ Selected calendars: {', '.join(calendars)}")
                else:
                    click.echo(
                        "      ℹ️  No calendars selected (will sync all calendars)"
                    )
            else:
                click.echo(
                    "      ⚠️  No calendar selection configured (will sync all calendars)"
                )
        else:
            click.echo("      ❌ iCloud credentials missing")

        click.echo("🎉 Configuration test completed!")

    except Exception as e:
        click.echo(f"❌ Configuration test failed: {e}")
        sys.exit(1)


@cli.command()
def setup_cron():
    """Set up automated cron job for Friday 16:00 China Time."""
    click.echo("⏰ Setting up cron job...")

    try:
        import subprocess
        import os

        # Get current script path
        script_path = Path(__file__).absolute()

        # Create cron job command
        # Friday 16:00 China Time (UTC+8) = Friday 08:00 UTC
        cron_command = f"0 8 * * 5 cd {script_path.parent} && /usr/bin/python3 {script_path} weekly-automation >> /tmp/notion_helper.log 2>&1"

        click.echo(f"   Cron command: {cron_command}")

        if click.confirm("   Add this cron job?"):
            # Add to crontab
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)

            current_crontab = result.stdout if result.returncode == 0 else ""

            # Check if job already exists
            if "notion_helper" in current_crontab:
                click.echo(
                    "   ⚠️  Cron job already exists. Remove it first if you want to update."
                )
                return

            # Add new job
            new_crontab = current_crontab + "\n" + cron_command + "\n"

            process = subprocess.Popen(
                ["crontab", "-"], stdin=subprocess.PIPE, text=True
            )
            process.communicate(input=new_crontab)

            if process.returncode == 0:
                click.echo("   ✅ Cron job added successfully!")
                click.echo("   📅 Will run every Friday at 16:00 China Time")
                click.echo("   📝 Logs will be saved to /tmp/notion_helper.log")
            else:
                click.echo("   ❌ Failed to add cron job")
        else:
            click.echo("   Cron job setup cancelled")

    except Exception as e:
        click.echo(f"❌ Error setting up cron job: {e}")
        sys.exit(1)


@cli.command()
def create_sample_config():
    """Create a sample configuration file."""
    click.echo("📝 Creating sample configuration...")

    config_path = Path("config.yaml")
    if config_path.exists():
        if not click.confirm(f"   {config_path} already exists. Overwrite?"):
            click.echo("   Configuration creation cancelled")
            return

    # The config.yaml template is already created, just copy it
    click.echo(f"   ✅ Sample configuration available at: {config_path}")
    click.echo("   📝 Please edit the file and fill in your actual values:")
    click.echo("      - Notion API token and database IDs")
    click.echo("      - iCloud credentials and calendar selection")
    click.echo("      - Email settings")


if __name__ == "__main__":
    cli()
