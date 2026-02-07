from __future__ import annotations

import dataclasses
import shutil
import time
from collections.abc import Iterator
from typing import Optional

from dvbt_demodulator import DvbtDemodulator
from dvbt_ts import TsServiceScanner

@dataclasses.dataclass(frozen=True)
class Channel:
    name: str
    frequency_mhz: float
    service_id: Optional[int] = None
    provider: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class ScanConfig:
    start_mhz: float
    end_mhz: float
    bandwidth_mhz: float = 8.0
    step_mhz: float = 8.0
    dwell_seconds: float = 1.5


class DvbtScanner:
    """
    Escáner básico de DVB-T para HackRF.

    Este módulo prepara la estructura para un flujo real, pero requiere
    herramientas externas (por ejemplo, "hackrf_transfer" + demodulador DVB-T).
    """

    def __init__(self, demodulator: Optional[DvbtDemodulator] = None) -> None:
        self.demodulator = demodulator or DvbtDemodulator()
        self.ts_scanner = TsServiceScanner()

    def scan(self, config: ScanConfig, stop_event) -> Iterator[Channel]:
        self._validate_tools()
        if (
            self.demodulator.config.mode == "external"
            and config.start_mhz != config.end_mhz
        ):
            raise RuntimeError(
                "Modo 'external': usa la misma frecuencia inicial y final "
                "porque el demodulador externo no se retunea automáticamente."
            )

        freq = config.start_mhz
        index = 1
        while freq <= config.end_mhz:
            if stop_event.is_set():
                break

            channels = self._probe_frequency(freq, index, config, stop_event)
            if channels:
                for channel in channels:
                    yield channel
                    index += 1

            freq = round(freq + config.step_mhz, 3)

    def _validate_tools(self) -> None:
        if shutil.which("hackrf_info") is None:
            raise RuntimeError(
                "No se encontró 'hackrf_info'. Instala los drivers y herramientas de HackRF."
            )
        self.demodulator.validate()

    def _probe_frequency(
        self,
        freq_mhz: float,
        index: int,
        config: ScanConfig,
        stop_event,
    ) -> list[Channel]:
        """
        Lanza el demodulador, escucha servicios DVB-T y devuelve canales detectados.
        """
        if stop_event.is_set():
            return []

        self.demodulator.start(freq_mhz=freq_mhz, bandwidth_mhz=config.bandwidth_mhz)
        try:
            services = self.ts_scanner.scan(
                udp_host=self.demodulator.config.udp_host,
                udp_port=self.demodulator.config.udp_port,
                duration_seconds=config.dwell_seconds,
                stop_event=stop_event,
            )
        finally:
            self.demodulator.stop()

        channels: list[Channel] = []
        for service in services:
            name = service["name"] or f"Canal {index}"
            channels.append(
                Channel(
                    name=name,
                    frequency_mhz=freq_mhz,
                    service_id=service["service_id"],
                    provider=service["provider"],
                )
            )
        if not channels:
            time.sleep(0.2)
        return channels
