"""iCalendar sync functionality for importing calendar events to daily todo lists."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import pytz
from icalendar import Calendar, Event

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
    """Handles iCalendar file parsing and sync to daily todo lists."""
    
    def __init__(self):
        self.config = get_config()
        self.timezone = pytz.timezone(self.config.timezone)
    
    def parse_ical_file(self, ical_path: Path = None) -> List[CalendarEvent]:
        """Parse iCalendar file and extract events."""
        if ical_path is None:
            ical_path = self.config.ical_file
        
        if not ical_path.exists():
            print(f"iCalendar file not found: {ical_path}")
            return []
        
        events = []
        
        try:
            with open(ical_path, 'rb') as f:
                calendar = Calendar.from_ical(f.read())
            
            for component in calendar.walk():
                if component.name == "VEVENT":
                    event = self._parse_event(component)
                    if event:
                        events.append(event)
        
        except Exception as e:
            print(f"Error parsing iCalendar file: {e}")
            return []
        
        return events
    
    def get_events_for_week(self, start_date: datetime, end_date: datetime, ical_path: Path = None) -> Dict[datetime, List[CalendarEvent]]:
        """Get events for a specific week, grouped by date."""
        all_events = self.parse_ical_file(ical_path)
        
        # Filter events for the specified week
        week_events = {}
        
        for event in all_events:
            event_date = event.start_time.date()
            
            # Check if event falls within the week
            if start_date.date() <= event_date <= end_date.date():
                event_datetime = datetime.combine(event_date, datetime.min.time())
                
                if event_datetime not in week_events:
                    week_events[event_datetime] = []
                
                week_events[event_datetime].append(event)
        
        return week_events
    
    def sync_to_daily_todos(self, start_date: datetime, end_date: datetime) -> None:
        """Sync calendar events to daily todo files for the specified date range."""
        events_by_date = self.get_events_for_week(start_date, end_date)
        
        for date_dt, events in events_by_date.items():
            self._update_daily_todo_file(date_dt, events)
    
    def sync_next_week(self) -> None:
        """Sync next week's calendar events to daily todo files."""
        # Calculate next week's date range
        today = datetime.now()
        days_until_monday = 7 - today.weekday()
        next_monday = today + timedelta(days=days_until_monday)
        next_sunday = next_monday + timedelta(days=6)
        
        print(f"Syncing calendar events for next week: {next_monday.strftime('%Y-%m-%d')} to {next_sunday.strftime('%Y-%m-%d')}")
        
        self.sync_to_daily_todos(next_monday, next_sunday)
    
    def _parse_event(self, vevent: Event) -> CalendarEvent:
        """Parse a single VEVENT component."""
        try:
            # Get event summary
            summary = str(vevent.get('summary', 'Untitled Event'))
            
            # Get start time
            dtstart = vevent.get('dtstart')
            if dtstart is None:
                return None
            
            start_time = dtstart.dt
            if isinstance(start_time, datetime):
                # Convert to local timezone if needed
                if start_time.tzinfo is None:
                    start_time = self.timezone.localize(start_time)
                else:
                    start_time = start_time.astimezone(self.timezone)
            else:
                # Date only (all-day event)
                start_time = datetime.combine(start_time, datetime.min.time())
                start_time = self.timezone.localize(start_time)
            
            # Get end time
            dtend = vevent.get('dtend')
            end_time = None
            if dtend:
                end_time = dtend.dt
                if isinstance(end_time, datetime):
                    if end_time.tzinfo is None:
                        end_time = self.timezone.localize(end_time)
                    else:
                        end_time = end_time.astimezone(self.timezone)
                else:
                    end_time = datetime.combine(end_time, datetime.min.time())
                    end_time = self.timezone.localize(end_time)
            
            # Get description
            description = str(vevent.get('description', ''))
            
            return CalendarEvent(summary, start_time, end_time, description)
        
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None
    
    def _update_daily_todo_file(self, date: datetime, events: List[CalendarEvent]) -> None:
        """Update or create daily todo file with calendar events."""
        # Generate filename
        filename = date.strftime(self.config.daily_todo_filename_pattern)
        file_path = self.config.daily_todos_dir / filename
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing content if file exists
        existing_content = ""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # Check if calendar section already exists
        calendar_section_start = "# Calendar Events"
        calendar_section_end = "# End Calendar Events"
        
        # Remove existing calendar section if present
        if calendar_section_start in existing_content:
            start_idx = existing_content.find(calendar_section_start)
            end_idx = existing_content.find(calendar_section_end)
            if end_idx != -1:
                end_idx += len(calendar_section_end)
                existing_content = existing_content[:start_idx] + existing_content[end_idx:]
            else:
                existing_content = existing_content[:start_idx]
        
        # Sort events by start time
        events.sort(key=lambda e: e.start_time)
        
        # Create calendar section
        calendar_lines = [
            "",
            "# Calendar Events",
            ""
        ]
        
        for event in events:
            calendar_lines.append(event.to_todo_item())
        
        calendar_lines.extend([
            "",
            "# End Calendar Events",
            ""
        ])
        
        # Combine content
        final_content = existing_content.rstrip() + "\n".join(calendar_lines)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"Updated {filename} with {len(events)} calendar events")
    
    def preview_sync(self, start_date: datetime, end_date: datetime) -> Dict[str, List[str]]:
        """Preview what would be synced without actually writing files."""
        events_by_date = self.get_events_for_week(start_date, end_date)
        
        preview = {}
        for date_dt, events in events_by_date.items():
            filename = date_dt.strftime(self.config.daily_todo_filename_pattern)
            
            # Sort events by start time
            events.sort(key=lambda e: e.start_time)
            
            todo_items = [event.to_todo_item() for event in events]
            preview[filename] = todo_items
        
        return preview