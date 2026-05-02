"""
Unit tests for the THM/ZON setters added in pysensorlinx 0.4.0.

These tests use the same mocking pattern as ``set_parameters_test.py``:
patch ``Sensorlinx._session.patch`` and assert on the JSON body that the
setter sends. They confirm:

* the right raw HBX field name is used (these are confirmed against live
  device dumps from a THM-0600 / ZON-0600 — see the project plan for the
  source of truth);
* enum strings are translated to the right integer values;
* range/type validation rejects bad inputs without making an HTTP call.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pysensorlinx import (
    InvalidParameterError,
    Sensorlinx,
    Temperature,
)
from pysensorlinx.sensorlinx import ThmDevice, ZonDevice


def _patched_sensorlinx(device_payload=None):
    sensorlinx = Sensorlinx()
    sensorlinx._session = MagicMock()
    sensorlinx._session.closed = False
    sensorlinx._bearer_token = "fake-bearer-token-for-tests"
    sensorlinx.headers["Authorization"] = f"Bearer {sensorlinx._bearer_token}"
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json = AsyncMock(return_value={})
    mock_response.text = AsyncMock(return_value="{}")
    mock_patch = MagicMock(return_value=mock_response)
    sensorlinx._session.patch = mock_patch

    # GET mock for read-modify-write setters (pysensorlinx 0.5.4+).
    # Defaults to a complete awayMode block matching real HBX firmware.
    if device_payload is None:
        device_payload = {
            "awayMode": {
                "title": "Away",
                "activated": True,
                "pgm": 2,
                "heatTarget": {"enabled": True, "value": 53},
                "coolTarget": {"enabled": True, "value": 87},
            },
        }
    get_response = MagicMock()
    get_response.__aenter__ = AsyncMock(return_value=get_response)
    get_response.__aexit__ = AsyncMock(return_value=None)
    get_response.status = 200
    get_response.headers = {"Content-Type": "application/json"}
    get_response.json = AsyncMock(return_value=device_payload)
    get_response.text = AsyncMock(return_value="{}")
    sensorlinx._session.get = MagicMock(return_value=get_response)
    return sensorlinx, mock_patch


@pytest.fixture
def thm_with_patch():
    sensorlinx, mock_patch = _patched_sensorlinx()
    device = ThmDevice(
        sensorlinx=sensorlinx,
        building_id="building123",
        device_id="thm456",
    )
    return sensorlinx, device, mock_patch


@pytest.fixture
def zon_with_patch():
    sensorlinx, mock_patch = _patched_sensorlinx()
    device = ZonDevice(
        sensorlinx=sensorlinx,
        building_id="building123",
        device_id="zon789",
    )
    return sensorlinx, device, mock_patch


# ---------------------------------------------------------------------------
# THM: set_hvac_mode (cngOvr 0=Auto 1=Heat 2=Cool 3=Off)
# ---------------------------------------------------------------------------

@pytest.mark.set_params
@pytest.mark.parametrize("mode,expected", [
    ("auto", {"cngOvr": 0}),
    ("heat", {"cngOvr": 1}),
    ("cool", {"cngOvr": 2}),
    ("off", {"cngOvr": 3}),
    ("HEAT", {"cngOvr": 1}),  # case-insensitive
])
async def test_thm_set_hvac_mode(thm_with_patch, mode, expected):
    sensorlinx, device, mock_patch = thm_with_patch

    await device.set_hvac_mode(mode)

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == expected


@pytest.mark.set_params
@pytest.mark.parametrize("bad", ["warm", "", "auto ", None, 1])
async def test_thm_set_hvac_mode_invalid(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_hvac_mode(bad)
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# THM: set_away_mode (away 0/1)
# ---------------------------------------------------------------------------

@pytest.mark.set_params
@pytest.mark.parametrize("enabled,expected", [
    (True, {"away": 1}),
    (False, {"away": 0}),
])
async def test_thm_set_away_mode(thm_with_patch, enabled, expected):
    sensorlinx, device, mock_patch = thm_with_patch

    await device.set_away_mode(enabled)

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == expected


@pytest.mark.set_params
@pytest.mark.parametrize("bad", [1, 0, "true", None])
async def test_thm_set_away_mode_invalid(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_away_mode(bad)
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# THM: set_fan_mode (fnMode 0=Off 1=On 2=Intermittent)
# ---------------------------------------------------------------------------

@pytest.mark.set_params
@pytest.mark.parametrize("mode,expected", [
    ("off", {"fnMode": 0}),
    ("on", {"fnMode": 1}),
    ("intermittent", {"fnMode": 2}),
    ("Intermittent", {"fnMode": 2}),
])
async def test_thm_set_fan_mode(thm_with_patch, mode, expected):
    sensorlinx, device, mock_patch = thm_with_patch

    await device.set_fan_mode(mode)

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == expected


@pytest.mark.set_params
@pytest.mark.parametrize("bad", ["auto", "", None, 1])
async def test_thm_set_fan_mode_invalid(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_fan_mode(bad)
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# THM: set_target_temperature — writes rmT (heat) or rmCT (cool) based on
# the current changeover state. Confirmed against live THM dumps 2026-04-26.
# ---------------------------------------------------------------------------

def _device_info(target_type, is_off=False):
    return {"target": {"type": target_type, "isOff": is_off}}


@pytest.mark.set_params
@pytest.mark.parametrize("temp_f,expected_value", [
    (35, 35),
    (68, 68),
    (72, 72),
    (99, 99),
    (68.4, 68),  # rounds down
    (68.6, 69),  # rounds up
])
async def test_thm_set_target_temperature_heat_mode(thm_with_patch, temp_f, expected_value):
    sensorlinx, device, mock_patch = thm_with_patch
    sensorlinx.get_devices = AsyncMock(return_value=_device_info("heat"))

    await device.set_target_temperature(Temperature(temp_f, "F"))

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == {"rmT": expected_value}


@pytest.mark.set_params
@pytest.mark.parametrize("temp_f,expected_value", [
    (35, 35),
    (79, 79),
    (84, 84),
    (99, 99),
])
async def test_thm_set_target_temperature_cool_mode(thm_with_patch, temp_f, expected_value):
    sensorlinx, device, mock_patch = thm_with_patch
    sensorlinx.get_devices = AsyncMock(return_value=_device_info("cooling"))

    await device.set_target_temperature(Temperature(temp_f, "F"))

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == {"rmCT": expected_value}


@pytest.mark.set_params
async def test_thm_set_target_temperature_celsius_input(thm_with_patch):
    """Celsius inputs should be converted to °F before being sent."""
    sensorlinx, device, mock_patch = thm_with_patch
    sensorlinx.get_devices = AsyncMock(return_value=_device_info("heat"))

    await device.set_target_temperature(Temperature(20, "C"))  # 68°F

    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == {"rmT": 68}


@pytest.mark.set_params
async def test_thm_set_target_temperature_off_mode_rejected(thm_with_patch):
    sensorlinx, device, mock_patch = thm_with_patch
    sensorlinx.get_devices = AsyncMock(return_value=_device_info("heat", is_off=True))

    with pytest.raises(InvalidParameterError):
        await device.set_target_temperature(Temperature(70, "F"))
    assert mock_patch.call_count == 0


@pytest.mark.set_params
async def test_thm_set_target_temperature_unknown_target_type_rejected(thm_with_patch):
    sensorlinx, device, mock_patch = thm_with_patch
    sensorlinx.get_devices = AsyncMock(return_value={"target": {}})

    with pytest.raises(InvalidParameterError):
        await device.set_target_temperature(Temperature(70, "F"))
    assert mock_patch.call_count == 0


@pytest.mark.set_params
@pytest.mark.parametrize("bad_temp_f", [34, 100, 0, 200])
async def test_thm_set_target_temperature_out_of_range(thm_with_patch, bad_temp_f):
    _, device, mock_patch = thm_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_target_temperature(Temperature(bad_temp_f, "F"))
    assert mock_patch.call_count == 0


@pytest.mark.set_params
@pytest.mark.parametrize("bad", [70, 70.5, "70", None])
async def test_thm_set_target_temperature_wrong_type(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_target_temperature(bad)
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# THM: set_schedule_enabled (pgmble 0/1)
# Field mapping confirmed via paired before/after dumps from a live
# THM-0600 on 2026-04-28: schedule off->on moved pgmble 0->1.
# ---------------------------------------------------------------------------

@pytest.mark.set_params
@pytest.mark.parametrize("enabled,expected", [
    (True, {"pgmble": 1}),
    (False, {"pgmble": 0}),
])
async def test_thm_set_schedule_enabled(thm_with_patch, enabled, expected):
    sensorlinx, device, mock_patch = thm_with_patch

    await device.set_schedule_enabled(enabled)

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == expected


@pytest.mark.set_params
@pytest.mark.parametrize("bad", [1, 0, "true", None])
async def test_thm_set_schedule_enabled_invalid(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_schedule_enabled(bad)
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# THM: set_humidity_mode (useHum 0=off 1=on 2=auto)
# Field mapping confirmed via paired before/after dumps on 2026-04-28.
# ---------------------------------------------------------------------------

@pytest.mark.set_params
@pytest.mark.parametrize("mode,expected", [
    ("off", {"useHum": 0}),
    ("on", {"useHum": 1}),
    ("auto", {"useHum": 2}),
    ("Auto", {"useHum": 2}),  # case-insensitive
])
async def test_thm_set_humidity_mode(thm_with_patch, mode, expected):
    sensorlinx, device, mock_patch = thm_with_patch

    await device.set_humidity_mode(mode)

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == expected


@pytest.mark.set_params
@pytest.mark.parametrize("bad", ["enabled", "", None, 1, "off "])
async def test_thm_set_humidity_mode_invalid(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_humidity_mode(bad)
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# THM: set_humidity_target (hmT integer percent, 0-100)
# Field mapping confirmed via paired before/after dumps on 2026-04-28
# (40% -> 45% moved hmT 40 -> 45).
# ---------------------------------------------------------------------------

@pytest.mark.set_params
@pytest.mark.parametrize("value,expected", [
    (0, {"hmT": 0}),
    (40, {"hmT": 40}),
    (45, {"hmT": 45}),
    (100, {"hmT": 100}),
])
async def test_thm_set_humidity_target(thm_with_patch, value, expected):
    sensorlinx, device, mock_patch = thm_with_patch

    await device.set_humidity_target(value)

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == expected


@pytest.mark.set_params
@pytest.mark.parametrize("bad", [-1, 101, 200])
async def test_thm_set_humidity_target_out_of_range(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_humidity_target(bad)
    assert mock_patch.call_count == 0


@pytest.mark.set_params
@pytest.mark.parametrize("bad", [40.5, "40", None, True, False])
async def test_thm_set_humidity_target_wrong_type(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_humidity_target(bad)
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# ZON: set_app_button (aBut 0/1)
# ---------------------------------------------------------------------------

@pytest.mark.set_params
@pytest.mark.parametrize("enabled,expected", [
    (True, {"aBut": 1}),
    (False, {"aBut": 0}),
])
async def test_zon_set_app_button(zon_with_patch, enabled, expected):
    sensorlinx, device, mock_patch = zon_with_patch

    await device.set_app_button(enabled)

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == expected


@pytest.mark.set_params
@pytest.mark.parametrize("bad", [1, 0, "on", None])
async def test_zon_set_app_button_invalid(zon_with_patch, bad):
    _, device, mock_patch = zon_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_app_button(bad)
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# ZON: set_aux_setpoint (dhwT int °F)
# ---------------------------------------------------------------------------

@pytest.mark.set_params
@pytest.mark.parametrize("temp_f,expected_value", [
    (33, 33),
    (90, 90),
    (140, 140),
    (180, 180),
    (140.4, 140),
    (140.6, 141),
])
async def test_zon_set_aux_setpoint(zon_with_patch, temp_f, expected_value):
    sensorlinx, device, mock_patch = zon_with_patch

    await device.set_aux_setpoint(Temperature(temp_f, "F"))

    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == {"dhwT": expected_value}


@pytest.mark.set_params
@pytest.mark.parametrize("bad_temp_f", [32, 181, -10, 500])
async def test_zon_set_aux_setpoint_out_of_range(zon_with_patch, bad_temp_f):
    _, device, mock_patch = zon_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_aux_setpoint(Temperature(bad_temp_f, "F"))
    assert mock_patch.call_count == 0


@pytest.mark.set_params
@pytest.mark.parametrize("bad", [120, "120", None])
async def test_zon_set_aux_setpoint_wrong_type(zon_with_patch, bad):
    _, device, mock_patch = zon_with_patch

    with pytest.raises(InvalidParameterError):
        await device.set_aux_setpoint(bad)
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# patch_device low-level setter
# ---------------------------------------------------------------------------

@pytest.mark.set_params
async def test_patch_device_sends_flat_json():
    sensorlinx, mock_patch = _patched_sensorlinx()

    await sensorlinx.patch_device("b1", "d1", cngOvr=1, away=0)

    assert mock_patch.call_count == 1
    args, kwargs = mock_patch.call_args
    # URL is the first positional arg
    assert "b1" in args[0] and "d1" in args[0]
    assert kwargs["json"] == {"cngOvr": 1, "away": 0}


@pytest.mark.set_params
async def test_patch_device_requires_ids():
    sensorlinx, mock_patch = _patched_sensorlinx()

    with pytest.raises(InvalidParameterError):
        await sensorlinx.patch_device("", "d1", cngOvr=1)
    with pytest.raises(InvalidParameterError):
        await sensorlinx.patch_device("b1", "", cngOvr=1)
    assert mock_patch.call_count == 0


@pytest.mark.set_params
async def test_patch_device_requires_fields():
    sensorlinx, mock_patch = _patched_sensorlinx()

    with pytest.raises(InvalidParameterError):
        await sensorlinx.patch_device("b1", "d1")
    assert mock_patch.call_count == 0

# ---------------------------------------------------------------------------
# THM 0.5.2: dual heat/cool setpoints + active demand bitfield
# ---------------------------------------------------------------------------

@pytest.mark.set_params
@pytest.mark.parametrize("temp_f,expected", [
    (35, 35),
    (68, 68),
    (99, 99),
    (68.4, 68),
    (68.6, 69),
])
async def test_thm_set_heat_setpoint(thm_with_patch, temp_f, expected):
    _, device, mock_patch = thm_with_patch
    await device.set_heat_setpoint(Temperature(temp_f, "F"))
    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == {"rmT": expected}


@pytest.mark.set_params
@pytest.mark.parametrize("temp_f,expected", [
    (35, 35),
    (79, 79),
    (99, 99),
])
async def test_thm_set_cool_setpoint(thm_with_patch, temp_f, expected):
    _, device, mock_patch = thm_with_patch
    await device.set_cool_setpoint(Temperature(temp_f, "F"))
    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == {"rmCT": expected}


@pytest.mark.set_params
@pytest.mark.parametrize("bad_temp", [34, 100, 0, 200])
async def test_thm_set_heat_setpoint_out_of_range(thm_with_patch, bad_temp):
    _, device, mock_patch = thm_with_patch
    with pytest.raises(InvalidParameterError):
        await device.set_heat_setpoint(Temperature(bad_temp, "F"))
    assert mock_patch.call_count == 0


@pytest.mark.set_params
@pytest.mark.parametrize("bad_temp", [34, 100])
async def test_thm_set_cool_setpoint_out_of_range(thm_with_patch, bad_temp):
    _, device, mock_patch = thm_with_patch
    with pytest.raises(InvalidParameterError):
        await device.set_cool_setpoint(Temperature(bad_temp, "F"))
    assert mock_patch.call_count == 0


@pytest.mark.set_params
@pytest.mark.parametrize("bad", [None, 72, "72", 72.0])
async def test_thm_set_heat_setpoint_wrong_type(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch
    with pytest.raises(InvalidParameterError):
        await device.set_heat_setpoint(bad)
    assert mock_patch.call_count == 0


@pytest.mark.set_params
async def test_thm_set_heat_cool_setpoints_single_patch(thm_with_patch):
    _, device, mock_patch = thm_with_patch
    await device.set_heat_cool_setpoints(
        Temperature(67, "F"), Temperature(79, "F"),
    )
    # Single PATCH containing both fields.
    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == {"rmT": 67, "rmCT": 79}


@pytest.mark.set_params
@pytest.mark.parametrize("heat,cool", [
    (70, 70),  # equal — no deadband
    (75, 70),  # inverted
    (80, 79),  # heat above cool
])
async def test_thm_set_heat_cool_setpoints_rejects_invalid_pair(thm_with_patch, heat, cool):
    _, device, mock_patch = thm_with_patch
    with pytest.raises(InvalidParameterError):
        await device.set_heat_cool_setpoints(
            Temperature(heat, "F"), Temperature(cool, "F"),
        )
    assert mock_patch.call_count == 0


@pytest.mark.set_params
async def test_thm_set_heat_cool_setpoints_validates_each_side(thm_with_patch):
    _, device, mock_patch = thm_with_patch
    # heat out of range
    with pytest.raises(InvalidParameterError):
        await device.set_heat_cool_setpoints(
            Temperature(34, "F"), Temperature(79, "F"),
        )
    # cool out of range
    with pytest.raises(InvalidParameterError):
        await device.set_heat_cool_setpoints(
            Temperature(67, "F"), Temperature(100, "F"),
        )
    assert mock_patch.call_count == 0


# ---------------------------------------------------------------------------
# THM 0.5.2: get_heat_setpoint / get_cool_setpoint / get_active_demands
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload,expected", [
    ({"rmT": 67}, 67),
    ({"rmT": 72}, 72),
    ({}, None),
    ({"rmT": None}, None),
])
async def test_thm_get_heat_setpoint(thm_with_patch, payload, expected):
    _, device, _ = thm_with_patch
    result = await device.get_heat_setpoint(payload)
    if expected is None:
        assert result is None
    else:
        assert result.to_fahrenheit() == expected


@pytest.mark.parametrize("payload,expected", [
    ({"rmCT": 79}, 79),
    ({"rmCT": 84}, 84),
    ({}, None),
    ({"rmCT": None}, None),
])
async def test_thm_get_cool_setpoint(thm_with_patch, payload, expected):
    _, device, _ = thm_with_patch
    result = await device.get_cool_setpoint(payload)
    if expected is None:
        assert result is None
    else:
        assert result.to_fahrenheit() == expected


@pytest.mark.parametrize("dmd,expected", [
    (0, []),
    (2, ["heating"]),       # heat call only
    (64, ["cooling"]),      # cool call only
    (128, ["fan"]),         # fan only
    (66, ["heating", "cooling"]),  # both bits (defensive: shouldn't happen but model it)
    (130, ["heating", "fan"]),     # heat + fan
    (192, ["cooling", "fan"]),     # cool + fan
    ("not-an-int", []),
    (None, []),  # field present but None
])
async def test_thm_get_active_demands(thm_with_patch, dmd, expected):
    _, device, _ = thm_with_patch
    result = await device.get_active_demands({"dmd": dmd})
    assert result == expected


async def test_thm_get_active_demands_missing_field(thm_with_patch):
    _, device, _ = thm_with_patch
    result = await device.get_active_demands({})
    assert result == []


# ---------------------------------------------------------------------------
# THM 0.5.3: get/set away-mode setpoints (awayMode.heatTarget.value etc.)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload,expected_f", [
    ({"awayMode": {"heatTarget": {"value": 53}}}, 53),
    ({"awayMode": {"heatTarget": {"value": 58}}}, 58),
])
async def test_thm_get_away_heat_setpoint(thm_with_patch, payload, expected_f):
    _, device, _ = thm_with_patch
    result = await device.get_away_heat_setpoint(payload)
    assert result is not None
    assert result.to_fahrenheit() == expected_f


@pytest.mark.parametrize("payload", [
    {},
    {"awayMode": {}},
    {"awayMode": {"heatTarget": {}}},
    {"awayMode": {"heatTarget": {"value": None}}},
])
async def test_thm_get_away_heat_setpoint_missing(thm_with_patch, payload):
    _, device, _ = thm_with_patch
    result = await device.get_away_heat_setpoint(payload)
    assert result is None


@pytest.mark.parametrize("payload,expected_f", [
    ({"awayMode": {"coolTarget": {"value": 87}}}, 87),
    ({"awayMode": {"coolTarget": {"value": 92}}}, 92),
])
async def test_thm_get_away_cool_setpoint(thm_with_patch, payload, expected_f):
    _, device, _ = thm_with_patch
    result = await device.get_away_cool_setpoint(payload)
    assert result is not None
    assert result.to_fahrenheit() == expected_f


@pytest.mark.parametrize("payload", [
    {},
    {"awayMode": {}},
    {"awayMode": {"coolTarget": {}}},
])
async def test_thm_get_away_cool_setpoint_missing(thm_with_patch, payload):
    _, device, _ = thm_with_patch
    result = await device.get_away_cool_setpoint(payload)
    assert result is None


@pytest.mark.set_params
async def test_thm_set_away_heat_setpoint(thm_with_patch):
    _, device, mock_patch = thm_with_patch
    await device.set_away_heat_setpoint(Temperature(58, "F"))
    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    # Flat-scalar PATCH: hRmT is the writable away-heat field. The cloud
    # silently drops PATCHes to the nested `awayMode` block, but writes
    # to the flat `hRmT` scalar land cleanly and propagate through to
    # `awayMode.heatTarget.value` server-side.
    assert kwargs["json"] == {"hRmT": 58}


@pytest.mark.set_params
async def test_thm_set_away_cool_setpoint(thm_with_patch):
    _, device, mock_patch = thm_with_patch
    await device.set_away_cool_setpoint(Temperature(92, "F"))
    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == {"hRmCT": 92}


@pytest.mark.set_params
@pytest.mark.parametrize("bad_temp", [34, 100])
async def test_thm_set_away_heat_setpoint_out_of_range(thm_with_patch, bad_temp):
    _, device, mock_patch = thm_with_patch
    with pytest.raises(InvalidParameterError):
        await device.set_away_heat_setpoint(Temperature(bad_temp, "F"))
    assert mock_patch.call_count == 0


@pytest.mark.set_params
@pytest.mark.parametrize("bad", [None, 72, "72", 72.0])
async def test_thm_set_away_heat_setpoint_wrong_type(thm_with_patch, bad):
    _, device, mock_patch = thm_with_patch
    with pytest.raises(InvalidParameterError):
        await device.set_away_heat_setpoint(bad)
    assert mock_patch.call_count == 0


@pytest.mark.set_params
async def test_thm_set_away_heat_cool_setpoints_single_patch(thm_with_patch):
    _, device, mock_patch = thm_with_patch
    await device.set_away_heat_cool_setpoints(
        Temperature(58, "F"), Temperature(92, "F"),
    )
    assert mock_patch.call_count == 1
    _, kwargs = mock_patch.call_args
    assert kwargs["json"] == {"hRmT": 58, "hRmCT": 92}


@pytest.mark.set_params
@pytest.mark.parametrize("heat,cool", [
    (70, 70),
    (75, 70),
    (80, 79),
])
async def test_thm_set_away_heat_cool_setpoints_rejects_invalid_pair(thm_with_patch, heat, cool):
    _, device, mock_patch = thm_with_patch
    with pytest.raises(InvalidParameterError):
        await device.set_away_heat_cool_setpoints(
            Temperature(heat, "F"), Temperature(cool, "F"),
        )
    assert mock_patch.call_count == 0


@pytest.mark.set_params
async def test_thm_set_away_heat_cool_setpoints_validates_each_side(thm_with_patch):
    _, device, mock_patch = thm_with_patch
    with pytest.raises(InvalidParameterError):
        await device.set_away_heat_cool_setpoints(
            Temperature(34, "F"), Temperature(79, "F"),
        )
    with pytest.raises(InvalidParameterError):
        await device.set_away_heat_cool_setpoints(
            Temperature(67, "F"), Temperature(100, "F"),
        )
    assert mock_patch.call_count == 0