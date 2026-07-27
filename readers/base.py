from abc import ABC, abstractmethod

from core.frame import Frame


class Reader(ABC):

    @abstractmethod
    def read(self) -> Frame | None:
        pass
