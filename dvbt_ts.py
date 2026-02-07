from __future__ import annotations

import socket
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class _SectionAssembler:
    buffer: bytearray = field(default_factory=bytearray)
    expected_length: Optional[int] = None

    def reset(self) -> None:
        self.buffer.clear()
        self.expected_length = None

    def feed(self, payload: bytes, payload_unit_start: bool) -> list[bytes]:
        sections: list[bytes] = []
        if payload_unit_start:
            if not payload:
                return sections
            pointer = payload[0]
            payload = payload[1 + pointer :]
            self.reset()

        if not payload:
            return sections

        self.buffer.extend(payload)
        while True:
            if self.expected_length is None:
                if len(self.buffer) < 3:
                    break
                section_length = ((self.buffer[1] & 0x0F) << 8) | self.buffer[2]
                self.expected_length = 3 + section_length
            if self.expected_length is not None and len(self.buffer) >= self.expected_length:
                section = bytes(self.buffer[: self.expected_length])
                sections.append(section)
                del self.buffer[: self.expected_length]
                self.expected_length = None
                continue
            break
        return sections


class TsServiceScanner:
    def __init__(self) -> None:
        self._assemblers = {
            0x00: _SectionAssembler(),
            0x11: _SectionAssembler(),
        }

    def scan(
        self,
        udp_host: str,
        udp_port: int,
        duration_seconds: float,
        stop_event,
    ) -> list[dict[str, Optional[str]]]:
        deadline = time.time() + duration_seconds
        services: dict[int, dict[str, Optional[str]]] = {}

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        sock.bind((udp_host, udp_port))
        try:
            while time.time() < deadline:
                if stop_event.is_set():
                    break
                try:
                    data, _ = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                self._consume_ts(data, services)
                if services:
                    break
        finally:
            sock.close()

        return list(services.values())

    def _consume_ts(self, data: bytes, services: dict[int, dict[str, Optional[str]]]) -> None:
        for offset in range(0, len(data), 188):
            packet = data[offset : offset + 188]
            if len(packet) < 188 or packet[0] != 0x47:
                continue
            pid = ((packet[1] & 0x1F) << 8) | packet[2]
            payload_unit_start = bool(packet[1] & 0x40)
            adaptation_field_control = (packet[3] >> 4) & 0x03
            if adaptation_field_control in (0, 2):
                continue
            payload_index = 4
            if adaptation_field_control == 3:
                adaptation_length = packet[4]
                payload_index += 1 + adaptation_length
            if payload_index >= 188:
                continue
            payload = packet[payload_index:]
            assembler = self._assemblers.get(pid)
            if assembler is None:
                continue
            for section in assembler.feed(payload, payload_unit_start):
                if pid == 0x11:
                    self._parse_sdt(section, services)

    def _parse_sdt(
        self, section: bytes, services: dict[int, dict[str, Optional[str]]]
    ) -> None:
        if len(section) < 11 or section[0] not in (0x42, 0x46):
            return
        section_length = ((section[1] & 0x0F) << 8) | section[2]
        if section_length + 3 > len(section):
            return
        data = section[11 : 3 + section_length - 4]
        idx = 0
        while idx + 5 <= len(data):
            service_id = (data[idx] << 8) | data[idx + 1]
            descriptors_length = ((data[idx + 3] & 0x0F) << 8) | data[idx + 4]
            descriptor_data = data[idx + 5 : idx + 5 + descriptors_length]
            name, provider = self._parse_service_descriptor(descriptor_data)
            services[service_id] = {
                "service_id": service_id,
                "name": name,
                "provider": provider,
            }
            idx += 5 + descriptors_length

    def _parse_service_descriptor(self, data: bytes) -> tuple[Optional[str], Optional[str]]:
        idx = 0
        while idx + 2 <= len(data):
            tag = data[idx]
            length = data[idx + 1]
            descriptor = data[idx + 2 : idx + 2 + length]
            if tag == 0x48 and len(descriptor) >= 3:
                provider_length = descriptor[1]
                provider_start = 2
                provider_end = provider_start + provider_length
                if provider_end >= len(descriptor):
                    return None, None
                provider = descriptor[provider_start:provider_end].decode(
                    "latin-1", errors="ignore"
                )
                name_length = descriptor[provider_end]
                name_start = provider_end + 1
                name_end = name_start + name_length
                name = descriptor[name_start:name_end].decode("latin-1", errors="ignore")
                return name.strip() or None, provider.strip() or None
            idx += 2 + length
        return None, None
