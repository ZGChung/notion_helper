import caldav
from datetime import datetime, timedelta
from typing import List
from .config import get_config
from notion_client import Client


class CalendarSync:
    """Calendar sync functionality using CalDAV (iCloud)."""

    def __init__(self):
        self.config = get_config()
        self.notion = Client(auth=self.config.notion_token)

        # 连接 iCloud CalDAV
        self.client = caldav.DAVClient(
            url="https://caldav.icloud.com/",
            username=self.config.icloud_username,
            password=self.config.icloud_app_password,
        )
        self.principal = self.client.principal()

    def fetch_calendar_events(
        self, start_date: datetime, end_date: datetime
    ) -> List["CalendarEvent"]:
        """Fetch events from iCloud via CalDAV."""
        events = []

        print(f"\nFetching events from CalDAV between {start_date} and {end_date}...")

        # 获取所有可用日历
        calendars = self.principal.calendars()
        available_calendars = {c.name: c for c in calendars}

        print("\nAvailable calendars:")
        for cal in available_calendars.keys():
            print(f"  • {cal}")

        # 挑选需要的日历
        selected_calendars = self.config.icloud_calendars or list(
            available_calendars.keys()
        )
        print(
            f"\nSelected calendars: {', '.join(selected_calendars) if selected_calendars else 'All'}"
        )

        # 从每个日历取事件
        for cal_name in selected_calendars:
            cal = available_calendars.get(cal_name)
            if not cal:
                print(f"Warning: Calendar '{cal_name}' not found in iCloud")
                continue

            results = cal.date_search(start=start_date, end=end_date)
            for raw_event in results:
                try:
                    ical = raw_event.icalendar_component
                    title = str(ical.get("summary"))
                    start = ical.decoded("dtstart")
                    end = ical.decoded("dtend", None)

                    events.append(
                        CalendarEvent(
                            title=title,
                            start=start,
                            end=end,
                            calendar_name=cal_name,
                        )
                    )
                except Exception as e:
                    print(f"Error parsing event: {e}")

        print(f"\nTotal events found: {len(events)}")
        return events

    def sync_next_week(self) -> None:
        """Sync next week's calendar events via CalDAV."""
        today = datetime.now()

        # 计算下周一 00:00
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = datetime.combine(
            today.date() + timedelta(days=days_until_monday), datetime.min.time()
        )

        # 下周日 23:59:59
        next_sunday = datetime.combine(
            next_monday.date() + timedelta(days=6), datetime.max.time()
        )

        # 拉取事件
        events = self.fetch_calendar_events(next_monday, next_sunday)

        # 同步到 Notion
        self.sync_to_notion(next_monday, next_sunday, events)
