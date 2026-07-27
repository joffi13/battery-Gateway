#!/usr/bin/env python3
"""Universal CAN reverse engineering analyzer.

The analyzer intentionally avoids protocol-specific assumptions. It reads
common candump text formats, aggregates compact statistics per CAN ID, and
prints terminal-friendly reports that help identify candidate signals for
later manual reverse engineering.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

BYTE_COUNT = 8
BYTE_PAIR_OFFSETS = tuple(range(BYTE_COUNT - 1))

_COMPACT_RE = re.compile(
    r"(?:\([^)]+\)\s+)?(?P<iface>\S+)\s+"
    r"(?P<can_id>[0-9A-Fa-f]{1,8})#(?P<data>[0-9A-Fa-f]+)"
)

_CLASSIC_RE = re.compile(
    r"(?:\([^)]+\)\s+)?(?P<iface>\S+)\s+"
    r"(?P<can_id>[0-9A-Fa-f]{1,8})\s+\[(?P<dlc>\d{1,2})\]\s+"
    r"(?P<data>(?:[0-9A-Fa-f]{2}\s*)+)"
)


@dataclass(frozen=True)
class CANFrame:
    """A parsed CAN data frame from a candump log."""

    can_id: str
    data: bytes
    interface: str | None = None
    timestamp: str | None = None


@dataclass(frozen=True)
class ParseResult:
    """Result of parsing one log line."""

    frame: CANFrame | None
    skipped: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class ByteStats:
    """Aggregated statistics for one byte position."""

    index: int
    count: int
    min_value: int
    max_value: int
    distinct_count: int
    constant: bool

    @property
    def delta(self) -> int:
        """Return max-min spread for this byte."""

        return self.max_value - self.min_value


@dataclass(frozen=True)
class WordStats:
    """Aggregated statistics for a 16-bit interpretation."""

    name: str
    min_value: int
    max_value: int
    distinct_count: int

    @property
    def delta(self) -> int:
        """Return max-min spread for this 16-bit interpretation."""

        return self.max_value - self.min_value


@dataclass(frozen=True)
class WordPairReport:
    """All 16-bit interpretations for one adjacent byte pair."""

    offset: int
    little_unsigned: WordStats
    little_signed: WordStats
    big_unsigned: WordStats
    big_signed: WordStats


@dataclass(frozen=True)
class HeuristicReport:
    """Statistical, protocol-neutral classification hints for one CAN ID."""

    strongest_byte: int | None
    practically_constant_bytes: tuple[int, ...]
    likely_measurement_bytes: tuple[int, ...]
    likely_status_bytes: tuple[int, ...]


@dataclass(frozen=True)
class CANIDReport:
    """Full analysis result for one CAN ID."""

    can_id: str
    frame_count: int
    byte_stats: tuple[ByteStats, ...]
    word_pairs: tuple[WordPairReport, ...]
    heuristics: HeuristicReport

    @property
    def constant_bytes(self) -> tuple[int, ...]:
        """Return positions that did not change."""

        return tuple(stat.index for stat in self.byte_stats if stat.constant)

    @property
    def variable_bytes(self) -> tuple[int, ...]:
        """Return positions that changed at least once."""

        return tuple(stat.index for stat in self.byte_stats if not stat.constant)


@dataclass(frozen=True)
class AnalysisReport:
    """Complete analyzer output."""

    can_ids: tuple[CANIDReport, ...]
    total_frames: int
    skipped_lines: int


class CandumpParser:
    """Parse supported candump line formats.

    Supported formats:
    - ``(timestamp) can0 351#4202E8039E07D001``
    - ``can0 351 [8] 42 02 E8 03 9E 07 D0 01``
    """

    def parse_line(self, line: str) -> ParseResult:
        """Parse one line and return a frame or a skip reason."""

        stripped = line.strip()
        if not stripped:
            return ParseResult(None, skipped=True, reason="empty")

        compact = _COMPACT_RE.search(stripped)
        if compact:
            return self._parse_compact(compact)

        classic = _CLASSIC_RE.search(stripped)
        if classic:
            return self._parse_classic(classic)

        return ParseResult(None, skipped=True, reason="unsupported format")

    def parse_lines(self, lines: Iterable[str]) -> Iterator[ParseResult]:
        """Yield parse results for an iterable of lines."""

        for line in lines:
            yield self.parse_line(line)

    def _parse_compact(self, match: re.Match[str]) -> ParseResult:
        hex_data = match.group("data")
        if len(hex_data) % 2:
            return ParseResult(None, skipped=True, reason="odd hex length")
        if len(hex_data) != BYTE_COUNT * 2:
            return ParseResult(None, skipped=True, reason="unsupported dlc")

        try:
            data = bytes.fromhex(hex_data)
        except ValueError:
            return ParseResult(None, skipped=True, reason="invalid hex")

        return ParseResult(
            CANFrame(
                can_id=self._normalize_can_id(match.group("can_id")),
                data=data,
                interface=match.group("iface"),
                timestamp=self._extract_timestamp(match.string),
            )
        )

    def _parse_classic(self, match: re.Match[str]) -> ParseResult:
        try:
            dlc = int(match.group("dlc"))
        except ValueError:
            return ParseResult(None, skipped=True, reason="invalid dlc")

        data_parts = match.group("data").split()
        if dlc != BYTE_COUNT or len(data_parts) != BYTE_COUNT:
            return ParseResult(None, skipped=True, reason="unsupported dlc")

        try:
            data = bytes(int(part, 16) for part in data_parts)
        except ValueError:
            return ParseResult(None, skipped=True, reason="invalid hex")

        return ParseResult(
            CANFrame(
                can_id=self._normalize_can_id(match.group("can_id")),
                data=data,
                interface=match.group("iface"),
                timestamp=self._extract_timestamp(match.string),
            )
        )

    @staticmethod
    def _normalize_can_id(can_id: str) -> str:
        return can_id.upper().lstrip("0") or "0"

    @staticmethod
    def _extract_timestamp(line: str) -> str | None:
        if not line.startswith("("):
            return None
        end = line.find(")")
        if end <= 1:
            return None
        return line[1:end]


@dataclass
class ByteAccumulator:
    """Streaming accumulator for one byte position."""

    index: int
    values: set[int] = field(default_factory=set)
    min_value: int | None = None
    max_value: int | None = None
    count: int = 0

    def add(self, value: int) -> None:
        """Add one observed byte value."""

        self.count += 1
        self.values.add(value)
        self.min_value = value if self.min_value is None else min(self.min_value, value)
        self.max_value = value if self.max_value is None else max(self.max_value, value)

    def to_stats(self) -> ByteStats:
        """Build immutable byte statistics."""

        min_value = self.min_value if self.min_value is not None else 0
        max_value = self.max_value if self.max_value is not None else 0
        return ByteStats(
            index=self.index,
            count=self.count,
            min_value=min_value,
            max_value=max_value,
            distinct_count=len(self.values),
            constant=len(self.values) <= 1,
        )


@dataclass
class WordAccumulator:
    """Streaming accumulator for one 16-bit interpretation."""

    name: str
    values: set[int] = field(default_factory=set)
    min_value: int | None = None
    max_value: int | None = None

    def add(self, value: int) -> None:
        """Add one observed 16-bit value."""

        self.values.add(value)
        self.min_value = value if self.min_value is None else min(self.min_value, value)
        self.max_value = value if self.max_value is None else max(self.max_value, value)

    def to_stats(self) -> WordStats:
        """Build immutable word statistics."""

        min_value = self.min_value if self.min_value is not None else 0
        max_value = self.max_value if self.max_value is not None else 0
        return WordStats(
            name=self.name,
            min_value=min_value,
            max_value=max_value,
            distinct_count=len(self.values),
        )


@dataclass
class WordPairAccumulator:
    """Streaming accumulator for all 16-bit views of one byte pair."""

    offset: int
    little_unsigned: WordAccumulator = field(
        default_factory=lambda: WordAccumulator("LE unsigned")
    )
    little_signed: WordAccumulator = field(
        default_factory=lambda: WordAccumulator("LE signed")
    )
    big_unsigned: WordAccumulator = field(
        default_factory=lambda: WordAccumulator("BE unsigned")
    )
    big_signed: WordAccumulator = field(
        default_factory=lambda: WordAccumulator("BE signed")
    )

    def add(self, data: bytes) -> None:
        """Add interpretations for this byte pair from one frame."""

        pair = data[self.offset : self.offset + 2]
        self.little_unsigned.add(int.from_bytes(pair, "little", signed=False))
        self.little_signed.add(int.from_bytes(pair, "little", signed=True))
        self.big_unsigned.add(int.from_bytes(pair, "big", signed=False))
        self.big_signed.add(int.from_bytes(pair, "big", signed=True))

    def to_report(self) -> WordPairReport:
        """Build immutable 16-bit pair report."""

        return WordPairReport(
            offset=self.offset,
            little_unsigned=self.little_unsigned.to_stats(),
            little_signed=self.little_signed.to_stats(),
            big_unsigned=self.big_unsigned.to_stats(),
            big_signed=self.big_signed.to_stats(),
        )


@dataclass
class CANIDAccumulator:
    """Streaming statistics for one CAN ID."""

    can_id: str
    frame_count: int = 0
    byte_accumulators: list[ByteAccumulator] = field(
        default_factory=lambda: [ByteAccumulator(i) for i in range(BYTE_COUNT)]
    )
    word_accumulators: list[WordPairAccumulator] = field(
        default_factory=lambda: [WordPairAccumulator(i) for i in BYTE_PAIR_OFFSETS]
    )

    def add(self, frame: CANFrame) -> None:
        """Add one frame to this CAN ID accumulator."""

        self.frame_count += 1
        for index, value in enumerate(frame.data):
            self.byte_accumulators[index].add(value)
        for word_accumulator in self.word_accumulators:
            word_accumulator.add(frame.data)

    def to_report(self) -> CANIDReport:
        """Build an immutable CAN ID report."""

        byte_stats = tuple(acc.to_stats() for acc in self.byte_accumulators)
        return CANIDReport(
            can_id=self.can_id,
            frame_count=self.frame_count,
            byte_stats=byte_stats,
            word_pairs=tuple(acc.to_report() for acc in self.word_accumulators),
            heuristics=HeuristicClassifier.classify(byte_stats, self.frame_count),
        )


class HeuristicClassifier:
    """Protocol-neutral statistical classification hints."""

    @staticmethod
    def classify(byte_stats: Sequence[ByteStats], frame_count: int) -> HeuristicReport:
        """Classify bytes using only variability statistics.

        The rules are intentionally conservative:
        - strongest byte: maximum delta, tie-broken by distinct value count
        - practically constant: one value or <=1% distinct ratio with tiny delta
        - measurement candidates: high spread and several distinct values
        - status candidates: low cardinality, changed at least once, small spread
        """

        if not byte_stats or frame_count <= 0:
            return HeuristicReport(None, (), (), ())

        strongest = max(
            byte_stats,
            key=lambda stat: (stat.delta, stat.distinct_count, stat.index),
        )
        strongest_byte = strongest.index if strongest.delta > 0 else None

        practically_constant: list[int] = []
        likely_measurement: list[int] = []
        likely_status: list[int] = []

        for stat in byte_stats:
            distinct_ratio = stat.distinct_count / max(frame_count, 1)
            if stat.constant or (distinct_ratio <= 0.01 and stat.delta <= 1):
                practically_constant.append(stat.index)
                continue

            if stat.distinct_count <= 8 and stat.delta <= 0x0F:
                likely_status.append(stat.index)
                continue

            if stat.distinct_count >= 3 and stat.delta >= 0x10:
                likely_measurement.append(stat.index)

        return HeuristicReport(
            strongest_byte=strongest_byte,
            practically_constant_bytes=tuple(practically_constant),
            likely_measurement_bytes=tuple(likely_measurement),
            likely_status_bytes=tuple(likely_status),
        )


class CANAnalyzer:
    """Streaming analyzer for candump files."""

    def __init__(self, parser: CandumpParser | None = None) -> None:
        self._parser = parser or CandumpParser()

    def analyze_lines(self, lines: Iterable[str]) -> AnalysisReport:
        """Analyze candump lines without storing individual frames."""

        accumulators: dict[str, CANIDAccumulator] = {}
        total_frames = 0
        skipped_lines = 0

        for result in self._parser.parse_lines(lines):
            if result.frame is None:
                if result.skipped:
                    skipped_lines += 1
                continue

            frame = result.frame
            accumulator = accumulators.setdefault(
                frame.can_id,
                CANIDAccumulator(frame.can_id),
            )
            accumulator.add(frame)
            total_frames += 1

        reports = tuple(
            accumulators[can_id].to_report()
            for can_id in sorted(accumulators, key=_can_id_sort_key)
        )
        return AnalysisReport(
            can_ids=reports,
            total_frames=total_frames,
            skipped_lines=skipped_lines,
        )

    def analyze_file(self, path: Path) -> AnalysisReport:
        """Analyze a candump file using streaming IO."""

        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return self.analyze_lines(handle)


class TerminalReportRenderer:
    """Render analysis reports for terminal users."""

    def render(self, report: AnalysisReport) -> str:
        """Return a human-readable terminal report."""

        lines: list[str] = []
        lines.append("CAN Reverse Engineering Report")
        lines.append("=" * 72)
        lines.append(f"Total frames        : {report.total_frames}")
        lines.append(f"CAN IDs             : {len(report.can_ids)}")
        lines.append(f"Skipped log lines   : {report.skipped_lines}")

        if not report.can_ids:
            lines.append("")
            lines.append("No valid CAN frames found.")
            return "\n".join(lines)

        for can_report in report.can_ids:
            lines.extend(self._render_can_id(can_report))

        return "\n".join(lines)

    def _render_can_id(self, report: CANIDReport) -> list[str]:
        lines: list[str] = []
        lines.append("")
        lines.append("=" * 72)
        lines.append(f"CAN ID {report.can_id}")
        lines.append("=" * 72)
        lines.append(f"Frames              : {report.frame_count}")
        lines.append(
            "Constant bytes      : "
            + _format_index_list(report.constant_bytes)
        )
        lines.append(
            "Variable bytes      : "
            + _format_index_list(report.variable_bytes)
        )
        lines.append("")
        lines.append("Byte statistics")
        lines.append("  Byte  Const  Distinct  Min   Max   Delta")
        for stat in report.byte_stats:
            lines.append(
                f"  {stat.index:>4}  {_yes_no(stat.constant):>5}"
                f"  {stat.distinct_count:>8}  {stat.min_value:02X}"
                f"    {stat.max_value:02X}    {stat.delta:>5}"
            )

        lines.append("")
        lines.append("16-bit adjacent byte-pair analysis")
        lines.append("  Pair  Interpretation  Min       Max       Delta     Distinct")
        for pair in report.word_pairs:
            for word in (
                pair.little_unsigned,
                pair.little_signed,
                pair.big_unsigned,
                pair.big_signed,
            ):
                lines.append(
                    f"  {pair.offset}-{pair.offset + 1:<1}   "
                    f"{word.name:<14} {word.min_value:>8}"
                    f"  {word.max_value:>8}  {word.delta:>8}"
                    f"  {word.distinct_count:>8}"
                )

        lines.append("")
        lines.append("Statistical hints")
        lines.append(
            "  Strongest changing byte      : "
            + _format_optional_index(report.heuristics.strongest_byte)
        )
        lines.append(
            "  Practically constant bytes   : "
            + _format_index_list(report.heuristics.practically_constant_bytes)
        )
        lines.append(
            "  Likely measurement bytes     : "
            + _format_index_list(report.heuristics.likely_measurement_bytes)
        )
        lines.append(
            "  Likely status bytes          : "
            + _format_index_list(report.heuristics.likely_status_bytes)
        )
        return lines


class AnalyzerApplication:
    """Command-line application wrapper."""

    def __init__(
        self,
        analyzer: CANAnalyzer | None = None,
        renderer: TerminalReportRenderer | None = None,
    ) -> None:
        self._analyzer = analyzer or CANAnalyzer()
        self._renderer = renderer or TerminalReportRenderer()

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Run the command-line application."""

        args = self._parse_args(argv)
        report = self._analyzer.analyze_file(args.logfile)
        print(self._renderer.render(report))
        return 0

    @staticmethod
    def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Analyze candump logs without protocol-specific rules.",
        )
        parser.add_argument(
            "logfile",
            type=Path,
            help="candump log file to analyze",
        )
        return parser.parse_args(argv)


def _can_id_sort_key(can_id: str) -> tuple[int, str]:
    try:
        return int(can_id, 16), can_id
    except ValueError:
        return 0, can_id


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _format_index_list(indexes: Sequence[int]) -> str:
    if not indexes:
        return "-"
    return ", ".join(str(index) for index in indexes)


def _format_optional_index(index: int | None) -> str:
    if index is None:
        return "-"
    return str(index)


def analyze_file(path: str | Path) -> AnalysisReport:
    """Compatibility helper for callers that want one-shot file analysis."""

    return CANAnalyzer().analyze_file(Path(path))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    return AnalyzerApplication().run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
