# lovelace/config/settings.py - JSON settings manager

import json
import os
from pathlib import Path


class Settings:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "lovelace"
        self.settings_file = self.config_dir / "settings.json"

        self.defaults = {
            "editor": {
                "font_family": "Source Code Pro",
                "font_size": 14,
                "tab_width": 3,
                "show_line_numbers": True,
            },
            "build": {
                "compiler_path": "/usr/bin/gnatmake",
                "compiler_flags": "-O2 -g",
                "output_dir": ".",
            },
            "browser": {
                "last_directory": str(Path.home()),
                "show_hidden": False,
                "ada_filter": True,
            },
            "theme": "dark",
            "window": {},
        }

        self.config = self.defaults.copy()
        self._deep_copy_defaults()
        self.load()

    def _deep_copy_defaults(self):
        """Ensure nested dicts are independent copies."""
        import copy
        self.config = copy.deepcopy(self.defaults)

    def load(self):
        if not self.settings_file.exists():
            self.save()  # Create default file on first run
            return

        try:
            with open(self.settings_file, "r") as f:
                user_config = json.load(f)
                self._update_dict_recursive(self.config, user_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings: {e}. Using defaults.")

    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving settings: {e}")

    def get(self, section, key=None):
        if section not in self.config:
            return None
        if key is None:
            return self.config[section]
        return self.config[section].get(key)

    def set(self, section, key, value=None):
        # set("theme", "dark")           → config["theme"] = "dark"
        # set("editor", "font_size", 14) → config["editor"]["font_size"] = 14
        if value is None:
            self.config[section] = key
        else:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value

    def _update_dict_recursive(self, target, source):
        for k, v in source.items():
            if isinstance(v, dict):
                target[k] = target.get(k, {})
                self._update_dict_recursive(target[k], v)
            else:
                target[k] = v
