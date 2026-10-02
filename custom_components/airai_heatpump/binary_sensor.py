"""Binary sensor entities for AIR.ai Pool Heat Pump."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    DP_DEFROST,
    DP_FAULT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_id = entry.data[CONF_DEVICE_ID]
    device_name = entry.data.get(CONF_DEVICE_NAME, "AIR.ai Heat Pump")

    device_info = DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=device_name,
        manufacturer=MANUFACTURER,
        model=MODEL,
    )

    async_add_entities(
        [
            DefrostBinarySensor(coordinator, device_id, device_info),
            FaultBinarySensor(coordinator, device_id, device_info),
        ],
        True,
    )


class DefrostBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating defrost cycle is active (DP 33)."""

    _attr_has_entity_name = True
    _attr_name = "Defrost Active"
    _attr_icon = "mdi:snowflake-melt"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the defrost binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{device_id}_defrost_active"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool | None:
        """Return True if defrost cycle is active."""
        data = self.coordinator.data or {}
        val = data.get(DP_DEFROST)
        if val is None:
            return None
        return bool(val)


class FaultBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating a fault condition (DP 15 != 0)."""

    _attr_has_entity_name = True
    _attr_name = "Fault Active"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the fault binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{device_id}_fault_active"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool | None:
        """Return True if any fault bits are set."""
        data = self.coordinator.data or {}
        val = data.get(DP_FAULT)
        if val is None:
            return None
        return int(val) != 0
