import asyncio
import logging
from dataclasses import asdict, dataclass
from queue import Empty, Queue
from threading import Event, Lock, Thread
from time import monotonic, time
from typing import Any


LOG = logging.getLogger("battery_gateway.ble")


@dataclass(frozen=True, slots=True)
class BLEDeviceConfig:
    device_id: str
    battery_id: str
    address: str
    enabled: bool = True
    poll_interval_s: float = 30.0
    reconnect_delay_s: float = 5.0
    scan_timeout_s: float = 12.0


@dataclass(slots=True)
class BLEDeviceStatus:
    device_id: str
    address: str
    connected: bool = False
    successful_updates: int = 0
    disconnect_count: int = 0
    reconnect_count: int = 0
    connection_count: int = 0
    connection_started: float | None = None
    total_connected_s: float = 0.0
    last_update: float | None = None
    last_error: str | None = None
    last_reconnect_s: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        connected_s = self.total_connected_s
        if self.connected and self.connection_started is not None:
            connected_s += monotonic() - self.connection_started
        result["total_connected_s"] = round(connected_s, 3)
        result["average_connection_s"] = round(
            connected_s / max(self.connection_count, 1), 3
        )
        return result


@dataclass(frozen=True, slots=True)
class BLESample:
    device_id: str
    battery_id: str
    timestamp: float
    values: dict[str, Any]


class BLEReader:
    """Manage independent Seplos BLE connections outside the CAN loop."""

    def __init__(self, devices: tuple[BLEDeviceConfig, ...]):
        self.devices = tuple(device for device in devices if device.enabled)
        self._samples: Queue[BLESample] = Queue()
        self._latest: dict[str, BLESample] = {}
        self._status = {
            device.device_id: BLEDeviceStatus(device.device_id, device.address)
            for device in self.devices
        }
        self._status_lock = Lock()
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if not self.devices or self._thread is not None:
            return
        self._thread = Thread(target=self._thread_main, name="ble-reader", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=15.0)
            self._thread = None

    def connected_samples(self) -> tuple[BLESample, ...]:
        while True:
            try:
                sample = self._samples.get_nowait()
            except Empty:
                break
            self._latest[sample.device_id] = sample
        with self._status_lock:
            connected = {
                device_id
                for device_id, status in self._status.items()
                if status.connected
            }
        return tuple(
            sample
            for device_id, sample in sorted(self._latest.items())
            if device_id in connected
        )

    def status(self) -> dict[str, dict[str, Any]]:
        with self._status_lock:
            return {
                device_id: status.to_dict()
                for device_id, status in self._status.items()
            }

    def _thread_main(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        tasks = [
            asyncio.create_task(self._device_loop(config))
            for config in self.devices
        ]
        try:
            while not self._stop.is_set():
                await asyncio.sleep(0.25)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _device_loop(self, config: BLEDeviceConfig) -> None:
        from aiobmsble import BMSConfig
        from aiobmsble.bms.seplos_v2_bms import BMS
        from bleak import BleakScanner

        bms: Any = None
        reconnect_started: float | None = None
        while not self._stop.is_set():
            try:
                device = await BleakScanner.find_device_by_address(
                    config.address,
                    timeout=config.scan_timeout_s,
                )
                if device is None:
                    raise TimeoutError(f"BLE device {config.address} not discovered")
                if bms is None:
                    bms = BMS(device, BMSConfig(keep_alive=True))
                values = await bms.async_update(raw=True)
                now = time()
                self._samples.put(
                    BLESample(
                        config.device_id,
                        config.battery_id,
                        now,
                        dict(values),
                    )
                )
                with self._status_lock:
                    status = self._status[config.device_id]
                    if not status.connected:
                        status.connected = True
                        status.connection_count += 1
                        status.connection_started = monotonic()
                        if status.successful_updates:
                            status.reconnect_count += 1
                            if reconnect_started is not None:
                                status.last_reconnect_s = round(
                                    monotonic() - reconnect_started, 3
                                )
                            reconnect_started = None
                    status.successful_updates += 1
                    status.last_update = now
                    status.last_error = None
                await self._interruptible_sleep(config.poll_interval_s)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                with self._status_lock:
                    status = self._status[config.device_id]
                    if status.connected:
                        status.connected = False
                        reconnect_started = monotonic()
                        status.disconnect_count += 1
                        if status.connection_started is not None:
                            status.total_connected_s += (
                                monotonic() - status.connection_started
                            )
                            status.connection_started = None
                    status.last_error = f"{type(error).__name__}: {error}"
                LOG.warning(
                    "BLE device=%s address=%s failed: %s",
                    config.device_id,
                    config.address,
                    error,
                )
                if bms is not None:
                    try:
                        await bms.disconnect(reset=True)
                    except Exception:
                        LOG.debug("BLE disconnect cleanup failed", exc_info=True)
                    bms = None
                await self._interruptible_sleep(config.reconnect_delay_s)

        if bms is not None:
            await bms.disconnect()

    async def _interruptible_sleep(self, seconds: float) -> None:
        deadline = monotonic() + seconds
        while not self._stop.is_set() and monotonic() < deadline:
            await asyncio.sleep(min(0.25, deadline - monotonic()))
