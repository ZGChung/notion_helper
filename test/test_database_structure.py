#!/usr/bin/env python3
"""Test script to examine the database structure and properties."""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import get_config
from notion_client import Client


def test_database_structure():
    """Test database structure to understand the properties."""
    try:
        config = get_config()
        notion = Client(auth=config.notion_token)

        print(f"Testing database structure: {config.project_database_id}")

        # First, get database info
        database_info = notion.databases.retrieve(
            database_id=config.project_database_id
        )

        print("\n=== Database Properties ===")
        for prop_name, prop_info in database_info["properties"].items():
            print(f"  {prop_name}: {prop_info['type']}")

        # Query the project database
        response = notion.databases.query(database_id=config.project_database_id)

        print(f"\n=== First Project Details ===")
        if response["results"]:
            first_project = response["results"][0]
            print(f"Project ID: {first_project['id']}")
            print("Properties:")
            for prop_name, prop_value in first_project["properties"].items():
                print(f"  {prop_name}: {json.dumps(prop_value, indent=4)}")
        else:
            print("No projects found in database")

    except Exception as e:
        print(f"❌ Error testing database structure: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_database_structure()
