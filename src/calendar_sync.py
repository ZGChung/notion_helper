"""iCloud Calendar sync functionality for importing calendar events to Notion."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
import caldav
from notion_client import Client
import dateutil.parser
import recurring_ical_events
from icalendar import Calendar

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
        # Connect to both iCloud and Apple Calendar
        self.icloud_client = caldav.DAVClient(
            url="https://caldav.icloud.com",
            username=self.config.icloud_username,
            password=self.config.icloud_password
        )
        # Apple Calendar uses a different URL
        self.apple_client = caldav.DAVClient(
            url="https://calendar.icloud.com",  # Main Apple Calendar endpoint
            username=self.config.icloud_username,
            password=self.config.icloud_password
        )
        self.notion = Client(auth=self.config.notion_token)

    def fetch_calendar_events(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Fetch calendar events from all calendars."""
        events = []
        
        print("\nFetching events from calendars...")
        
        # Try both clients to get all calendars
        for client, client_name in [(self.icloud_client, "iCloud"), (self.apple_client, "Apple")]:
            try:
                print(f"\nTrying {client_name} calendars...")
                # Get the principal (main calendar user)
                principal = client.principal()
                
                # Get all calendars
                calendars = principal.calendars()
                print(f"Found {len(calendars)} calendars in {client_name}:")
                
                # Define the calendars we want to fetch from
                target_calendars = {"Calendar", "Personal", "Apple", "MD AI/ML COE"}
                
                for calendar in calendars:
                    calendar_name = calendar.name
                    print(f"  • {calendar_name}")
                    
                    # Only process calendars we're interested in
                    if calendar_name not in target_calendars:
                        print(f"    Skipping (not in target calendars)")
                        continue
                    
                    print(f"    Fetching events...")
                    
                    try:
                        # Get events in the date range
                        events_in_calendar = calendar.search(
                            start=start_date,
                            end=end_date,
                            event=True,
                            expand=True  # Expand recurring events
                        )
                        
                        print(f"    Found {len(events_in_calendar)} events")
                        
                        for event in events_in_calendar:
                            try:
                                # Parse the event data
                                event_data = event.instance.vevent
                                title = str(event_data.summary.value if hasattr(event_data, 'summary') else 'No Title')
                                start = event_data.dtstart.value if hasattr(event_data, 'dtstart') else None
                                end = event_data.dtend.value if hasattr(event_data, 'dtend') else None
                                
                                # Convert to datetime if date
                                if hasattr(start, 'date'):
                                    start = start
                                else:
                                    start = datetime.combine(start, datetime.min.time())
                                
                                if end and hasattr(end, 'date'):
                                    end = end
                                elif end:
                                    end = datetime.combine(end, datetime.min.time())
                                
                                print(f"      • {title}")
                                events.append(CalendarEvent(
                                    title=title,
                                    start=start,
                                    end=end,
                                    calendar_name=f"{client_name}/{calendar_name}"
                                ))
                            except Exception as e:
                                print(f"      Error processing event: {e}")
                                continue
                                
                    except Exception as e:
                        print(f"    Error fetching events from calendar: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error accessing {client_name} calendars: {e}")
        
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