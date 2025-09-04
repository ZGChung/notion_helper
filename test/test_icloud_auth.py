from pyicloud import PyiCloudService
import yaml
import logging
import os
import keyring
from pathlib import Path

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("pyicloud")

def load_config():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["icloud"]["username"], config["icloud"]["password"]

def check_existing_sessions(username):
    """Check for existing session files."""
    possible_paths = [
        Path.home() / ".pyicloud",
        Path("/var/folders") / "mr/w6lwwcmn5gd3xy1fl55g4vxh0000gn/T/pyicloud",
        Path.home() / "Library/Caches/pyicloud",
        Path("/tmp/pyicloud")
    ]
    
    print("\nChecking for existing sessions:")
    for base_path in possible_paths:
        if base_path.exists():
            print(f"Found directory: {base_path}")
            session_file = base_path / f"{username.replace('@', '').replace('.', '')}.session"
            if session_file.exists():
                print(f"Found session file: {session_file}")
                return str(session_file)
    return None

def check_keyring(username):
    """Check if credentials exist in keyring."""
    print("\nChecking keyring:")
    try:
        password = keyring.get_password("pyicloud", username)
        if password:
            print("Found credentials in keyring")
            return True
    except Exception as e:
        print(f"Error checking keyring: {e}")
    return False

def test_icloud_connection():
    username, password = load_config()
    print(f"Using email: {username}")
    
    # Check for existing credentials
    has_keyring = check_keyring(username)
    session_file = check_existing_sessions(username)
    
    try:
        print("\nAttempting to connect to iCloud...")
        
        # Try with existing session if available
        if session_file:
            print(f"Using existing session file: {session_file}")
            api = PyiCloudService(username, china_mainland=True)
        else:
            print("Using direct authentication")
            api = PyiCloudService(username, password, china_mainland=True)
        
        print("\n✅ Successfully connected to iCloud")
        print(f"Session valid: {api.session.has_token}")
        print(f"2FA required: {api.requires_2fa}")
        print(f"2SA required: {api.requires_2sa}")
        print(f"Session trusted: {getattr(api, 'is_trusted_session', False)}")
        
        # Try to access calendar
        print("\nAttempting to access calendar...")
        calendar = api.calendar
        print("✅ Calendar service accessed")
        
        # List available services
        print("\nAvailable services:")
        for service in ['calendar', 'contacts', 'drive', 'photos']:
            try:
                getattr(api, service)
                print(f"✅ {service}")
            except Exception as e:
                print(f"❌ {service}: {str(e)}")
            
    except Exception as e:
        print("\n❌ Error:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        import traceback
        print("\nDetailed error trace:")
        traceback.print_exc()

if __name__ == "__main__":
    test_icloud_connection()
