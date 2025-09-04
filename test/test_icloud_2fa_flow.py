from pyicloud import PyiCloudService
import yaml
import logging
import sys
import time
from datetime import datetime, timedelta

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("pyicloud")

def load_config():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["icloud"]["username"], config["icloud"]["password"]

def handle_2fa(api):
    """Handle 2FA verification."""
    if api.requires_2fa:
        print("\nTwo-factor authentication required.")
        print("Please check your Apple device for the code.")
        code = input("Enter the verification code: ")
        
        if not api.validate_2fa_code(code):
            print("Failed to verify 2FA code")
            return False
        
        print("✅ 2FA code verified")
        
        if not api.is_trusted_session:
            print("\nRequesting session trust...")
            result = api.trust_session()
            print(f"Trust result: {result}")
    
    elif api.requires_2sa:
        print("\nTwo-step authentication required.")
        devices = api.trusted_devices
        
        print("\nTrusted devices:")
        for i, device in enumerate(devices):
            print(f"{i}: {device.get('deviceName', device.get('phoneNumber'))}")
        
        device_index = int(input("\nWhich device would you like to use? [0]: ") or "0")
        device = devices[device_index]
        
        if not api.send_verification_code(device):
            print("Failed to send verification code")
            return False
        
        code = input("Enter verification code: ")
        if not api.validate_verification_code(device, code):
            print("Failed to verify verification code")
            return False
        
        print("✅ Verification successful")
    
    return True

def test_icloud_connection():
    username, password = load_config()
    print(f"Using email: {username}")
    
    try:
        print("\nAttempting to connect to iCloud...")
        api = PyiCloudService(username, password, china_mainland=True)
        
        # Handle 2FA if needed
        if not handle_2fa(api):
            print("❌ Authentication failed")
            return
        
        print("\n✅ Successfully authenticated with iCloud")
        print(f"Session valid: {api.session.has_token}")
        print(f"Session trusted: {getattr(api, 'is_trusted_session', False)}")
        
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
