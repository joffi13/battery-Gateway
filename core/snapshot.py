import json
from dataclasses import dataclass, field
from typing import Any, Literal


QualityState = Literal[
    "valid",
    "suspect",
    "invalid",
    "missing",
    "estimated",
    "sentinel",
    "stale",
    "unknown",
]


@dataclass(frozen=True, slots=True)
class Quality:
    state: QualityState = "valid"
    confidence: float = 1.0
    flags: tuple[str, ...] = ()
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "confidence": self.confidence,
            "flags": list(self.flags),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class RawReference:
    raw_id: str
    source_id: str
    timestamp: float
    frame_id: str | None = None
    byte_offset: int | None = None
    byte_length: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_id": self.raw_id,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "frame_id": self.frame_id,
            "byte_offset": self.byte_offset,
            "byte_length": self.byte_length,
        }


@dataclass(frozen=True, slots=True)
class NormalizedMeasurement:
    name: str
    value: int | float | bool | str
    unit: str | None
    timestamp: float
    source_id: str
    quality: Quality = field(default_factory=Quality)
    raw_reference: RawReference | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "source_id": self.source_id,
            "quality": self.quality.to_dict(),
            "raw_reference": (
                self.raw_reference.to_dict() if self.raw_reference else None
            ),
        }


@dataclass(frozen=True, slots=True)
class Cell:
    index: int
    voltage: NormalizedMeasurement | None = None
    quality: Quality = field(default_factory=Quality)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "voltage": self.voltage.to_dict() if self.voltage else None,
            "quality": self.quality.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class Temperature:
    temperature_id: str
    kind: str
    value: NormalizedMeasurement | None = None
    quality: Quality = field(default_factory=Quality)

    def to_dict(self) -> dict[str, Any]:
        return {
            "temperature_id": self.temperature_id,
            "kind": self.kind,
            "value": self.value.to_dict() if self.value else None,
            "quality": self.quality.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class BatterySnapshot:
    snapshot_id: str
    battery_id: str
    timestamp: float
    measurements: tuple[NormalizedMeasurement, ...] = ()
    cells: tuple[Cell, ...] = ()
    temperatures: tuple[Temperature, ...] = ()
    quality: Quality = field(default_factory=Quality)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "battery_id": self.battery_id,
            "timestamp": self.timestamp,
            "quality": self.quality.to_dict(),
            "measurements": [item.to_dict() for item in self.measurements],
            "cells": [item.to_dict() for item in self.cells],
            "temperatures": [item.to_dict() for item in self.temperatures],
        }

    def json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
