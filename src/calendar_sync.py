"""iCloud Calendar sync functionality for importing calendar events to Notion."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
from notion_client import Client
import dateutil.parser
import subprocess
import json
import re

from .config import get_config


class CalendarEvent:
    """Represents a calendar event."""

    def __init__(self, title: str, start: datetime, end: datetime = None, calendar_name: str = None):
        self.title = title
        self.start = start
        self.end = end
        self.calendar_name = calendar_name

    def to_notion_todo(self) -> Dict[str, Any]:
        """Convert calendar event to Notion todo block."""
        content = self.title
        if self.calendar_name:
            content = f"[{self.calendar_name}] {content}"
            
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [
                    {"type": "text", "text": {"content": content}}
                ],
                "checked": False,
            },
        }


class CalendarSync:
    """Calendar sync functionality using macOS Calendar.app."""

    def __init__(self):
        self.config = get_config()
        self.notion = Client(auth=self.config.notion_token)

    def _run_applescript(self, script: str) -> str:
        """Run AppleScript and return its output."""
        try:
            process = subprocess.Popen(
                ['osascript', '-e', script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"AppleScript error: {stderr}")
                return ""
                
            return stdout.strip()
            
        except Exception as e:
            print(f"Error running AppleScript: {e}")
            return ""

    def _format_date(self, date: datetime) -> str:
        """Format date for AppleScript."""
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def fetch_calendar_events(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Fetch events from Calendar.app."""
        events = []
        
        print("\nFetching events from Calendar.app...")
        
        # First, get list of calendars
        calendar_script = """
            tell application "Calendar"
                set calList to {}
                repeat with calendarAccount in calendars
                    set end of calList to {name:name of calendarAccount, id:id of calendarAccount}
                end repeat
                return calList as text
            end tell
        """
        
        calendars_output = self._run_applescript(calendar_script)
        print("\nAvailable calendars:")
        print(calendars_output)
        
        # Parse calendar list
        calendar_matches = re.finditer(r'{name:(.+?), id:(.+?)}', calendars_output)
        calendars = [(m.group(1), m.group(2)) for m in calendar_matches]
        
        for cal_name, cal_id in calendars:
            print(f"\nFetching events from calendar: {cal_name}")
            
            # Get events for this calendar
            events_script = f"""
                tell application "Calendar"
                    set eventList to {{}}
                    set startDate to date "{self._format_date(start_date)}"
                    set endDate to date "{self._format_date(end_date)}"
                    set targetCal to calendar id "{cal_id}"
                    
                    set theEvents to (every event of targetCal whose start date is greater than or equal to startDate and start date is less than or equal to endDate)
                    
                    repeat with anEvent in theEvents
                        set eventTitle to summary of anEvent
                        set eventStart to start date of anEvent
                        set eventEnd to end date of anEvent
                        
                        set end of eventList to {{title:eventTitle, start:eventStart, end:eventEnd}}
                    end repeat
                    
                    return eventList as text
                end tell
            """
            
            events_output = self._run_applescript(events_script)
            print(f"Raw events output: {events_output[:200]}...")  # Show first 200 chars
            
            # Parse events
            event_matches = re.finditer(r'{title:(.+?), start:date "(.+?)", end:date "(.+?)"}', events_output)
            
            for match in event_matches:
                try:
                    title = match.group(1)
                    start = dateutil.parser.parse(match.group(2))
                    end = dateutil.parser.parse(match.group(3))
                    
                    print(f"  • {title}")
                    events.append(CalendarEvent(
                        title=title,
                        start=start,
                        end=end,
                        calendar_name=cal_name
                    ))
                except Exception as e:
                    print(f"Error parsing event: {e}")
                    continue
        
        print(f"\nTotal events found: {len(events)}")
        return events

    def sync_to_notion(self, start_date: datetime, end_date: datetime) -> None:
        """Sync calendar events to Notion for the specified date range."""
        events = self.fetch_calendar_events(start_date, end_date)

        # Group events by date
        events_by_date = {}
        for event in events:
            date_key = event.start.date()
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append(event)

        # Update Notion
        for date, date_events in events_by_date.items():
            self._update_notion_todos(date, date_events)

    def _update_notion_todos(
        self, date: datetime.date, events: List[CalendarEvent]
    ) -> None:
        """Update Notion page with calendar events."""
        if not events:
            return

        # Format date as "Sep 1 Mon"
        date_str = date.strftime("%b %-d %a")

        # Create toggle block with events as children
        blocks = [
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": date_str}
                        }
                    ],
                    "color": "default",
                    "children": [event.to_notion_todo() for event in events]
                }
            }
        ]

        # Append blocks to Notion page
        if blocks:
            print(f"\nAdding toggle list '{date_str}' with {len(events)} events to Notion page:")
            print(f"- Events under '{date_str}':")
            for event in events:
                calendar_info = f"[{event.calendar_name}] " if event.calendar_name else ""
                print(f"  • {calendar_info}{event.title}")
            
            self.notion.blocks.children.append(
                block_id=self.config.daily_log_page_id,
                children=blocks
            )

    def preview_sync(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, List[str]]:
        """Preview calendar events that would be synced."""
        events = self.fetch_calendar_events(start_date, end_date)

        # Group events by date
        preview = {}
        for event in events:
            date_key = event.start.strftime("%Y-%m-%d")
            if date_key not in preview:
                preview[date_key] = []

            calendar_info = f"[{event.calendar_name}] " if event.calendar_name else ""
            time_str = event.start.strftime("%H:%M")
            if event.end:
                time_str += f"-{event.end.strftime('%H:%M')}"
            preview[date_key].append(f"{calendar_info}{event.title} at {time_str}")

        return preview

    def sync_next_week(self) -> None:
        """Sync next week's calendar events."""
        today = datetime.now()
        days_until_monday = 7 - today.weekday()
        next_monday = today + timedelta(days=days_until_monday)
        next_sunday = next_monday + timedelta(days=6)

        self.sync_to_notion(next_monday, next_sunday)