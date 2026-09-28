import os
import sys

import customtkinter as ctk
from PIL import Image


class BatteryView(ctk.CTk):
    def __init__(self, assets_dir: str):
        super().__init__()
        self.assets_dir = assets_dir
        self.title("Battery Monitor")
        self.geometry("380x300")
        self.resizable(False, False)

        # Configure icon respecting platform
        self._set_platform_icon()

        # Closing protocol
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self._build_ui()

    def _set_platform_icon(self):
        """Handle the icon according to the operating system without forcing iconbitmap on Linux"""
        ico_path = os.path.join(self.assets_dir, "icon.ico")
        png_path = os.path.join(self.assets_dir, "icon.png")

        try:
            if sys.platform.startswith("win"):
                if os.path.exists(ico_path):
                    self.iconbitmap(ico_path)
            else:
                # Linux / macOS use PhotoImage
                if os.path.exists(png_path):
                    img = ctk.CTkImage(light_image=Image.open(png_path), size=(32, 32))
                    self.iconphoto(True, img._light_image)
        except Exception as e:
            print(f"[Error IconView]: {e}")

    def _build_ui(self):
        self.lbl_title = ctk.CTkLabel(self, text="Battery Monitor", font=("Helvetica", 18, "bold"))
        self.lbl_title.pack(pady=10)

        self.lbl_battery = ctk.CTkLabel(self, text="Battery: --%", font=("Helvetica", 16))
        self.lbl_battery.pack(pady=5)

        self.lbl_status = ctk.CTkLabel(self, text="Status: --", font=("Helvetica", 12))
        self.lbl_status.pack(pady=2)

        # Frame Limits
        frame_limits = ctk.CTkFrame(self)
        frame_limits.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(frame_limits, text="Minimum Limit (%):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_low = ctk.CTkEntry(frame_limits, width=60)
        self.entry_low.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(frame_limits, text="Maximum Limit (%):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_high = ctk.CTkEntry(frame_limits, width=60)
        self.entry_high.grid(row=1, column=1, padx=10, pady=5)

        # Autostart & Save
        self.chk_autostart = ctk.CTkCheckBox(self, text="Start with the system")
        self.chk_autostart.pack(pady=5)

        self.btn_save = ctk.CTkButton(self, text="Save Settings")
        self.btn_save.pack(pady=10)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color="red", font=("Helvetica", 11))
        self.lbl_error.pack(pady=2)

    # Robust validations
    def validate_and_get_limits(self):
        """Validates that the entries are integers, are between 1-100 and that low < high."""
        try:
            low = int(self.entry_low.get().strip())
            high = int(self.entry_high.get().strip())
        except ValueError:
            return None, "Limits must be valid integers."

        if not (1 <= low <= 99) or not (2 <= high <= 100):
            return None, "Values must be between 1" + "%" + " and 100" + "%" + "."

        if low >= high:
            return None, "The minimum limit must be less than the maximum limit."

        return (low, high), ""

    def show_error(self, message: str):
        self.lbl_error.configure(text=message)

    def clear_error(self):
        self.lbl_error.configure(text="")

    # Safe update in GUI Thread
    def update_battery_data(self, percent: int, is_plugged: bool):
        """Update the GUI from any thread safely using thread-safe callbacks."""
        state = "Charging ⚡" if is_plugged else "On Battery 🔋"
        
        def _update():
            self.lbl_battery.configure(text=f"Battery: {percent}%")
            self.lbl_status.configure(text=f"Status: {state}")

        self.after(0, _update)

    def hide_to_tray(self):
        self.withdraw()

    def show_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()