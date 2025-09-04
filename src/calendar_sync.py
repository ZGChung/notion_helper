"""iCalendar sync functionality for importing calendar events to daily todo lists."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import pytz
from icalendar import Calendar, Event
import pyicloud

from .config import get_config


class CalendarEvent:
    """Represents a calendar event."""
    
    def __init__(self, summary: str, start_time: datetime, end_time: datetime, description: str = ""):
        self.summary = summary
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
    
    def to_todo_item(self) -> str:
        """Convert calendar event to todo item format."""
        # Format time for todo item
        if self.start_time.hour == 0 and self.start_time.minute == 0:
            # All-day event
            return f"- [ ] {self.summary}"
        else:
            # Timed event
            time_str = self.start_time.strftime("%H:%M")
            if self.end_time and self.end_time != self.start_time:
                end_time_str = self.end_time.strftime("%H:%M")
                return f"- [ ] {time_str}-{end_time_str}: {self.summary}"
            else:
                return f"- [ ] {time_str}: {self.summary}"


class CalendarSync:
    """iCalendar sync functionality for importing calendar events to daily todo lists."""

    def __init__(self):
        self.config = get_config()
        self.api = pyicloud.PyiCloudService(self.config.icloud_username, self.config.icloud_password)

    def fetch_ical_data(self):
        """Fetch iCal data from iCloud."""
        calendar = self.api.calendar
        events = calendar.events(start_date=datetime.now(), end_date=datetime.now() + timedelta(days=7))
        return events

    def sync_to_daily_todos(self, start_date: datetime, end_date: datetime) -> None:
        """Sync calendar events to daily todo files for the specified date range."""
        events = self.fetch_ical_data()
        for event in events:
            self._update_daily_todo_file(event.start, [event])

    def _update_daily_todo_file(self, date: datetime, events: List[CalendarEvent]) -> None:
        """Update or create daily todo file with calendar events."""
        filename = date.strftime(self.config.daily_todo_filename_pattern)
        file_path = self.config.daily_todos_dir / filename
        
        # Append events to the file
        with open(file_path, 'a', encoding='utf-8') as f:
            for event in events:
                f.write(f"- {event.title} at {event.start.strftime('%H:%M')}\n")