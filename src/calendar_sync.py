"""iCloud Calendar sync functionality for importing calendar events to Notion."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
from notion_client import Client
import dateutil.parser
import subprocess

from .config import get_config


class CalendarEvent:
    """Represents a calendar event."""

    def __init__(
        self,
        title: str,
        start: datetime,
        end: datetime = None,
        calendar_name: str = None,
    ):
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
                "rich_text": [{"type": "text", "text": {"content": content}}],
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
                ["osascript", "-e", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                print(f"AppleScript error: {stderr}")
                return ""

            return stdout.strip()

        except Exception as e:
            print(f"Error running AppleScript: {e}")
            return ""

    def fetch_calendar_events(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Fetch events from Calendar.app."""
        events = []

        print("\nFetching events from Calendar.app...")

        # First, get list of calendars
        calendar_script = """
            tell application "Calendar"
                set output to ""
                repeat with cal in calendars
                    set output to output & name of cal & linefeed
                end repeat
                return output
            end tell
        """

        calendars_output = self._run_applescript(calendar_script)
        available_calendars = [
            cal.strip() for cal in calendars_output.split("\n") if cal.strip()
        ]

        print("\nAvailable calendars:")
        for cal in available_calendars:
            print(f"  • {cal}")

        # Get selected calendars from config
        selected_calendars = self.config.icloud_calendars
        if selected_calendars is not None:
            print(
                f"\nSelected calendars: {', '.join(selected_calendars) if selected_calendars else 'All'}"
            )
        else:
            print("\nNo calendar selection configured, using all calendars")
            selected_calendars = available_calendars

        # Build script to get events from selected calendars
        calendar_list = ", ".join(f'"{cal}"' for cal in selected_calendars)
        
        # Format dates properly for AppleScript
        start_str = start_date.strftime("%B %d, %Y")
        end_str = end_date.strftime("%B %d, %Y")
        
        events_script = f"""
            tell application "Calendar"
                set output to ""
                set start_date to date "{start_str}"
                set end_date to date "{end_str}"
                
                repeat with cal_name in {{{calendar_list}}}
                    try
                        set cal to first calendar whose name is cal_name
                        set output to output & "Calendar:" & cal_name & linefeed
                        
                        set theEvents to (every event of cal whose start date is greater than or equal to start_date and start date is less than or equal to end_date)
                        repeat with evt in theEvents
                            set output to output & "Event:" & summary of evt & linefeed
                            set output to output & "Start:" & ((start date of evt) as string) & linefeed
                            set output to output & "End:" & ((end date of evt) as string) & linefeed
                            set output to output & "---" & linefeed
                        end repeat
                    on error errMsg
                        set output to output & "Error:" & cal_name & ":" & errMsg & linefeed
                    end try
                end repeat
                
                return output
            end tell
        """

        events_output = self._run_applescript(events_script)

        # Parse events output
        current_calendar = None
        current_event = {}

        for line in events_output.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("Calendar:"):
                current_calendar = line[9:].strip()
            elif line.startswith("Event:"):
                if current_event:
                    try:
                        events.append(
                            CalendarEvent(
                                title=current_event["title"],
                                start=dateutil.parser.parse(current_event["start"]),
                                end=dateutil.parser.parse(current_event["end"]),
                                calendar_name=current_event["calendar"],
                            )
                        )
                    except Exception as e:
                        print(f"Error parsing event: {e}")
                current_event = {
                    "title": line[6:].strip(),
                    "calendar": current_calendar,
                }
            elif line.startswith("Start:"):
                current_event["start"] = line[6:].strip()
            elif line.startswith("End:"):
                current_event["end"] = line[4:].strip()
            elif line == "---" and current_event:
                try:
                    events.append(
                        CalendarEvent(
                            title=current_event["title"],
                            start=dateutil.parser.parse(current_event["start"]),
                            end=dateutil.parser.parse(current_event["end"]),
                            calendar_name=current_event["calendar"],
                        )
                    )
                except Exception as e:
                    print(f"Error parsing event: {e}")
                current_event = {}

        print(f"\nTotal events found: {len(events)}")
        return events

    def sync_to_notion(self, start_date: datetime, end_date: datetime, events: List[CalendarEvent] = None) -> None:
        """Sync calendar events to Notion for the specified date range."""
        if events is None:
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
                    "rich_text": [{"type": "text", "text": {"content": date_str}}],
                    "color": "default",
                    "children": [event.to_notion_todo() for event in events],
                },
            }
        ]

        # Append blocks to Notion page
        if blocks:
            print(
                f"\nAdding toggle list '{date_str}' with {len(events)} events to Notion page:"
            )
            print(f"- Events under '{date_str}':")
            for event in events:
                calendar_info = (
                    f"[{event.calendar_name}] " if event.calendar_name else ""
                )
                print(f"  • {calendar_info}{event.title}")

            self.notion.blocks.children.append(
                block_id=self.config.daily_log_page_id, children=blocks
            )

    def preview_sync(
        self, start_date: datetime, end_date: datetime, events: List[CalendarEvent] = None
    ) -> Dict[str, List[str]]:
        """Preview calendar events that would be synced."""
        if events is None:
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
