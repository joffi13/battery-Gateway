from pathlib import Path

from core.frame import Frame
from readers.base import Reader


class ReplayReader(Reader):

    def __init__(self, filename: str):
        self.file = open(Path(filename), "r")

    def read(self) -> Frame | None:

        while True:

            line = self.file.readline()

            if not line:
                return None

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            parts = line.split()

            return Frame(
                bus=parts[1],
                identifier=int(parts[2], 16),
                data=bytes.fromhex("".join(parts[3:])),
                timestamp=float(parts[0]),
            )
