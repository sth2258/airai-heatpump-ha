"""Local device controller — wraps tinytuya for async HA use."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import tinytuya

from .const import ALL_DPS, TUYA_PROTOCOL_VERSION

_LOGGER = logging.getLogger(__name__)


class TuyaDeviceError(Exception):
    """Base error for tinytuya device communication."""


class TuyaKeyError(TuyaDeviceError):
    """Wrong local key or protocol version (tinytuya error 914)."""


class TuyaNetworkError(TuyaDeviceError):
    """Device unreachable or network timeout (tinytuya error 900)."""


class HeatPumpDevice:
    """Async wrapper around tinytuya.Device for pool heat pump control.

    All tinytuya calls are blocking, so they run via run_in_executor.
    Uses persistent socket connection for reliability.
    """

    def __init__(
        self,
        device_id: str,
        ip_address: str,
        local_key: str,
        protocol_version: float = TUYA_PROTOCOL_VERSION,
    ) -> None:
        self._dev_id = device_id
        self._ip = ip_address
        self._local_key = local_key
        self._version = protocol_version
        self._device: tinytuya.Device | None = None
        self._dps: dict[str, Any] = {}

    @property
    def device_id(self) -> str:
        """Return the Tuya device ID."""
        return self._dev_id

    def _get_device(self) -> tinytuya.Device:
        """Get or create the tinytuya device (lazy init)."""
        if self._device is None:
            self._device = tinytuya.Device(
                self._dev_id,
                self._ip,
                self._local_key,
                version=self._version,
            )
            self._device.set_socketPersistent(True)
            self._device.set_socketTimeout(5)
            self._device.set_socketRetryLimit(2)
        return self._device

    # ─── Public async interface ──────────────────────────────────────────

    async def async_update(self) -> dict[str, Any]:
        """Poll all DPs from the device. Returns the merged DP dict."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._poll)

    async def async_set_dp(self, dp_id: str, value: Any) -> None:
        """Set a single DP value."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._set_dp, dp_id, value)

    async def async_set_dps(self, dps: dict[str, Any]) -> None:
        """Set multiple DP values at once."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._set_dps, dps)

    # ─── Sync helpers (run in executor) ──────────────────────────────────

    def _poll(self) -> dict[str, Any]:
        """Blocking poll — called from executor.

        Raises on tinytuya errors so the coordinator sees the failure.
        """
        dev = self._get_device()
        try:
            status = self._poll_once(dev)
        except Exception:
            _LOGGER.warning(
                "Poll failed for %s, reconnecting", self._dev_id, exc_info=True
            )
            self._reconnect()
            dev = self._get_device()
            status = self._poll_once(dev)

        return status

    def _poll_once(self, dev: tinytuya.Device) -> dict[str, Any]:
        """Single poll attempt. Raises TuyaDeviceError on failure."""
        status = dev.status()
        self._check_error(status)
        if "dps" in status:
            self._dps.update(status["dps"])

        # Request all known DPs (extended range)
        dev.updatedps(ALL_DPS)
        status2 = dev.receive()
        if status2:
            self._check_error(status2)
            if "dps" in status2:
                self._dps.update(status2["dps"])

        if not self._dps:
            raise TuyaDeviceError("Device returned no DPs")

        return dict(self._dps)

    @staticmethod
    def _check_error(response: dict[str, Any]) -> None:
        """Raise TuyaDeviceError if the response contains an error."""
        if "Error" in response:
            err_code = response.get("Err", "")
            err_msg = response.get("Error", "Unknown error")
            if err_code == "914":
                raise TuyaKeyError(
                    f"Wrong local key or protocol version (error {err_code})"
                )
            if err_code == "900":
                raise TuyaNetworkError(f"Network timeout: {err_msg}")
            raise TuyaDeviceError(f"Device error {err_code}: {err_msg}")

    def _set_dp(self, dp_id: str, value: Any) -> None:
        """Set a single DP — blocking."""
        dev = self._get_device()
        try:
            dev.set_value(int(dp_id), value)
        except Exception:
            self._reconnect()
            dev.set_value(int(dp_id), value)

    def _set_dps(self, dps: dict[str, Any]) -> None:
        """Set multiple DPs at once — blocking."""
        dev = self._get_device()
        int_dps = {int(k): v for k, v in dps.items()}
        try:
            payload = dev.generate_payload(tinytuya.CONTROL, int_dps)
            dev.send(payload)
        except Exception:
            self._reconnect()
            payload = dev.generate_payload(tinytuya.CONTROL, int_dps)
            dev.send(payload)

    def _reconnect(self) -> None:
        """Close and recreate the tinytuya device."""
        if self._device:
            try:
                self._device.close()
            except Exception:  # noqa: BLE001
                pass
            self._device = None
        self._get_device()

    def disconnect(self) -> None:
        """Cleanly close the device socket."""
        if self._device:
            try:
                self._device.close()
            except Exception:  # noqa: BLE001
                pass
            self._device = None
