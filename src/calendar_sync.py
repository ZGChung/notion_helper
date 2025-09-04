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
        # Connect to iCloud Calendar
        self.api = pyicloud.PyiCloudService(
            self.config.icloud_username,
            self.config.icloud_password,
            china_mainland=False  # Use global endpoint
        )
        self.notion = Client(auth=self.config.notion_token)

    def fetch_calendar_events(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Fetch calendar events from all calendars."""
        events = []
        
        print("\nFetching events from calendars...")
        
        try:
            # Get calendar service
            calendar = self.api.calendar
            
            # Debug: Print calendar object details
            print("\nCalendar service details:")
            print(f"Type: {type(calendar)}")
            print(f"Available attributes: {dir(calendar)}")
            
            # Try to get all calendars
            try:
                print("\nTrying to access calendars...")
                if hasattr(calendar, 'calendars'):
                    print("Found calendars attribute!")
                    for cal_id, cal in calendar.calendars.items():
                        print(f"Calendar: {cal_id}")
                        print(f"  Title: {getattr(cal, 'title', 'Unknown')}")
                        print(f"  Type: {type(cal)}")
                        print(f"  Attributes: {dir(cal)}")
                else:
                    print("No calendars attribute found")
                
                if hasattr(calendar, 'list'):
                    print("\nTrying calendar.list()...")
                    cal_list = calendar.list()
                    print(f"List result: {cal_list}")
            except Exception as e:
                print(f"Error accessing calendar list: {e}")
            
            # Try to get events from all sources
            try:
                print("\nFetching events...")
                
                # Try direct events
                raw_events = calendar.get_events(start_date, end_date)
                print(f"\nDirect events found: {len(raw_events)}")
                
                # Process events
                for event in raw_events:
                    try:
                        # Debug: Print event details
                        print(f"\nEvent details:")
                        print(f"Type: {type(event)}")
                        if isinstance(event, dict):
                            print(f"Keys: {event.keys()}")
                        else:
                            print(f"Attributes: {dir(event)}")
                        
                        # Extract event data
                        if isinstance(event, dict):
                            title = event.get('title')
                            start = event.get('startDate')
                            end = event.get('endDate')
                            calendar_name = event.get('calendar', {}).get('title', 'Calendar')
                        else:
                            title = getattr(event, 'title', None)
                            start = getattr(event, 'startDate', None)
                            end = getattr(event, 'endDate', None)
                            calendar_name = getattr(getattr(event, 'calendar', None), 'title', 'Calendar')
                        
                        # Parse dates
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
                        
                        print(f"  • [{calendar_name}] {title}")
                        events.append(CalendarEvent(
                            title=title,
                            start=start,
                            end=end,
                            calendar_name=calendar_name
                        ))
                    except Exception as e:
                        print(f"    Error processing event: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error fetching events: {e}")
                
        except Exception as e:
            print(f"Error accessing calendar service: {e}")
        
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