"""Mail draft creator for macOS Mail.app integration."""

import os
import subprocess
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class MailDraftCreator:
    """Creates email drafts in macOS Mail.app from generated email files."""

    def __init__(self):
        self.emails_dir = Path("emails")

    def get_latest_email_file(self) -> Optional[Path]:
        """Get the latest email file from the emails directory."""
        if not self.emails_dir.exists():
            return None

        email_files = list(self.emails_dir.glob("weekly_update_*.txt"))
        if not email_files:
            return None

        # Sort by modification time, get the latest
        latest_file = max(email_files, key=lambda f: f.stat().st_mtime)
        return latest_file

    def parse_email_file(self, file_path: Path) -> Dict[str, str]:
        """Parse email file to extract components."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            email_data = {}
            body_start_index = 0

            # Parse headers
            for i, line in enumerate(lines):
                if line.startswith("To: "):
                    email_data["to"] = line[4:].strip()
                elif line.startswith("From: "):
                    email_data["from"] = line[6:].strip()
                elif line.startswith("Subject: "):
                    email_data["subject"] = line[9:].strip()
                elif line.startswith("CC: "):
                    email_data["cc"] = line[4:].strip()
                elif line.startswith("="):
                    body_start_index = i + 1
                    break

            # Extract body (everything after the separator line)
            if body_start_index < len(lines):
                body_lines = lines[
                    body_start_index + 1 :
                ]  # Skip empty line after separator
                email_data["body"] = "\n".join(body_lines).strip()

            return email_data

        except Exception as e:
            raise Exception(f"Failed to parse email file: {e}")

    def create_mail_draft(self, email_file: Optional[Path] = None) -> bool:
        """Create a draft in Mail.app from the email file."""
        try:
            # Get email file
            if email_file is None:
                email_file = self.get_latest_email_file()

            if email_file is None:
                raise Exception("No email files found in emails/ directory")

            if not email_file.exists():
                raise Exception(f"Email file not found: {email_file}")

            # Parse email content
            email_data = self.parse_email_file(email_file)

            # Validate required fields
            required_fields = ["to", "subject", "body"]
            for field in required_fields:
                if field not in email_data or not email_data[field]:
                    raise Exception(f"Missing required field: {field}")

            # Create Mail.app draft using AppleScript
            success = self._create_applescript_draft(email_data)

            if success:
                self._send_notification(
                    "Email Draft Created",
                    f"Draft created in Mail.app\nSubject: {email_data['subject'][:50]}...",
                )
                return True
            else:
                raise Exception("Failed to create draft in Mail.app")

        except Exception as e:
            error_msg = str(e)
            self._send_notification("Mail Draft Error", error_msg)
            print(f"❌ Error creating mail draft: {error_msg}")
            return False

    def _create_applescript_draft(self, email_data: Dict[str, str]) -> bool:
        """Create email draft using AppleScript."""
        try:
            # Escape special characters for AppleScript
            to_recipients = email_data["to"].replace('"', '\\"')
            subject = email_data["subject"].replace('"', '\\"')
            cc_recipients = email_data.get("cc", "").replace('"', '\\"')

            # Convert markdown to rich text or fallback to plain text
            formatted_body = self._convert_markdown_to_richtext(email_data["body"])

            # Build AppleScript
            applescript = f"""
            tell application "Mail"
                activate
                
                set newMessage to make new outgoing message with properties {{subject:"{subject}"}}
                
                tell newMessage
                    {formatted_body}
                    
                    -- Add To recipients
                    set recipientList to my splitString("{to_recipients}", ", ")
                    repeat with recipientEmail in recipientList
                        make new to recipient at end of to recipients with properties {{address:recipientEmail}}
                    end repeat
                    
                    -- Add CC recipients if they exist
                    if "{cc_recipients}" is not "" then
                        set ccList to my splitString("{cc_recipients}", ", ")
                        repeat with ccEmail in ccList
                            make new cc recipient at end of cc recipients with properties {{address:ccEmail}}
                        end repeat
                    end if
                    
                    -- Save as draft
                    save
                    
                    -- Open the draft window for editing
                    set visible to true
                end tell
                
                return true
            end tell
            
            -- Helper function to split strings
            on splitString(theString, theDelimiter)
                set AppleScript's text item delimiters to theDelimiter
                set theList to text items of theString
                set AppleScript's text item delimiters to ""
                return theList
            end splitString
            """

            # Execute AppleScript
            process = subprocess.Popen(
                ["osascript", "-e", applescript],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                print(f"AppleScript error: {stderr}")
                return False

            return True

        except Exception as e:
            print(f"Error executing AppleScript: {e}")
            return False

    def _send_notification(self, title: str, message: str):
        """Send macOS native notification."""
        try:
            # Use osascript to send notification
            applescript = f"""
            display notification "{message}" with title "{title}" sound name "default"
            """

            subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
            )

        except Exception as e:
            print(f"Failed to send notification: {e}")

    def _convert_markdown_to_richtext(self, body: str) -> str:
        """Convert markdown to clean plain text for Mail.app."""
        try:
            # Simple approach: strip markdown syntax and use plain text
            # This is more reliable than complex rich text formatting

            # Remove **bold** markers but keep the text
            import re

            clean_body = re.sub(r"\*\*(.*?)\*\*", r"\1", body)

            # Escape quotes for AppleScript
            clean_body_escaped = clean_body.replace('"', '\\"')

            # Return simple content setting
            return f'set the content to "{clean_body_escaped}"'

        except Exception as e:
            print(f"Markdown conversion failed: {e}, using plain text")
            # Fallback to original body
            body_escaped = body.replace('"', '\\"')
            return f'set the content to "{body_escaped}"'

    def create_latest_draft(self) -> bool:
        """Create a draft from the latest email file."""
        return self.create_mail_draft()
