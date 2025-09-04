from pyicloud import PyiCloudService
import yaml
import logging
import getpass
import sys
import time

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
    
    # Try both global and China endpoints
    endpoints = [
        {"name": "Global", "china_mainland": False},
        {"name": "China", "china_mainland": True}
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTrying {endpoint['name']} endpoint...")
            api = PyiCloudService(
                username, 
                password, 
                china_mainland=endpoint["china_mainland"]
            )
            
            if api.requires_2fa:
                print("\nTwo-factor authentication required.")
                print("Please check your Apple device for the code.")
                code = input("Enter the verification code: ")
                
                if not api.validate_2fa_code(code):
                    print("Failed to verify 2FA code")
                    continue
                
                print("✅ 2FA code verified")
            
            print(f"\n✅ Successfully authenticated with {endpoint['name']} endpoint")
            print(f"Session valid: {api.session.has_token}")
            
            # Try to access calendar
            print("\nAttempting to access calendar...")
            calendar = api.calendar
            print("✅ Calendar service accessed")
            return  # Exit if successful
                
        except Exception as e:
            print(f"\n❌ Error with {endpoint['name']} endpoint:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            
            if "503" in str(e):
                print("Server temporarily unavailable, trying next endpoint...")
            
        # Wait before trying next endpoint
        time.sleep(2)

if __name__ == "__main__":
    test_icloud_connection()
