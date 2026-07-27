from core.manager import BatteryManager
from core.event import Event, EventType
from core.eventbus import EventBus

manager = BatteryManager()
bus = EventBus()

battery = manager.get("seplos_01")

battery.set_voltage(53.42)
battery.set_current(-71.80)
battery.set_soc(88.0)

bus.publish(
    Event(
        battery_id=battery.id,
        event_type=EventType.VALUE_CHANGED,
        source="main",
        message="Battery updated",
    )
)

print(battery)

while bus.has_events():
    print(bus.get())
