from time import time

import can

from core.frame import RawFrame
from readers.base import Reader


class SocketCANReader(Reader):
    def __init__(self, interface: str = "can0", timeout_s: float = 1.0):
        self.interface = interface
        self.timeout_s = timeout_s
        self.sequence = 0
        self.bus = can.interface.Bus(channel=interface, interface="socketcan")

    def read(self) -> RawFrame | None:
        message = self.bus.recv(timeout=self.timeout_s)
        if message is None:
            return None
        self.sequence += 1
        timestamp = float(message.timestamp or time())
        return RawFrame(
            bus=self.interface,
            identifier=message.arbitration_id,
            data=bytes(message.data),
            timestamp=timestamp,
            direction="RX" if message.is_rx else "TX",
            sequence=self.sequence,
        )

    def close(self) -> None:
        self.bus.shutdown()
