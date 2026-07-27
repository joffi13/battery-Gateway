from dataclasses import dataclass, field
from enum import Enum
from time import time


class EventType(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    VALUE_CHANGED = "value_changed"
    WARNING = "warning"
    ALARM = "alarm"


@dataclass(slots=True)
class Event:
    timestamp: float = field(default_factory=time)
    battery_id: str = ""
    event_type: EventType = EventType.VALUE_CHANGED
    source: str = ""
    message: str = ""
