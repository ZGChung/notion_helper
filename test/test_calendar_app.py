import appscript
from datetime import datetime, timedelta


def test_calendar_access():
    try:
        print("Attempting to access Calendar.app...")
        cal = appscript.app("Calendar")
        print("✅ Successfully connected to Calendar.app")

        # List available calendars
        print("\nAvailable calendars:")
        calendars = cal.calendars.get()
        for calendar in calendars:
            print(f"- {calendar.name.get()}")

        # Get events for next 7 days
        start = datetime.now()
        end = start + timedelta(days=7)
        print(f"\nFetching events from {start.date()} to {end.date()}")

        # Get events from all calendars
        total_events = 0
        for calendar in calendars:
            events = calendar.events[
                appscript.its.start_date.ge(start).AND(appscript.its.start_date.le(end))
            ].get()
            if events:
                print(f"\nEvents in {calendar.name.get()}:")
                for event in events:
                    print(f"- {event.summary.get()} at {event.start_date.get()}")
                    total_events += 1

        print(f"\n✅ Found {total_events} total events")

    except Exception as e:
        print("\n❌ Error:")
        print(f"Error message: {str(e)}")
        print("\nDebug information:")
        print("1. Make sure you're signed into iCloud on your Mac")
        print("2. Check if Calendar.app has necessary permissions")
        print("3. Open Calendar.app and verify your calendars are visible")


if __name__ == "__main__":
    test_calendar_access()
