"""Email generator for weekly update reports."""

import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from .config import get_config
from .todo_parser import TodoItem
from .email_prompt import EMAIL_POLISHING_PROMPT
import appscript

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EmailGenerator:
    """Generator for weekly update emails."""

    def __init__(self):
        self.config = get_config()
        self.deepseek_client = self._init_deepseek_client()

    def _init_deepseek_client(self) -> Optional[openai.OpenAI]:
        """Initialize DeepSeek API client."""
        if not OPENAI_AVAILABLE:
            print("Warning: OpenAI library not available. AI polishing disabled.")
            return None

        try:
            api_key = self.config.deepseek_api_key
            if api_key and api_key != "YOUR_DEEPSEEK_API_KEY":
                # Create client with explicit parameters
                import openai

                client = openai.OpenAI(
                    api_key=api_key, base_url="https://api.deepseek.com/v1"
                )
                return client
            else:
                print(
                    "Warning: DeepSeek API key not configured. AI polishing disabled."
                )
                return None
        except Exception as e:
            print(f"Warning: Failed to initialize DeepSeek client: {e}")
            # Try alternative initialization
            try:
                import openai

                openai.api_key = api_key
                openai.api_base = "https://api.deepseek.com/v1"
                return openai
            except:
                return None

    def generate_weekly_email(
        self,
        completed_tasks_by_project: Dict[str, List[TodoItem]],
        week_start: datetime,
        week_end: datetime,
    ) -> Dict[str, str]:
        """Generate weekly update email content."""
        # Load email template if exists
        template = self._load_email_template()

        if template:
            # Use template
            email_body = self._fill_template(
                template, completed_tasks_by_project, week_start, week_end
            )
        else:
            # Generate default email
            email_body = self._generate_default_email(
                completed_tasks_by_project, week_start, week_end
            )

        # Generate subject
        subject = self.config.email_subject_template.format(
            week_start=week_start.strftime("%B %d"),
            week_end=week_end.strftime("%B %d, %Y"),
        )

        # Polish email with AI if available
        polished_body = self._polish_email_with_ai(email_body)
        if polished_body:
            email_body = polished_body
            print("   ✨ Email polished with DeepSeek AI")

        return {
            "subject": subject,
            "body": email_body,
            "to": ", ".join(self.config.email_to_list()),
            "cc": ", ".join(self.config.email_cc_list()),
            "from": self.config.your_name,
        }

    def _polish_email_with_ai(self, email_content: str) -> Optional[str]:
        """Polish email content using DeepSeek AI."""
        if not self.deepseek_client:
            return None

        try:
            prompt = EMAIL_POLISHING_PROMPT.format(email_content=email_content)

            response = self.deepseek_client.chat.completions.create(
                model=self.config.deepseek_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.deepseek_temperature,
                max_tokens=self.config.deepseek_max_tokens,
                timeout=30,  # 30 second timeout
            )

            polished_content = response.choices[0].message.content.strip()
            return polished_content

        except Exception as e:
            print(f"   ⚠️  AI polishing failed: {e}")
            print("   📝 Using original content")
            return None

    def save_email_draft(
        self, email_content: Dict[str, str], output_path: str = None
    ) -> str:
        """Save email draft to emails/ folder with date-only filename."""
        if output_path is None:
            # Create emails directory if it doesn't exist
            emails_dir = Path("emails")
            emails_dir.mkdir(exist_ok=True)

            # Use current date for filename
            date_str = datetime.now().strftime("%Y%m%d")
            output_path = emails_dir / f"weekly_update_{date_str}.txt"

        output_file = Path(output_path)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"To: {email_content['to']}\n")
            f.write(f"From: {email_content['from']}\n")
            f.write(f"Subject: {email_content['subject']}\n")
            f.write("\n" + "=" * 50 + "\n\n")
            f.write(email_content["body"])

        return str(output_file)

    def save_email_draft_in_mail_app(self, email_content: Dict[str, str]) -> None:
        """Save email draft directly in the Mail app."""
        mail = appscript.app("Mail")
        draft = mail.make(
            new=appscript.k.outgoing_message,
            with_properties={
                appscript.k.subject: email_content["subject"],
                appscript.k.content: email_content["body"],
                appscript.k.visible: True,
            },
        )
        draft.sender.set(mail.accounts[0])
        draft.to_recipients.set([appscript.k.to_recipient(email_content["to"])])
        draft.cc_recipients.set(
            [appscript.k.cc_recipient(cc) for cc in email_content.get("cc", [])]
        )
        draft.save()

    def _load_email_template(self) -> str:
        """Load email template from file if it exists."""
        template_path = self.config.email_template_file

        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()

        return None

    def _fill_template(
        self,
        template: str,
        completed_tasks_by_project: Dict[str, List[TodoItem]],
        week_start: datetime,
        week_end: datetime,
    ) -> str:
        """Fill email template with actual data."""
        # Create project summaries
        project_summaries = {}
        for project_name, tasks in completed_tasks_by_project.items():
            project_summaries[project_name] = self._create_project_summary(tasks)

        # Template variables
        template_vars = {
            "week_start": week_start.strftime("%B %d"),
            "week_end": week_end.strftime("%B %d, %Y"),
            "your_name": self.config.your_name,
            "total_tasks": sum(
                len(tasks) for tasks in completed_tasks_by_project.values()
            ),
            "project_count": len(completed_tasks_by_project),
            "project_summaries": "\n\n".join(
                f"## {name}\n{summary}" for name, summary in project_summaries.items()
            ),
        }

        # Fill template
        try:
            return template.format(**template_vars)
        except KeyError as e:
            print(
                f"Warning: Template variable {e} not found, using default email format"
            )
            return self._generate_default_email(
                completed_tasks_by_project, week_start, week_end
            )

    def _generate_default_email(
        self,
        completed_tasks_by_project: Dict[str, List[TodoItem]],
        week_start: datetime,
        week_end: datetime,
    ) -> str:
        """Generate default email format."""
        lines = [
            f"Hi,",
            "",
            f"Here's my weekly update for {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}:",
            "",
        ]

        # Add project summaries
        for project_name, tasks in sorted(completed_tasks_by_project.items()):
            lines.append(f"## {project_name}")
            lines.append("")

            # Group tasks by date for better organization
            tasks_by_date = {}
            for task in tasks:
                date_key = task.date.strftime("%A, %B %d")
                if date_key not in tasks_by_date:
                    tasks_by_date[date_key] = []
                tasks_by_date[date_key].append(task)

            for date_str, date_tasks in sorted(tasks_by_date.items()):
                if len(tasks_by_date) > 1:  # Only show date if multiple dates
                    lines.append(f"**{date_str}:**")

                for task in date_tasks:
                    lines.append(f"- {task.text}")

                if len(tasks_by_date) > 1:
                    lines.append("")

            lines.append("")

        # Add summary
        total_tasks = sum(len(tasks) for tasks in completed_tasks_by_project.values())
        lines.extend(
            [
                f"**Summary:** Completed {total_tasks} tasks across {len(completed_tasks_by_project)} projects this week.",
                "",
                "Let me know if you have any questions!",
                "",
                f"Best regards,",
                f"{self.config.your_name}",
            ]
        )

        return "\n".join(lines)

    def _create_project_summary(self, tasks: List[TodoItem]) -> str:
        """Create a summary for a specific project."""
        if not tasks:
            return "No tasks completed this week."

        # Group by date
        tasks_by_date = {}
        for task in tasks:
            date_key = task.date.strftime("%m/%d")
            if date_key not in tasks_by_date:
                tasks_by_date[date_key] = []
            tasks_by_date[date_key].append(task)

        summary_lines = []
        for date_str, date_tasks in sorted(tasks_by_date.items()):
            for task in date_tasks:
                summary_lines.append(f"- {date_str}: {task.text}")

        return "\n".join(summary_lines)

    def create_email_template(self, template_path: str = None) -> str:
        """Create a sample email template file."""
        if template_path is None:
            template_path = self.config.email_template_file

        template_content = """Hi,

Here's my weekly update for {week_start} - {week_end}:

{project_summaries}

**Summary:** Completed {total_tasks} tasks across {project_count} projects this week.

Let me know if you have any questions!

Best regards,
{your_name}"""

        template_file = Path(template_path)
        template_file.parent.mkdir(parents=True, exist_ok=True)

        with open(template_file, "w", encoding="utf-8") as f:
            f.write(template_content)

        return str(template_file)
