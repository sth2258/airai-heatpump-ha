"""Config flow for AIR.ai Pool Heat Pump."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REGION,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_DEVICE_IP,
    CONF_COUNTRY_CODE,
    CONF_DEVICE_NAME,
    DEFAULT_REGION,
)

_LOGGER = logging.getLogger(__name__)

CLOUD_REGIONS = {
    "US": "United States",
    "EU": "Europe",
    "IN": "India",
}

COUNTRY_CODES = {
    "US": "1",
    "EU": "44",
    "IN": "91",
}


class AirAiHeatPumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AIR.ai Heat Pump."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: list[dict[str, Any]] = []
        self._cloud_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step — choose setup method."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["cloud_login", "manual"],
        )

    # ─── Cloud Login Flow ────────────────────────────────────────────────

    async def async_step_cloud_login(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Log in to AIR.ai cloud to discover devices and fetch local keys."""
        errors: dict[str, str] = {}

        if user_input is not None:
            from .api import AirAiApiClient  # noqa: PLC0415

            region = user_input.get(CONF_REGION, DEFAULT_REGION)
            country_code = COUNTRY_CODES.get(region, "1")

            client = AirAiApiClient(
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
                region=region,
                country_code=country_code,
            )
            try:
                if await client.login():
                    devices = await client.get_devices()
                    if devices:
                        # Store for device selection step
                        self._discovered_devices = devices
                        self._cloud_data = {
                            CONF_EMAIL: user_input[CONF_EMAIL],
                            CONF_REGION: region,
                            CONF_DEVICE_IP: user_input.get(CONF_DEVICE_IP, ""),
                        }
                        # If only one device, skip selection
                        if len(devices) == 1:
                            return await self._create_entry_from_device(devices[0])
                        return await self.async_step_select_device()
                    errors["base"] = "no_devices"
                else:
                    errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Cloud login failed")
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

        return self.async_show_form(
            step_id="cloud_login",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(
                        CLOUD_REGIONS
                    ),
                    vol.Optional(CONF_DEVICE_IP): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let user pick from discovered devices."""
        if user_input is not None:
            selected_id = user_input[CONF_DEVICE_ID]
            for dev in self._discovered_devices:
                if dev["device_id"] == selected_id:
                    return await self._create_entry_from_device(dev)
            return self.async_abort(reason="device_not_found")

        device_options = {
            dev["device_id"]: f"{dev.get('name', 'Heat Pump')} ({dev['device_id'][:8]}…)"
            for dev in self._discovered_devices
        }

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): vol.In(device_options),
                }
            ),
        )

    async def _create_entry_from_device(self, device: dict[str, Any]) -> FlowResult:
        """Create a config entry from a discovered device."""
        device_id = device["device_id"]
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        # Use device IP from cloud data or from device info
        device_ip = self._cloud_data.get(CONF_DEVICE_IP) or device.get("ip", "")

        return self.async_create_entry(
            title=device.get("name", "AIR.ai Heat Pump"),
            data={
                CONF_DEVICE_ID: device_id,
                CONF_LOCAL_KEY: device["local_key"],
                CONF_DEVICE_IP: device_ip,
                CONF_DEVICE_NAME: device.get("name", "AIR.ai Heat Pump"),
                CONF_EMAIL: self._cloud_data.get(CONF_EMAIL, ""),
                CONF_REGION: self._cloud_data.get(CONF_REGION, DEFAULT_REGION),
            },
        )

    # ─── Manual Flow ─────────────────────────────────────────────────────

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manual setup with known device_id, local_key, and IP."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            # Quick validation — try connecting
            from .device import HeatPumpDevice  # noqa: PLC0415

            device = HeatPumpDevice(
                device_id=device_id,
                ip_address=user_input[CONF_DEVICE_IP],
                local_key=user_input[CONF_LOCAL_KEY],
            )
            try:
                data = await device.async_update()
                if data:
                    return self.async_create_entry(
                        title="AIR.ai Heat Pump",
                        data={
                            CONF_DEVICE_ID: device_id,
                            CONF_LOCAL_KEY: user_input[CONF_LOCAL_KEY],
                            CONF_DEVICE_IP: user_input[CONF_DEVICE_IP],
                        },
                    )
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Manual connection test failed")
                errors["base"] = "cannot_connect"
            finally:
                device.disconnect()

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): str,
                    vol.Required(CONF_LOCAL_KEY): str,
                    vol.Required(CONF_DEVICE_IP): str,
                }
            ),
            errors=errors,
        )
