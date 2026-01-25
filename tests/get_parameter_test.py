import pytest
from unittest.mock import AsyncMock
import datetime
from pysensorlinx import Sensorlinx, SensorlinxDevice, Temperature
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
async def test_get_rotate_cycles_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"rotCy": 4}
    device._get_device_info_value = AsyncMock(return_value=4)
    result = await device.get_rotate_cycles(device_info)
    device._get_device_info_value.assert_awaited_once_with("rotCy", device_info)
    assert result == 4

@pytest.mark.get_params
async def test_get_rotate_time_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"rotTi": 12}
    device._get_device_info_value = AsyncMock(return_value=12)
    result = await device.get_rotate_time(device_info)
    device._get_device_info_value.assert_awaited_once_with("rotTi", device_info)
    assert result == 12

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
async def test_get_warm_weather_shutdown_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"wwsd": 75}
    device._get_device_info_value = AsyncMock(return_value=75)
    result = await device.get_warm_weather_shutdown(device_info)
    device._get_device_info_value.assert_awaited_once_with("wwsd", device_info)
    assert result == 75

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
    assert result == 10

@pytest.mark.get_params
async def test_get_hot_tank_min_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"dbt": 100}
    device._get_device_info_value = AsyncMock(return_value=100)
    result = await device.get_hot_tank_min_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("dbt", device_info)
    assert result == 100

@pytest.mark.get_params
async def test_get_hot_tank_max_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"mbt": 150}
    device._get_device_info_value = AsyncMock(return_value=150)
    result = await device.get_hot_tank_max_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("mbt", device_info)
    assert result == 150

@pytest.mark.get_params
async def test_get_cold_weather_shutdown_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"cwsd": 40}
    device._get_device_info_value = AsyncMock(return_value=40)
    result = await device.get_cold_weather_shutdown(device_info)
    device._get_device_info_value.assert_awaited_once_with("cwsd", device_info)
    assert result == 40

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
    assert result == 8

@pytest.mark.get_params
async def test_get_cold_tank_min_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"dst": 45}
    device._get_device_info_value = AsyncMock(return_value=45)
    result = await device.get_cold_tank_min_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("dst", device_info)
    assert result == 45

@pytest.mark.get_params
async def test_get_cold_tank_max_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"mst": 55}
    device._get_device_info_value = AsyncMock(return_value=55)
    result = await device.get_cold_tank_max_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("mst", device_info)
    assert result == 55

@pytest.mark.get_params
async def test_get_backup_lag_time_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkLag": 20}
    device._get_device_info_value = AsyncMock(return_value=20)
    result = await device.get_backup_lag_time(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkLag", device_info)
    assert result == 20

@pytest.mark.get_params
async def test_get_backup_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkTemp": 30}
    device._get_device_info_value = AsyncMock(return_value=30)
    result = await device.get_backup_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkTemp", device_info)
    assert result == 30

@pytest.mark.get_params
async def test_get_backup_differential_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkDif": 5}
    device._get_device_info_value = AsyncMock(return_value=5)
    result = await device.get_backup_differential(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkDif", device_info)
    assert result == 5

@pytest.mark.get_params
async def test_get_backup_only_outdoor_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkOd": 10}
    device._get_device_info_value = AsyncMock(return_value=10)
    result = await device.get_backup_only_outdoor_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkOd", device_info)
    assert result == 10

@pytest.mark.get_params
async def test_get_backup_only_tank_temp_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"bkTk": 120}
    device._get_device_info_value = AsyncMock(return_value=120)
    result = await device.get_backup_only_tank_temp(device_info)
    device._get_device_info_value.assert_awaited_once_with("bkTk", device_info)
    assert result == 120

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