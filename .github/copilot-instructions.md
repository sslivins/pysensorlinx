# Copilot Instructions — pysensorlinx

## Project Overview

**pysensorlinx** is an async Python library for communicating with HBX ECO-0600 HVAC controllers via the SensorLinx cloud API (`https://mobile.sensorlinx.co`). It is published to PyPI and used as a dependency in a Home Assistant custom integration.

- **Author:** Stefan Slivinski (`sslivins`)
- **License:** MIT
- **Python:** ≥3.7 (developed/tested on 3.11.9)
- **Repository:** `https://github.com/sslivins/pysensorlinx`
- **PyPI:** `pysensorlinx`

## Project Structure

```
src/pysensorlinx/          # Main package (src layout)
  __init__.py               # Exports + __version__
  sensorlinx.py             # All library code (~2200 lines)
tests/
  get_parameter_test.py     # Getter unit tests (mocked)
  set_parameters_test.py    # Setter unit tests (mocked)
  temperature_class_test.py # Temperature/TemperatureDelta unit tests
  live_test.py              # Live integration tests (requires network + .env credentials)
.github/workflows/
  unit_tests.yml            # CI: runs unit tests on push/PR
  live_tests.yml            # CI: runs live tests (manual trigger)
  publish_to_pypi.yml       # CI: auto-tags from pyproject.toml version, publishes to PyPI
```

## Key Classes

### `Sensorlinx`
The API client. Handles login, session management, and raw API calls.
- `async login(username, password)` — authenticates and stores session cookie
- `async get_profile()` — returns user profile dict
- `async get_buildings(building_id=None)` — returns building(s)
- `async get_devices(building_id, device_id=None)` — returns device(s)
- `async set_device_parameter(building_id, device_id, parameter, value)` — sets a parameter on a device

### `SensorlinxDevice`
Wraps a single device. Constructed with a `Sensorlinx` client + building/device IDs. Provides all the typed getter/setter methods.

### `Temperature`
Represents an absolute temperature value.
- Constructor: `Temperature(value, unit="C")` where unit is `"C"` or `"F"`
- `to_celsius()` / `to_fahrenheit()` → returns `float`
- `as_celsius()` / `as_fahrenheit()` → returns new `Temperature` object
- Conversion: `°F = °C × 9/5 + 32`

### `TemperatureDelta`
Represents a temperature *difference* (differential), not an absolute value.
- Same interface as `Temperature` but conversion has **no +32 offset**: `ΔF = ΔC × 9/5`
- Used for: `htDif`, `clDif`, `bkDif`, `wPDif`, `auxDif`

### Exceptions
- `InvalidCredentialsError` — wrong username/password
- `LoginTimeoutError` — login request timed out
- `LoginError` — generic login failure
- `InvalidParameterError` — invalid parameter name or value in setter

## API Key Mappings (Critical)

The SensorLinx API uses short abbreviated keys. The constant names map as follows:

| Constant | API Key | Meaning |
|----------|---------|---------|
| `HOT_TANK_MAX_TEMP` | `dbt` | **D**esign **B**oiler **T**emp (max target at coldest weather) |
| `HOT_TANK_MIN_TEMP` | `mbt` | **M**inimum **B**oiler **T**emp (min target at mild weather) |
| `COLD_TANK_MAX_TEMP` | `dst` | **D**esign **S**upply **T**emp (max cold target) |
| `COLD_TANK_MIN_TEMP` | `mst` | **M**inimum **S**upply **T**emp (min cold target) |
| `HOT_TANK_OUTDOOR_RESET` | `dot` | Design outdoor temp for hot reset curve |
| `COLD_TANK_OUTDOOR_RESET` | `cdot` | Design outdoor temp for cold reset curve |
| `WARM_WEATHER_SHUTDOWN` | `wwsd` | Warm weather shutdown threshold |
| `COLD_WEATHER_SHUTDOWN` | `cwsd` | Cold weather shutdown threshold |
| `HOT_TANK_DIFFERENTIAL` | `htDif` | Hot tank differential (TemperatureDelta) |
| `COLD_TANK_DIFFERENTIAL` | `clDif` | Cold tank differential (TemperatureDelta) |
| `BACKUP_DIFFERENTIAL` | `bkDif` | Backup differential (TemperatureDelta) |

**Important:** `dbt` = max, `mbt` = min. These were historically swapped and fixed in v0.1.9. Do NOT swap them back.

## Temperature Handling Conventions

- The API stores **all temperatures in Fahrenheit**.
- Getters return `Temperature` or `TemperatureDelta` objects (in Fahrenheit from the API).
- Setters accept `Temperature` or `TemperatureDelta` objects and convert to Fahrenheit before sending.
- When a feature is disabled (e.g., outdoor reset at -41°F, backup off), the getter returns the string `"off"` instead of a Temperature object.
- The disabled sentinel value is `-41` (°F) for temperature fields that support disabling.

## Return Type Patterns

- **Absolute temperatures:** Return `Temperature` object, or `"off"` (string) if disabled → type hint: `Union[Temperature, str]`
- **Differentials:** Return `TemperatureDelta` object, or `"off"` if disabled → type hint: `Union[TemperatureDelta, str]`
- **Booleans (on/off):** Return `bool` — the getter converts `0/1` to `False/True`
- **Integers with "off":** Return `int` or `"off"` → type hint: `Union[int, str]`
- **Read-only info:** Return `str` (firmware version, sync code, pin, device type)
- **Temperatures dict:** `get_temperatures(temp_name=None)` returns a dict of all sensor readings or a single sensor's data

## Method Naming

Use the actual method names from the source code. Key ones that are easy to get wrong:

- `get_profile()` — NOT `get_user_profile()`
- `get_heatpump_stages_state()` — NOT `get_stages()`
- `get_backup_state()` — NOT `get_backup()`
- `set_permanent_hd()` / `set_permanent_cd()` — NOT `set_permanent_heat_demand()` / `set_permanent_cool_demand()`
- `get_temperatures(temp_name=None)` — optional filter parameter

## Testing

- **Framework:** pytest + pytest-asyncio
- **Config:** `pytest.ini` sets `asyncio_mode = auto`
- **Markers:** `get_params`, `set_params`, `temperature`, `live`
- **Mocking:** `aioresponses` for HTTP mocking in unit tests
- **Live tests:** Require `.env` file with `SENSORLINX_USERNAME`, `SENSORLINX_PASSWORD`, `SENSORLINX_BUILDING_ID`, `SENSORLINX_DEVICE_ID`
- **Run all unit tests:** `pytest tests/get_parameter_test.py tests/set_parameters_test.py tests/temperature_class_test.py`
- **Run live tests:** `pytest tests/live_test.py -s -v` (needs network + credentials)
- **Current test count:** ~669 tests

## CI/CD Workflows

### `publish_to_pypi.yml`
- Trigger: `workflow_dispatch` (manual only)
- Reads version from `pyproject.toml`, creates a git tag if it doesn't exist, then publishes to PyPI via trusted publishing (OIDC)
- Requires `contents: write` and `id-token: write` permissions

### `unit_tests.yml`
- Runs on push and PR to main

### `live_tests.yml`
- Manual trigger, requires repository secrets for credentials

## Version Management

- Version is defined in **two places** that must stay in sync:
  1. `pyproject.toml` → `version = "x.y.z"`
  2. `src/pysensorlinx/__init__.py` → `__version__ = "x.y.z"`
- The CI workflow reads from `pyproject.toml` for auto-tagging.

## Dependencies

- **Runtime:** `aiohttp` (>=3.11.12), `glom` (for nested dict access)
- **Test:** `pytest`, `pytest-asyncio`, `aioresponses`, `python-dotenv`

## HVAC Domain Knowledge

The HBX ECO-0600 is a heat pump staging controller for hydronic (water-based) heating/cooling systems:

- **Outdoor Reset:** When enabled, the controller linearly interpolates the tank target temperature between `mbt` (min, at mild weather) and `dbt` (max, at the design outdoor temp `dot`). When disabled (`dot = -41`), a single fixed target is used.
- **Weather Shutdown:** `wwsd` (warm weather) and `cwsd` (cold weather) define outdoor temps at which heating/cooling shuts off entirely.
- **Stages:** Up to 16 heat pump stages can be managed with configurable lag times, rotation, and sequencing.
- **Backup:** An auxiliary/backup heat source with its own differential, outdoor temp lockout, and tank temp lockout.
- **Demands:** Heat demand (`hd`), cool demand (`cd`), and domestic hot water (`dhw`) are independent demand channels.
- **Temperature sensors:** Up to 4 sensor inputs (tank, outdoor, and two auxiliary). Accessed via `tB1`–`tB4` (raw) or the `temperatures` array (structured).

## Development Environment

- **OS:** Windows
- **Python venv:** `.venv/` at project root
- **Activate:** `.venv/Scripts/python.exe`
- **Install dev deps:** `pip install -e ".[tests]"`

## Style & Conventions

- All API methods on `SensorlinxDevice` are `async`.
- Getters accept an optional `device_info` dict parameter to avoid redundant API calls.
- The `_get_parameter()` and `_get_temperature_parameter()` internal methods handle fetching and type conversion.
- Don't use popup/quickpick questions — ask plainly in chat if clarification is needed.
