from pyicloud import PyiCloudService
import yaml
import logging
import keyring
import os
from datetime import datetime, timedelta

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("pyicloud")


def load_config():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["icloud"]["username"], config["icloud"]["password"]


def check_safari_cookies():
    """Check Safari cookies directory."""
    cookie_paths = [
        os.path.expanduser(
            "~/Library/Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies"
        ),
        os.path.expanduser("~/Library/Cookies/Cookies.binarycookies"),
    ]

    for path in cookie_paths:
        if os.path.exists(path):
            print(f"Found cookies at: {path}")
            return os.path.dirname(path)

    print("No Safari cookie files found")
    return None


def test_icloud_connection():
    username, password = load_config()
    print(f"Using email: {username}")

    # Check Safari cookies
    cookie_dir = check_safari_cookies()
    print("Cookie directory:", cookie_dir)

    try:
        print("\nAttempting to connect to iCloud...")
        api = PyiCloudService(
            username, password, china_mainland=True, cookie_directory=cookie_dir
        )

        print("\n✅ Successfully authenticated with iCloud")

        # Try to access calendar
        print("\nAttempting to access calendar...")
        calendar = api.calendar

        # Get events for next 7 days
        start = datetime.now()
        end = start + timedelta(days=7)
        print(f"\nFetching events from {start.date()} to {end.date()}")

        events = calendar.events(start, end)
        print(f"✅ Successfully fetched calendar events")
        print(f"Found {len(events)} events")

        # Print first few events
        for event in events[:3]:
            print(f"\nEvent: {event.get('title')}")
            print(f"Start: {event.get('startDate')}")
            print(f"End: {event.get('endDate')}")

    except Exception as e:
        print("\n❌ Error:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")

        import traceback

        print("\nDetailed error trace:")
        traceback.print_exc()


if __name__ == "__main__":
    test_icloud_connection()
