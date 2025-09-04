"""Configuration management for Notion Helper."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List


class Config:
    """Configuration manager for the Notion Helper application."""

    def __init__(self, config_path: str = None):
        """Initialize configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "my_config.yaml"

        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Expand user paths
        if "paths" in config:
            for key, path in config["paths"].items():
                if isinstance(path, str) and path.startswith("~"):
                    config["paths"][key] = os.path.expanduser(path)

        return config

    @property
    def notion_token(self) -> str:
        """Get Notion API token."""
        return self._config["notion"]["token"]

    @property
    def notion_daily_log_page_id(self) -> str:
        """Get Notion daily log page ID."""
        return self._config["notion"]["daily_log_page_id"]

    @property
    def project_database_id(self) -> str:
        """Get Notion project database ID."""
        return self._config["notion"]["project_database_id"]

    @property
    def daily_log_page_id(self) -> str:
        """Get Notion daily log page ID."""
        return self._config["notion"]["daily_log_page_id"]

    @property
    def icloud_username(self) -> str:
        """Get iCloud username."""
        return self._config["icloud"]["username"]

    @property
    def icloud_password(self) -> str:
        """Get iCloud app-specific password."""
        return self._config["icloud"]["password"]

    @property
    def email_template_file(self) -> Path:
        """Get email template file path."""
        return Path(self._config["paths"]["email_template"])

    @property
    def boss_email(self) -> str:
        """Get boss email address."""
        return self._config["email"]["boss_email"]

    @property
    def your_name(self) -> str:
        """Get your name for email signature."""
        return self._config["email"]["your_name"]

    @property
    def email_subject_template(self) -> str:
        """Get email subject template."""
        return self._config["email"]["subject_template"]

    @property
    def timezone(self) -> str:
        """Get timezone setting."""
        return self._config["timezone"]

    @property
    def daily_todo_filename_pattern(self) -> str:
        """Get daily todo filename pattern."""
        return self._config["daily_todo_filename_pattern"]

    def email_to_list(self) -> List[str]:
        """Get email destination list."""
        return self._config["email"]["to_list"]

    def email_cc_list(self) -> List[str]:
        """Get email CC list."""
        return self._config["email"]["cc_list"]

    def get(self, key: str, default=None):
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


# Global config instance
config = None


def get_config(config_path: str = None) -> Config:
    """Get global configuration instance."""
    global config
    if config is None:
        config = Config(config_path)
    return config
