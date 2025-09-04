from pyicloud import PyiCloudService
import yaml
import logging
from datetime import datetime, timedelta
import requests
import urllib3

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("pyicloud")


def test_icloud_servers():
    """Test connectivity to iCloud servers."""
    servers = [
        "https://www.icloud.com.cn",
        "https://setup.icloud.com.cn",
        "https://p12-caldav.icloud.com.cn",
    ]

    print("Testing iCloud server connectivity:")
    for server in servers:
        try:
            response = requests.get(server, timeout=5)
            print(f"✅ {server}: {response.status_code}")
        except Exception as e:
            print(f"❌ {server}: {str(e)}")


def load_config():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["icloud"]["username"], config["icloud"]["password"]


def test_icloud_connection():
    username, password = load_config()
    print(f"Using email: {username}")
    print("Using app-specific password: ****-****-****-****")

    # Test server connectivity first
    print("\nTesting server connectivity...")
    test_icloud_servers()

    try:
        # Try to connect with debug options
        print("\nAttempting to connect to iCloud (China Mainland)...")
        api = PyiCloudService(username, password, china_mainland=True)

        # Print session details
        print("\nSession details:")
        print(f"Session valid: {api.session.has_token}")
        print(f"Session cookies: {api.session.cookies.get_dict()}")

        # Try basic authentication
        print("\nTesting basic authentication...")
        user = api.user
        print(f"User info: {user}")

        # Try to access different services
        print("\nTesting service access...")
        for service in ["calendar", "contacts", "drive"]:
            try:
                getattr(api, service)
                print(f"✅ {service.title()} service accessible")
            except Exception as e:
                print(f"❌ {service.title()} service error: {str(e)}")

        print("\n✅ Successfully connected to iCloud")

    except Exception as e:
        print("\n❌ Error:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nDebug information:")
        print("1. Check network connection to iCloud servers")
        print("2. Verify you can access https://www.icloud.com.cn")
        print("3. Try logging out and back in to iCloud on your device")

        # Print exception traceback for more details
        import traceback

        print("\nDetailed error trace:")
        traceback.print_exc()


if __name__ == "__main__":
    # Disable SSL warnings for debugging
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    test_icloud_connection()
