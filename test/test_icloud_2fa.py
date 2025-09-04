from pyicloud import PyiCloudService
import yaml
from datetime import datetime, timedelta
import keyring
import sys


def load_config():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["icloud"]["username"], config["icloud"]["password"]


def handle_2fa(api):
    print("\n2FA Authentication required!")
    print("Check your Apple devices for a verification code.")
    code = input("Enter verification code: ")
    result = api.validate_2fa_code(code)
    print("2FA validation result:", result)
    return result


def test_icloud_connection():
    username, password = load_config()
    print(f"Using email: {username}")
    print("Using app-specific password: ****-****-****-****")

    try:
        # Try to connect
        print("\nAttempting to connect to iCloud...")
        api = PyiCloudService(username, password)

        # Handle 2FA if needed
        if api.requires_2fa:
            print("Two-factor authentication required.")
            result = handle_2fa(api)
            if not result:
                print("Failed to verify 2FA code.")
                return

        print("✅ Successfully connected to iCloud")

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
        print(f"Error message: {str(e)}")
        print("\nDebug information:")
        print("1. Check if you're logged into iCloud on this device")
        print("2. Try logging in to https://www.icloud.com manually first")
        print("3. Make sure Calendar access is enabled in iCloud settings")


if __name__ == "__main__":
    test_icloud_connection()
