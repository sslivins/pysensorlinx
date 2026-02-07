# pysensorlinx

An async Python library for the [SensorLinx](https://mobile.sensorlinx.co) API. It provides full control of HBX HVAC controllers (such as the ECO-0600) — reading sensor data, getting and setting device parameters, and managing heat-pump staging, tank temperatures, backup settings, and more.

[![PyPI](https://img.shields.io/pypi/v/pysensorlinx)](https://pypi.org/project/pysensorlinx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Features

- **Async** — built on `aiohttp` for non-blocking I/O
- **Login & session management** — authenticate, auto-refresh tokens, and close sessions
- **Buildings & devices** — list buildings and enumerate devices per building
- **Get & set parameters** — read and write every ECO-0600 configuration parameter
- **Temperature objects** — `Temperature` and `TemperatureDelta` classes with automatic °F ↔ °C conversion
- **Read sensor data** — retrieve live temperature sensor readings and stage runtimes
- **Exception hierarchy** — typed exceptions for login failures and invalid parameters

## Installation

```bash
pip install pysensorlinx
```

### Development install

```bash
git clone https://github.com/sslivins/pysensorlinx.git
cd pysensorlinx
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -e .[tests]
```

## Quick start

```python
import asyncio
from pysensorlinx import Sensorlinx, SensorlinxDevice

async def main():
    api = Sensorlinx()
    await api.login("your_username", "your_password")

    # List buildings
    buildings = await api.get_buildings()
    building_id = buildings[0]["_id"]

    # List devices in the first building
    devices = await api.get_devices(building_id)
    device_id = devices[0]["_id"]

    # Create a device helper
    device = SensorlinxDevice(api, building_id, device_id)

    # Read parameters
    mode = await device.get_hvac_mode_priority()        # "heat", "cool", or "auto"
    temps = await device.get_temperatures()              # dict of sensor readings
    max_temp = await device.get_hot_tank_max_temp()      # Temperature(150, 'F')

    # Write parameters
    await device.set_hvac_mode_priority("auto")
    await device.set_hot_tank_max_temp(160)              # accepts int (°F) or Temperature

    await api.close()

asyncio.run(main())
```

## Temperature & TemperatureDelta

The library returns temperature values as `Temperature` or `TemperatureDelta` objects that handle unit conversion automatically. The API stores all values in °F.

```python
from pysensorlinx import Temperature, TemperatureDelta

# Absolute temperatures  (°F = °C × 9/5 + 32)
t = Temperature(212, "F")
print(t.celsius)          # 100.0
print(t.to_celsius())     # Temperature(100.0, 'C')
print(t)                  # 212.00°F

# Temperature differentials  (ΔF = ΔC × 9/5, no +32 offset)
d = TemperatureDelta(9, "F")
print(d.celsius)          # 5.0
print(d.to_celsius())     # TemperatureDelta(5.0, 'C')
print(d)                  # 9.00Δ°F
```

Some getters return `'off'` when the feature is disabled:

```python
shutdown = await device.get_warm_weather_shutdown()  # Temperature(75, 'F') or 'off'
```

## API reference

### Sensorlinx

The low-level API client. Manages authentication and HTTP requests.

| Method | Description |
|---|---|
| `login(username, password)` | Authenticate with SensorLinx |
| `close()` | Close the HTTP session |
| `get_user_profile()` | Fetch the authenticated user's profile |
| `get_buildings(building_id=None)` | List all buildings, or fetch one by ID |
| `get_devices(building_id, device_id=None)` | List devices in a building, or fetch one |
| `set_device_parameter(building_id, device_id, **kwargs)` | Set one or more device parameters |

### SensorlinxDevice

A high-level wrapper around a single device. All methods are `async`.

#### Getters

| Method | Returns | Notes |
|---|---|---|
| `get_hvac_mode_priority()` | `str` | `"heat"`, `"cool"`, or `"auto"` |
| `get_permanent_heat_demand()` | `bool` | |
| `get_permanent_cool_demand()` | `bool` | |
| `get_weather_shutdown_lag_time()` | `int` | hours |
| `get_heat_cool_switch_delay()` | `int` | seconds |
| `get_wide_priority_differential()` | `bool` | |
| `get_number_of_stages()` | `int` | 1–4 |
| `get_two_stage_heat_pump()` | `bool` | |
| `get_stage_on_lag_time()` | `int` | minutes |
| `get_stage_off_lag_time()` | `int` | seconds |
| `get_rotate_cycles()` | `int \| 'off'` | |
| `get_rotate_time()` | `int \| 'off'` | hours |
| `get_off_staging()` | `bool` | |
| `get_warm_weather_shutdown()` | `Temperature \| 'off'` | |
| `get_hot_tank_outdoor_reset()` | `Temperature \| 'off'` | |
| `get_hot_tank_differential()` | `TemperatureDelta` | |
| `get_hot_tank_min_temp()` | `Temperature` | |
| `get_hot_tank_max_temp()` | `Temperature` | |
| `get_cold_weather_shutdown()` | `Temperature \| 'off'` | |
| `get_cold_tank_outdoor_reset()` | `Temperature \| 'off'` | |
| `get_cold_tank_differential()` | `TemperatureDelta` | |
| `get_cold_tank_min_temp()` | `Temperature` | |
| `get_cold_tank_max_temp()` | `Temperature` | |
| `get_backup_lag_time()` | `int \| 'off'` | minutes |
| `get_backup_temp()` | `Temperature \| 'off'` | |
| `get_backup_differential()` | `TemperatureDelta \| 'off'` | |
| `get_backup_only_outdoor_temp()` | `Temperature \| 'off'` | |
| `get_backup_only_tank_temp()` | `Temperature \| 'off'` | |
| `get_temperatures(sensor=None)` | `dict` | Live sensor readings |
| `get_stages()` | `list[dict]` | Stage info with runtimes |
| `get_backup()` | `dict` | Backup state and runtime |
| `get_firmware_version()` | `float` | |
| `get_device_type()` | `str` | e.g. `"ECO-0600"` |

#### Setters

All setters accept the value as the first argument. Temperature setters accept `int` (°F), `Temperature`, or `'off'` where applicable.

| Method | Accepts |
|---|---|
| `set_hvac_mode_priority(value)` | `"heat"`, `"cool"`, `"auto"` |
| `set_permanent_heat_demand(value)` | `bool` |
| `set_permanent_cool_demand(value)` | `bool` |
| `set_weather_shutdown_lag_time(value)` | `int` (0–240 hours) |
| `set_number_of_stages(value)` | `int` (1–4) |
| `set_two_stage_heat_pump(value)` | `bool` |
| `set_stage_on_lag_time(value)` | `int` (1–240 min) |
| `set_stage_off_lag_time(value)` | `int` (1–240 sec) |
| `set_rotate_cycles(value)` | `int` (1–240) or `"off"` |
| `set_rotate_time(value)` | `int` (1–240 hours) or `"off"` |
| `set_off_staging(value)` | `bool` |
| `set_heat_cool_switch_delay(value)` | `int` (30–600 sec) |
| `set_warm_weather_shutdown(value)` | `int` (34–180 °F) or `"off"` |
| `set_hot_tank_outdoor_reset(value)` | `int` (-40–127 °F) or `"off"` |
| `set_hot_tank_differential(value)` | `int` (2–100 °F) |
| `set_hot_tank_min_temp(value)` | `int` (2–180 °F) |
| `set_hot_tank_max_temp(value)` | `int` (2–180 °F) |
| `set_cold_weather_shutdown(value)` | `int` (33–119 °F) or `"off"` |
| `set_cold_tank_outdoor_reset(value)` | `int` (0–119 °F) or `"off"` |
| `set_cold_tank_differential(value)` | `int` (2–100 °F) |
| `set_cold_tank_min_temp(value)` | `int` (2–180 °F) |
| `set_cold_tank_max_temp(value)` | `int` (2–180 °F) |
| `set_backup_lag_time(value)` | `int` (1–240 min) or `"off"` |
| `set_backup_temp(value)` | `int` (2–100 °F) or `"off"` |
| `set_backup_differential(value)` | `int` (2–100 °F) or `"off"` |
| `set_backup_only_outdoor_temp(value)` | `int` (-40–127 °F) or `"off"` |
| `set_backup_only_tank_temp(value)` | `int` (33–200 °F) or `"off"` |

### Exceptions

| Exception | When raised |
|---|---|
| `LoginError` | Base class for login failures |
| `InvalidCredentialsError` | Wrong username or password |
| `LoginTimeoutError` | Login request timed out |
| `InvalidParameterError` | A setter received an out-of-range or invalid value |

## Testing

```bash
pip install -e .[tests]
pytest
```

## License

[MIT](LICENSE)
