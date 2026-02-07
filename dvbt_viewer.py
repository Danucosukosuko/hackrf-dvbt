import tkinter as tk
from dataclasses import dataclass
from typing import Optional

import vlc

from dvbt_scanner import Channel


@dataclass
class PlayerConfig:
    udp_host: str = "127.0.0.1"
    udp_port: int = 1234


class DvbtViewer:
    """
    Reproductor de canales DVB-T usando VLC embebido en Tkinter.
    """

    def __init__(self, master: tk.Tk, config: Optional[PlayerConfig] = None) -> None:
        self.master = master
        self.config = config or PlayerConfig()
        self._vlc_instance = vlc.Instance("--no-video-title-show")
        self._player = self._vlc_instance.media_player_new()
        self._window: Optional[tk.Toplevel] = None
        self._canvas: Optional[tk.Canvas] = None

    def play(self, channel: Channel) -> None:
        if self._window is None or not self._window.winfo_exists():
            self._create_window()

        stream_url = f"udp://@{self.config.udp_host}:{self.config.udp_port}"
        media = self._vlc_instance.media_new(stream_url)
        self._player.set_media(media)
        self._attach_player()
        self._player.play()
        if self._window is not None:
            self._window.title(f"Canal: {channel.name}")

    def stop(self) -> None:
        self._player.stop()

    def _create_window(self) -> None:
        self._window = tk.Toplevel(self.master)
        self._window.title("Reproductor DVB-T")
        self._window.geometry("900x520")
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._canvas = tk.Canvas(self._window, bg="black")
        self._canvas.pack(fill=tk.BOTH, expand=True)

    def _attach_player(self) -> None:
        if self._canvas is None:
            return

        handle = self._canvas.winfo_id()
        if tk.TkVersion >= 8.6:
            self._player.set_hwnd(handle)
        else:
            self._player.set_xwindow(handle)

    def _on_close(self) -> None:
        self.stop()
        if self._window is not None:
            self._window.destroy()
        self._window = None
