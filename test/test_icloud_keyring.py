from pyicloud import PyiCloudService
import yaml
from datetime import datetime, timedelta

def load_config():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["icloud"]["username"]

def test_icloud_connection():
    username = load_config()
    print(f"Using email: {username}")
    print("Using credentials from keyring")
    
    try:
        # Try to connect using stored credentials
        print("\nAttempting to connect to iCloud (China Mainland)...")
        api = PyiCloudService(username, china_mainland=True)
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
        print("1. Try running 'icloud --username zgchung@outlook.com' again")
        print("2. Make sure you can log in to https://www.icloud.com.cn")
        print("3. Check if your iCloud calendar is enabled")

if __name__ == "__main__":
    test_icloud_connection()
