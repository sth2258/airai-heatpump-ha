# AIR.ai Pool Heat Pump — Home Assistant Integration

Custom Home Assistant integration for TURBRO and other pool heat pumps controlled by the AIR.ai (iMatic.Ozone) app.

## Features

- **Automatic cloud login** — enter your AIR.ai email/password, the integration discovers devices and fetches local keys automatically
- **100% local control** — after initial setup, all communication is direct to the device over your LAN (Tuya protocol v3.5)
- **No cloud dependency** — no Tuya IoT platform account needed, no re-pairing with Smart Life
- **Full sensor suite** — 23 sensors including temperatures, compressor/fan frequencies, power monitoring, 3-phase electrical data

## Supported Devices

Pool heat pumps using the AIR.ai app, including:
- TURBRO 33,000 BTU Inverter Swimming Pool Heat Pump
- Other OEM heat pumps paired with the AIR.ai (iMatic.Ozone) app

## Installation

### HACS (recommended)
1. Add this repository as a custom repository in HACS
2. Install "AIR.ai Pool Heat Pump"
3. Restart Home Assistant

### Manual
1. Copy `custom_components/airai_heatpump/` to your HA `config/custom_components/` directory
2. Restart Home Assistant

## Setup

### Cloud Login (automatic)
1. Go to Settings → Devices & Services → Add Integration
2. Search for "AIR.ai Pool Heat Pump"
3. Select "Cloud Login"
4. Enter your AIR.ai app email, password, and region
5. Select your device from the discovered list
6. Done — the local key is fetched automatically

### Manual Setup
1. Go to Settings → Devices & Services → Add Integration
2. Search for "AIR.ai Pool Heat Pump"
3. Select "Manual"
4. Enter your device ID, local key, and IP address

## Entities Created

### Climate
- **Pool Heat Pump** — HVAC modes (Off/Heat/Cool/Auto), presets (ECO/Normal/Boost), target temperature (47–104°F)

### Sensors (23)
| Sensor | Unit | Description |
|--------|------|-------------|
| Inlet Water Temp | °F | Water entering the heat pump |
| Outlet Water Temp | °F | Water leaving the heat pump |
| Coil Temp | °F | Evaporator coil temperature |
| Discharge Temp | °F | Compressor discharge temperature |
| Ambient Temp | °F | Outdoor air temperature |
| Incoiler Temp | °F | Inner coil (condenser) temperature |
| Suction Temp | °F | Suction/return gas temperature |
| Compressor Frequency | Hz | Inverter compressor speed |
| Fan Frequency | Hz | Fan motor speed |
| Main EEV Position | P | Main expansion valve position |
| Aux EEV Position | P | Auxiliary expansion valve position |
| DC Bus Voltage | V | Inverter DC bus voltage |
| Power | W | Current power consumption |
| Today's Energy | kWh | Energy consumed today |
| Total Energy | kWh | Lifetime energy consumed |
| Phase A/B/C Voltage | V | 3-phase supply voltages |
| Phase A/B/C Current | A | 3-phase supply currents |
| Fault Code | — | Active fault bitmap |
| Firmware Version | — | Mainboard program version |

### Binary Sensors (2)
| Sensor | Description |
|--------|-------------|
| Defrost Active | Defrost cycle is running |
| Fault Active | A fault condition exists |

## Technical Details

This integration was built by reverse-engineering the AIR.ai Android app (iMatic.Ozone), a Tuya OEM white-label application. The authentication credentials were extracted from the APK's steganographic BMP image and native security libraries. The device communicates using the Tuya v3.5 local protocol over TCP port 6668.

## License

MIT
