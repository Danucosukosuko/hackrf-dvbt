from __future__ import annotations

import dataclasses
import json
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Optional


@dataclasses.dataclass
class DemodConfig:
    mode: str
    command: str
    udp_host: str = "127.0.0.1"
    udp_port: int = 1234
    sample_rate_hz: int = 8_000_000

    @classmethod
    def load(cls, path: Path) -> "DemodConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            mode=data.get("mode", "command"),
            command=data["command"],
            udp_host=data.get("udp_host", "127.0.0.1"),
            udp_port=data.get("udp_port", 1234),
            sample_rate_hz=data.get("sample_rate_hz", 8_000_000),
        )


class DvbtDemodulator:
    """
    Lanza un demodulador externo (GNU Radio, leandvb, etc.) configurable por comando.
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or Path("demod_config.json")
        self.config = self._load_config()
        self._process: Optional[subprocess.Popen] = None

    def _load_config(self) -> DemodConfig:
        if self.config_path.exists():
            return DemodConfig.load(self.config_path)
        return DemodConfig(mode="command", command="")

    def validate(self) -> None:
        if self.config.mode == "external":
            return
        if not self.config.command:
            raise RuntimeError(
                "Configura 'demod_config.json' con el comando del demodulador DVB-T."
            )
        executable = shlex.split(self.config.command)[0]
        if shutil.which(executable) is None:
            raise RuntimeError(
                f"No se encontró '{executable}'. Ajusta el comando del demodulador."
            )

    def start(self, freq_mhz: float, bandwidth_mhz: float) -> None:
        if self.config.mode == "external":
            return
        self.stop()
        command = self.config.command.format(
            freq_hz=int(freq_mhz * 1_000_000),
            bandwidth_hz=int(bandwidth_mhz * 1_000_000),
            sample_rate_hz=self.config.sample_rate_hz,
            udp_host=self.config.udp_host,
            udp_port=self.config.udp_port,
        )
        self._process = subprocess.Popen(command, shell=True)

    def stop(self) -> None:
        if self.config.mode == "external":
            return
        if self._process is None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._process.kill()
        self._process = None
