from abc import ABC, abstractmethod

from core.frame import Frame
from core.manager import BatteryManager


class Decoder(ABC):

    @abstractmethod
    def decode(
        self,
        frame: Frame,
        manager: BatteryManager,
    ) -> bool:
        pass
