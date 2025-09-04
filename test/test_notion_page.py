from notion_client import Client
import yaml


def load_token():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["notion"]["token"]


def test_page_access():
    token = load_token()
    page_id = "1fc09df71e738085b028e4e720c53e7e"
    print(f"Using token: {token}")
    print(f"Testing access to page: {page_id}")

    try:
        # Initialize the client
        notion = Client(auth=token)

        # First verify basic connection
        user = notion.users.me()
        print("\n✅ Basic API connection successful")
        print(f"Connected as user: {user.get('name', 'Unknown')}")

        # Try to access the specific page
        page = notion.pages.retrieve(page_id=page_id)
        print("\n✅ Successfully accessed the page!")
        print(
            f"Page title: {page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')}"
        )

        # Try to list the page contents
        blocks = notion.blocks.children.list(block_id=page_id)
        print(f"\n✅ Successfully listed page contents")
        print(f"Number of blocks found: {len(blocks.get('results', []))}")

    except Exception as e:
        print("\n❌ Error:")
        print(f"Error message: {str(e)}")


if __name__ == "__main__":
    test_page_access()
