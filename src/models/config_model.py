import json
import os


class ConfigModel:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.low_limit = 20
        self.high_limit = 80
        self.autostart = False
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.low_limit = data.get("low_limit", 20)
                    self.high_limit = data.get("high_limit", 80)
                    self.autostart = data.get("autostart", False)
            except Exception as e:
                print(f"[Error ConfigLoad]: {e}")

    def save(self):
        data = {
            "low_limit": self.low_limit,
            "high_limit": self.high_limit,
            "autostart": self.autostart
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[Error ConfigSave]: {e}")