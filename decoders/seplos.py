from core.frame import RawFrame
from core.snapshot import NormalizedMeasurement, Quality, RawReference


class SeplosCANDecoder:
    source_id: str = "seplos_can"

    def decode(self, frame: RawFrame) -> tuple[NormalizedMeasurement, ...]:
        if frame.dlc != 8:
            return ()

        if frame.identifier == 0x351:
            return (
                self._u16(frame, "limit.charge_voltage", "V", 0, 10),
                self._u16(frame, "limit.charge_current", "A", 2, 10),
                self._u16(frame, "limit.discharge_current", "A", 4, 10),
                self._u16(frame, "limit.discharge_voltage", "V", 6, 10),
            )

        if frame.identifier == 0x355:
            return (
                self._u16(frame, "battery.soc", "%", 0, 1),
                self._u16(frame, "battery.soh", "%", 2, 1),
            )

        if frame.identifier == 0x356:
            temperature = self._i16(frame, "temperature.pack", "degC", 4, 10)
            if temperature.value == -50.0:
                temperature = self._replace_quality(
                    temperature,
                    Quality(
                        state="sentinel",
                        confidence=0.5,
                        flags=("sentinel_candidate",),
                        reason="Device reported fixed -50.0 degC value.",
                    ),
                )
            return (
                self._u16(frame, "battery.voltage", "V", 0, 100),
                self._i16(frame, "battery.current", "A", 2, 10),
                temperature,
            )

        if frame.identifier == 0x35A:
            return (
                NormalizedMeasurement(
                    name="alarm.raw_bitfield",
                    value=int.from_bytes(frame.data, "little"),
                    unit=None,
                    timestamp=frame.timestamp,
                    source_id=self.source_id,
                    quality=Quality(),
                    raw_reference=self._raw_ref(frame, 0, 8),
                ),
            )

        if frame.identifier == 0x379:
            return (
                self._u16(frame, "battery.design_capacity", "Ah", 0, 1),
            )

        return ()

    def _u16(
        self,
        frame: RawFrame,
        name: str,
        unit: str | None,
        offset: int,
        divider: int,
    ) -> NormalizedMeasurement:
        raw = int.from_bytes(frame.data[offset : offset + 2], "little", signed=False)
        return self._measurement(frame, name, raw / divider, unit, offset, 2)

    def _i16(
        self,
        frame: RawFrame,
        name: str,
        unit: str | None,
        offset: int,
        divider: int,
    ) -> NormalizedMeasurement:
        raw = int.from_bytes(frame.data[offset : offset + 2], "little", signed=True)
        return self._measurement(frame, name, raw / divider, unit, offset, 2)

    def _measurement(
        self,
        frame: RawFrame,
        name: str,
        value: int | float | bool | str,
        unit: str | None,
        offset: int,
        length: int,
    ) -> NormalizedMeasurement:
        return NormalizedMeasurement(
            name=name,
            value=value,
            unit=unit,
            timestamp=frame.timestamp,
            source_id=self.source_id,
            quality=Quality(),
            raw_reference=self._raw_ref(frame, offset, length),
        )

    def _raw_ref(self, frame: RawFrame, offset: int, length: int) -> RawReference:
        return RawReference(
            raw_id=f"{frame.bus}:{frame.identifier:X}:{frame.sequence}",
            source_id=self.source_id,
            timestamp=frame.timestamp,
            frame_id=f"0x{frame.identifier:X}",
            byte_offset=offset,
            byte_length=length,
        )

    @staticmethod
    def _replace_quality(
        measurement: NormalizedMeasurement,
        quality: Quality,
    ) -> NormalizedMeasurement:
        return NormalizedMeasurement(
            name=measurement.name,
            value=measurement.value,
            unit=measurement.unit,
            timestamp=measurement.timestamp,
            source_id=measurement.source_id,
            quality=quality,
            raw_reference=measurement.raw_reference,
        )
