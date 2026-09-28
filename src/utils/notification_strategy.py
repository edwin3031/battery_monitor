import os
import sys
from abc import ABC, abstractmethod

from plyer import notification


class NotificationStrategy(ABC):
    @abstractmethod
    def notify(self, title: str, message: str, assets_dir: str = None):
        pass

class DesktopNotificationStrategy(NotificationStrategy):
    def notify(self, title: str, message: str, assets_dir: str = None):
        kwargs = {
            "title": title,
            "message": message,
            "app_name": "Battery Monitor",
            "timeout": 10
        }

        # Strict platform dependent icon selection
        if assets_dir and os.path.exists(assets_dir):
            if sys.platform.startswith("win"):
                icon_file = os.path.join(assets_dir, "icon.ico")
                if os.path.exists(icon_file):
                    kwargs["app_icon"] = icon_file
            elif sys.platform.startswith("linux"):
                icon_file = os.path.join(assets_dir, "icon.png")
                if os.path.exists(icon_file):
                    kwargs["app_icon"] = icon_file
            # MacOS (darwin), scripted notifications do not accept external app_icon

        try:
            notification.notify(**kwargs)
        except Exception as e:
            print(f"[Notification Warning]: Sending with icon failed ({e}). Retrying without icon...")
            try:
                kwargs.pop("app_icon", None)
                notification.notify(**kwargs)
            except Exception as ex:
                print(f"[Definitive Notification Error]: {ex}")