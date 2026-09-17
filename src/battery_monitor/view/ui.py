import os
import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class BatteryView(ctk.CTk):
    def __init__(self, controller, initial_low, initial_high, initial_autostart):
        super().__init__()
        self.controller = controller

        self.title("Monitor de Batería")
        self.geometry("420x510")
        self.resizable(False, False)

        self.set_window_icon()
        self.protocol("WM_DELETE_WINDOW", self.controller.hide_to_tray)

        # --- Componentes UI ---
        self.title_label = ctk.CTkLabel(self, text="⚡ Alerta de Batería", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        self.status_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray20"))
        self.status_frame.pack(fill="x", padx=20, pady=10)

        self.lbl_battery = ctk.CTkLabel(self.status_frame, text="Batería: --%", font=ctk.CTkFont(size=16))
        self.lbl_battery.pack(pady=8)

        self.lbl_plugged = ctk.CTkLabel(self.status_frame, text="Estado: Desconocido", font=ctk.CTkFont(size=14))
        self.lbl_plugged.pack(pady=(0, 8))

        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.pack(fill="x", padx=20, pady=10)

        # Límite Inferior
        self.low_label = ctk.CTkLabel(self.config_frame, text="Avisar si baja de (%):")
        self.low_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.entry_low = ctk.CTkEntry(self.config_frame, width=80)
        self.entry_low.insert(0, str(initial_low))
        self.entry_low.grid(row=0, column=1, padx=15, pady=10)

        # Límite Superior
        self.high_label = ctk.CTkLabel(self.config_frame, text="Avisar si sube de (%):")
        self.high_label.grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.entry_high = ctk.CTkEntry(self.config_frame, width=80)
        self.entry_high.insert(0, str(initial_high))
        self.entry_high.grid(row=1, column=1, padx=15, pady=10)

        # Interruptor de Autostart
        self.switch_autostart = ctk.CTkSwitch(
            self.config_frame, text="Iniciar con el Sistema", 
            command=self.on_autostart_toggle
        )
        self.switch_autostart.grid(row=2, column=0, columnspan=2, padx=15, pady=12, sticky="w")
        if initial_autostart:
            self.switch_autostart.select()
        else:
            self.switch_autostart.deselect()

        self.btn_toggle = ctk.CTkButton(
            self, text="Iniciar Monitoreo", fg_color="green", hover_color="darkgreen",
            command=self.controller.toggle_monitoring_from_ui
        )
        self.btn_toggle.pack(pady=15, ipadx=10, ipady=5)

    def on_autostart_toggle(self):
        """Comunica al controlador cuando el usuario cambia el switch de autostart."""
        is_checked = self.switch_autostart.get() == 1
        self.controller.toggle_autostart(is_checked)

    def set_window_icon(self):
        """Apunta a la carpeta assets/ para cargar el icono de la ventana."""
        # 1. Definir la carpeta assets y el archivo de icono
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        os.makedirs(assets_dir, exist_ok=True)  # Asegura que la carpeta exista
        
        icon_path = os.path.join(assets_dir, "battery.ico")
        png_path = os.path.join(assets_dir, "battery.png") # Soporte adicional para PNG

        # 2. Si no hay icono en assets, genera uno por defecto allí mismo
        if not os.path.exists(icon_path) and not os.path.exists(png_path):
            try:
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (64, 64), color=(33, 150, 243))
                dc = ImageDraw.Draw(img)
                dc.rectangle((16, 16, 48, 48), fill=(255, 255, 255))
                img.save(icon_path, format='ICO')
            except Exception as e:
                print(f"No se pudo crear icono por defecto en assets: {e}")

        # 3. Intentar cargar el icono (.ico o .png) desde la carpeta assets
        target_icon = icon_path if os.path.exists(icon_path) else png_path

        if os.path.exists(target_icon):
            try:
                # Método nativo de Tkinter/CustomTkinter para .ico en Windows
                self.iconbitmap(target_icon)
            except Exception:
                try:
                    # Método compatible con Linux / macOS usando PIL
                    from PIL import Image, ImageTk
                    img = Image.open(target_icon)
                    photo = ImageTk.PhotoImage(img)
                    self.iconphoto(False, photo)
                except Exception as e:
                    print(f"Error al aplicar icono a la ventana: {e}")

    def update(self, data):
        percent = data["percent"]
        plugged = data["plugged"]
        status_text = "🔌 Conectado (Cargando)" if plugged else "🔋 Desconectado (En uso)"
        
        self.after(0, lambda: self.lbl_battery.configure(text=f"Batería: {percent}%"))
        self.after(0, lambda: self.lbl_plugged.configure(text=f"Estado: {status_text}"))

    def set_button_state(self, is_monitoring):
        if is_monitoring:
            self.btn_toggle.configure(text="Detener Monitoreo", fg_color="firebrick", hover_color="darkred")
        else:
            self.btn_toggle.configure(text="Iniciar Monitoreo", fg_color="green", hover_color="darkgreen")

    def get_limits(self):
        try:
            low = int(self.entry_low.get())
        except ValueError:
            low = 20
        try:
            high = int(self.entry_high.get())
        except ValueError:
            high = 80
        return low, high