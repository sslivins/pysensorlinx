import pytest
from unittest.mock import AsyncMock
import datetime
from pysensorlinx import Sensorlinx, SensorlinxDevice, Temperature, TemperatureDelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@pytest.mark.get_params
@pytest.mark.parametrize(
  "device_info, key, get_devices_side_effect, expected_result, expected_exception, expected_message",
  [
    # Key present in device_info
    ({"foo": "bar"}, "foo", None, "bar", None, None),
    # Key present as dotted path
    ({"parent": {"child": "val"}}, "parent.child", None, "val", None, None),
    # Key missing in device_info
    ({"foo": "bar"}, "baz", None, None, RuntimeError, "baz not found."),
    # Value is None
    ({"foo": None}, "foo", None, None, RuntimeError, "foo not found."),
    # device_info is None, get_devices returns dict with key
    (None, "foo", {"foo": "bar"}, "bar", None, None),
    # device_info is None, get_devices returns dict without key
    (None, "foo", {"baz": "qux"}, None, RuntimeError, "foo not found."),
    # device_info is None, get_devices returns None
    (None, "foo", None, None, RuntimeError, "Device info not found."),
    # device_info is None, get_devices returns empty dict
    (None, "foo", {}, None, RuntimeError, "Device info not found."),
    # device_info is None, get_devices raises exception
    (None, "foo", Exception("network error"), None, RuntimeError, "Failed to fetch device info: network error"),
  ]
)
async def test_get_device_info_value_cases(device_info, key, get_devices_side_effect, expected_result, expected_exception, expected_message):
  sensorlinx = Sensorlinx()
  device = SensorlinxDevice(sensorlinx, "building123", "device456")

  # Patch get_devices if needed
  if device_info is None:
    if isinstance(get_devices_side_effect, Exception):
      sensorlinx.get_devices = AsyncMock(side_effect=get_devices_side_effect)
    else:
      sensorlinx.get_devices = AsyncMock(return_value=get_devices_side_effect)
    call_device_info = None
  else:
    call_device_info = device_info

  if expected_exception:
    with pytest.raises(expected_exception, match=expected_message):
      await device._get_device_info_value(key, call_device_info)
  else:
    result = await device._get_device_info_value(key, call_device_info)
    assert result == expected_result
    
@pytest.mark.get_params
async def test_get_permanent_heat_demand_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"permHD": True}
    device._get_device_info_value = AsyncMock(return_value=True)
    result = await device.get_permanent_heat_demand(device_info)
    device._get_device_info_value.assert_awaited_once_with("permHD", device_info)
    assert result is True

@pytest.mark.get_params
async def test_get_permanent_cool_demand_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"permCD": True}
    device._get_device_info_value = AsyncMock(return_value=True)
    result = await device.get_permanent_cool_demand(device_info)
    device._get_device_info_value.assert_awaited_once_with("permCD", device_info)
    assert result is True

@pytest.mark.get_params
async def test_get_hvac_mode_priority_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"prior": "auto"}
    device._get_device_info_value = AsyncMock(return_value="auto")
    result = await device.get_hvac_mode_priority(device_info)
    device._get_device_info_value.assert_awaited_once_with("prior", device_info)
    assert result == "auto"

@pytest.mark.get_params
async def test_get_weather_shutdown_lag_time_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"wwTime": 10}
    device._get_device_info_value = AsyncMock(return_value=10)
    result = await device.get_weather_shutdown_lag_time(device_info)
    device._get_device_info_value.assert_awaited_once_with("wwTime", device_info)
    assert result == 10

@pytest.mark.get_params
async def test_get_heat_cool_switch_delay_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"hpSw": 60}
    device._get_device_info_value = AsyncMock(return_value=60)
    result = await device.get_heat_cool_switch_delay(device_info)
    device._get_device_info_value.assert_awaited_once_with("hpSw", device_info)
    assert result == 60

@pytest.mark.get_params
async def test_get_wide_priority_differential_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"wPDif": False}
    device._get_device_info_value = AsyncMock(return_value=False)
    result = await device.get_wide_priority_differential(device_info)
    device._get_device_info_value.assert_awaited_once_with("wPDif", device_info)
    assert result is False

@pytest.mark.get_params
async def test_get_number_of_stages_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"numStg": 2}
    device._get_device_info_value = AsyncMock(return_value=2)
    result = await device.get_number_of_stages(device_info)
    device._get_device_info_value.assert_awaited_once_with("numStg", device_info)
    assert result == 2

@pytest.mark.get_params
async def test_get_two_stage_heat_pump_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"twoS": True}
    device._get_device_info_value = AsyncMock(return_value=True)
    result = await device.get_two_stage_heat_pump(device_info)
    device._get_device_info_value.assert_awaited_once_with("twoS", device_info)
    assert result is True

@pytest.mark.get_params
async def test_get_stage_on_lag_time_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"lagT": 5}
    device._get_device_info_value = AsyncMock(return_value=5)
    result = await device.get_stage_on_lag_time(device_info)
    device._get_device_info_value.assert_awaited_once_with("lagT", device_info)
    assert result == 5

@pytest.mark.get_params
async def test_get_stage_off_lag_time_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"lagOff": 3}
    device._get_device_info_value = AsyncMock(return_value=3)
    result = await device.get_stage_off_lag_time(device_info)
    device._get_device_info_value.assert_awaited_once_with("lagOff", device_info)
    assert result == 3

@pytest.mark.get_params
@pytest.mark.parametrize(
    "raw_value, expected_result",
    [
        # Value is 0, should return 'off'
        (0, 'off'),
        # Normal values, should return the integer
        (4, 4),
        (1, 1),
        (240, 240),
    ]
)
async def test_get_rotate_cycles(raw_value, expected_result):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"rotCy": raw_value}
    device._get_device_info_value = AsyncMock(return_value=raw_value)
    result = await device.get_rotate_cycles(device_info)
    device._get_device_info_value.assert_awaited_once_with("rotCy", device_info)
    assert result == expected_result

@pytest.mark.get_params
@pytest.mark.parametrize("api_value,expected", [
    (0, 'off'),      # 0 means disabled
    (12, 12),        # normal value
    (1, 1),          # minimum enabled value
    (240, 240),      # maximum value
])
async def test_get_rotate_time(api_value, expected):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"rotTi": api_value}
    device._get_device_info_value = AsyncMock(return_value=api_value)
    result = await device.get_rotate_time(device_info)
    device._get_device_info_value.assert_awaited_once_with("rotTi", device_info)
    assert result == expected

@pytest.mark.get_params
async def test_get_off_staging_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"hpStg": True}
    device._get_device_info_value = AsyncMock(return_value=True)
    result = await device.get_off_staging(device_info)
    device._get_device_info_value.assert_awaited_once_with("hpStg", device_info)
    assert result is True

@pytest.mark.get_params
@pytest.mark.parametrize(
    "raw_value, expected_result",
    [
        # Value is 32, should return 'off'
        (32, 'off'),
        # Normal value, should return Temperature object
        (75, Temperature(75, 'F')),
        (34, Temperature(34, 'F')),
        (180, Temperature(180, 'F')),
    ]
)
async def test_get_warm_weather_shutdown(raw_value, expected_result):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"wwsd": raw_value}
    device._get_device_info_value = AsyncMock(return_value=raw_value)
    result = await device.get_warm_weather_shutdown(device_info)
    device._get_device_info_value.assert_awaited_once_with("wwsd", device_info)
    if expected_result == 'off':
        assert result == 'off'
    else:
        assert isinstance(result, Temperature)
        assert result.value == expected_result.value
        assert result.unit == expected_result.unit

@pytest.mark.get_params
@pytest.mark.parametrize(
    "raw_value, expected_result",
    [
        # Value is -41, should return 'off'
        (-41, 'off'),
        # Normal value, should return Temperature object
        (60, Temperature(60, 'F')),
        (0, Temperature(0, 'F')),
        (-40, Temperature(-40, 'F')),
    ]
)
async def test_get_hot_tank_outdoor_reset(raw_value, expected_result):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"dot": raw_value}
    device._get_device_info_value = AsyncMock(return_value=raw_value)
    result = await device.get_hot_tank_outdoor_reset(device_info)
    device._get_device_info_value.assert_awaited_once_with("dot", device_info)
    if expected_result == 'off':
        assert result == 'off'
    else:
        assert isinstance(result, Temperature)
        assert result.value == expected_result.value
        assert result.unit == expected_result.unit

@pytest.mark.get_params
async def test_get_hot_tank_differential_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"htDif": 10}
    device._get_device_info_value = AsyncMock(return_value=10)
    result = await device.get_hot_tank_differential(device_info)
    device._get_device_info_value.assert_awaited_once_with("htDif", device_info)
    assert isinstance(result, TemperatureDelta)
    assert result.value == 10
    assert result.unit == 'F'

@pytest.mark.get_params
async def test_get_hot_tank_min_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"mbt": 100}
    device._get_device_info_value = AsyncMock(return_value=100)
    result = await device.get_hot_tank_min_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("mbt", device_info)
    assert isinstance(result, Temperature)
    assert result.value == 100
    assert result.unit == 'F'

@pytest.mark.get_params
async def test_get_hot_tank_max_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"dbt": 150}
    device._get_device_info_value = AsyncMock(return_value=150)
    result = await device.get_hot_tank_max_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("dbt", device_info)
    assert isinstance(result, Temperature)
    assert result.value == 150
    assert result.unit == 'F'

@pytest.mark.get_params
@pytest.mark.parametrize(
    "raw_value, expected_result",
    [
        # Value is 32, should return 'off'
        (32, 'off'),
        # Normal value, should return Temperature object
        (40, Temperature(40, 'F')),
        (33, Temperature(33, 'F')),
        (119, Temperature(119, 'F')),
    ]
)
async def test_get_cold_weather_shutdown(raw_value, expected_result):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"cwsd": raw_value}
    device._get_device_info_value = AsyncMock(return_value=raw_value)
    result = await device.get_cold_weather_shutdown(device_info)
    device._get_device_info_value.assert_awaited_once_with("cwsd", device_info)
    if expected_result == 'off':
        assert result == 'off'
    else:
        assert isinstance(result, Temperature)
        assert result.value == expected_result.value
        assert result.unit == expected_result.unit

@pytest.mark.get_params
@pytest.mark.parametrize(
    "raw_value, expected_result",
    [
        # Value is -41, should return 'off'
        (-41, 'off'),
        # Normal value, should return Temperature object
        (50, Temperature(50, 'F')),
        (0, Temperature(0, 'F')),
        (-40, Temperature(-40, 'F')),
    ]
)
async def test_get_cold_tank_outdoor_reset(raw_value, expected_result):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"cdot": raw_value}
    device._get_device_info_value = AsyncMock(return_value=raw_value)
    result = await device.get_cold_tank_outdoor_reset(device_info)
    device._get_device_info_value.assert_awaited_once_with("cdot", device_info)
    if expected_result == 'off':
        assert result == 'off'
    else:
        assert isinstance(result, Temperature)
        assert result.value == expected_result.value
        assert result.unit == expected_result.unit

@pytest.mark.get_params
async def test_get_cold_tank_differential_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"clDif": 8}
    device._get_device_info_value = AsyncMock(return_value=8)
    result = await device.get_cold_tank_differential(device_info)
    device._get_device_info_value.assert_awaited_once_with("clDif", device_info)
    assert isinstance(result, TemperatureDelta)
    assert result.value == 8
    assert result.unit == 'F'

@pytest.mark.get_params
async def test_get_cold_tank_min_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"mst": 45}
    device._get_device_info_value = AsyncMock(return_value=45)
    result = await device.get_cold_tank_min_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("mst", device_info)
    assert isinstance(result, Temperature)
    assert result.value == 45
    assert result.unit == 'F'

@pytest.mark.get_params
async def test_get_cold_tank_max_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"dst": 55}
    device._get_device_info_value = AsyncMock(return_value=55)
    result = await device.get_cold_tank_max_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("dst", device_info)
    assert isinstance(result, Temperature)
    assert result.value == 55
    assert result.unit == 'F'

@pytest.mark.get_params
@pytest.mark.parametrize("api_value,expected", [
    (0, 'off'),      # 0 means disabled
    (20, 20),        # normal value
    (1, 1),          # minimum enabled value
    (240, 240),      # maximum value
])
async def test_get_backup_lag_time(api_value, expected):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkLag": api_value}
    device._get_device_info_value = AsyncMock(return_value=api_value)
    result = await device.get_backup_lag_time(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkLag", device_info)
    assert result == expected

@pytest.mark.get_params
@pytest.mark.parametrize("api_value,expected", [
    (0, 'off'),      # 0 means disabled
    (30, Temperature(30, 'F')),        # normal value
    (2, Temperature(2, 'F')),          # minimum enabled value
    (100, Temperature(100, 'F')),      # maximum value
])
async def test_get_backup_temp(api_value, expected):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkTemp": api_value}
    device._get_device_info_value = AsyncMock(return_value=api_value)
    result = await device.get_backup_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkTemp", device_info)
    if expected == 'off':
        assert result == 'off'
    else:
        assert isinstance(result, Temperature)
        assert result.value == expected.value
        assert result.unit == expected.unit

@pytest.mark.get_params
@pytest.mark.parametrize("api_value,expected", [
    (0, 'off'),      # 0 means disabled
    (5, TemperatureDelta(5, 'F')),          # normal value
    (2, TemperatureDelta(2, 'F')),          # minimum enabled value
    (100, TemperatureDelta(100, 'F')),      # maximum value
])
async def test_get_backup_differential(api_value, expected):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkDif": api_value}
    device._get_device_info_value = AsyncMock(return_value=api_value)
    result = await device.get_backup_differential(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkDif", device_info)
    if expected == 'off':
        assert result == 'off'
    else:
        assert isinstance(result, TemperatureDelta)
        assert result.value == expected.value
        assert result.unit == expected.unit

@pytest.mark.get_params
@pytest.mark.parametrize("api_value,expected", [
    (-41, 'off'),    # -41 means disabled
    (10, Temperature(10, 'F')),        # normal value
    (-40, Temperature(-40, 'F')),      # minimum enabled value
    (127, Temperature(127, 'F')),      # maximum value
])
async def test_get_backup_only_outdoor_temp(api_value, expected):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkOd": api_value}
    device._get_device_info_value = AsyncMock(return_value=api_value)
    result = await device.get_backup_only_outdoor_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkOd", device_info)
    if expected == 'off':
        assert result == 'off'
    else:
        assert isinstance(result, Temperature)
        assert result.value == expected.value
        assert result.unit == expected.unit

@pytest.mark.get_params
@pytest.mark.parametrize("api_value,expected", [
    (32, 'off'),     # 32 means disabled
    (120, Temperature(120, 'F')),      # normal value
    (33, Temperature(33, 'F')),        # minimum enabled value
    (200, Temperature(200, 'F')),      # maximum value
])
async def test_get_backup_only_tank_temp(api_value, expected):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkTk": api_value}
    device._get_device_info_value = AsyncMock(return_value=api_value)
    result = await device.get_backup_only_tank_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkTk", device_info)
    if expected == 'off':
        assert result == 'off'
    else:
        assert isinstance(result, Temperature)
        assert result.value == expected.value
        assert result.unit == expected.unit

@pytest.mark.get_params
async def test_get_firmware_version_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"firmVer": 2.07}
    # Patch _get_device_info_value to ensure delegation
    device._get_device_info_value = AsyncMock(return_value=2.07)
    result = await device.get_firmware_version(device_info)
    device._get_device_info_value.assert_awaited_once_with("firmVer", device_info)
    assert result == 2.07

@pytest.mark.get_params
async def test_get_sync_code_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"syncCode": "ABC123"}
    device._get_device_info_value = AsyncMock(return_value="ABC123")
    result = await device.get_sync_code(device_info)
    device._get_device_info_value.assert_awaited_once_with("syncCode", device_info)
    assert result == "ABC123"
    
@pytest.mark.get_params
async def test_get_device_pin_smoke():
  sensorlinx = Sensorlinx()
  device = SensorlinxDevice(sensorlinx, "building123", "device456")
  device_info = {"production": {"pin": "1234"}}
  # Patch _get_device_info_value to simulate correct key lookup
  device._get_device_info_value = AsyncMock(return_value="1234")
  result = await device.get_device_pin(device_info)
  device._get_device_info_value.assert_awaited_once_with("production.pin", device_info)
  assert result == "1234"
  
  
@pytest.mark.get_params
async def test_get_device_type_smoke():
  sensorlinx = Sensorlinx()
  device = SensorlinxDevice(sensorlinx, "building123", "device456")
  device_info = {"deviceType": "ECO"}
  device._get_device_info_value = AsyncMock(return_value="ECO")
  result = await device.get_device_type(device_info)
  device._get_device_info_value.assert_awaited_once_with("deviceType", device_info)
  assert result == "ECO"

@pytest.mark.get_params
@pytest.mark.parametrize(
    "device_info, get_devices_side_effect, expected_result, expected_exception, expected_message",
    [
        # device_info provided, valid temps
        (
            {"temps": {"temp1": {"actual": 67.5, "target": 70.0, "title": "TANK"}}},
            None,
            {"TANK": {"actual": Temperature(67.5, "F"), "target": Temperature(70.0, "F")}},
            None,
            None,
        ),
        # device_info provided, missing temps
        (
            {},
            None,
            {},
            RuntimeError,
            "Device info not found.",
        ),
        # device_info is None, get_devices returns valid temps
        (
            None,
            {"temps": {"temp2": {"actual": 58.1, "target": None, "title": "OUTDOOR"}}},
            {"OUTDOOR": {"actual": Temperature(58.1, "F"), "target": None}},
            None,
            None,
        ),
        # device_info is None, get_devices returns None
        (
            None,
            None,
            None,
            RuntimeError,
            "Device info not found.",
        ),
        # device_info is None, get_devices raises exception
        (
            None,
            Exception("network error"),
            None,
            RuntimeError,
            "Failed to fetch device info: network error",
        ),
    ]
)
async def test_get_temperatures_cases(device_info, get_devices_side_effect, expected_result, expected_exception, expected_message):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    # Patch get_devices if needed
    if device_info is None:
        if isinstance(get_devices_side_effect, Exception):
            sensorlinx.get_devices = AsyncMock(side_effect=get_devices_side_effect)
        else:
            sensorlinx.get_devices = AsyncMock(return_value=get_devices_side_effect)
        call_device_info = None
    else:
        call_device_info = device_info

    if expected_exception:
        with pytest.raises(expected_exception, match=expected_message):
            await device.get_temperatures(device_info=call_device_info)
    else:
        result = await device.get_temperatures(device_info=call_device_info)
        # Compare keys and values (Temperature objects) for equality
        assert result.keys() == expected_result.keys()
        for k in result:
            for subk in result[k]:
                if isinstance(result[k][subk], Temperature):
                    assert result[k][subk].value == expected_result[k][subk].value
                else:
                    assert result[k][subk] == expected_result[k][subk]
                    
@pytest.mark.get_params
@pytest.mark.parametrize(
    "device_info, get_devices_side_effect, expected_result, expected_exception, expected_message",
    [
        # Success: all values present and valid
        (
            {
                "stgRun": ["1:15", "0:45", "2:00"],
                "numStg": 3,
                "bkRun": "5:30"
            },
            None,
            {
                "stages": [
                    datetime.timedelta(hours=1, minutes=15),
                    datetime.timedelta(hours=0, minutes=45),
                    datetime.timedelta(hours=2, minutes=0)
                ],
                "backup": datetime.timedelta(hours=5, minutes=30)
            },
            None,
            None,
        ),
        # Success: backup runtime missing
        (
            {
                "stgRun": ["0:30", "0:30"],
                "numStg": 2
            },
            None,
            {
                "stages": [
                    datetime.timedelta(hours=0, minutes=30),
                    datetime.timedelta(hours=0, minutes=30)
                ]
            },
            None,
            None,
        ),
        # Success: fewer runtimes than stages (should fill with 0:00)
        (
            {
                "stgRun": ["0:10"],
                "numStg": 2,
                "bkRun": "0:05"
            },
            None,
            {
                "stages": [
                    datetime.timedelta(hours=0, minutes=10),
                    datetime.timedelta(hours=0, minutes=0)
                ],
                "backup": datetime.timedelta(hours=0, minutes=5)
            },
            None,
            None,
        ),
        # Failure: stgRun not a list
        (
            {
                "stgRun": "1:00",
                "numStg": 1,
                "bkRun": "0:10"
            },
            None,
            None,
            RuntimeError,
            "Stage runtimes must be a list.",
        ),
        # Failure: numStg out of range
        (
            {
                "stgRun": ["0:10"],
                "numStg": 0,
                "bkRun": "0:05"
            },
            None,
            None,
            RuntimeError,
            "Number of stages must be between 1 and 16.",
        ),
        # Failure: device_info is None, get_devices returns None
        (
            None,
            None,
            None,
            RuntimeError,
            "Device info not found.",
        ),
        # Failure: get_devices raises exception
        (
            None,
            Exception("network error"),
            None,
            RuntimeError,
            "Failed to fetch device info: network error",
        ),
        # Failure: numStg out of range (too high)
        (
            {
                "stgRun": ["0:10", "0:20", "0:30", "0:40", "0:50"],
                "numStg": 20,
                "bkRun": "0:05"
            },
            None,
            None,
            RuntimeError,
            "Number of stages must be between 1 and 16.",
        ),        
    ]
)
async def test_get_runtimes_cases(device_info, get_devices_side_effect, expected_result, expected_exception, expected_message):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    # Patch get_devices if needed
    if device_info is None:
        if isinstance(get_devices_side_effect, Exception):
            sensorlinx.get_devices = AsyncMock(side_effect=get_devices_side_effect)
        else:
            sensorlinx.get_devices = AsyncMock(return_value=get_devices_side_effect)
        call_device_info = None
    else:
        call_device_info = device_info

    if expected_exception:
        with pytest.raises(expected_exception, match=expected_message):
            await device.get_runtimes(device_info=call_device_info)
    else:
        result = await device.get_runtimes(device_info=call_device_info)
        assert "stages" in result
        assert all(isinstance(x, datetime.timedelta) for x in result["stages"])
        assert result["stages"] == expected_result["stages"]
        if "backup" in expected_result:
            assert result["backup"] == expected_result["backup"]
        else:
            assert "backup" not in result

@pytest.mark.get_params
async def test_get_dhw_enabled_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"dhwOn": 1}
    device._get_device_info_value = AsyncMock(return_value=1)
    result = await device.get_dhw_enabled(device_info)
    device._get_device_info_value.assert_awaited_once_with("dhwOn", device_info)
    assert result is True

@pytest.mark.get_params
async def test_get_dhw_enabled_false():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"dhwOn": 0}
    device._get_device_info_value = AsyncMock(return_value=0)
    result = await device.get_dhw_enabled(device_info)
    assert result is False

@pytest.mark.get_params
async def test_get_dhw_differential_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"auxDif": 3}
    device._get_device_info_value = AsyncMock(return_value=3)
    result = await device.get_dhw_differential(device_info)
    device._get_device_info_value.assert_awaited_once_with("auxDif", device_info)
    assert isinstance(result, TemperatureDelta)
    assert result.to_fahrenheit() == 3

@pytest.mark.get_params
async def test_get_dhw_target_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"dhwT": 120}
    device._get_device_info_value = AsyncMock(return_value=120)
    result = await device.get_dhw_target_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("dhwT", device_info)
    assert isinstance(result, Temperature)
    assert result.to_fahrenheit() == 120

@pytest.mark.get_params
@pytest.mark.parametrize(
    "device_info, get_devices_side_effect, expected_result, expected_exception, expected_message",
    [
        # Success: all three demands present
        (
            {"demands": [
                {"name": "hd", "title": "Heat", "enabled": True, "activated": True},
                {"name": "cd", "title": "Cool", "enabled": True, "activated": False},
                {"name": "dhw", "title": "DHW", "enabled": True, "activated": False},
            ]},
            None,
            [
                {"activated": True, "enabled": True, "name": "hd", "title": "Heat"},
                {"activated": False, "enabled": True, "name": "cd", "title": "Cool"},
                {"activated": False, "enabled": True, "name": "dhw", "title": "DHW"},
            ],
            None,
            None,
        ),
        # Success: single demand
        (
            {"demands": [
                {"name": "hd", "title": "Heat", "enabled": True, "activated": False},
            ]},
            None,
            [
                {"activated": False, "enabled": True, "name": "hd", "title": "Heat"},
            ],
            None,
            None,
        ),
        # Success: missing optional fields get defaults
        (
            {"demands": [
                {"name": "hd"},
            ]},
            None,
            [
                {"activated": False, "enabled": False, "name": "hd", "title": ""},
            ],
            None,
            None,
        ),
        # Failure: demands not a list
        (
            {"demands": {"name": "hd"}},
            None,
            None,
            RuntimeError,
            "Demands data must be a list.",
        ),
        # Failure: device_info is None, get_devices returns None
        (
            None,
            None,
            None,
            RuntimeError,
            "Device info not found.",
        ),
        # Failure: get_devices raises exception
        (
            None,
            Exception("network error"),
            None,
            RuntimeError,
            "Failed to fetch device info: network error",
        ),
    ]
)
async def test_get_demands_cases(device_info, get_devices_side_effect, expected_result, expected_exception, expected_message):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    if device_info is None:
        if isinstance(get_devices_side_effect, Exception):
            sensorlinx.get_devices = AsyncMock(side_effect=get_devices_side_effect)
        else:
            sensorlinx.get_devices = AsyncMock(return_value=get_devices_side_effect)
        call_device_info = None
    else:
        call_device_info = device_info

    if expected_exception:
        with pytest.raises(expected_exception, match=expected_message):
            await device.get_demands(device_info=call_device_info)
    else:
        result = await device.get_demands(device_info=call_device_info)
        assert result == expected_result

@pytest.mark.get_params
@pytest.mark.parametrize(
    "device_info, get_devices_side_effect, expected_result, expected_exception, expected_message",
    [
        # Success: DHW present and enabled
        (
            {"demands": [
                {"name": "hd", "title": "Heat", "enabled": True, "activated": True},
                {"name": "cd", "title": "Cool", "enabled": True, "activated": False},
                {"name": "dhw", "title": "DHW", "enabled": True, "activated": False},
            ]},
            None,
            {"activated": False, "enabled": True, "title": "DHW"},
            None,
            None,
        ),
        # Success: DHW activated
        (
            {"demands": [
                {"name": "dhw", "title": "DHW", "enabled": True, "activated": True},
            ]},
            None,
            {"activated": True, "enabled": True, "title": "DHW"},
            None,
            None,
        ),
        # Failure: demands not a list
        (
            {"demands": {"name": "dhw"}},
            None,
            None,
            RuntimeError,
            "Demands data must be a list.",
        ),
        # Failure: dhw entry missing from demands
        (
            {"demands": [
                {"name": "hd", "title": "Heat", "enabled": True, "activated": False},
            ]},
            None,
            None,
            RuntimeError,
            "DHW demand not found.",
        ),
        # Failure: device_info is None, get_devices returns None
        (
            None,
            None,
            None,
            RuntimeError,
            "Device info not found.",
        ),
        # Failure: get_devices raises exception
        (
            None,
            Exception("network error"),
            None,
            RuntimeError,
            "Failed to fetch device info: network error",
        ),
    ]
)
async def test_get_dhw_state_cases(device_info, get_devices_side_effect, expected_result, expected_exception, expected_message):
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    if device_info is None:
        if isinstance(get_devices_side_effect, Exception):
            sensorlinx.get_devices = AsyncMock(side_effect=get_devices_side_effect)
        else:
            sensorlinx.get_devices = AsyncMock(return_value=get_devices_side_effect)
        call_device_info = None
    else:
        call_device_info = device_info

    if expected_exception:
        with pytest.raises(expected_exception, match=expected_message):
            await device.get_dhw_state(device_info=call_device_info)
    else:
        result = await device.get_dhw_state(device_info=call_device_info)
        assert result == expected_result

FULL_DEVICE_INFO = {
    "demands": [
        {"name": "hd", "title": "Heat", "enabled": True, "activated": True},
        {"name": "cd", "title": "Cool", "enabled": True, "activated": False},
        {"name": "dhw", "title": "DHW", "enabled": True, "activated": False},
    ],
    "temperatures": [
        {
            "activated": True, "activatedColor": "green", "activatedState": "satisfied",
            "current": 107.7, "enabled": True, "target": 103.2,
            "title": "Tank", "type": "single",
            "priority": {"enabled": True, "title": "Heating", "type": "hot"},
        },
        {
            "activated": False, "activatedColor": None, "activatedState": None,
            "current": None, "enabled": False, "target": None,
            "title": None, "type": None,
            "priority": {"enabled": False, "title": "Heating", "type": "hot"},
        },
        {
            "activated": False, "activatedColor": None, "activatedState": None,
            "current": 49.6, "enabled": True, "target": None,
            "title": "Outdoor", "type": "outdoor",
            "priority": {"enabled": False, "title": "Heating", "type": "hot"},
        },
        {
            "activated": False, "activatedColor": None, "activatedState": None,
            "current": 121.6, "enabled": True, "target": 119,
            "title": "DHW Tank", "type": "dhw",
            "priority": {"enabled": False, "title": "Heating", "type": "hot"},
        },
    ],
    "stages": [
        {"activated": False, "device": "AECO-0982", "enabled": True,
         "index": 1, "runTime": "3455:32", "title": "Stage 1"},
    ],
    "backup": {"activated": False, "enabled": False, "runTime": "65535:00", "title": "Backup"},
    "pumps": [
        {"activated": False, "title": "Pump 1"},
        {"activated": False, "title": "Pump 2"},
    ],
    "pmp1Set": 1,
    "pmp2Set": 3,
    "reversingValve": {"activated": False, "title": "Reversing Valve"},
    "wsd": {
        "wwsd": {"activated": False, "title": "WWSD"},
        "cwsd": {"activated": False, "title": "CWSD"},
    },
}

@pytest.mark.get_params
async def test_get_system_state_full():
    """All sections present and populated."""
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    result = await device.get_system_state(device_info=FULL_DEVICE_INFO)

    # Demands
    assert len(result['demands']) == 3
    assert result['demands'][0] == {'activated': True, 'enabled': True, 'name': 'hd', 'title': 'Heat'}

    # Temperatures — disabled sensor filtered out
    assert len(result['temperatures']) == 3
    tank = result['temperatures'][0]
    assert tank['title'] == 'Tank'
    assert tank['type'] == 'single'
    assert tank['activatedState'] == 'satisfied'
    assert isinstance(tank['current'], Temperature)
    assert tank['current'].to_fahrenheit() == 107.7
    assert isinstance(tank['target'], Temperature)
    assert tank['target'].to_fahrenheit() == 103.2

    outdoor = result['temperatures'][1]
    assert outdoor['title'] == 'Outdoor'
    assert outdoor['target'] is None

    dhw_tank = result['temperatures'][2]
    assert dhw_tank['type'] == 'dhw'
    assert isinstance(dhw_tank['current'], Temperature)

    # Stages
    assert len(result['stages']) == 1
    assert result['stages'][0]['activated'] is False
    assert result['stages'][0]['title'] == 'Stage 1'

    # Backup
    assert result['backup']['activated'] is False
    assert result['backup']['enabled'] is False

    # Pumps — mode resolved from pmp1Set/pmp2Set
    assert len(result['pumps']) == 2
    assert result['pumps'][0] == {'activated': False, 'title': 'Pump 1', 'mode': 'heating'}
    assert result['pumps'][1] == {'activated': False, 'title': 'Pump 2', 'mode': 'dhw'}

    # Reversing valve
    assert result['reversingValve'] == {'activated': False, 'title': 'Reversing Valve'}

    # Weather shutdown
    assert result['weatherShutdown']['wwsd'] == {'activated': False, 'title': 'WWSD'}
    assert result['weatherShutdown']['cwsd'] == {'activated': False, 'title': 'CWSD'}


@pytest.mark.get_params
async def test_get_system_state_missing_optional_sections():
    """Sections missing from device_info return None instead of raising."""
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    minimal_info = {
        "demands": [
            {"name": "hd", "title": "Heat", "enabled": True, "activated": False},
        ],
        "stages": [
            {"activated": False, "enabled": True, "index": 1, "title": "Stage 1",
             "device": "X", "runTime": "0:00"},
        ],
        "backup": {"activated": False, "enabled": False, "title": "Backup", "runTime": "0:00"},
    }
    result = await device.get_system_state(device_info=minimal_info)

    assert result['demands'] is not None
    assert result['stages'] is not None
    assert result['backup'] is not None
    assert result['temperatures'] is None
    assert result['pumps'] is None
    assert result['reversingValve'] is None
    assert result['weatherShutdown'] is None


@pytest.mark.get_params
async def test_get_system_state_device_info_none_fetch_failure():
    """Raises RuntimeError when device_info is None and fetch fails."""
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    sensorlinx.get_devices = AsyncMock(side_effect=Exception("network error"))

    with pytest.raises(RuntimeError, match="Failed to fetch device info: network error"):
        await device.get_system_state()


@pytest.mark.get_params
async def test_get_system_state_device_info_empty():
    """Raises RuntimeError when device_info is empty."""
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    with pytest.raises(RuntimeError, match="Device info not found."):
        await device.get_system_state(device_info={})


@pytest.mark.get_params
async def test_get_system_state_pump_unknown_mode():
    """Unknown pump mode value renders as 'unknown (N)'."""
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    info = {
        "demands": [],
        "temperatures": [],
        "stages": [],
        "backup": {"activated": False, "enabled": False, "title": "Backup", "runTime": "0:00"},
        "pumps": [{"activated": True, "title": "Pump 1"}],
        "pmp1Set": 99,
        "reversingValve": {"activated": False, "title": "RV"},
        "wsd": {"wwsd": {"activated": False, "title": "WWSD"}, "cwsd": {"activated": False, "title": "CWSD"}},
    }
    result = await device.get_system_state(device_info=info)
    assert result['pumps'][0]['mode'] == 'unknown (99)'


@pytest.mark.get_params
async def test_get_dhw_state_tolerates_sparse_demand_entry():
    """Regression guard: get_dhw_state must handle an upstream DHW demand
    that is missing optional fields. If get_demands' default-supplying
    contract is ever weakened, this test will catch the resulting KeyError.
    """
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    # Upstream returns a dhw entry with only 'name' — all other fields absent.
    sparse_info = {"demands": [{"name": "dhw"}]}

    result = await device.get_dhw_state(device_info=sparse_info)
    assert result == {"activated": False, "enabled": False, "title": ""}


@pytest.mark.get_params
async def test_get_demands_supplies_defaults_for_sparse_entries():
    """Regression guard: get_demands must always return dicts with all
    four canonical keys (activated, enabled, name, title), even when the
    upstream API omits fields. get_dhw_state and get_system_state depend
    on this contract.
    """
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")

    info = {"demands": [{"name": "hd"}, {"name": "cd"}, {"name": "dhw"}]}
    result = await device.get_demands(device_info=info)

    assert len(result) == 3
    for entry in result:
        assert set(entry.keys()) == {"activated", "enabled", "name", "title"}
        assert entry["activated"] is False
        assert entry["enabled"] is False
        assert entry["title"] == ""


SAMPLE_BUILDING_INFO= {
    "weather": {
        "weather": {
            "temp": 45.52,
            "feelsLike": 42.48,
            "min": 43.34,
            "max": 47.86,
            "pressure": 1024,
            "humidity": 89,
            "wind": 5.75,
            "windDir": 210,
            "clouds": 100,
            "snow": 0,
            "rain": 0,
            "type": "Mist",
            "description": "mist",
            "icon": "50d",
            "weatherId": 701,
        },
        "forecast": [
            {
                "time": "2026-04-03T18:00:00.000Z",
                "pop": 0,
                "snow": 0,
                "temp": 49.6,
                "min": 49.6,
                "max": 63.91,
                "description": "overcast clouds",
                "icon": "04d",
                "weatherId": 804,
            },
            {
                "time": "2026-04-04T00:00:00.000Z",
                "pop": 0,
                "snow": 0,
                "temp": 58.17,
                "min": 44.83,
                "max": 60.78,
                "description": "overcast clouds",
                "icon": "04n",
                "weatherId": 804,
            },
        ],
    }
}

@pytest.mark.get_params
async def test_get_current_weather_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    result = await device.get_current_weather(SAMPLE_BUILDING_INFO)
    assert isinstance(result["temp"], Temperature)
    assert result["temp"].to_fahrenheit() == 45.52
    assert isinstance(result["feelsLike"], Temperature)
    assert result["feelsLike"].to_fahrenheit() == 42.48
    assert result["humidity"] == 89
    assert result["pressure"] == 1024
    assert result["description"] == "mist"
    assert result["icon"] == "50d"
    assert result["weatherId"] == 701

@pytest.mark.get_params
async def test_get_current_weather_fetches_building():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    sensorlinx.get_buildings = AsyncMock(return_value=SAMPLE_BUILDING_INFO)
    result = await device.get_current_weather()
    sensorlinx.get_buildings.assert_awaited_once_with("building123")
    assert result["temp"].to_fahrenheit() == 45.52

@pytest.mark.get_params
async def test_get_current_weather_accepts_list():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    result = await device.get_current_weather([SAMPLE_BUILDING_INFO])
    assert result["temp"].to_fahrenheit() == 45.52

@pytest.mark.get_params
async def test_get_current_weather_missing_data():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    with pytest.raises(RuntimeError, match="Current weather data not found."):
        await device.get_current_weather({"weather": {}})

@pytest.mark.get_params
async def test_get_current_weather_fetch_failure():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    sensorlinx.get_buildings = AsyncMock(side_effect=Exception("network error"))
    with pytest.raises(RuntimeError, match="Failed to fetch building info: network error"):
        await device.get_current_weather()

@pytest.mark.get_params
async def test_get_forecast_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    result = await device.get_forecast(SAMPLE_BUILDING_INFO)
    assert len(result) == 2
    assert isinstance(result[0]["time"], datetime.datetime)
    assert result[0]["time"].tzinfo is not None
    assert isinstance(result[0]["temp"], Temperature)
    assert result[0]["temp"].to_fahrenheit() == 49.6
    assert result[0]["pop"] == 0
    assert result[0]["description"] == "overcast clouds"
    assert result[0]["weatherId"] == 804
    assert result[1]["temp"].to_fahrenheit() == 58.17

@pytest.mark.get_params
async def test_get_forecast_fetches_building():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    sensorlinx.get_buildings = AsyncMock(return_value=SAMPLE_BUILDING_INFO)
    result = await device.get_forecast()
    sensorlinx.get_buildings.assert_awaited_once_with("building123")
    assert len(result) == 2

@pytest.mark.get_params
async def test_get_forecast_missing_data():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    with pytest.raises(RuntimeError, match="Forecast data not found."):
        await device.get_forecast({"weather": {}})

@pytest.mark.get_params
async def test_get_forecast_not_a_list():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    with pytest.raises(RuntimeError, match="Forecast data must be a list."):
        await device.get_forecast({"weather": {"forecast": "bad"}})

@pytest.mark.get_params
async def test_get_forecast_fetch_failure():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    sensorlinx.get_buildings = AsyncMock(side_effect=Exception("timeout"))
    with pytest.raises(RuntimeError, match="Failed to fetch building info: timeout"):
        await device.get_forecast()

@pytest.mark.get_params
async def test_get_current_weather_no_weather_key():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    with pytest.raises(RuntimeError, match="Current weather data not found."):
        await device.get_current_weather({"other_key": "value"})

@pytest.mark.get_params
async def test_get_forecast_no_weather_key():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    with pytest.raises(RuntimeError, match="Forecast data not found."):
        await device.get_forecast({"other_key": "value"})

@pytest.mark.get_params
async def test_get_forecast_empty_list():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    result = await device.get_forecast({"weather": {"forecast": []}})
    assert result == []
