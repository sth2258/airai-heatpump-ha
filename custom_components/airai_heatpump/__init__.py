"""AIR.ai Pool Heat Pump integration for Home Assistant.

Coordinator-based integration using tinytuya for local polling of
TURBRO / AIR.ai pool heat pumps over Tuya protocol v3.5.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_DEVICE_IP,
    SCAN_INTERVAL_SECONDS,
)
from .device import HeatPumpDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AIR.ai Heat Pump from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    device = HeatPumpDevice(
        device_id=entry.data[CONF_DEVICE_ID],
        ip_address=entry.data[CONF_DEVICE_IP],
        local_key=entry.data[CONF_LOCAL_KEY],
    )

    async def _async_update() -> dict:
        """Fetch latest data from the device."""
        try:
            return await device.async_update()
        except Exception as err:
            raise UpdateFailed(f"Error polling heat pump: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"airai_{entry.data[CONF_DEVICE_ID]}",
        update_method=_async_update,
        update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        data["device"].disconnect()
    return unload_ok
