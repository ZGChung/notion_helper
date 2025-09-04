"""iCloud Calendar sync functionality for importing calendar events to Notion."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
import pyicloud
from notion_client import Client
import dateutil.parser

from .config import get_config


class CalendarEvent:
    """Represents a calendar event."""

    def __init__(self, title: str, start: datetime, end: datetime = None):
        self.title = title
        self.start = start
        self.end = end

    def to_notion_todo(self) -> Dict[str, Any]:
        """Convert calendar event to Notion todo block."""
        time_str = self.start.strftime("%H:%M")
        if self.end:
            time_str += f"-{self.end.strftime('%H:%M')}"

        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"{self.title} at {time_str}"}}
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
        """Fetch calendar events from iCloud."""
        calendar = self.api.calendar
        events = []

        # Get events from calendar service
        try:
            # Try to get events directly
            raw_events = calendar.get_events(start_date, end_date)
        except AttributeError:
            # If get_events doesn't exist, try accessing events property
            try:
                raw_events = calendar.events
            except AttributeError:
                # If neither works, try accessing raw calendar data
                raw_events = calendar.get("Event", [])

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
                    events.append(CalendarEvent(title=title, start=start, end=end))
            except Exception as e:
                print(f"Error processing event: {e}")

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
        # Convert events to Notion blocks
        blocks = []

        # Add date header if events exist
        if events:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Calendar Events for {date.strftime('%Y-%m-%d')}"
                                },
                            }
                        ]
                    },
                }
            )

        # Add events as todo items
        for event in events:
            blocks.append(event.to_notion_todo())

        # Append blocks to Notion page
        if blocks:
            self.notion.blocks.children.append(
                block_id=self.config.daily_log_page_id, children=blocks
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

            time_str = event.start.strftime("%H:%M")
            if event.end:
                time_str += f"-{event.end.strftime('%H:%M')}"
            preview[date_key].append(f"{event.title} at {time_str}")

        return preview

    def sync_next_week(self) -> None:
        """Sync next week's calendar events."""
        today = datetime.now()
        days_until_monday = 7 - today.weekday()
        next_monday = today + timedelta(days=days_until_monday)
        next_sunday = next_monday + timedelta(days=6)

        self.sync_to_notion(next_monday, next_sunday)
