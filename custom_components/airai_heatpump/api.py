"""AIR.ai Pool Heat Pump — Tuya Mobile API client.

Uses the tuya-mobile library with hardcoded AIR.ai (iMatic.Ozone) OEM
credentials to authenticate and fetch device local keys.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    TUYA_APP_ID,
    TUYA_APP_SECRET,
    TUYA_CERT_SHA256,
    TUYA_APP_KEY,
    TUYA_PACKAGE,
    TUYA_APP_VERSION,
    TUYA_TTID,
    TUYA_SDK_VERSION,
    TUYA_DEVICE_CORE_VERSION,
    REGION_ENDPOINTS,
    DEFAULT_REGION,
)

_LOGGER = logging.getLogger(__name__)


def _build_profile():
    """Build the TuyaMobileAppProfile for AIR.ai."""
    from tuya_mobile import TuyaMobileAppProfile  # noqa: PLC0415

    return TuyaMobileAppProfile(
        name="AIR.ai",
        app_id=TUYA_APP_ID,
        app_secret=TUYA_APP_SECRET,
        cert_sha256_hex=TUYA_CERT_SHA256,
        app_key=TUYA_APP_KEY,
        package=TUYA_PACKAGE,
        app_version=TUYA_APP_VERSION,
        ttid=TUYA_TTID,
        sdk_version=TUYA_SDK_VERSION,
        device_core_version=TUYA_DEVICE_CORE_VERSION,
    )


class AirAiApiClient:
    """Async client for the AIR.ai (Tuya OEM) mobile cloud API.

    Uses tuya-mobile's TuyaPasswordClient to authenticate and fetch
    device credentials (local keys) needed for local tinytuya control.
    """

    def __init__(
        self,
        email: str,
        password: str,
        region: str = DEFAULT_REGION,
        country_code: str = "1",
    ) -> None:
        self._email = email
        self._password = password
        self._region = region
        self._country_code = country_code
        self._endpoint = REGION_ENDPOINTS.get(region, REGION_ENDPOINTS[DEFAULT_REGION])
        self._session: aiohttp.ClientSession | None = None
        self._client: Any = None  # TuyaPasswordClient
        self._owns_session = False

    async def _ensure_client(self) -> Any:
        """Create the aiohttp session and TuyaPasswordClient if needed."""
        if self._client is not None:
            return self._client

        from tuya_mobile import TuyaPasswordClient  # noqa: PLC0415

        self._session = aiohttp.ClientSession()
        self._owns_session = True
        profile = _build_profile()
        self._client = TuyaPasswordClient(
            profile=profile,
            session=self._session,
            username=self._email,
            endpoint=self._endpoint,
        )
        return self._client

    async def close(self) -> None:
        """Close the aiohttp session if we own it."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        self._client = None

    async def login(self) -> bool:
        """Authenticate with the AIR.ai cloud. Returns True on success."""
        try:
            client = await self._ensure_client()
            result = await client.login_with_password(
                self._password, self._country_code
            )
            if result and hasattr(result, "sid") and result.sid:
                _LOGGER.info("AIR.ai cloud login successful")
                return True
            _LOGGER.error("AIR.ai login returned no session ID")
            return False
        except Exception:
            _LOGGER.exception("AIR.ai cloud login failed")
            return False

    async def get_devices(self) -> list[dict[str, Any]]:
        """Fetch all devices with their local keys.

        Returns a list of dicts with keys: device_id, name, local_key, product_id.
        """
        if self._client is None:
            raise RuntimeError("Not logged in — call login() first")

        try:
            # tuya-mobile returns device list with credentials
            devices_raw = await self._client.get_device_list()
            devices = []
            for dev in devices_raw:
                device_id = getattr(dev, "id", None) or getattr(dev, "devId", None)
                if not device_id:
                    continue
                devices.append({
                    "device_id": device_id,
                    "name": getattr(dev, "name", "AIR.ai Heat Pump"),
                    "local_key": getattr(dev, "local_key", None) or getattr(dev, "localKey", None),
                    "product_id": getattr(dev, "product_id", None) or getattr(dev, "productId", None),
                    "ip": getattr(dev, "ip", None),
                })
            _LOGGER.info("Found %d device(s)", len(devices))
            return devices
        except Exception:
            _LOGGER.exception("Failed to fetch device list")
            return []

    async def get_device_credentials(self, device_id: str) -> dict[str, Any] | None:
        """Fetch local_key for a specific device."""
        if self._client is None:
            raise RuntimeError("Not logged in — call login() first")

        try:
            creds = await self._client.get_device_credentials(device_id)
            return {
                "local_key": creds.local_key,
                "device_id": device_id,
            }
        except Exception:
            _LOGGER.exception("Failed to fetch credentials for %s", device_id)
            return None
