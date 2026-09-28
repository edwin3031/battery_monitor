import os
import threading

import pystray
from PIL import Image


class SystemTrayManager:
    def __init__(self, assets_dir: str, on_show: callable, on_exit: callable):
        self.assets_dir = assets_dir
        self.on_show = on_show
        self.on_exit = on_exit
        self.icon = None

    def _get_tray_image(self):
        png_path = os.path.join(self.assets_dir, "icon.png")
        if os.path.exists(png_path):
            return Image.open(png_path)
        return Image.new("RGB", (64, 64), color="green")

    def run(self):
        menu = pystray.Menu(
            pystray.MenuItem("Show", lambda icon, item: self.on_show()),
            pystray.MenuItem("Exit", lambda icon, item: self.on_exit())
        )
        self.icon = pystray.Icon(
            "battery_monitor",
            self._get_tray_image(),
            "Battery Monitor",
            menu
        )
        threading.Thread(target=self.icon.run, daemon=True).start()

    def stop(self):
        if self.icon:
            self.icon.stop()