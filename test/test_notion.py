from notion_client import Client
import yaml


def load_token():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["notion"]["token"]


def test_notion_connection():
    token = load_token()
    print(f"Using token: {token}")

    try:
        # Initialize the client
        notion = Client(auth=token)

        # Try to get user info (most basic API call)
        user = notion.users.me()
        print("\nSuccess! Connected to Notion API")
        print(f"Connected as user: {user.get('name', 'Unknown')}")
        print(f"User type: {user.get('type', 'Unknown')}")

    except Exception as e:
        print("\nError connecting to Notion API:")
        print(f"Error message: {str(e)}")


if __name__ == "__main__":
    test_notion_connection()
