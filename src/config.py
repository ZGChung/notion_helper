"""Configuration management for Notion Helper."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


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

    # -------------------------------
    # Notion API
    # -------------------------------
    @property
    def notion_token(self) -> str:
        return self._config["notion"]["token"]

    @property
    def project_database_id(self) -> str:
        return self._config["notion"]["project_database_id"]

    @property
    def daily_log_page_id(self) -> str:
        return self._config["notion"]["daily_log_page_id"]

    # -------------------------------
    # iCloud CalDAV
    # -------------------------------
    @property
    def icloud_username(self) -> str:
        return self._config["icloud"]["username"]

    @property
    def icloud_app_password(self) -> str:
        """Get iCloud app-specific password (not Apple ID password)."""
        return self._config["icloud"]["app_password"]

    @property
    def icloud_calendars(self) -> Optional[List[str]]:
        """Get list of calendars to sync.

        Returns:
            List of calendar names to sync, or None if not configured.
            Empty list means sync all calendars.
        """
        try:
            return self._config["icloud"]["calendars"]
        except KeyError:
            return None

    @property
    def email_template_file(self) -> Path:
        return Path(self._config["paths"]["email_template"])

    @property
    def your_name(self) -> str:
        return self._config["email"]["your_name"]

    @property
    def email_subject_template(self) -> str:
        return self._config["email"]["subject_template"]

    @property
    def timezone(self) -> str:
        return self._config["timezone"]

    @property
    def recurring_events(self) -> Dict[str, list]:
        """Get manually configured weekly recurring events."""
        return self._config.get("recurring_events", {})

    def email_to_list(self) -> List[str]:
        return self._config["email"]["to_list"]

    def email_cc_list(self) -> List[str]:
        return self._config["email"]["cc_list"]

    # -------------------------------
    # Generic getter
    # -------------------------------
    def get(self, key: str, default=None):
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
