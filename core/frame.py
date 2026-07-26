#!/usr/bin/env python3
"""
Battery Gateway

Universelles Frame-Objekt
Herstellerunabhängig
"""

from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass(slots=True)
class Frame:
    bus: str
    identifier: int
    data: bytes

    timestamp: float = field(default_factory=time.time)

    direction: str = "RX"
    sequence: int = 0

    crc_ok: bool = True
    comment: Optional[str] = None

    @property
    def dlc(self) -> int:
        return len(self.data)

    def hex(self) -> str:
        return self.data.hex(" ").upper()

    def __str__(self) -> str:
        return (
            f"{self.timestamp:.3f}  "
            f"{self.bus:<6} "
            f"0x{self.identifier:03X}  "
            f"[{self.dlc}]  "
            f"{self.hex()}"
        )
