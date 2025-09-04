"""Daily todo list parser for extracting completed tasks."""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

from .config import get_config
from notion_client import NotionClient


@dataclass
class TodoItem:
    """Represents a todo item."""
    text: str
    completed: bool
    date: datetime
    project: str = None
    
    def __post_init__(self):
        """Extract project from todo text if not provided."""
        if self.project is None:
            self.project = self._extract_project()
    
    def _extract_project(self) -> str:
        """Extract project name from todo text using common patterns."""
        # Look for patterns like [ProjectName], @ProjectName, #ProjectName
        patterns = [
            r'\[([^\]]+)\]',  # [ProjectName]
            r'@(\w+)',        # @ProjectName
            r'#(\w+)',        # #ProjectName
            r'- (\w+):',      # - ProjectName:
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text)
            if match:
                return match.group(1)
        
        # If no project pattern found, try to infer from keywords
        text_lower = self.text.lower()
        if any(word in text_lower for word in ['meeting', 'call', 'standup']):
            return 'Meetings'
        elif any(word in text_lower for word in ['email', 'respond', 'reply']):
            return 'Communication'
        elif any(word in text_lower for word in ['code', 'develop', 'implement', 'fix', 'bug']):
            return 'Development'
        elif any(word in text_lower for word in ['review', 'document', 'write']):
            return 'Documentation'
        
        return 'General'


class TodoParser:
    """Parser for daily todo list from Notion."""
    
    def __init__(self):
        self.config = get_config()
        self.notion_client = NotionClient(token=self.config.notion_token)
    
    def fetch_daily_todos(self, date: datetime) -> List[TodoItem]:
        """Fetch daily todos from Notion page."""
        page_id = self.config.notion_daily_log_page_id
        todos = []
        
        # Fetch the page content from Notion
        page_content = self.notion_client.get_page_content(page_id)
        
        # Parse the content to extract todos
        todos.extend(self._parse_notion_format(page_content, date))
        
        return todos
    
    def _parse_notion_format(self, content: str, date: datetime) -> List[TodoItem]:
        """Parse Notion format for todos."""
        todos = []
        
        # Example parsing logic for Notion format
        # This needs to be customized based on actual Notion page structure
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('- [ ]') or line.startswith('- [x]'):
                completed = '[x]' in line
                text = line.split(']', 1)[1].strip()
                todos.append(TodoItem(text=text, completed=completed, date=date))
        
        return todos
    
    def parse_week_files(self, start_date: datetime) -> List[TodoItem]:
        """Parse all daily todo files for a given week."""
        all_todos = []
        
        for i in range(7):  # Parse 7 days
            current_date = start_date + timedelta(days=i)
            filename = current_date.strftime(self.config.daily_todo_filename_pattern)
            file_path = self.config.daily_todos_dir / filename
            
            todos = self.parse_daily_file(file_path)
            all_todos.extend(todos)
        
        return all_todos
    
    def get_completed_tasks_by_project(self, todos: List[TodoItem]) -> Dict[str, List[TodoItem]]:
        """Group completed tasks by project."""
        completed_by_project = {}
        
        for todo in todos:
            if todo.completed:
                if todo.project not in completed_by_project:
                    completed_by_project[todo.project] = []
                completed_by_project[todo.project].append(todo)
        
        return completed_by_project
    
    def _extract_date_from_filename(self, file_path: Path) -> datetime:
        """Extract date from filename using the configured pattern."""
        filename = file_path.stem  # Remove extension
        
        # Try to parse using the configured pattern
        try:
            return datetime.strptime(filename, self.config.daily_todo_filename_pattern.replace('.txt', ''))
        except ValueError:
            # Fallback: try common date formats
            formats = ['%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y', '%Y%m%d']
            for fmt in formats:
                try:
                    return datetime.strptime(filename, fmt)
                except ValueError:
                    continue
            
            # If all fails, use file modification time
            return datetime.fromtimestamp(file_path.stat().st_mtime)
    
    def _parse_checkbox_format(self, content: str, date: datetime) -> List[TodoItem]:
        """Parse checkbox format: - [x] Task or - [ ] Task."""
        todos = []
        
        # Match patterns like "- [x] Task" or "- [ ] Task"
        pattern = r'^[-*]\s*\[([x\s])\]\s*(.+)$'
        
        for line in content.split('\n'):
            line = line.strip()
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                completed = match.group(1).lower() == 'x'
                text = match.group(2).strip()
                todos.append(TodoItem(text=text, completed=completed, date=date))
        
        return todos
    
    def _parse_dash_format(self, content: str, date: datetime) -> List[TodoItem]:
        """Parse dash format with strikethrough: - ~~Task~~ or - Task."""
        todos = []
        
        # Match patterns like "- ~~Task~~" (completed) or "- Task" (not completed)
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('-') and not re.match(r'^[-*]\s*\[', line):
                # Remove leading dash and whitespace
                text = re.sub(r'^[-*]\s*', '', line).strip()
                
                # Check if strikethrough (completed)
                if text.startswith('~~') and text.endswith('~~'):
                    completed = True
                    text = text[2:-2]  # Remove strikethrough markers
                else:
                    completed = False
                
                if text:  # Only add non-empty tasks
                    todos.append(TodoItem(text=text, completed=completed, date=date))
        
        return todos
    
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