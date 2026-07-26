from dataclasses import dataclass, field
from time import time


@dataclass
class Cell:
    voltage: float = 0.0
    balancing: bool = False
    timestamp: float = field(default_factory=time)


@dataclass
class Temperature:
    value: float = 0.0
    timestamp: float = field(default_factory=time)


class Battery:

    def __init__(self, battery_id: str):

        self.id = battery_id

        self.manufacturer = ""
        self.model = ""
        self.serial = ""
        self.firmware = ""

        self.voltage = 0.0
        self.current = 0.0
        self.power = 0.0
        self.soc = 0.0
        self.soh = 0.0

        self.cells = [Cell() for _ in range(16)]
        self.temperatures = [Temperature() for _ in range(4)]

        self.online = False
        self.changed = False
        self.last_update = time()

    def touch(self):
        self.last_update = time()
        self.online = True

    def _changed(self):
        self.changed = True
        self.touch()

    def clear_changed(self):
        self.changed = False

    def set_voltage(self, value: float):
        if value != self.voltage:
            self.voltage = value
            self.power = self.voltage * self.current
            self._changed()

    def set_current(self, value: float):
        if value != self.current:
            self.current = value
            self.power = self.voltage * self.current
            self._changed()

    def set_soc(self, value: float):
        if value != self.soc:
            self.soc = value
            self._changed()

    def set_soh(self, value: float):
        if value != self.soh:
            self.soh = value
            self._changed()

    def set_cell_voltage(self, index: int, value: float):
        self.cells[index].voltage = value
        self.cells[index].timestamp = time()
        self._changed()

    def set_temperature(self, index: int, value: float):
        self.temperatures[index].value = value
        self.temperatures[index].timestamp = time()
        self._changed()

    def __repr__(self):
        return (
            f"<Battery {self.id} "
            f"V={self.voltage:.2f} "
            f"I={self.current:.2f} "
            f"P={self.power:.1f} "
            f"SOC={self.soc:.1f}%>"
        )
