"""Constants for AIR.ai Pool Heat Pump integration."""

from __future__ import annotations

DOMAIN = "airai_heatpump"
MANUFACTURER = "TURBRO"
MODEL = "AIR.ai Pool Heat Pump"

# Polling interval
SCAN_INTERVAL_SECONDS = 30

# ─── AIR.ai / Tuya OEM credentials (iMatic.Ozone) ───────────────────────────
TUYA_APP_ID = "yqs9kenstkqjxmgnac75"
TUYA_APP_SECRET = "grwnwe7q57da3ffnsn55fg4s93dqd53v"
TUYA_CERT_SHA256 = (
    "3348FA3F0A652D42624784DD0CD881002BBD0889AE69015170F4DE6D1A52DD0A"
)
TUYA_APP_KEY = "37df4xcyxrt8tf7fphcayvadxvgrrtph"
TUYA_PACKAGE = "iMatic.Ozone"
TUYA_APP_VERSION = "5.0.4"
TUYA_TTID = "iMaticOzone"
TUYA_SDK_VERSION = "5.0.0"
TUYA_DEVICE_CORE_VERSION = "5.0.0"
TUYA_PROTOCOL_VERSION = 3.5

# ─── Regional API endpoints ──────────────────────────────────────────────────
REGION_ENDPOINTS: dict[str, str] = {
    "US": "https://a1-us.iotbing.com/api.json",
    "EU": "https://a1-eu.iotbing.com/api.json",
    "IN": "https://a1-in.iotbing.com/api.json",
}
DEFAULT_REGION = "US"

# ─── Config entry keys ───────────────────────────────────────────────────────
CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_DEVICE_IP = "device_ip"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_REGION = "region"
CONF_COUNTRY_CODE = "country_code"
CONF_DEVICE_NAME = "device_name"

# ─── Tuya Data Points (verified from cloud SchemaBean) ────────────────────────
# Writable (rw)
DP_SWITCH = "1"             # bool — Power on/off
DP_MODE = "2"               # enum — make_cold / make_hot / auto
DP_TEMP_SET = "4"           # int 47-104 — Target temperature (°F)
DP_WORK_MODE = "5"          # enum — ECO / Normal / Boost
DP_VOLUME_SET = "106"       # int 0-2 — Energy monitoring setting

# Read-only – Temperatures (raw °F, no scaling)
DP_INLET_TEMP = "21"        # Inlet water temp (°F)
DP_OUTLET_TEMP = "22"       # Outlet water temp (°F)
DP_COIL_TEMP = "23"         # Evaporator coil temp (°F)
DP_DISCHARGE_TEMP = "24"    # Discharge/exhaust temp (°F)
DP_AMBIENT_TEMP = "26"      # Ambient outdoor temp (°F)
DP_INCOILER_TEMP = "37"     # Inner coil (incoiler) temp (°F)
DP_SUCTION_TEMP = "41"      # Suction/return gas temp (°F)

# Read-only – System
DP_FW_VERSION = "14"        # Mainboard program version
DP_FAULT = "15"             # Fault alarm codes (bitmap, 30 bits)
DP_MAIN_EEV = "16"          # Main EEV valve position (pulses)
DP_ENERGY_TODAY = "18"      # Today's energy (kWh, scale 2 → ÷100)
DP_COMPRESSOR_FREQ = "20"   # Compressor frequency (Hz)
DP_AUX_EEV = "25"           # Aux EEV valve position (pulses)
DP_DEFROST = "33"           # Defrost cycle active (bool)
DP_DC_BUS_VOLTAGE = "35"    # DC bus voltage (V)
DP_FAN_FREQ = "40"          # Fan frequency (Hz)

# Read-only – Electrical (3-phase power monitoring)
DP_PHASE_A_CURRENT = "102"  # Phase A current (A, scale 3 → ÷1000)
DP_PHASE_A_VOLTAGE = "103"  # Phase A voltage (V, scale 1 → ÷10)
DP_POWER = "104"            # Power consumption (W, scale 1 → ÷10)
DP_ENERGY_TOTAL = "105"     # Total energy (kWh, scale 2 → ÷100)
DP_PHASE_B_CURRENT = "109"  # Phase B current (A, scale 3 → ÷1000)
DP_PHASE_C_CURRENT = "110"  # Phase C current (A, scale 3 → ÷1000)
DP_PHASE_B_VOLTAGE = "111"  # Phase B voltage (V, scale 1 → ÷10)
DP_PHASE_C_VOLTAGE = "112"  # Phase C voltage (V, scale 1 → ÷10)

# ─── Mode mappings ───────────────────────────────────────────────────────────
TUYA_MODE_TO_HVAC = {
    "make_hot": "heat",
    "make_cold": "cool",
    "auto": "heat_cool",
}
HVAC_TO_TUYA_MODE = {v: k for k, v in TUYA_MODE_TO_HVAC.items()}

TUYA_WORK_MODES = ["ECO", "Normal", "Boost"]

# All DPs we poll (every DP the device exposes)
ALL_DPS = [
    1, 2, 4, 5, 14, 15, 16, 18, 20, 21, 22, 23, 24, 25, 26, 33,
    35, 37, 40, 41, 102, 103, 104, 105, 106, 109, 110, 111, 112,
]

# ─── Fault code bitmap descriptions (DP 15, 30-bit bitmap) ────────────────────
# Bit position → fault name. Known codes from device observation and OEM docs.
FAULT_CODES: dict[int, str] = {
    0: "High-pressure protection",
    1: "Low-pressure protection",
    2: "Compressor overload",
    3: "Water flow switch fault",
    4: "Discharge temp too high",
    5: "Ambient temp sensor fault",
    6: "Coil temp sensor fault",
    7: "Discharge temp sensor fault",
    8: "Suction temp sensor fault",
    9: "Inlet water temp sensor fault",
    10: "Outlet water temp sensor fault",
    11: "Communication fault",
    12: "EEPROM fault",
    13: "Phase loss / power fault",
    14: "Fan motor fault",
    15: "Incoiler temp sensor fault",
    16: "EEV fault",
    17: "Anti-freeze protection",
    18: "Phase sequence fault",
    19: "Compressor startup failure",
    20: "Voltage out of range",
    21: "Current overload",
    22: "Inverter module fault",
    23: "PFC fault",
    24: "DC bus voltage fault",
    25: "IPM overheat",
    26: "Compressor demagnetization",
    27: "Compressor stall",
    28: "Reserved",
    29: "Reserved",
}


def decode_fault_bitmap(raw: int) -> list[str]:
    """Decode a fault bitmap into a list of active fault descriptions."""
    if not raw:
        return []
    faults = []
    for bit, name in FAULT_CODES.items():
        if raw & (1 << bit):
            faults.append(name)
    return faults
