#!/usr/bin/env python3
"""Test script to debug email generation."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.todo_parser import TodoParser
from src.email_generator import EmailGenerator


def test_email_generation():
    """Test email generation with debug info."""
    try:
        print("Testing email generation...")

        # Get current week's data (since this runs on Friday)
        parser = TodoParser()
        week_start, week_end = parser.get_current_week_range()

        print(
            f"Week range: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
        )

        # Get todos
        todos = parser.parse_week_files(week_start)
        completed_by_project = parser.get_completed_tasks_by_project(todos)

        print(f"Found {len(completed_by_project)} projects with completed tasks:")
        for project, tasks in completed_by_project.items():
            print(f"  {project}: {len(tasks)} tasks")

        # Generate email
        email_gen = EmailGenerator()

        print("\nGenerating email...")
        email_content = email_gen.generate_weekly_email(
            completed_by_project, week_start, week_end
        )

        print("✅ Email generated successfully!")
        print(f"Subject: {email_content['subject']}")
        print(f"To: {email_content['to']}")
        print(f"CC: {email_content['cc']}")
        print(f"Body length: {len(email_content['body'])} characters")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_email_generation()
