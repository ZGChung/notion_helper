"""Daily todo list parser for extracting completed tasks and syncing to projects."""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from .config import get_config
from notion_client import Client


@dataclass
class TodoItem:
    """Represents a todo item."""

    text: str
    completed: bool
    date: datetime
    prefix: Optional[str] = None
    children: List["TodoItem"] = None
    notion_block_id: Optional[str] = None

    def __post_init__(self):
        """Extract prefix from todo text and initialize children list."""
        if self.children is None:
            self.children = []
        if self.prefix is None:
            self.prefix = self._extract_prefix()

    def _extract_prefix(self) -> Optional[str]:
        """Extract prefix from todo text in format [prefix]."""
        # Look for pattern [prefix] at the beginning of the text
        pattern = r"^\[([a-zA-Z0-9]+)\]"
        match = re.search(pattern, self.text.strip())
        if match:
            return match.group(1)
        return None

    def get_text_without_prefix(self) -> str:
        """Get todo text without the prefix."""
        if self.prefix:
            return re.sub(
                r"^\[" + re.escape(self.prefix) + r"\]\s*", "", self.text.strip()
            )
        return self.text.strip()

    def to_notion_block(self) -> Dict:
        """Convert todo item to Notion block format."""
        text_content = self.get_text_without_prefix()

        block = {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": text_content}}],
                "checked": self.completed,
            },
        }

        # Add children if they exist
        if self.children:
            block["to_do"]["children"] = [
                child.to_notion_block() for child in self.children
            ]

        return block


class TodoParser:
    """Parser for daily todo list from Notion."""

    def __init__(self):
        self.config = get_config()
        self.notion = Client(auth=self.config.notion_token)
        self._project_cache = None

    def get_projects(self) -> Dict[str, Dict]:
        """Get all projects from the database and cache them."""
        if self._project_cache is None:
            self._project_cache = {}

            # Query the project database
            response = self.notion.databases.query(
                database_id=self.config.project_database_id
            )

            for project in response["results"]:
                # Extract project name from title property
                title_property = project["properties"].get("Name") or project[
                    "properties"
                ].get("Title")
                if title_property and title_property["title"]:
                    project_name = title_property["title"][0]["text"]["content"]

                    # Extract prefix from project name
                    prefix_match = re.search(r"^\[([a-zA-Z0-9]+)\]", project_name)
                    if prefix_match:
                        prefix = prefix_match.group(1)
                        self._project_cache[prefix] = {
                            "id": project["id"],
                            "name": project_name,
                            "page_id": project[
                                "id"
                            ],  # In Notion, database entries are also pages
                        }

        return self._project_cache

    def fetch_daily_todos(self, date: datetime) -> List[TodoItem]:
        """Fetch daily todos from Notion page."""
        page_id = self.config.notion_daily_log_page_id

        # Get all blocks from the page
        blocks = self.notion.blocks.children.list(block_id=page_id)

        # Parse blocks to extract hierarchical todos
        todos = self._parse_notion_blocks(blocks["results"], date)

        return todos

    def _parse_notion_blocks(
        self, blocks: List[Dict], date: datetime
    ) -> List[TodoItem]:
        """Parse Notion blocks to extract hierarchical todos."""
        todos = []

        for block in blocks:
            if block["type"] == "to_do":
                # Extract text from rich_text
                text = ""
                if block["to_do"]["rich_text"]:
                    text = block["to_do"]["rich_text"][0]["text"]["content"]

                completed = block["to_do"]["checked"]

                # Create todo item
                todo = TodoItem(
                    text=text,
                    completed=completed,
                    date=date,
                    notion_block_id=block["id"],
                )

                # Parse children if they exist
                if block.get("has_children", False):
                    children_response = self.notion.blocks.children.list(
                        block_id=block["id"]
                    )
                    todo.children = self._parse_notion_blocks(
                        children_response["results"], date
                    )

                todos.append(todo)

            elif block["type"] in ["toggle", "bulleted_list_item"]:
                # For toggle blocks and bulleted lists, recursively parse children
                if block.get("has_children", False):
                    children_response = self.notion.blocks.children.list(
                        block_id=block["id"]
                    )
                    child_todos = self._parse_notion_blocks(
                        children_response["results"], date
                    )
                    todos.extend(child_todos)

        return todos

    def sync_todos_to_projects(self, date: datetime = None) -> Dict[str, int]:
        """Sync todos with prefixes to their corresponding project pages."""
        if date is None:
            date = datetime.now()

        # Get all todos from the daily log
        todos = self.fetch_daily_todos(date)

        # Get projects mapping
        projects = self.get_projects()

        # Group todos by prefix
        todos_by_prefix = {}
        for todo in todos:
            if todo.prefix and todo.prefix in projects:
                if todo.prefix not in todos_by_prefix:
                    todos_by_prefix[todo.prefix] = []
                todos_by_prefix[todo.prefix].append(todo)

        # Sync each group to its project page
        sync_results = {}
        for prefix, prefix_todos in todos_by_prefix.items():
            project = projects[prefix]
            synced_count = self._sync_todos_to_project_page(prefix_todos, project)
            sync_results[project["name"]] = synced_count
            print(f"Synced {synced_count} todos to project: {project['name']}")

        return sync_results

    def _sync_todos_to_project_page(self, todos: List[TodoItem], project: Dict) -> int:
        """Sync a list of todos to a specific project page."""
        if not todos:
            return 0

        project_page_id = project["page_id"]

        # Get existing content from project page to check for duplicates
        existing_blocks = self.notion.blocks.children.list(block_id=project_page_id)
        existing_todo_texts = self._extract_existing_todo_texts(
            existing_blocks["results"]
        )

        # Filter out todos that already exist
        new_todos = []
        for todo in todos:
            todo_text_without_prefix = todo.get_text_without_prefix()
            if todo_text_without_prefix not in existing_todo_texts:
                new_todos.append(todo)

        if not new_todos:
            return 0

        # Convert todos to Notion blocks
        blocks_to_add = [todo.to_notion_block() for todo in new_todos]

        # Add blocks to project page
        self.notion.blocks.children.append(
            block_id=project_page_id, children=blocks_to_add
        )

        return len(new_todos)

    def _extract_existing_todo_texts(self, blocks: List[Dict]) -> set:
        """Extract text content from existing todo blocks to check for duplicates."""
        todo_texts = set()

        for block in blocks:
            if block["type"] == "to_do":
                if block["to_do"]["rich_text"]:
                    text = block["to_do"]["rich_text"][0]["text"]["content"]
                    todo_texts.add(text.strip())

                # Recursively check children
                if block.get("has_children", False):
                    children_response = self.notion.blocks.children.list(
                        block_id=block["id"]
                    )
                    child_texts = self._extract_existing_todo_texts(
                        children_response["results"]
                    )
                    todo_texts.update(child_texts)

            elif block["type"] in ["toggle", "bulleted_list_item"] and block.get(
                "has_children", False
            ):
                children_response = self.notion.blocks.children.list(
                    block_id=block["id"]
                )
                child_texts = self._extract_existing_todo_texts(
                    children_response["results"]
                )
                todo_texts.update(child_texts)

        return todo_texts

    def parse_week_files(self, start_date: datetime) -> List[TodoItem]:
        """Parse all daily todo files for a given week."""
        all_todos = []

        for i in range(7):  # Parse 7 days
            current_date = start_date + timedelta(days=i)
            todos = self.fetch_daily_todos(current_date)
            all_todos.extend(todos)

        return all_todos

    def get_completed_tasks_by_project(
        self, todos: List[TodoItem]
    ) -> Dict[str, List[TodoItem]]:
        """Group completed tasks by project prefix."""
        completed_by_project = {}

        for todo in todos:
            if todo.completed and todo.prefix:
                project_key = todo.prefix
                if project_key not in completed_by_project:
                    completed_by_project[project_key] = []
                completed_by_project[project_key].append(todo)

        return completed_by_project

    def get_last_week_range(self) -> Tuple[datetime, datetime]:
        """Get the date range for last week (Monday to Sunday)."""
        today = datetime.now()

        # Find last Monday
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        last_sunday = last_monday + timedelta(days=6)

        return last_monday, last_sunday

    def get_next_week_range(self) -> Tuple[datetime, datetime]:
        """Get the date range for next week (Monday to Sunday)."""
        today = datetime.now()

        # Find next Monday
        days_until_monday = 7 - today.weekday()
        next_monday = today + timedelta(days=days_until_monday)
        next_sunday = next_monday + timedelta(days=6)

        return next_monday, next_sunday
