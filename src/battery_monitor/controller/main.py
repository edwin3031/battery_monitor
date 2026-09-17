import os
import sys
import threading
import platform
from PIL import Image, ImageDraw, ImageFont
pystray = None
try:
    import pystray
    from pystray import MenuItem as item
except ImportError:
    pystray = None

from battery_monitor.model.battery_service import BatteryService
from battery_monitor.view.ui import BatteryView

class BatteryController:
    def __init__(self):
        self.model = BatteryService()
        self.view = BatteryView(self, self.model.low_limit, self.model.high_limit, self.is_autostart_enabled())

        # Suscribir la vista y al controlador como observadores
        self.model.add_observer(self.view)
        self.model.add_observer(self) # Para actualizar el icono del tray

        self.tray_icon = None
        self._setup_tray()

        self.model.start()
        self.view.set_button_state(True)
        self.view.withdraw()

    def update(self, data):
        """Método Observer para actualizar dinámicamente el icono de la bandeja."""
        percent = data["percent"]
        plugged = data["plugged"]
        if self.tray_icon:
            try:
                self.tray_icon.icon = self._create_dynamic_image(percent, plugged)
                status_text = f"Batería: {percent}% ({'Cargando' if plugged else 'En uso'})"
                self.tray_icon.title = f"Battery Monitor - {percent}%"
            except Exception:
                pass

    def _create_dynamic_image(self, percent, plugged):
        """Genera dinámicamente una imagen con el porcentaje y estado de batería."""
        image = Image.new('RGB', (64, 64), color=(33, 150, 243) if not plugged else (76, 175, 80))
        dc = ImageDraw.Draw(image)
        
        # Dibujar marco blanco
        dc.rectangle((4, 4, 60, 60), outline=(255, 255, 255), width=3)
        
        # Escribir el porcentaje de texto dentro del icono
        text = f"{int(percent)}"
        try:
            # Intentar usar una fuente estándar si está disponible
            font = ImageFont.load_default()
            dc.text((14, 20), text, fill=(255, 255, 255), font=font)
        except Exception:
            dc.text((14, 20), text, fill=(255, 255, 255))
            
        return image

    def _setup_tray(self):
        if not pystray:
            return
        
        menu = (
            item('Mostrar / Ocultar Ventana', self.toggle_window_visibility),
            item('Salir Completamente', self.quit_app)
        )
        # Iniciar con un icono por defecto
        initial_image = self._create_dynamic_image(100, False)
        self.tray_icon = pystray.Icon("battery_monitor", initial_image, "Monitor de Batería", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        self.view.withdraw()

    def toggle_window_visibility(self, icon, item):
        if self.view.winfo_viewable():
            self.view.after(0, self.view.withdraw)
        else:
            self.view.after(0, self.view.deiconify)
            self.view.after(0, self.view.lift)

    def toggle_monitoring_from_ui(self):
        low, high = self.view.get_limits()
        self.model.save_config(low, high)

        if self.model.monitoring:
            self.model.stop()
            self.view.set_button_state(False)
        else:
            self.model.start()
            self.view.set_button_state(True)

    # --- LÓGICA DE AUTOSTART ---
    def is_autostart_enabled(self):
        system = platform.system()
        if system == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
                winreg.QueryValueEx(key, "BatteryMonitor")
                winreg.CloseKey(key)
                return True
            except Exception:
                return False
        elif system == "Linux":
            desktop_file = os.path.expanduser("~/.config/autostart/battery-monitor.desktop")
            return os.path.exists(desktop_file)
        return False

    def toggle_autostart(self, enabled):
        system = platform.system()
        app_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
        
        if system == "Windows":
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
                if enabled:
                    winreg.SetValueEx(key, "BatteryMonitor", 0, winreg.REG_SZ, f'"{app_path}"')
                else:
                    try:
                        winreg.DeleteValue(key, "BatteryMonitor")
                    except FileNotFoundError:
                        pass
                winreg.CloseKey(key)
            except Exception as e:
                print(f"Error configurando autostart en Windows: {e}")
                
        elif system == "Linux":
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_file = os.path.join(autostart_dir, "battery-monitor.desktop")
            if enabled:
                os.makedirs(autostart_dir, exist_ok=True)
                content = f"""[Desktop Entry]
Type=Application
Name=Battery Monitor
Exec=python3 "{app_path}"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
                with open(desktop_file, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                if os.path.exists(desktop_file):
                    os.remove(desktop_file)

    def quit_app(self, icon, item):
        low, high = self.view.get_limits()
        self.model.save_config(low, high)
        self.model.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        self.view.after(0, self.view.destroy)

    def run(self):
        self.view.mainloop()

if __name__ == "__main__":
    controller = BatteryController()
    controller.run()