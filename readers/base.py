from abc import ABC, abstractmethod

from core.frame import RawFrame


class Reader(ABC):

    @abstractmethod
    def read(self) -> RawFrame | None:
        pass
