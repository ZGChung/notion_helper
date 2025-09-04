from pyicloud import PyiCloudService
import yaml
import logging
import getpass
import sys

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("pyicloud")

def load_username():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["icloud"]["username"]

def test_icloud_connection():
    username = load_username()
    print(f"Username: {username}")
    password = getpass.getpass("Enter your iCloud password: ")
    
    try:
        print("\nAttempting to connect to iCloud...")
        api = PyiCloudService(username, password, china_mainland=True)
        
        if api.requires_2fa:
            print("\nTwo-factor authentication required.")
            print("Please check your Apple device for the code.")
            code = input("Enter the verification code: ")
            
            if not api.validate_2fa_code(code):
                print("Failed to verify 2FA code")
                return
            
            print("✅ 2FA code verified")
        
        print("\n✅ Successfully authenticated with iCloud")
        print(f"Session valid: {api.session.has_token}")
        
        # Try to access calendar
        print("\nAttempting to access calendar...")
        calendar = api.calendar
        print("✅ Calendar service accessed")
            
    except Exception as e:
        print("\n❌ Error:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        import traceback
        print("\nDetailed error trace:")
        traceback.print_exc()

if __name__ == "__main__":
    test_icloud_connection()
