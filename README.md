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
    max_temp = await device.get_hot_tank_max_temp()      # Temperature(150.00, 'F')

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
print(t.to_celsius())     # 100.0
print(t.as_celsius())     # Temperature(100.00, 'C')
print(t)                  # 212.00°F

# Temperature differentials  (ΔF = ΔC × 9/5, no +32 offset)
d = TemperatureDelta(9, "F")
print(d.to_celsius())     # 5.0
print(d.as_celsius())     # TemperatureDelta(5.00, 'C')
print(d)                  # 9.00Δ°F
```

### Temperature methods

| Method | Returns | Description |
|---|---|---|
| `to_celsius()` | `float` | Value converted to °C |
| `to_fahrenheit()` | `float` | Value converted to °F |
| `as_celsius()` | `Temperature` | New Temperature object in °C |
| `as_fahrenheit()` | `Temperature` | New Temperature object in °F |

`TemperatureDelta` has the same methods (returns `TemperatureDelta` for `as_*`).

Some getters return `'off'` when the feature is disabled:

```python
shutdown = await device.get_warm_weather_shutdown()  # Temperature(75.00, 'F') or 'off'
```

## API reference

### Sensorlinx

The low-level API client. Manages authentication and HTTP requests.

| Method | Description |
|---|---|
| `login(username, password)` | Authenticate with SensorLinx |
| `close()` | Close the HTTP session |
| `get_profile()` | Fetch the authenticated user's profile |
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
| `get_dhw_enabled()` | `bool` | |
| `get_dhw_target_temp()` | `Temperature` | |
| `get_dhw_differential()` | `TemperatureDelta` | |
| `get_dhw_state()` | `dict` | DHW demand state with `activated`, `enabled`, `title` |
| `get_backup_lag_time()` | `int \| 'off'` | minutes |
| `get_backup_temp()` | `Temperature \| 'off'` | |
| `get_backup_differential()` | `TemperatureDelta \| 'off'` | |
| `get_backup_only_outdoor_temp()` | `Temperature \| 'off'` | |
| `get_backup_only_tank_temp()` | `Temperature \| 'off'` | |
| `get_firmware_version()` | `str` | |
| `get_sync_code()` | `str` | |
| `get_device_pin()` | `str` | |
| `get_device_type()` | `str` | e.g. `"ECO"` |
| `get_temperatures(temp_name=None)` | `dict` | Dict of sensor dicts with `actual` and `target` as `Temperature` objects. Pass `temp_name` to get one sensor. |
| `get_runtimes()` | `dict` | Stage runtimes as `list[timedelta]`, backup runtime as `timedelta` |
| `get_heatpump_stages_state()` | `list[dict]` | Stage info with `activated`, `enabled`, `title`, `device`, `index`, `runTime` |
| `get_backup_state()` | `dict` | Backup state with `activated`, `enabled`, `title`, `runTime` |
| `get_current_weather()` | `dict` | Current conditions: `temp`, `feelsLike`, `min`, `max` as `Temperature`; `pressure`, `humidity`, `wind`, `windDir`, `clouds`, `snow`, `rain`, `description`, `icon`, `weatherId` |
| `get_forecast()` | `list[dict]` | Forecast periods: `time` as `datetime`, `temp`/`min`/`max` as `Temperature`, `pop`, `snow`, `description`, `icon`, `weatherId` |

#### Weather conditions

The `description` and `weatherId` fields in weather and forecast data come from [OpenWeatherMap](https://openweathermap.org/weather-conditions). Use `weatherId` for programmatic checks — it is more reliable than parsing the description string.

| Group | `weatherId` range | Example descriptions |
|---|---|---|
| Thunderstorm | 200–232 | "thunderstorm with light rain", "heavy thunderstorm" |
| Drizzle | 300–321 | "light intensity drizzle", "drizzle rain" |
| Rain | 500–531 | "light rain", "moderate rain", "heavy intensity rain" |
| Snow | 600–622 | "light snow", "heavy snow", "sleet" |
| Atmosphere | 701–781 | "mist", "smoke", "haze", "fog", "tornado" |
| Clear | 800 | "clear sky" |
| Clouds | 801–804 | "few clouds", "scattered clouds", "broken clouds", "overcast clouds" |

#### Setters

All setters accept the value as the first argument. Temperature setters accept `int` (°F), `Temperature`, or `'off'` where applicable.

| Method | Accepts |
|---|---|
| `set_hvac_mode_priority(value)` | `"heat"`, `"cool"`, `"auto"` |
| `set_permanent_hd(value)` | `bool` |
| `set_permanent_cd(value)` | `bool` |
| `set_wide_priority_differential(value)` | `bool` |
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
| `set_hot_tank_target_temp(value)` | Alias for `set_hot_tank_min_temp` |
| `set_cold_weather_shutdown(value)` | `int` (33–119 °F) or `"off"` |
| `set_cold_tank_outdoor_reset(value)` | `int` (0–119 °F) or `"off"` |
| `set_cold_tank_differential(value)` | `int` (2–100 °F) |
| `set_cold_tank_min_temp(value)` | `int` (2–180 °F) |
| `set_cold_tank_max_temp(value)` | `int` (2–180 °F) |
| `set_cold_tank_target_temp(value)` | Alias for `set_cold_tank_min_temp` |
| `set_dhw_enabled(value)` | `bool` |
| `set_dhw_target_temp(value)` | `Temperature` (33–180 °F) |
| `set_dhw_differential(value)` | `TemperatureDelta` (2–100 °F) |
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
