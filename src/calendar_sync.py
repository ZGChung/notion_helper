"""iCloud Calendar sync functionality for importing calendar events to Notion."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
import pyicloud
from notion_client import Client
import dateutil.parser

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
    """iCloud Calendar sync functionality."""

    def __init__(self):
        self.config = get_config()
        # Use global endpoint since China endpoint has issues
        self.api = pyicloud.PyiCloudService(
            self.config.icloud_username,
            self.config.icloud_password,
            china_mainland=False,  # Use global endpoint
        )
        self.notion = Client(auth=self.config.notion_token)

    def fetch_calendar_events(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Fetch calendar events from all iCloud calendars."""
        calendar = self.api.calendar
        events = []

        print("\nFetching events from iCloud calendars...")
        
        # Try different methods to get calendars
        try:
            print("Attempting to get all calendars...")
            # Try to get raw calendar data first
            raw_calendars = calendar.get("Calendar", [])
            print(f"Found {len(raw_calendars)} calendars in raw data:")
            for cal in raw_calendars:
                print(f"  • {cal.get('title', 'Unknown')}")
            
            # Try to get calendars through the API
            if hasattr(calendar, 'calendars'):
                print("\nFound calendars through API:")
                for cal_id, cal in calendar.calendars.items():
                    print(f"  • Calendar ID: {cal_id}")
                    print(f"    Title: {getattr(cal, 'title', 'Unknown')}")
                raw_calendars = calendar.calendars.values()
            
            # If both failed, try direct events
            if not raw_calendars:
                print("\nNo calendars found, trying direct event access...")
                raw_calendars = [calendar]
        except Exception as e:
            print(f"Error getting calendars: {e}")
            print("Falling back to main calendar...")
            raw_calendars = [calendar]

        # Process each calendar
        for cal in raw_calendars:
            calendar_name = None
            if isinstance(cal, dict):
                calendar_name = cal.get('title')
            else:
                calendar_name = getattr(cal, 'title', None)
            
            print(f"\nProcessing calendar: {calendar_name or 'Main Calendar'}")
            
            # Get events from calendar
            try:
                if isinstance(cal, dict):
                    raw_events = cal.get("Event", [])
                else:
                    try:
                        raw_events = cal.get_events(start_date, end_date)
                    except AttributeError:
                        try:
                            raw_events = cal.events
                        except AttributeError:
                            raw_events = getattr(cal, "Event", [])

                print(f"Found {len(raw_events) if isinstance(raw_events, list) else '?'} events")

                # Process events
                for event in raw_events:
                    # Handle different event formats
                    if isinstance(event, dict):
                        title = event.get("title") or event.get("summary")
                        start = event.get("startDate") or event.get("start")
                        end = event.get("endDate") or event.get("end")
                    else:
                        # If event is an object
                        title = getattr(event, "title", None) or getattr(event, "summary", None)
                        start = getattr(event, "startDate", None) or getattr(
                            event, "start", None
                        )
                        end = getattr(event, "endDate", None) or getattr(event, "end", None)

                    # Parse dates if needed
                    try:
                        if isinstance(start, (list, tuple)):
                            # Format: [YYYYMMDD, YYYY, MM, DD, HH, MM, Offset]
                            year = start[1]
                            month = start[2]
                            day = start[3]
                            hour = start[4]
                            minute = start[5]
                            start = datetime(year, month, day, hour, minute)
                        
                        if isinstance(end, (list, tuple)):
                            year = end[1]
                            month = end[2]
                            day = end[3]
                            hour = end[4]
                            minute = end[5]
                            end = datetime(year, month, day, hour, minute)
                        
                        elif isinstance(start, str):
                            start = dateutil.parser.parse(start)
                        elif isinstance(end, str):
                            end = dateutil.parser.parse(end)

                        if title and start:
                            print(f"  • Adding event: {title}")
                            events.append(CalendarEvent(
                                title=title,
                                start=start,
                                end=end,
                                calendar_name=calendar_name
                            ))
                    except Exception as e:
                        print(f"Error processing event: {e}")

            except Exception as e:
                print(f"Error getting events from calendar: {e}")

        print(f"\nTotal events found across all calendars: {len(events)}")
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