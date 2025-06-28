import pytest
from unittest.mock import AsyncMock, MagicMock
from pysensorlinx import Sensorlinx, SensorlinxDevice, InvalidParameterError

@pytest.fixture
def sensorlinx_device_with_patch():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id="building123",
        device_id="device456"
    )
    
    sensorlinx._session = MagicMock()
    mock_patch = MagicMock()
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_patch.return_value = mock_response
    sensorlinx._session.patch = mock_patch
    return sensorlinx, device, mock_patch

###################################################################################################
# Set HVAC mode priority tests
###################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("mode,expected_json", [
  ("heat", {"prior": 0}),
  ("cool", {"prior": 1}),
  ("auto", {"prior": 2}),
])
async def test_set_hvac_mode_priority(sensorlinx_device_with_patch, mode, expected_json):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_hvac_mode_priority(mode)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected_json
    
@pytest.mark.asyncio
async def test_set_hvac_mode_priority_invalid_value(sensorlinx_device_with_patch):
    sensorlinx, device, mock_patch = sensorlinx_device_with_patch

    with pytest.raises(InvalidParameterError) as excinfo:
        await device.set_hvac_mode_priority("invalid_value")
        
    assert str(excinfo.value) == "Invalid HVAC mode priority. Must be 'cool', 'heat' or 'auto'."
    
##################################################################################################
# Permanent heating demand tests
##################################################################################################   
 
@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (True, {"permHD": 1}),
  (False, {"permHD": 0}),
])
async def test_set_permanent_hd(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_permanent_hd(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected

  
##################################################################################################
# Permanent cooling demand tests
##################################################################################################  
  
@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (True, {"permCD": 1}),
  (False, {"permCD": 0}),
])
async def test_set_permanent_cd(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_permanent_cd(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected
    

##################################################################################################
# Weather shutdown lag time tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (120, {"wwTime": 120}),
  (0, {"wwTime": 0}),
  (240, {"wwTime": 240}),
])
async def test_set_weather_shutdown_lag_time_valid(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_weather_shutdown_lag_time(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_value", [-1, 241, 1000, -100])
async def test_set_weather_shutdown_lag_time_invalid_value(sensorlinx_device_with_patch, invalid_value):
    sensorlinx, device, mock_patch = sensorlinx_device_with_patch

    with pytest.raises(InvalidParameterError) as excinfo:
      await device.set_weather_shutdown_lag_time(invalid_value)
    assert str(excinfo.value) == "Invalid weather shutdown lag time. Must be an integer between 0 and 240."


##################################################################################################
# Wide priority differential tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (True, {"wPDif": 1}),
  (False, {"wPDif": 0}),
])
async def test_set_wide_priority_differential(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_wide_priority_differential(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected
  
##################################################################################################
# Number of stages tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("num_stages", [1, 2, 3, 4])
async def test_set_number_of_stages_valid(sensorlinx_device_with_patch, num_stages):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_number_of_stages(num_stages)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"numStg": num_stages}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_value", [0, 5, -1, 100])
async def test_set_number_of_stages_invalid(sensorlinx_device_with_patch, invalid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_number_of_stages(invalid_value)
  assert str(excinfo.value) == "Number of stages must be an integer between 1 and 4."
  
##################################################################################################
# Two stage heat pump tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (True, {"twoS": 1}),
  (False, {"twoS": 0}),
])
async def test_set_two_stage_heat_pump(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_two_stage_heat_pump(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected
  
##################################################################################################
# Stage On Lag Time tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("valid_value", [1, 50, 120, 240])
async def test_set_stage_on_lag_time_valid(sensorlinx_device_with_patch, valid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_stage_on_lag_time(valid_value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"lagT": valid_value}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_value", [0, -1, 241, 1000])
async def test_set_stage_on_lag_time_invalid(sensorlinx_device_with_patch, invalid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_stage_on_lag_time(invalid_value)
  assert str(excinfo.value) == "Stage ON Lagtime value must be an integer between 1 and 240 minutes."
  
##################################################################################################
# Stage Off Lag Time tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("valid_value", [1, 120, 240])
async def test_set_stage_off_lag_time_valid(sensorlinx_device_with_patch, valid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_stage_off_lag_time(valid_value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"lagOff": valid_value}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_value", [0, -5, 241, 1000])
async def test_set_stage_off_lag_time_invalid(sensorlinx_device_with_patch, invalid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_stage_off_lag_time(invalid_value)
  assert str(excinfo.value) == "Stage OFF lag time value must be an integer between 1 and 240 seconds."
  
  
##################################################################################################
# Rotate Cycles tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (1, {"rotCy": 1}),
  (120, {"rotCy": 120}),
  (240, {"rotCy": 240}),
  ("off", {"rotCy": 0}),
  ("OFF", {"rotCy": 0}),
  ("Off", {"rotCy": 0}),
])
async def test_set_rotate_cycles_valid(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_rotate_cycles(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_value", [0, -1, 241, 1000, "invalid", "on", "OFFF", "of", "Offf"])
async def test_set_rotate_cycles_invalid(sensorlinx_device_with_patch, invalid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_rotate_cycles(invalid_value)
  assert str(excinfo.value) == "Rotate cycles value must be an integer between 1 and 240 or 'off'."
  
  
##################################################################################################
# Rotate Time tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (1, {"rotTi": 1}),
  (120, {"rotTi": 120}),
  (240, {"rotTi": 240}),
  ("off", {"rotTi": 0}),
  ("OFF", {"rotTi": 0}),
  ("Off", {"rotTi": 0}),
])
async def test_set_rotate_time_valid(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_rotate_time(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_value", [0, -1, 241, 1000, "invalid", "on", "OFFF", "of", "Offf"])
async def test_set_rotate_time_invalid(sensorlinx_device_with_patch, invalid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_rotate_time(invalid_value)
  assert str(excinfo.value) == "Rotate time must be an integer between 1 and 240 or 'off'."
  

##################################################################################################
# Off Staging tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (True, {"hpStg": 1}),
  (False, {"hpStg": 0}),
])
async def test_set_off_staging(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_off_staging(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected
