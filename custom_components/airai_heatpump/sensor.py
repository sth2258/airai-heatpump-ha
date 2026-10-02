"""Sensor entities for AIR.ai Pool Heat Pump."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
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
    DP_INLET_TEMP,
    DP_OUTLET_TEMP,
    DP_COIL_TEMP,
    DP_DISCHARGE_TEMP,
    DP_AMBIENT_TEMP,
    DP_INCOILER_TEMP,
    DP_SUCTION_TEMP,
    DP_COMPRESSOR_FREQ,
    DP_FAN_FREQ,
    DP_MAIN_EEV,
    DP_AUX_EEV,
    DP_DC_BUS_VOLTAGE,
    DP_POWER,
    DP_ENERGY_TODAY,
    DP_ENERGY_TOTAL,
    DP_PHASE_A_VOLTAGE,
    DP_PHASE_B_VOLTAGE,
    DP_PHASE_C_VOLTAGE,
    DP_PHASE_A_CURRENT,
    DP_PHASE_B_CURRENT,
    DP_PHASE_C_CURRENT,
    DP_FAULT,
    DP_FW_VERSION,
    decode_fault_bitmap,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HeatPumpSensorDescription(SensorEntityDescription):
    """Describe an AIR.ai heat pump sensor."""

    dp_id: str = ""
    scale: float = 1.0  # Divide raw value by this


# ─── Sensor definitions ─────────────────────────────────────────────────────
SENSOR_DESCRIPTIONS: tuple[HeatPumpSensorDescription, ...] = (
    # ── Temperatures (raw °F, no scaling) ────────────────────────────────
    HeatPumpSensorDescription(
        key="inlet_temp",
        name="Inlet Water Temperature",
        dp_id=DP_INLET_TEMP,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HeatPumpSensorDescription(
        key="outlet_temp",
        name="Outlet Water Temperature",
        dp_id=DP_OUTLET_TEMP,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HeatPumpSensorDescription(
        key="coil_temp",
        name="Evaporator Coil Temperature",
        dp_id=DP_COIL_TEMP,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HeatPumpSensorDescription(
        key="discharge_temp",
        name="Discharge Temperature",
        dp_id=DP_DISCHARGE_TEMP,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HeatPumpSensorDescription(
        key="ambient_temp",
        name="Ambient Temperature",
        dp_id=DP_AMBIENT_TEMP,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HeatPumpSensorDescription(
        key="incoiler_temp",
        name="Inner Coil Temperature",
        dp_id=DP_INCOILER_TEMP,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HeatPumpSensorDescription(
        key="suction_temp",
        name="Suction Gas Temperature",
        dp_id=DP_SUCTION_TEMP,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── System ───────────────────────────────────────────────────────────
    HeatPumpSensorDescription(
        key="compressor_freq",
        name="Compressor Frequency",
        dp_id=DP_COMPRESSOR_FREQ,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
    ),
    HeatPumpSensorDescription(
        key="fan_freq",
        name="Fan Frequency",
        dp_id=DP_FAN_FREQ,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fan",
    ),
    HeatPumpSensorDescription(
        key="main_eev",
        name="Main EEV Position",
        dp_id=DP_MAIN_EEV,
        native_unit_of_measurement="P",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:valve",
    ),
    HeatPumpSensorDescription(
        key="aux_eev",
        name="Aux EEV Position",
        dp_id=DP_AUX_EEV,
        native_unit_of_measurement="P",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:valve",
    ),
    HeatPumpSensorDescription(
        key="dc_bus_voltage",
        name="DC Bus Voltage",
        dp_id=DP_DC_BUS_VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Electrical (with scale factors) ──────────────────────────────────
    HeatPumpSensorDescription(
        key="power",
        name="Power Consumption",
        dp_id=DP_POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        scale=10.0,  # raw ÷ 10
    ),
    HeatPumpSensorDescription(
        key="energy_today",
        name="Energy Today",
        dp_id=DP_ENERGY_TODAY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=100.0,  # raw ÷ 100
    ),
    HeatPumpSensorDescription(
        key="energy_total",
        name="Total Energy",
        dp_id=DP_ENERGY_TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=100.0,  # raw ÷ 100
    ),
    # ── 3-Phase Voltages ─────────────────────────────────────────────────
    HeatPumpSensorDescription(
        key="phase_a_voltage",
        name="Phase A Voltage",
        dp_id=DP_PHASE_A_VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=10.0,
    ),
    HeatPumpSensorDescription(
        key="phase_b_voltage",
        name="Phase B Voltage",
        dp_id=DP_PHASE_B_VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=10.0,
    ),
    HeatPumpSensorDescription(
        key="phase_c_voltage",
        name="Phase C Voltage",
        dp_id=DP_PHASE_C_VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=10.0,
    ),
    # ── 3-Phase Currents ─────────────────────────────────────────────────
    HeatPumpSensorDescription(
        key="phase_a_current",
        name="Phase A Current",
        dp_id=DP_PHASE_A_CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=1000.0,
    ),
    HeatPumpSensorDescription(
        key="phase_b_current",
        name="Phase B Current",
        dp_id=DP_PHASE_B_CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=1000.0,
    ),
    HeatPumpSensorDescription(
        key="phase_c_current",
        name="Phase C Current",
        dp_id=DP_PHASE_C_CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=1000.0,
    ),
    # ── Diagnostics ──────────────────────────────────────────────────────
    HeatPumpSensorDescription(
        key="fault_code",
        name="Fault Code",
        dp_id=DP_FAULT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-circle-outline",
    ),
    HeatPumpSensorDescription(
        key="firmware_version",
        name="Firmware Version",
        dp_id=DP_FW_VERSION,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_id = entry.data[CONF_DEVICE_ID]
    device_name = entry.data.get(CONF_DEVICE_NAME, "AIR.ai Heat Pump")

    entities = [
        HeatPumpSensor(coordinator, entry, desc, device_id, device_name)
        for desc in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities, True)


class HeatPumpSensor(CoordinatorEntity, SensorEntity):
    """A sensor from the AIR.ai heat pump."""

    _attr_has_entity_name = True
    entity_description: HeatPumpSensorDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        description: HeatPumpSensorDescription,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_sensor_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def native_value(self) -> float | int | str | None:
        """Return the sensor value, applying scale factor if needed."""
        data = self.coordinator.data or {}
        raw = data.get(self.entity_description.dp_id)
        if raw is None:
            return None
        # Fault code: show decoded description instead of raw bitmap
        if self.entity_description.dp_id == DP_FAULT:
            if not raw:
                return "OK"
            faults = decode_fault_bitmap(int(raw))
            return "; ".join(faults) if faults else f"Fault {raw}"
        if self.entity_description.scale != 1.0:
            return round(float(raw) / self.entity_description.scale, 2)
        return raw

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes for the fault sensor."""
        if self.entity_description.dp_id != DP_FAULT:
            return None
        data = self.coordinator.data or {}
        raw = data.get(DP_FAULT)
        if raw is None:
            return None
        return {
            "raw_bitmap": int(raw),
            "active_faults": decode_fault_bitmap(int(raw)),
        }
