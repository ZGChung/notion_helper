"""iCloud Calendar sync functionality for importing calendar events to Notion."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
import caldav
from notion_client import Client
import dateutil.parser
import vobject
import urllib3
import requests

from .config import get_config

# Disable insecure HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        self.notion = Client(auth=self.config.notion_token)
        
        # Generate iCloud-specific CalDAV URL
        username = self.config.icloud_username
        server_num = "160"  # This might need to be adjusted
        
        # Try different URL formats
        self.caldav_urls = [
            f"https://p{server_num}-caldav.icloud.com/",
            f"https://p{server_num}-caldav.icloud.com/{username}/",
            f"https://p{server_num}-caldav.icloud.com/principalpath/{username}/",
            f"https://caldav.icloud.com/{username}/",
            f"https://caldav.icloud.com/principalpath/{username}/",
        ]
        
        # Custom headers for iCloud
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "text/calendar,application/xml,application/json",
            "Content-Type": "text/calendar; charset=utf-8",
        }

    def _try_connect_caldav(self) -> caldav.DAVClient:
        """Try to connect to CalDAV server using different URLs."""
        last_error = None
        
        for url in self.caldav_urls:
            try:
                print(f"\nTrying CalDAV URL: {url}")
                
                # First try a HEAD request to check the URL
                response = requests.head(
                    url,
                    auth=(self.config.icloud_username, self.config.icloud_password),
                    headers=self.headers,
                    verify=False,
                    timeout=10
                )
                print(f"HEAD request status: {response.status_code}")
                
                # Create CalDAV client
                client = caldav.DAVClient(
                    url=url,
                    username=self.config.icloud_username,
                    password=self.config.icloud_password,
                    headers=self.headers,
                    ssl_verify_cert=False
                )
                
                # Test connection by getting principal
                principal = client.principal()
                print("Connection successful!")
                return client
                
            except Exception as e:
                print(f"Failed to connect: {e}")
                last_error = e
                continue
                
        raise Exception(f"Failed to connect to any CalDAV URL. Last error: {last_error}")

    def fetch_calendar_events(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Fetch events from all calendars."""
        events = []
        
        print("\nFetching events from calendars...")
        
        try:
            # Connect to CalDAV server
            client = self._try_connect_caldav()
            
            # Get principal (main calendar user)
            principal = client.principal()
            
            # Get all calendars
            calendars = principal.calendars()
            print(f"\nFound {len(calendars)} calendars:")
            
            for calendar in calendars:
                try:
                    cal_name = calendar.name
                    print(f"\nAccessing calendar: {cal_name}")
                    
                    # Get calendar properties
                    try:
                        props = calendar.get_properties([
                            caldav.elements.dav.DisplayName(),
                            caldav.elements.caldav.CalendarDescription()
                        ])
                        print(f"Calendar properties: {props}")
                    except Exception as e:
                        print(f"Error getting calendar properties: {e}")
                    
                    # Get events in the date range
                    events_in_calendar = calendar.search(
                        start=start_date,
                        end=end_date,
                        event=True,
                        expand=True  # Expand recurring events
                    )
                    
                    print(f"Found {len(events_in_calendar)} events")
                    
                    # Process each event
                    for event in events_in_calendar:
                        try:
                            # Get event data
                            vevent = event.vobject_instance.vevent
                            
                            # Extract event details
                            title = str(vevent.summary.value)
                            start = vevent.dtstart.value
                            end = vevent.dtend.value if hasattr(vevent, 'dtend') else None
                            
                            # Convert to datetime if needed
                            if not isinstance(start, datetime):
                                start = datetime.combine(start, datetime.min.time())
                            if end and not isinstance(end, datetime):
                                end = datetime.combine(end, datetime.min.time())
                            
                            print(f"  • {title}")
                            events.append(CalendarEvent(
                                title=title,
                                start=start,
                                end=end,
                                calendar_name=cal_name
                            ))
                        except Exception as e:
                            print(f"    Error processing event: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error accessing calendar {cal_name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error accessing calendars: {e}")
        
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