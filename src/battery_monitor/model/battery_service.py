import time
import threading
import json
import os
import psutil
from abc import ABC, abstractmethod
from plyer import notification

CONFIG_FILE = "config.json"

class NotificationStrategy(ABC):
    @abstractmethod
    def send(self, title: str, message: str):
        pass

class PlyerNotificationStrategy(NotificationStrategy):
    def send(self, title: str, message: str):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Battery Monitor",
                timeout=10
            )
        except Exception as e:
            print(f"Error en notificación: {e}")

class BatteryService:
    def __init__(self):
        # Cargar límites guardados o usar valores por defecto (20 y 80)
        config = self.load_config()
        self.low_limit = config.get("low_limit", 20)
        self.high_limit = config.get("high_limit", 80)
        
        self._observers = []
        self.monitoring = False
        self.thread = None
        
        self.persistence_interval = 120 
        self.last_low_time = 0
        self.last_high_time = 0
        
        self.notification_strategy = PlyerNotificationStrategy()

    @staticmethod
    def load_config():
        """Carga la configuración desde un archivo JSON local."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"low_limit": 20, "high_limit": 80}

    def save_config(self, low: int, high: int):
        """Guarda los umbrales actuales en el archivo de configuración."""
        self.low_limit = low
        self.high_limit = high
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"low_limit": self.low_limit, "high_limit": self.high_limit}, f, indent=4)
        except Exception as e:
            print(f"Error al guardar configuración: {e}")

    def add_observer(self, observer):
        self._observers.append(observer)

    def notify_observers(self, data):
        for observer in self._observers:
            observer.update(data)

    def set_notification_strategy(self, strategy: NotificationStrategy):
        self.notification_strategy = strategy

    def start(self):
        if not self.monitoring:
            self.monitoring = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        self.monitoring = False

    def _run(self):
        while self.monitoring:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = battery.power_plugged
                current_time = time.time()

                if percent <= self.low_limit and not plugged:
                    if current_time - self.last_low_time >= self.persistence_interval:
                        if self.notification_strategy:
                            self.notification_strategy.send(
                                "⚠️ ¡ALERTA: Batería Crítica!",
                                f"Tu batería está en {percent}%. ¡Conecta el cargador!"
                            )
                        self.last_low_time = current_time
                else:
                    if percent > self.low_limit + 3 or plugged:
                        self.last_low_time = 0

                if percent >= self.high_limit and plugged:
                    if current_time - self.last_high_time >= self.persistence_interval:
                        if self.notification_strategy:
                            self.notification_strategy.send(
                                "⚡ ¡ALERTA: Carga Alcanzada!",
                                f"La batería ha llegado a {percent}%. Desconéctala."
                            )
                        self.last_high_time = current_time
                else:
                    if percent < self.high_limit - 3 or not plugged:
                        self.last_high_time = 0

                self.notify_observers({
                    "percent": percent,
                    "plugged": plugged
                })

            time.sleep(15)