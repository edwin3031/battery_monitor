import threading
import time
from collections.abc import Callable

import psutil


class BatteryService:
    def __init__(self, check_interval: int = 15):
        self.check_interval = check_interval
        self._observers: list[Callable[[int, bool], None]] = []
        self._running = False
        self._thread = None

    def add_observer(self, callback: Callable[[int, bool], None]):
        """Callback recibe (percent: int, is_plugged: bool)"""
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[int, bool], None]):
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify(self, percent: int, is_plugged: bool):
        for callback in self._observers:
            try:
                callback(percent, is_plugged)
            except Exception as e:
                print(f"[Error ObserverCallback]: {e}")

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            battery = psutil.sensors_battery()
            if battery:
                self._notify(battery.percent, battery.power_plugged)
            time.sleep(self.check_interval)