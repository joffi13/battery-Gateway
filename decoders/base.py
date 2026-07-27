from abc import ABC, abstractmethod

from core.frame import RawFrame
from core.manager import BatteryManager


class Decoder(ABC):

    @abstractmethod
    def decode(
        self,
        frame: RawFrame,
        manager: BatteryManager,
    ) -> bool:
        pass
