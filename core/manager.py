from core.battery import Battery


class BatteryManager:

    def __init__(self):
        self._batteries = {}

    def create(self, battery_id: str) -> Battery:
        if battery_id not in self._batteries:
            self._batteries[battery_id] = Battery(battery_id)
        return self._batteries[battery_id]

    def get(self, battery_id: str) -> Battery:
        return self.create(battery_id)

    def remove(self, battery_id: str):
        self._batteries.pop(battery_id, None)

    def exists(self, battery_id: str) -> bool:
        return battery_id in self._batteries

    def all(self):
        return list(self._batteries.values())

    def count(self) -> int:
        return len(self._batteries)

    def clear(self):
        self._batteries.clear()

    def __repr__(self):
        return f"<BatteryManager batteries={len(self._batteries)}>"
