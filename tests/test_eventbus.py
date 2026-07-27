import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.event import Event
from core.eventbus import EventBus

bus = EventBus()

bus.publish(Event(battery_id="seplos_01", message="SOC changed"))
bus.publish(Event(battery_id="seplos_02", message="Voltage changed"))

assert bus.count() == 2

while bus.has_events():
    print(bus.get())

print("TEST OK")
