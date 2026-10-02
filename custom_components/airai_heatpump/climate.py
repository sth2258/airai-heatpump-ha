"""Climate entity for AIR.ai Pool Heat Pump."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
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
    DP_SWITCH,
    DP_MODE,
    DP_TEMP_SET,
    DP_WORK_MODE,
    DP_INLET_TEMP,
    DP_COMPRESSOR_FREQ,
    TUYA_MODE_TO_HVAC,
    HVAC_TO_TUYA_MODE,
    TUYA_WORK_MODES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate entity from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [AirAiHeatPumpClimate(data["coordinator"], data["device"], entry)],
        True,
    )


class AirAiHeatPumpClimate(CoordinatorEntity, ClimateEntity):
    """HA Climate entity for AIR.ai / TURBRO pool heat pumps.

    Temperature values from the device are in Fahrenheit.
    We declare FAHRENHEIT as our native unit so HA handles C/F conversion.
    Target temp range: 47–104 °F (8.3–40 °C).
    """

    _attr_has_entity_name = True
    _attr_name = "Pool Heat Pump"
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_precision = 1.0
    _attr_target_temperature_step = 1.0
    _attr_min_temp = 47  # °F
    _attr_max_temp = 104  # °F
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
    ]
    _attr_preset_modes = TUYA_WORK_MODES  # ECO, Normal, Boost

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._device = device
        self._device_id = entry.data[CONF_DEVICE_ID]
        self._attr_unique_id = f"{self._device_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=entry.data.get(CONF_DEVICE_NAME, "AIR.ai Heat Pump"),
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def _dps(self) -> dict[str, Any]:
        """Shortcut to coordinator data (DP dict)."""
        return self.coordinator.data or {}

    # ─── State properties ────────────────────────────────────────────────

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        if not self._dps.get(DP_SWITCH):
            return HVACMode.OFF
        tuya_mode = self._dps.get(DP_MODE, "")
        ha_mode = TUYA_MODE_TO_HVAC.get(tuya_mode, "heat_cool")
        return HVACMode(ha_mode)

    @property
    def hvac_action(self) -> HVACAction | None:
        """Determine HVAC action from compressor frequency and mode."""
        if not self._dps.get(DP_SWITCH):
            return HVACAction.OFF

        comp_freq = self._dps.get(DP_COMPRESSOR_FREQ, 0)
        if not comp_freq or comp_freq == 0:
            return HVACAction.IDLE

        # Compressor is running — determine heating vs cooling from mode
        tuya_mode = self._dps.get(DP_MODE, "")
        if tuya_mode == "make_cold":
            return HVACAction.COOLING
        return HVACAction.HEATING

    @property
    def current_temperature(self) -> float | None:
        """Return current inlet water temperature (°F, HA converts)."""
        raw = self._dps.get(DP_INLET_TEMP)
        if raw is not None:
            return float(raw)
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature (°F)."""
        raw = self._dps.get(DP_TEMP_SET)
        if raw is not None:
            return float(raw)
        return None

    @property
    def preset_mode(self) -> str | None:
        """Return current work/performance mode."""
        mode = self._dps.get(DP_WORK_MODE)
        if mode in TUYA_WORK_MODES:
            return mode
        return None

    # ─── Commands ────────────────────────────────────────────────────────

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode (OFF, HEAT, COOL, HEAT_COOL)."""
        if hvac_mode == HVACMode.OFF:
            await self._device.async_set_dp(DP_SWITCH, False)
        else:
            tuya_mode = HVAC_TO_TUYA_MODE.get(hvac_mode.value)
            if tuya_mode:
                await self._device.async_set_dps(
                    {DP_SWITCH: True, DP_MODE: tuya_mode}
                )
            else:
                await self._device.async_set_dp(DP_SWITCH, True)
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature (value in °F from HA)."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        # Clamp to valid range and send as integer °F
        temp_int = max(47, min(104, int(round(temp))))
        await self._device.async_set_dp(DP_TEMP_SET, temp_int)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set work mode (ECO / Normal / Boost)."""
        if preset_mode in TUYA_WORK_MODES:
            await self._device.async_set_dp(DP_WORK_MODE, preset_mode)
            await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the heat pump on."""
        await self._device.async_set_dp(DP_SWITCH, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the heat pump off."""
        await self._device.async_set_dp(DP_SWITCH, False)
        await self.coordinator.async_request_refresh()
