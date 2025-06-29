import pytest
from unittest.mock import AsyncMock
import datetime
from pysensorlinx import Sensorlinx, SensorlinxDevice, Temperature

@pytest.mark.asyncio
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

@pytest.mark.asyncio
async def test_get_firmware_version_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"firmVer": 2.07}
    # Patch _get_device_info_value to ensure delegation
    device._get_device_info_value = AsyncMock(return_value=2.07)
    result = await device.get_firmware_version(device_info)
    device._get_device_info_value.assert_awaited_once_with("firmVer", device_info)
    assert result == 2.07

@pytest.mark.asyncio
async def test_get_sync_code_smoke():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(sensorlinx, "building123", "device456")
    device_info = {"syncCode": "ABC123"}
    device._get_device_info_value = AsyncMock(return_value="ABC123")
    result = await device.get_sync_code(device_info)
    device._get_device_info_value.assert_awaited_once_with("syncCode", device_info)
    assert result == "ABC123"
    
@pytest.mark.asyncio
async def test_get_device_pin_smoke():
  sensorlinx = Sensorlinx()
  device = SensorlinxDevice(sensorlinx, "building123", "device456")
  device_info = {"production": {"pin": "1234"}}
  # Patch _get_device_info_value to simulate correct key lookup
  device._get_device_info_value = AsyncMock(return_value="1234")
  result = await device.get_device_pin(device_info)
  device._get_device_info_value.assert_awaited_once_with("production.pin", device_info)
  assert result == "1234"
  
  
@pytest.mark.asyncio
async def test_get_device_type_smoke():
  sensorlinx = Sensorlinx()
  device = SensorlinxDevice(sensorlinx, "building123", "device456")
  device_info = {"deviceType": "ECO"}
  device._get_device_info_value = AsyncMock(return_value="ECO")
  result = await device.get_device_type(device_info)
  device._get_device_info_value.assert_awaited_once_with("deviceType", device_info)
  assert result == "ECO"

@pytest.mark.asyncio
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
                    
@pytest.mark.asyncio
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