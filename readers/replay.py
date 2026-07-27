from pathlib import Path
import re

from core.frame import RawFrame
from readers.base import Reader


class ReplayReader(Reader):
    _COMPACT_RE = re.compile(
        r"^\((?P<timestamp>[0-9]+(?:\.[0-9]+)?)\)\s+"
        r"(?P<bus>\S+)\s+"
        r"(?P<identifier>[0-9A-Fa-f]+)#(?P<data>[0-9A-Fa-f]*)$"
    )
    _CLASSIC_RE = re.compile(
        r"^(?P<timestamp>\([0-9]+(?:\.[0-9]+)?\)|[0-9]+(?:\.[0-9]+)?)?\s*"
        r"(?P<bus>\S+)\s+"
        r"(?P<identifier>[0-9A-Fa-f]+)\s+"
        r"\[(?P<dlc>[0-9]+)\]\s+"
        r"(?P<data>(?:[0-9A-Fa-f]{2}\s*)*)$"
    )

    def __init__(self, filename: str):
        self.file = open(Path(filename), "r", encoding="utf-8")
        self.sequence = 0

    def read(self) -> RawFrame | None:
        while True:
            line = self.file.readline()

            if not line:
                return None

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            frame = self._parse_line(line)
            if frame is not None:
                return frame

    def close(self) -> None:
        self.file.close()

    def __iter__(self):
        return self

    def __next__(self) -> RawFrame:
        frame = self.read()
        if frame is None:
            raise StopIteration
        return frame

    def _next_sequence(self) -> int:
        self.sequence += 1
        return self.sequence

    def _parse_line(self, line: str) -> RawFrame | None:
        if match := self._COMPACT_RE.match(line):
            return RawFrame(
                bus=match.group("bus"),
                identifier=int(match.group("identifier"), 16),
                data=bytes.fromhex(match.group("data")),
                timestamp=float(match.group("timestamp")),
                sequence=self._next_sequence(),
            )

        if match := self._CLASSIC_RE.match(line):
            timestamp = (match.group("timestamp") or "0").strip("()")
            data = bytes.fromhex(match.group("data"))
            if int(match.group("dlc")) != len(data):
                return None
            return RawFrame(
                bus=match.group("bus"),
                identifier=int(match.group("identifier"), 16),
                data=data,
                timestamp=float(timestamp),
                sequence=self._next_sequence(),
            )

        parts = line.split()
        if len(parts) < 4:
            return None

        try:
            return RawFrame(
                bus=parts[1],
                identifier=int(parts[2], 16),
                data=bytes.fromhex("".join(parts[3:])),
                timestamp=float(parts[0]),
                sequence=self._next_sequence(),
            )
        except ValueError:
            return None
