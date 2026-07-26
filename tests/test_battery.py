import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.manager import BatteryManager

manager = BatteryManager()

battery = manager.get("seplos_01")

battery.set_voltage(53.40)
battery.set_current(-72.50)
battery.set_soc(87.2)

print(battery)
print(f"Anzahl Batterien: {manager.count()}")

assert manager.count() == 1
assert battery.voltage == 53.40
assert battery.current == -72.50
assert battery.soc == 87.2
assert round(battery.power, 1) == -3871.5

print("TEST OK")
