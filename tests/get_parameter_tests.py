import pytest
from unittest.mock import AsyncMock
from pysensorlinx import Sensorlinx, SensorlinxDevice

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