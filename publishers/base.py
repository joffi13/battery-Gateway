from abc import ABC, abstractmethod

from core.manager import BatteryManager


class Publisher(ABC):

    @abstractmethod
    def publish(self, manager: BatteryManager):
        pass
