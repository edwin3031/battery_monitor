import os
import sys
import time


class BatteryController:
    def __init__(
        self, 
        config_model, 
        battery_service, 
        view, 
        tray_manager, 
        notification_strategy, 
        assets_dir: str,
        reminder_interval: int = 60  # Re-notify every 60 seconds (1 minute)
    ):
        self.config = config_model
        self.service = battery_service
        self.view = view
        self.tray = tray_manager
        self.notifier = notification_strategy
        self.assets_dir = assets_dir
        self.reminder_interval = reminder_interval

        # Persistence check
        self._last_notified_state = None
        self._last_notification_time = 0.0

        self._init_view()
        self._setup_events()

    def _init_view(self):
        self.view.entry_low.insert(0, str(self.config.low_limit))
        self.view.entry_high.insert(0, str(self.config.high_limit))
        if self.config.autostart:
            self.view.chk_autostart.select()

    def _setup_events(self):
        self.view.btn_save.configure(command=self.save_configuration)
        self.service.add_observer(self.on_battery_update)

    def save_configuration(self):
        limits, error = self.view.validate_and_get_limits()
        if error:
            self.view.show_error(error)
            return

        self.view.clear_error()
        low, high = limits
        self.config.low_limit = low
        self.config.high_limit = high
        
        autostart_selected = bool(self.view.chk_autostart.get())
        if self.config.autostart != autostart_selected:
            self.config.autostart = autostart_selected
            self._toggle_autostart(autostart_selected)

        self.config.save()
        self.notifier.notify("Settings Saved", "Your battery limits have been updated.", self.assets_dir)

    def _toggle_autostart(self, enable: bool):
        """Handles cross-platform autostart (Windows, Linux, macOS)."""
        app_script = os.path.abspath(sys.argv[0])
        python_exec = sys.executable

        # 1. WINDOWS
        if sys.platform.startswith("win"):
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
                if enable:
                    cmd = f'"{python_exec}" "{app_script}"'
                    winreg.SetValueEx(key, "BatteryMonitorApp", 0, winreg.REG_SZ, cmd)
                else:
                    try:
                        winreg.DeleteValue(key, "BatteryMonitorApp")
                    except FileNotFoundError:
                        pass
                winreg.CloseKey(key)
            except Exception as e:
                print(f"[Error Autostart Windows]: {e}")

        # 2. LINUX
        elif sys.platform.startswith("linux"):
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_file = os.path.join(autostart_dir, "battery_monitor.desktop")

            if enable:
                os.makedirs(autostart_dir, exist_ok=True)
                content = f"""[Desktop Entry]
Type=Application
Name=Battery Monitor
Exec="{python_exec}" "{app_script}"
Terminal=false
X-GNOME-Autostart-enabled=true
"""
                try:
                    with open(desktop_file, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    print(f"[Error Autostart Linux]: {e}")
            else:
                if os.path.exists(desktop_file):
                    os.remove(desktop_file)

        # 3. macOS (DARWIN)
        elif sys.platform.startswith("darwin"):
            launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
            plist_file = os.path.join(launch_agents_dir, "com.batterymonitor.app.plist")

            if enable:
                os.makedirs(launch_agents_dir, exist_ok=True)
                content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PLIST PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.batterymonitor.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exec}</string>
        <string>{app_script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
                try:
                    with open(plist_file, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    print(f"[Error Autostart macOS]: {e}")
            else:
                if os.path.exists(plist_file):
                    os.remove(plist_file)

    def on_battery_update(self, percent: int, is_plugged: bool):
        self.view.update_battery_data(percent, is_plugged)
        current_time = time.time()

        # CASE 1: Battery charged above the maximum limit and still connected
        if is_plugged and percent >= self.config.high_limit:
            should_notify = (
                self._last_notified_state != "HIGH" or 
                (current_time - self._last_notification_time) >= self.reminder_interval
            )

            if should_notify:
                self.notifier.notify(
                    "Unplug the Charger!",
                    f"The battery is at {percent}%. Disconnect the cable to protect the battery.",
                    self.assets_dir
                )
                self._last_notified_state = "HIGH"
                self._last_notification_time = current_time

        # CASE 2: Battery drops below the minimum limit and remains disconnected
        elif not is_plugged and percent <= self.config.low_limit:
            should_notify = (
                self._last_notified_state != "LOW" or 
                (current_time - self._last_notification_time) >= self.reminder_interval
            )

            if should_notify:
                self.notifier.notify(
                    "Connect the Charger!",
                    f"The battery has dropped to {percent}%. Connect the device to the power.",
                    self.assets_dir
                )
                self._last_notified_state = "LOW"
                self._last_notification_time = current_time

        # CASE 3: Normal state (within range or condition resolved)
        else:
            self._last_notified_state = None
            self._last_notification_time = 0.0