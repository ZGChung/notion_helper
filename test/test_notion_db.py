from notion_client import Client
import yaml


def load_config():
    with open("my_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        return config["notion"]["token"], config["notion"]["project_database_id"]


def test_database_access():
    token, db_id = load_config()
    print(f"Using token: {token}")
    print(f"Testing access to database: {db_id}")

    try:
        # Initialize the client
        notion = Client(auth=token)

        # First verify basic connection
        user = notion.users.me()
        print("\n✅ Basic API connection successful")
        print(f"Connected as user: {user.get('name', 'Unknown')}")

        # Try to access the database
        db = notion.databases.retrieve(database_id=db_id)
        print("\n✅ Successfully accessed the database!")
        print(
            f"Database title: {db.get('title', [{}])[0].get('text', {}).get('content', 'Untitled')}"
        )

        # List database properties
        print("\nDatabase properties:")
        for prop_name, prop_data in db.get("properties", {}).items():
            print(f"- {prop_name} ({prop_data.get('type', 'unknown type')})")

        # Try to query the database
        results = notion.databases.query(database_id=db_id, page_size=5)
        print(f"\n✅ Successfully queried the database")
        print(f"Number of entries found: {len(results.get('results', []))}")

    except Exception as e:
        print("\n❌ Error:")
        print(f"Error message: {str(e)}")


if __name__ == "__main__":
    test_database_access()
