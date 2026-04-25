"""
Tests for THM/ZON device support and the ``device_for`` factory.

These tests are fixture-driven: the JSON files in ``tests/fixtures``
are sanitized dumps from real HBX cloud responses (issue #12). All
accessors under test accept ``device_info=`` so the network is never
touched.
"""
import json
import os
from unittest.mock import AsyncMock

import pytest

from pysensorlinx import (
    Sensorlinx,
    SensorlinxDevice,
    Temperature,
    ThmDevice,
    ZonDevice,
    device_for,
    DEVICE_TYPE_ECO,
    DEVICE_TYPE_THM,
    DEVICE_TYPE_ZON,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name):
    with open(os.path.join(FIXTURE_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture
def thm_info():
    return _load("device_thm_0600.json")


@pytest.fixture
def zon_info():
    return _load("device_zon_0600.json")


@pytest.fixture
def sensorlinx():
    """A bare Sensorlinx client; methods are not called by these tests."""
    return Sensorlinx()


# ---------------------------------------------------------------------------
# device_for() factory
# ---------------------------------------------------------------------------


def test_device_for_returns_thm_device(sensorlinx, thm_info):
    dev = device_for(sensorlinx, "bld-1", thm_info)
    assert isinstance(dev, ThmDevice)
    assert isinstance(dev, SensorlinxDevice)  # inheritance preserved
    assert dev.device_id == thm_info["syncCode"]
    assert dev.building_id == "bld-1"


def test_device_for_returns_zon_device(sensorlinx, zon_info):
    dev = device_for(sensorlinx, "bld-1", zon_info)
    assert isinstance(dev, ZonDevice)
    assert dev.device_id == zon_info["syncCode"]


def test_device_for_eco_falls_back_to_base(sensorlinx):
    eco_info = {"deviceType": "ECO", "syncCode": "AECO-1234"}
    dev = device_for(sensorlinx, "bld-1", eco_info)
    assert type(dev) is SensorlinxDevice  # not a subclass
    assert dev.device_id == "AECO-1234"


def test_device_for_unknown_type_falls_back_to_base(sensorlinx):
    dev = device_for(sensorlinx, "bld-1", {"deviceType": "MYSTERY", "syncCode": "X"})
    assert type(dev) is SensorlinxDevice


def test_device_for_missing_devicetype_falls_back_to_base(sensorlinx):
    dev = device_for(sensorlinx, "bld-1", {"syncCode": "X"})
    assert type(dev) is SensorlinxDevice


def test_device_for_uses_id_when_synccode_missing(sensorlinx):
    dev = device_for(sensorlinx, "bld-1", {"deviceType": "THM", "id": "raw-id"})
    assert isinstance(dev, ThmDevice)
    assert dev.device_id == "raw-id"


def test_device_for_uses_underscore_id_when_others_missing(sensorlinx):
    dev = device_for(sensorlinx, "bld-1", {"deviceType": "ZON", "_id": "mongo-id"})
    assert isinstance(dev, ZonDevice)
    assert dev.device_id == "mongo-id"


def test_device_for_rejects_non_dict(sensorlinx):
    with pytest.raises(TypeError):
        device_for(sensorlinx, "bld-1", None)
    with pytest.raises(TypeError):
        device_for(sensorlinx, "bld-1", ["not", "a", "dict"])


def test_device_for_rejects_missing_id(sensorlinx):
    with pytest.raises(ValueError):
        device_for(sensorlinx, "bld-1", {"deviceType": "THM"})


def test_device_for_devicetype_case_insensitive(sensorlinx):
    dev = device_for(sensorlinx, "bld-1", {"deviceType": "thm", "syncCode": "X"})
    assert isinstance(dev, ThmDevice)


# ---------------------------------------------------------------------------
# ThmDevice accessors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_thm_room_temperature_uses_temperature_block(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", thm_info["syncCode"])
    temp = await dev.get_room_temperature(thm_info)
    assert temp is not None
    assert temp.to_fahrenheit() == pytest.approx(56.2)


@pytest.mark.asyncio
async def test_thm_room_temperature_falls_back_to_rm(sensorlinx):
    info = {"rm": 70.0}  # no ``temperature`` block
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    temp = await dev.get_room_temperature(info)
    assert temp is not None
    assert temp.to_fahrenheit() == pytest.approx(70.0)


@pytest.mark.asyncio
async def test_thm_room_temperature_returns_none_when_missing(sensorlinx):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_room_temperature({}) is None


@pytest.mark.asyncio
async def test_thm_floor_temperature(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    temp = await dev.get_floor_temperature(thm_info)
    assert temp.to_fahrenheit() == pytest.approx(50.5)


@pytest.mark.asyncio
async def test_thm_humidity(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_humidity(thm_info) == pytest.approx(33.2)


@pytest.mark.asyncio
async def test_thm_target_temperature_returns_none_when_off(sensorlinx, thm_info):
    # Fixture has target.isOff == true
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_target_temperature(thm_info) is None
    assert await dev.is_off(thm_info) is True


@pytest.mark.asyncio
async def test_thm_target_temperature_when_active(sensorlinx):
    info = {"target": {"type": "heat", "value": 68, "isOff": False}}
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    temp = await dev.get_target_temperature(info)
    assert temp.to_fahrenheit() == pytest.approx(68)
    assert await dev.is_off(info) is False
    assert await dev.get_target_type(info) == "heat"


@pytest.mark.asyncio
async def test_thm_hvac_mode_picks_activated_changeover(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    # Fixture has the "off" entry activated.
    assert await dev.get_hvac_mode(thm_info) == "off"


@pytest.mark.asyncio
async def test_thm_hvac_mode_none_when_no_activated(sensorlinx):
    info = {"changeover": [{"key": "heat", "activated": False}]}
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_hvac_mode(info) is None


@pytest.mark.asyncio
async def test_thm_fan_mode(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    # Fixture activates "off"
    assert await dev.get_fan_mode(thm_info) == "off"


@pytest.mark.asyncio
async def test_thm_thm_mode_label(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_thm_mode(thm_info) == "Air"


@pytest.mark.asyncio
async def test_thm_away_mode(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    away = await dev.get_away_mode(thm_info)
    assert away["activated"] is False
    assert away["heatTarget"]["value"] == 50
    assert away["coolTarget"]["enabled"] is True


@pytest.mark.asyncio
async def test_thm_is_heating_cooling_flags(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    assert await dev.is_heating(thm_info) is False
    assert await dev.is_cooling(thm_info) is False


@pytest.mark.asyncio
async def test_thm_demands_returns_list(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    demands = await dev.get_demands(thm_info)
    assert len(demands) == 6
    activated = [d for d in demands if d.get("activated")]
    assert len(activated) == 1
    assert activated[0]["key"] == "satisfied"


@pytest.mark.asyncio
async def test_thm_schedules(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    schedules = await dev.get_schedules(thm_info)
    assert len(schedules) == 8
    keys = [s["key"] for s in schedules]
    assert keys == ["wkd1", "wkd2", "wkd3", "wkd4", "wke1", "wke2", "wke3", "wke4"]


@pytest.mark.asyncio
async def test_thm_name(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_name(thm_info) == "Garage"


@pytest.mark.asyncio
async def test_thm_get_temperatures_returns_room_and_floor(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    temps = await dev.get_temperatures(device_info=thm_info)
    assert "Room" in temps
    assert "Floor" in temps
    assert temps["Room"]["actual"].to_fahrenheit() == pytest.approx(56.2)
    # Fixture's target is off → None
    assert temps["Room"]["target"] is None
    assert temps["Floor"]["actual"].to_fahrenheit() == pytest.approx(50.5)


@pytest.mark.asyncio
async def test_thm_get_temperatures_by_name(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    temps = await dev.get_temperatures(temp_name="Room", device_info=thm_info)
    assert temps["actual"].to_fahrenheit() == pytest.approx(56.2)


@pytest.mark.asyncio
async def test_thm_get_temperatures_unknown_name_raises(sensorlinx, thm_info):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    with pytest.raises(RuntimeError, match="not found"):
        await dev.get_temperatures(temp_name="Nope", device_info=thm_info)


@pytest.mark.asyncio
async def test_thm_get_temperatures_no_data_raises(sensorlinx):
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    with pytest.raises(RuntimeError):
        await dev.get_temperatures(device_info={})


@pytest.mark.asyncio
async def test_thm_get_firmware_inherited(sensorlinx, thm_info):
    """The base SensorlinxDevice helpers must keep working for THM."""
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    fw = await dev.get_firmware_version(thm_info)
    assert fw == 1.22


# ---------------------------------------------------------------------------
# ZonDevice accessors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_zon_relays_16_bools(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    relays = await dev.get_relays(zon_info)
    assert len(relays) == 16
    assert all(r is False for r in relays)


@pytest.mark.asyncio
async def test_zon_relay_types(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_relay_types(zon_info) == [1, 1, 1, 0]


@pytest.mark.asyncio
async def test_zon_demands(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    demands = await dev.get_demands(zon_info)
    assert [d["abbr"] for d in demands] == ["HD", "CD2", "APP"]


@pytest.mark.asyncio
async def test_zon_pumps(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    pumps = await dev.get_pumps(zon_info)
    assert len(pumps) == 2
    assert pumps[0]["key"] == "pump1"


@pytest.mark.asyncio
async def test_zon_fancoil(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    fc = await dev.get_fancoil(zon_info)
    assert [f["key"] for f in fc] == ["heating", "cooling", "fan", "humidity"]


@pytest.mark.asyncio
async def test_zon_app_button(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    btn = await dev.get_app_button(zon_info)
    assert btn["enabled"] is True
    assert btn["activated"] is False
    assert btn["text"] == "App Button"


@pytest.mark.asyncio
async def test_zon_aux_setpoint(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    aux = await dev.get_aux_setpoint(zon_info)
    assert aux["target"] == 68
    assert aux["hasTarget"] is True
    assert aux["mode"]["title"] == "Auxiliary Setpoint"


@pytest.mark.asyncio
async def test_zon_thermostat_sync_codes_filters_nulls(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    codes = await dev.get_thermostat_sync_codes(zon_info)
    assert codes == ["ATHM-4304", "ATHM-2625", "ATHM-2619"]


@pytest.mark.asyncio
async def test_zon_thermostat_sync_codes_handles_missing(sensorlinx):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_thermostat_sync_codes({}) == []


@pytest.mark.asyncio
async def test_zon_zone_id(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_zone_id(zon_info) == 24


@pytest.mark.asyncio
async def test_zon_name(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    assert await dev.get_name(zon_info) == "AZON-0224"


@pytest.mark.asyncio
async def test_zon_get_temperatures_raises(sensorlinx, zon_info):
    """ZON has no temp sensors of its own; force callers to use linked THMs."""
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    with pytest.raises(RuntimeError, match="ZON devices do not"):
        await dev.get_temperatures(device_info=zon_info)


@pytest.mark.asyncio
async def test_zon_get_firmware_inherited(sensorlinx, zon_info):
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    fw = await dev.get_firmware_version(zon_info)
    assert fw == 1.32


# ---------------------------------------------------------------------------
# Network bypass: ``device_info`` parameter prevents API calls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_thm_does_not_call_api_when_device_info_passed(sensorlinx, thm_info):
    """Critical for the integration: passing device_info must short-circuit fetch."""
    sensorlinx.get_devices = AsyncMock(side_effect=AssertionError("must not be called"))
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    await dev.get_room_temperature(thm_info)
    await dev.get_target_temperature(thm_info)
    await dev.get_hvac_mode(thm_info)
    sensorlinx.get_devices.assert_not_called()


@pytest.mark.asyncio
async def test_zon_does_not_call_api_when_device_info_passed(sensorlinx, zon_info):
    sensorlinx.get_devices = AsyncMock(side_effect=AssertionError("must not be called"))
    dev = ZonDevice(sensorlinx, "bld-1", "X")
    await dev.get_relays(zon_info)
    await dev.get_thermostat_sync_codes(zon_info)
    await dev.get_app_button(zon_info)
    sensorlinx.get_devices.assert_not_called()


@pytest.mark.asyncio
async def test_thm_fetches_when_device_info_omitted(sensorlinx, thm_info):
    sensorlinx.get_devices = AsyncMock(return_value=thm_info)
    dev = ThmDevice(sensorlinx, "bld-1", thm_info["syncCode"])
    temp = await dev.get_room_temperature()
    assert temp.to_fahrenheit() == pytest.approx(56.2)
    sensorlinx.get_devices.assert_awaited_once_with("bld-1", thm_info["syncCode"])


@pytest.mark.asyncio
async def test_thm_fetch_failure_raises_runtime_error(sensorlinx):
    sensorlinx.get_devices = AsyncMock(side_effect=ConnectionError("boom"))
    dev = ThmDevice(sensorlinx, "bld-1", "X")
    with pytest.raises(RuntimeError, match="Failed to fetch device info"):
        await dev.get_room_temperature()


# ---------------------------------------------------------------------------
# Constants exposed
# ---------------------------------------------------------------------------


def test_device_type_constants_match_payload(thm_info, zon_info):
    assert thm_info["deviceType"] == DEVICE_TYPE_THM
    assert zon_info["deviceType"] == DEVICE_TYPE_ZON
    assert DEVICE_TYPE_ECO == "ECO"
