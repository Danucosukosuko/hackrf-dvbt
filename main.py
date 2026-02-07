import threading
import tkinter as tk
from tkinter import messagebox, ttk

from dvbt_scanner import Channel, DvbtScanner, ScanConfig
from dvbt_viewer import DvbtViewer


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("HackRF DVB-T Scanner (8 MHz)")
        self.geometry("780x480")
        self.resizable(True, True)

        self.scanner = DvbtScanner()
        self.viewer = DvbtViewer(self)
        self.channels: list[Channel] = []
        self.scan_thread: threading.Thread | None = None
        self.stop_scan = threading.Event()

        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 10, "pady": 8}
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)

        controls = ttk.LabelFrame(main, text="Búsqueda")
        controls.pack(fill=tk.X, **padding)

        ttk.Label(controls, text="Frecuencia inicial (MHz)").grid(row=0, column=0, sticky=tk.W)
        self.start_freq_var = tk.StringVar(value="474")
        ttk.Entry(controls, textvariable=self.start_freq_var, width=12).grid(row=0, column=1)

        ttk.Label(controls, text="Frecuencia final (MHz)").grid(row=0, column=2, sticky=tk.W, padx=(16, 0))
        self.end_freq_var = tk.StringVar(value="858")
        ttk.Entry(controls, textvariable=self.end_freq_var, width=12).grid(row=0, column=3)

        ttk.Label(controls, text="Ancho de banda (MHz)").grid(row=0, column=4, sticky=tk.W, padx=(16, 0))
        self.bandwidth_var = tk.StringVar(value="8")
        ttk.Entry(controls, textvariable=self.bandwidth_var, width=6, state="disabled").grid(row=0, column=5)

        self.scan_button = ttk.Button(controls, text="Buscar", command=self.start_scan)
        self.scan_button.grid(row=0, column=6, padx=(16, 0))

        self.stop_button = ttk.Button(controls, text="Detener", command=self.request_stop, state="disabled")
        self.stop_button.grid(row=0, column=7, padx=(8, 0))

        results = ttk.LabelFrame(main, text="Canales detectados")
        results.pack(fill=tk.BOTH, expand=True, **padding)

        self.channel_list = tk.Listbox(results, height=14)
        self.channel_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(results, orient=tk.VERTICAL, command=self.channel_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.channel_list.config(yscrollcommand=scrollbar.set)

        action_frame = ttk.Frame(main)
        action_frame.pack(fill=tk.X, **padding)

        self.view_button = ttk.Button(action_frame, text="Ver canal", command=self.view_channel)
        self.view_button.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Listo")
        ttk.Label(action_frame, textvariable=self.status_var).pack(side=tk.RIGHT)

    def start_scan(self) -> None:
        if self.scan_thread and self.scan_thread.is_alive():
            messagebox.showwarning("Escaneo activo", "Ya hay un escaneo en curso.")
            return

        try:
            start_mhz = float(self.start_freq_var.get())
            end_mhz = float(self.end_freq_var.get())
        except ValueError:
            messagebox.showerror("Error", "Frecuencias inválidas.")
            return

        if start_mhz >= end_mhz:
            messagebox.showerror("Error", "La frecuencia inicial debe ser menor que la final.")
            return

        self.channels.clear()
        self.channel_list.delete(0, tk.END)
        self.stop_scan.clear()
        self.status_var.set("Buscando canales...")
        self.scan_button.config(state="disabled")
        self.stop_button.config(state="normal")

        config = ScanConfig(
            start_mhz=start_mhz,
            end_mhz=end_mhz,
            bandwidth_mhz=8.0,
        )

        self.scan_thread = threading.Thread(target=self._scan_worker, args=(config,), daemon=True)
        self.scan_thread.start()

    def _scan_worker(self, config: ScanConfig) -> None:
        try:
            for channel in self.scanner.scan(config, self.stop_scan):
                self.channels.append(channel)
                label = f"{channel.name} ({channel.frequency_mhz:.3f} MHz)"
                if channel.provider:
                    label = f"{label} · {channel.provider}"
                self.channel_list.insert(tk.END, label)
        except RuntimeError as exc:
            self.after(0, lambda: messagebox.showerror("Error", str(exc)))
        finally:
            self.after(0, self._scan_complete)

    def _scan_complete(self) -> None:
        self.scan_button.config(state="normal")
        self.stop_button.config(state="disabled")
        if self.stop_scan.is_set():
            self.status_var.set("Escaneo detenido")
        else:
            self.status_var.set("Escaneo completado")

    def request_stop(self) -> None:
        self.stop_scan.set()
        self.status_var.set("Deteniendo...")

    def view_channel(self) -> None:
        selection = self.channel_list.curselection()
        if not selection:
            messagebox.showinfo("Selecciona un canal", "Selecciona un canal de la lista.")
            return
        channel = self.channels[selection[0]]
        try:
            self.viewer.play(channel)
        except RuntimeError as exc:
            messagebox.showerror("Error", str(exc))


if __name__ == "__main__":
    App().mainloop()
