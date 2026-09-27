import os
import platform

# Explicitly registering AppUserModelID in Windows for the icon and name in the taskbar/notifications
if platform.system() == "Windows":
    try:
        import ctypes
        myappid = "Utility.BatteryMonitor.App.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as e:
        print(f"[Warning AppUserModelID]: {e}")

from controllers.battery_controller import BatteryController
from models.battery_service import BatteryService
from models.config_model import ConfigModel
from utils.icon_generator import ensure_assets_exist
from utils.notification_strategy import DesktopNotificationStrategy
from views.battery_view import BatteryView
from views.system_tray import SystemTrayManager


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "assets")

    ensure_assets_exist(assets_dir)

    config = ConfigModel(os.path.join(base_dir, "config.json"))
    service = BatteryService(check_interval=15)
    notifier = DesktopNotificationStrategy()

    view = BatteryView(assets_dir=assets_dir)

    def on_exit():
        service.stop()
        tray.stop()
        view.after(0, view.destroy)

    tray = SystemTrayManager(
        assets_dir=assets_dir,
        on_show=view.show_from_tray,
        on_exit=on_exit
    )

    controller = BatteryController(
        config_model=config,
        battery_service=service,
        view=view,
        tray_manager=tray,
        notification_strategy=notifier,
        assets_dir=assets_dir
    )

    service.start()
    tray.run()

    view.mainloop()

if __name__ == "__main__":
    main()