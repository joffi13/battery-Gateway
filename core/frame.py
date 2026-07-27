from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass(frozen=True, slots=True)
class RawFrame:
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

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp,
            "bus": self.bus,
            "identifier": f"0x{self.identifier:X}",
            "data": self.data.hex().upper(),
            "dlc": self.dlc,
            "direction": self.direction,
            "sequence": self.sequence,
            "crc_ok": self.crc_ok,
            "comment": self.comment,
        }


Frame = RawFrame
