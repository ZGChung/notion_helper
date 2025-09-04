#!/usr/bin/env python3
"""Test script to debug project database connection and content."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import get_config
from notion_client import Client
import re


def test_project_database():
    """Test project database connection and list all projects."""
    try:
        config = get_config()
        notion = Client(auth=config.notion_token)

        print(f"Testing project database: {config.project_database_id}")

        # Query the project database
        response = notion.databases.query(database_id=config.project_database_id)

        print(f"\nFound {len(response['results'])} projects in database:")

        projects_with_prefixes = 0

        for i, project in enumerate(response["results"], 1):
            # Extract project name from title property
            title_property = project["properties"].get("Name") or project[
                "properties"
            ].get("Title")

            if title_property and title_property["title"]:
                project_name = title_property["title"][0]["text"]["content"]
                project_id = project["id"]

                # Check for prefix
                prefix_match = re.search(r"^\[([a-zA-Z0-9]+)\]", project_name)
                if prefix_match:
                    prefix = prefix_match.group(1)
                    print(f"  {i}. [{prefix}] -> {project_name} (ID: {project_id})")
                    projects_with_prefixes += 1
                else:
                    print(f"  {i}. (no prefix) {project_name} (ID: {project_id})")
            else:
                print(f"  {i}. (no title) Project ID: {project['id']}")

        print(f"\nProjects with prefixes: {projects_with_prefixes}")

        if projects_with_prefixes == 0:
            print("\n❌ No projects found with prefixes in format [prefix]")
            print("   Make sure your project names start with [prefix], e.g.:")
            print("   - [adr] Architecture Decision Records")
            print("   - [proj] Main Project")
            print("   - [ch] Personal Chores")
        else:
            print(f"\n✅ Found {projects_with_prefixes} projects with prefixes")

    except Exception as e:
        print(f"❌ Error testing project database: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_project_database()
