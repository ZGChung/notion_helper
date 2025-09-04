"""Notion API client for updating project database and daily logs."""

from datetime import datetime
from typing import List, Dict, Any
from notion_client import Client

from .config import get_config
from .todo_parser import TodoItem


class NotionClient:
    """Client for interacting with Notion API."""
    
    def __init__(self):
        self.config = get_config()
        self.client = Client(auth=self.config.notion_token)
    
    def update_project_database(self, completed_tasks_by_project: Dict[str, List[TodoItem]]) -> None:
        """Update project database with completed tasks summary."""
        for project_name, tasks in completed_tasks_by_project.items():
            # Find or create project page
            project_page = self._find_or_create_project(project_name)
            
            # Create summary of completed tasks
            summary = self._create_task_summary(tasks)
            
            # Update project page with summary
            self._append_to_project_page(project_page['id'], summary)
    
    def update_daily_log(self, completed_tasks_by_project: Dict[str, List[TodoItem]], week_start: datetime, week_end: datetime) -> None:
        """Update daily log page with weekly summary."""
        # Create weekly summary content
        content = self._create_weekly_log_content(completed_tasks_by_project, week_start, week_end)
        
        # Append to daily log page
        self._append_to_daily_log(content)
    
    def _find_or_create_project(self, project_name: str) -> Dict[str, Any]:
        """Find existing project or create new one in project database."""
        # Search for existing project
        try:
            response = self.client.databases.query(
                database_id=self.config.project_database_id,
                filter={
                    "property": "Name",
                    "title": {
                        "equals": project_name
                    }
                }
            )
            
            if response['results']:
                return response['results'][0]
        except Exception as e:
            print(f"Error searching for project {project_name}: {e}")
        
        # Create new project if not found
        try:
            new_project = self.client.pages.create(
                parent={"database_id": self.config.project_database_id},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": project_name
                                }
                            }
                        ]
                    }
                }
            )
            return new_project
        except Exception as e:
            print(f"Error creating project {project_name}: {e}")
            return None
    
    def _create_task_summary(self, tasks: List[TodoItem]) -> str:
        """Create a summary of completed tasks."""
        if not tasks:
            return ""
        
        # Group tasks by date
        tasks_by_date = {}
        for task in tasks:
            date_str = task.date.strftime("%Y-%m-%d")
            if date_str not in tasks_by_date:
                tasks_by_date[date_str] = []
            tasks_by_date[date_str].append(task)
        
        # Create summary
        summary_lines = [f"## Weekly Update - {tasks[0].date.strftime('%B %d, %Y')} Week"]
        summary_lines.append("")
        
        for date_str, date_tasks in sorted(tasks_by_date.items()):
            summary_lines.append(f"### {datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d')}")
            for task in date_tasks:
                summary_lines.append(f"- {task.text}")
            summary_lines.append("")
        
        return "\n".join(summary_lines)
    
    def _create_weekly_log_content(self, completed_tasks_by_project: Dict[str, List[TodoItem]], week_start: datetime, week_end: datetime) -> str:
        """Create weekly log content for daily log page."""
        content_lines = [
            f"# Weekly Summary: {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}",
            ""
        ]
        
        for project_name, tasks in completed_tasks_by_project.items():
            content_lines.append(f"## {project_name}")
            for task in tasks:
                content_lines.append(f"- {task.date.strftime('%m/%d')}: {task.text}")
            content_lines.append("")
        
        return "\n".join(content_lines)
    
    def _append_to_project_page(self, page_id: str, content: str) -> None:
        """Append content to a project page."""
        try:
            # Convert content to Notion blocks
            blocks = self._text_to_notion_blocks(content)
            
            # Append blocks to page
            self.client.blocks.children.append(
                block_id=page_id,
                children=blocks
            )
        except Exception as e:
            print(f"Error appending to project page {page_id}: {e}")
    
    def _append_to_daily_log(self, content: str) -> None:
        """Append content to daily log page."""
        try:
            # Convert content to Notion blocks
            blocks = self._text_to_notion_blocks(content)
            
            # Append blocks to daily log page
            self.client.blocks.children.append(
                block_id=self.config.daily_log_page_id,
                children=blocks
            )
        except Exception as e:
            print(f"Error appending to daily log: {e}")
    
    def _text_to_notion_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Convert plain text to Notion blocks."""
        blocks = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('# '):
                # Heading 1
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line[2:]
                                }
                            }
                        ]
                    }
                })
            elif line.startswith('## '):
                # Heading 2
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line[3:]
                                }
                            }
                        ]
                    }
                })
            elif line.startswith('### '):
                # Heading 3
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line[4:]
                                }
                            }
                        ]
                    }
                })
            elif line.startswith('- '):
                # Bullet point
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line[2:]
                                }
                            }
                        ]
                    }
                })
            else:
                # Regular paragraph
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line
                                }
                            }
                        ]
                    }
                })
        
        return blocks
    
    def test_connection(self) -> bool:
        """Test connection to Notion API."""
        try:
            # Try to get user info
            user = self.client.users.me()
            print(f"Connected to Notion as: {user.get('name', 'Unknown')}")
            return True
        except Exception as e:
            print(f"Failed to connect to Notion: {e}")
            return False