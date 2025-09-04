from datetime import datetime, timedelta
from dateutil.parser import parse
from typing import List, Dict, Any
from notion_client import Client
import subprocess

from .config import get_config


class CalendarEvent:
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
        content = f"{self.title}" if self.calendar_name else self.title
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": content}}],
                "checked": False,
            },
        }


class CalendarSync:
    def __init__(self):
        self.config = get_config()
        self.notion = Client(auth=self.config.notion_token)

    def _run_applescript(self, script: str) -> List[Dict[str, Any]]:
        try:
            proc = subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                print(f"AppleScript error: {stderr}")
                return []
        except Exception as e:
            print(f"Error running AppleScript: {e}")
            return []

        events = []
        current_cal, current_event = None, {}
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("Calendar:"):
                current_cal = line[9:].strip()
            elif line.startswith("Event:"):
                current_event = {"title": line[6:].strip(), "calendar": current_cal}
            elif line.startswith("Start:"):
                current_event["start"] = parse(line[6:].strip())
            elif line.startswith("End:"):
                current_event["end"] = parse(line[4:].strip())
            elif line == "---" and current_event:
                events.append(current_event)
                current_event = {}
        return events

    def fetch_calendar_events(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        selected_calendars = self.config.icloud_calendars or []

        if not selected_calendars:
            cal_list_script = """
            tell application "Calendar"
                set cal_names to {}
                repeat with cal in calendars
                    set end of cal_names to name of cal
                end repeat
                return cal_names
            end tell
            """
            raw_output = self._run_applescript(cal_list_script)
            selected_calendars = [cal.strip() for cal in raw_output]

        cal_list_str = ", ".join(f'"{c}"' for c in selected_calendars)
        start_str, end_str = start_date.strftime(
            "%m/%d/%Y %H:%M:%S"
        ), end_date.strftime("%m/%d/%Y %H:%M:%S")

        events_script = f"""
        set startDate to date "{start_str}"
        set endDate to date "{end_str}"
        tell application "Calendar"
            set output to ""
            repeat with cal_name in {{{cal_list_str}}}
                try
                    set cal to first calendar whose name is cal_name
                    set output to output & "Calendar:" & cal_name & linefeed
                    set theEvents to every event of cal whose start date ≤ endDate and end date ≥ startDate
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

        raw_events = self._run_applescript(events_script)
        filtered = []
        for e in raw_events:
            if start_date.date() <= e["start"].date() <= end_date.date():
                filtered.append(
                    CalendarEvent(e["title"], e["start"], e["end"], e["calendar"])
                )
        return filtered

    def sync_to_notion(
        self,
        start_date: datetime,
        end_date: datetime,
        events: List[CalendarEvent] = None,
    ) -> None:
        if events is None:
            events = self.fetch_calendar_events(start_date, end_date)

        # Merge automatic events and manual recurring events
        events_by_date: Dict[datetime.date, List[CalendarEvent]] = {}
        for event in events:
            day = event.start.date()  # always use date
            events_by_date.setdefault(day, []).append(event)

        for n in range((end_date - start_date).days + 1):
            single_date = (start_date + timedelta(days=n)).date()  # normalize to date
            weekday_name = (start_date + timedelta(days=n)).strftime("%A")
            manual_events = self.config.recurring_events.get(weekday_name, [])
            for m_evt in manual_events:
                start_time_str, end_time_str = m_evt.get("time", "00:00-01:00").split(
                    "-"
                )
                start_dt = datetime.combine(
                    single_date, datetime.strptime(start_time_str, "%H:%M").time()
                )
                end_dt = datetime.combine(
                    single_date, datetime.strptime(end_time_str, "%H:%M").time()
                )
                cal_event = CalendarEvent(
                    title=m_evt["title"],
                    start=start_dt,
                    end=end_dt,
                    calendar_name="Manual",
                )
                events_by_date.setdefault(single_date, []).append(cal_event)

        # Sort the days and events
        for day in sorted(events_by_date.keys()):
            day_events = sorted(events_by_date[day], key=lambda e: e.start)
            self._update_notion_todos(day, day_events)

    def _update_notion_todos(
        self, date: datetime.date, events: List[CalendarEvent]
    ) -> None:
        if not events:
            return
        date_str = date.strftime("%b %-d %a")
        blocks = [
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": date_str}}],
                    "color": "default",
                    "children": [evt.to_notion_todo() for evt in events],
                },
            }
        ]
        self.notion.blocks.children.append(
            block_id=self.config.daily_log_page_id, children=blocks
        )
        print(f"Added {len(events)} events for {date_str} to Notion.")

    def sync_next_week(self) -> None:
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        next_monday = today + timedelta(days=days_until_monday)
        next_sunday = next_monday + timedelta(days=6)
        self.sync_to_notion(next_monday, next_sunday)

    def preview_sync(
        self,
        start_date: datetime,
        end_date: datetime,
        events: List[CalendarEvent] = None,
    ) -> Dict[str, List[str]]:
        if events is None:
            events = self.fetch_calendar_events(start_date, end_date)

        preview: Dict[str, List[str]] = {}
        for event in events:
            key = event.start.strftime("%Y-%m-%d")
            preview.setdefault(key, []).append(
                f"{event.title} at {event.start.strftime('%H:%M')}"
            )

        for n in range((end_date - start_date).days + 1):
            single_date = start_date + timedelta(days=n)
            weekday_name = single_date.strftime("%A")
            manual_events = self.config.recurring_events.get(weekday_name, [])
            for m_evt in manual_events:
                key = single_date.strftime("%Y-%m-%d")
                preview.setdefault(key, []).append(
                    f"{m_evt['title']} at {m_evt.get('time', '00:00-01:00')}"
                )

        # Sort keys and events
        sorted_preview = {}
        for date in sorted(preview.keys()):
            sorted_preview[date] = sorted(preview[date])
        return sorted_preview
