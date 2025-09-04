from pyicloud import PyiCloudService
import yaml
import logging
import sys

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("pyicloud")

def load_config():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        username = config["icloud"]["username"]
        password = config["icloud"]["password"]
        return username, password

def test_password():
    username, password = load_config()
    print(f"Username: {username}")
    print(f"Password length: {len(password)}")
    print(f"Password format: {'-'.join(password.split('-'))}")  # Show format without revealing password
    
    # Try different password formats
    passwords_to_try = [
        password,                    # Original from config
        password.replace("-", ""),   # Without dashes
        password.lower(),            # Lowercase
        password.upper(),            # Uppercase
    ]
    
    for i, test_password in enumerate(passwords_to_try, 1):
        print(f"\nTrying password format {i}...")
        print(f"Format: {len(test_password)} chars, {'-' if '-' in test_password else 'no'} dashes")
        
        try:
            print("Attempting connection...")
            api = PyiCloudService(username, test_password, china_mainland=True)
            print("✅ Connection successful!")
            return  # Exit if successful
            
        except Exception as e:
            print(f"❌ Failed: {type(e).__name__}")
            print(f"Error message: {str(e)}")
        
        print("Waiting before next attempt...")
        import time
        time.sleep(2)

if __name__ == "__main__":
    test_password()
