import pytest
from unittest.mock import AsyncMock, MagicMock
from pysensorlinx import Sensorlinx, SensorlinxDevice, Temperature, InvalidParameterError

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
# Heat/Cool Switch Delay tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("valid_value", [30, 60, 300, 600])
async def test_set_heat_cool_switch_delay_valid(sensorlinx_device_with_patch, valid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_heat_cool_switch_delay(valid_value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"hpSw": valid_value}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_value", [0, 29, 601, 1000, -10])
async def test_set_heat_cool_switch_delay_invalid(sensorlinx_device_with_patch, invalid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_heat_cool_switch_delay(invalid_value)
  assert str(excinfo.value) == "Heat/Cool Switch Delay must be an integer between 30 and 600 seconds."


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
  
##################################################################################################
# Warm Weather Shutdown tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (Temperature(34, "F"), {"wwsd": 34}),
  (Temperature(100, "F"), {"wwsd": 100}),
  (Temperature(180, "F"), {"wwsd": 180}),
  ("off", {"wwsd": 32}),
  ("OFF", {"wwsd": 32}),
  ("Off", {"wwsd": 32}),
])
async def test_set_warm_weather_shutdown_valid(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_warm_weather_shutdown(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (1.12, 34),    # 1°C ≈ 33.8°F, should round to 34
  (37.8, 100),# 37.8°C ≈ 100°F
  (82.2, 180),# 82.2°C ≈ 180°F
])
async def test_set_warm_weather_shutdown_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_warm_weather_shutdown(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"wwsd": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  ("K"),
  ("celsius"),
  ("farenheit"),
  (""), 
  (None),
])
async def test_set_warm_weather_shutdown_invalid_temperature_unit(sensorlinx_device_with_patch, invalid_unit):
    sensorlinx, device, mock_patch = sensorlinx_device_with_patch

    with pytest.raises(ValueError) as excinfo:
        temp = Temperature(100, invalid_unit)
        await device.set_warm_weather_shutdown(temp)
    assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"
    
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Invalid type for warm weather shutdown. Must be a Temperature or 'off'."),
  (45.6, "Invalid type for warm weather shutdown. Must be a Temperature or 'off'."),
  (True, "Invalid type for warm weather shutdown. Must be a Temperature or 'off'."),
  (False, "Invalid type for warm weather shutdown. Must be a Temperature or 'off'."),
  (["F", 100], "Invalid type for warm weather shutdown. Must be a Temperature or 'off'."),
  ({"value": 100, "unit": "F"}, "Invalid type for warm weather shutdown. Must be a Temperature or 'off'."),
  (None, "At least one optional parameter must be provided."),
])
async def test_set_warm_weather_shutdown_invalid_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_warm_weather_shutdown(invalid_input)
  assert str(excinfo.value) == expected_error

   
##################################################################################################
# Hot Tank Outdoor Reset tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (Temperature(-40, "F"), {"dot": -40}),
  (Temperature(0, "F"), {"dot": 0}),
  (Temperature(127, "F"), {"dot": 127}),
  ("off", {"dot": -41}),
  ("OFF", {"dot": -41}),
  ("Off", {"dot": -41}),
])
async def test_hot_tank_outdoor_reset_valid(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_hot_tank_outdoor_reset(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (-40, -40),    # -40°C == -40°F
  (0, 32),       # 0°C == 32°F
  (52.7, 127),     # 53°C ≈ 127°F
])
async def test_hot_tank_outdoor_reset_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_hot_tank_outdoor_reset(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"dot": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_value", [
  -41, 128, 200, -100, 1000
])
async def test_hot_tank_outdoor_reset_invalid_fahrenheit(sensorlinx_device_with_patch, invalid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_value, "F")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_outdoor_reset(temp)
  assert str(excinfo.value) == "Hot tank outdoor reset must be between -40°F and 127°F or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_celsius", [
  -41, 54, 100, -100, 1000
])
async def test_hot_tank_outdoor_reset_invalid_celsius(sensorlinx_device_with_patch, invalid_celsius):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_celsius, "C")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_outdoor_reset(temp)
  assert str(excinfo.value) == "Hot tank outdoor reset must be between -40°F and 127°F or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_str", [
  "invalid", "on", "OFFF", "of", "Offf"
])
async def test_hot_tank_outdoor_reset_invalid_string(sensorlinx_device_with_patch, invalid_str):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_outdoor_reset(invalid_str)
  assert str(excinfo.value) == "Hot tank outdoor reset must be a Temperature instance or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  ("K"),
  ("celsius"),
  ("farenheit"),
  (""), 
  (None),
])
async def test_hot_tank_outdoor_reset_invalid_temperature_unit(sensorlinx_device_with_patch, invalid_unit):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(ValueError) as excinfo:
    temp = Temperature(100, invalid_unit)
    await device.set_hot_tank_outdoor_reset(temp)
  assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"
  
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Hot tank outdoor reset must be a Temperature instance or 'off'."),
  (45.6, "Hot tank outdoor reset must be a Temperature instance or 'off'."),
  (True, "Hot tank outdoor reset must be a Temperature instance or 'off'."),
  (False, "Hot tank outdoor reset must be a Temperature instance or 'off'."),
  (["F", 100], "Hot tank outdoor reset must be a Temperature instance or 'off'."),
  ({"value": 100, "unit": "F"}, "Hot tank outdoor reset must be a Temperature instance or 'off'."),
  (None, "At least one optional parameter must be provided."),
])
async def test_set_hot_tank_outdoor_reset_invalid_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_outdoor_reset(invalid_input)
  assert str(excinfo.value) == expected_error

##################################################################################################
# Hot Tank Differential tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("fahrenheit,expected_json", [
  (2, {"htDif": 2}),
  (50, {"htDif": 50}),
  (100, {"htDif": 100}),
])
async def test_set_hot_tank_differential_valid_fahrenheit(sensorlinx_device_with_patch, fahrenheit, expected_json):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(fahrenheit, "F")
  await device.set_hot_tank_differential(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected_json

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (1.1, 34),   # 1.1°C ≈ 34°F (rounded)
  (10, 50),    # 10°C ≈ 50°F
  (37.7, 100), # 37.8°C ≈ 100°F
])
async def test_set_hot_tank_differential_valid_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_hot_tank_differential(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"htDif": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_f", [1, 0, 101, 200, -10])
async def test_set_hot_tank_differential_invalid_fahrenheit(sensorlinx_device_with_patch, invalid_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_f, "F")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_differential(temp)
  assert str(excinfo.value) == "Hot tank differential must be between 2°F and 100°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_c", [-100, -17, 38, 100, 1000])
async def test_set_hot_tank_differential_invalid_celsius(sensorlinx_device_with_patch, invalid_c):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_c, "C")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_differential(temp)
  assert str(excinfo.value) == "Hot tank differential must be between 2°F and 100°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  "K", "celsius", "farenheit", "", None
])
async def test_set_hot_tank_differential_invalid_unit(sensorlinx_device_with_patch, invalid_unit):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(ValueError) as excinfo:
    temp = Temperature(10, invalid_unit)
    await device.set_hot_tank_differential(temp)
  assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"
  
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Hot tank differential must be a Temperature instance."),
  (45.6, "Hot tank differential must be a Temperature instance."),
  (True, "Hot tank differential must be a Temperature instance."),
  (False, "Hot tank differential must be a Temperature instance."),
  ("100F", "Hot tank differential must be a Temperature instance."),
  ("180", "Hot tank differential must be a Temperature instance."),
  (["F", 100], "Hot tank differential must be a Temperature instance."),
  ({"value": 100, "unit": "F"}, "Hot tank differential must be a Temperature instance."),
  (None, "At least one optional parameter must be provided."),
])
async def test_set_hot_tank_differential_non_temperature_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_differential(invalid_input)
  assert str(excinfo.value) == expected_error

##################################################################################################
# Hot Tank Minimum Temperature tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("fahrenheit,expected_json", [
  (2, {"dbt": 2}),
  (32, {"dbt": 32}),
  (100, {"dbt": 100}),
  (180, {"dbt": 180}),
])
async def test_set_hot_tank_min_temp_valid_fahrenheit(sensorlinx_device_with_patch, fahrenheit, expected_json):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(fahrenheit, "F")
  await device.set_hot_tank_min_temp(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected_json

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (1.1, 34),    # 1.1°C ≈ 34°F (rounded)
  (37.8, 100),  # 37.8°C ≈ 100°F
  (82.2, 180),  # 82.2°C ≈ 180°F
])
async def test_set_hot_tank_min_temp_valid_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_hot_tank_min_temp(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"dbt": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_f", [1, 0, 181, 200, -10])
async def test_set_hot_tank_min_temp_invalid_fahrenheit(sensorlinx_device_with_patch, invalid_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_f, "F")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_min_temp(temp)
  assert str(excinfo.value) == "Minimum tank temperature for the hot tank must be between 2°F and 180°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_c", [-100, -17, 82.3, 100, 1000])
async def test_set_hot_tank_min_temp_invalid_celsius(sensorlinx_device_with_patch, invalid_c):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_c, "C")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_min_temp(temp)
  assert str(excinfo.value) == "Minimum tank temperature for the hot tank must be between 2°F and 180°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  "K", "celsius", "farenheit", "", None
])
async def test_set_hot_tank_min_temp_invalid_unit(sensorlinx_device_with_patch, invalid_unit):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(ValueError) as excinfo:
    temp = Temperature(10, invalid_unit)
    await device.set_hot_tank_min_temp(temp)
  assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"
  
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Minimum tank temperature for the hot tank must be a Temperature instance."),
  (45.6, "Minimum tank temperature for the hot tank must be a Temperature instance."),
  (True, "Minimum tank temperature for the hot tank must be a Temperature instance."),
  (False, "Minimum tank temperature for the hot tank must be a Temperature instance."),
  ("100F", "Minimum tank temperature for the hot tank must be a Temperature instance."),
  ("180", "Minimum tank temperature for the hot tank must be a Temperature instance."),
  (["F", 100], "Minimum tank temperature for the hot tank must be a Temperature instance."),
  ({"value": 100, "unit": "F"}, "Minimum tank temperature for the hot tank must be a Temperature instance."),
  (None, "At least one optional parameter must be provided."),
])
async def test_set_hot_tank_min_temp_non_temperature_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_min_temp(invalid_input)
  assert str(excinfo.value) == expected_error  

##################################################################################################
# Hot Tank Maximum Temperature tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("fahrenheit,expected_json", [
  (2, {"mbt": 2}),
  (32, {"mbt": 32}),
  (100, {"mbt": 100}),
  (180, {"mbt": 180}),
])
async def test_set_hot_tank_max_temp_valid_fahrenheit(sensorlinx_device_with_patch, fahrenheit, expected_json):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(fahrenheit, "F")
  await device.set_hot_tank_max_temp(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected_json

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (1.1, 34),    # 1.1°C ≈ 34°F (rounded)
  (37.8, 100),  # 37.8°C ≈ 100°F
  (82.2, 180),  # 82.2°C ≈ 180°F
])
async def test_set_hot_tank_max_temp_valid_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_hot_tank_max_temp(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"mbt": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_f", [1, 0, 181, 200, -10])
async def test_set_hot_tank_max_temp_invalid_fahrenheit(sensorlinx_device_with_patch, invalid_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_f, "F")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_max_temp(temp)
  assert str(excinfo.value) == "Maximum tank temperature for the hot tank must be between 2°F and 180°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_c", [-100, -17, 82.3, 100, 1000])
async def test_set_hot_tank_max_temp_invalid_celsius(sensorlinx_device_with_patch, invalid_c):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_c, "C")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_max_temp(temp)
  assert str(excinfo.value) == "Maximum tank temperature for the hot tank must be between 2°F and 180°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  "K", "celsius", "farenheit", "", None
])
async def test_set_hot_tank_max_temp_invalid_unit(sensorlinx_device_with_patch, invalid_unit):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(ValueError) as excinfo:
    temp = Temperature(10, invalid_unit)
    await device.set_hot_tank_max_temp(temp)
  assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"
  

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Maximum tank temperature for the hot tank must be a Temperature instance."),
  (45.6, "Maximum tank temperature for the hot tank must be a Temperature instance."),
  (True, "Maximum tank temperature for the hot tank must be a Temperature instance."),
  (False, "Maximum tank temperature for the hot tank must be a Temperature instance."),
  ("100F", "Maximum tank temperature for the hot tank must be a Temperature instance."),
  ("180", "Maximum tank temperature for the hot tank must be a Temperature instance."),
  (["F", 100], "Maximum tank temperature for the hot tank must be a Temperature instance."),
  ({"value": 100, "unit": "F"}, "Maximum tank temperature for the hot tank must be a Temperature instance."),
  (None, "At least one optional parameter must be provided."),
])
async def test_set_hot_tank_max_temp_non_temperature_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_hot_tank_max_temp(invalid_input)
  assert str(excinfo.value) == expected_error

 
##################################################################################################
# Cold Weather Shutdown tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (Temperature(33, "F"), {"cwsd": 33}),
  (Temperature(119, "F"), {"cwsd": 119}),
  (Temperature(50, "F"), {"cwsd": 50}),
  ("off", {"cwsd": 32}),
  ("OFF", {"cwsd": 32}),
  ("Off", {"cwsd": 32}),
])
async def test_set_cold_weather_shutdown_valid(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_cold_weather_shutdown(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (0.6, 33),    # 0.6°C ≈ 33°F
  (48.3, 119),  # 48.3°C ≈ 119°F
  (10, 50),     # 10°C ≈ 50°F
])
async def test_set_cold_weather_shutdown_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_cold_weather_shutdown(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"cwsd": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_f", [32, 120, 0, -10, 200])
async def test_set_cold_weather_shutdown_invalid_fahrenheit(sensorlinx_device_with_patch, invalid_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_f, "F")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_weather_shutdown(temp)
  assert str(excinfo.value) == "Cold weather shutdown must be between 33°F and 119°F or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_c", [-100, 0, 48.4, 100, 1000])
async def test_set_cold_weather_shutdown_invalid_celsius(sensorlinx_device_with_patch, invalid_c):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_c, "C")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_weather_shutdown(temp)
  assert str(excinfo.value) == "Cold weather shutdown must be between 33°F and 119°F or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_str", [
  "invalid", "on", "OFFF", "of", "Offf"
])
async def test_set_cold_weather_shutdown_invalid_string(sensorlinx_device_with_patch, invalid_str):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_weather_shutdown(invalid_str)
  assert str(excinfo.value) == "Cold weather shutdown must be a Temperature instance or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  "K", "celsius", "farenheit", "", None
])
async def test_set_cold_weather_shutdown_invalid_unit(sensorlinx_device_with_patch, invalid_unit):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(ValueError) as excinfo:
    temp = Temperature(10, invalid_unit)
    await device.set_cold_weather_shutdown(temp)
  assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"
  
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Cold weather shutdown must be a Temperature instance or 'off'."),
  (45.6, "Cold weather shutdown must be a Temperature instance or 'off'."),
  (True, "Cold weather shutdown must be a Temperature instance or 'off'."),
  (False, "Cold weather shutdown must be a Temperature instance or 'off'."),
  (["F", 100], "Cold weather shutdown must be a Temperature instance or 'off'."),
  ({"value": 100, "unit": "F"}, "Cold weather shutdown must be a Temperature instance or 'off'."),
  (None, "At least one optional parameter must be provided."),
])
async def test_set_cold_weather_shutdown_invalid_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_weather_shutdown(invalid_input)
  assert str(excinfo.value) == expected_error

##################################################################################################
# Cold Tank Outdoor Reset tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (Temperature(0, "F"), {"cdot": 0}),
  (Temperature(119, "F"), {"cdot": 119}),
  (Temperature(50, "F"), {"cdot": 50}),
  ("off", {"cdot": -41}),
  ("OFF", {"cdot": -41}),
  ("Off", {"cdot": -41}),
])
async def test_set_cold_tank_outdoor_reset_valid(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_cold_tank_outdoor_reset(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (0, 32),      # 0°C == 32°F
  (10, 50),     # 10°C == 50°F
  (48.3, 119),  # 48.3°C ≈ 119°F
])
async def test_set_cold_tank_outdoor_reset_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_cold_tank_outdoor_reset(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"cdot": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_f", [-1, 120, 200, -100, 1000])
async def test_set_cold_tank_outdoor_reset_invalid_fahrenheit(sensorlinx_device_with_patch, invalid_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_f, "F")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_outdoor_reset(temp)
  assert str(excinfo.value) == "Cold tank outdoor reset must be between 0°F and 119°F or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_c", [-100, -18, 48.4, 100, 1000])
async def test_set_cold_tank_outdoor_reset_invalid_celsius(sensorlinx_device_with_patch, invalid_c):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_c, "C")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_outdoor_reset(temp)
  assert str(excinfo.value) == "Cold tank outdoor reset must be between 0°F and 119°F or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_str", [
  "invalid", "on", "OFFF", "of", "Offf"
])
async def test_set_cold_tank_outdoor_reset_invalid_string(sensorlinx_device_with_patch, invalid_str):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_outdoor_reset(invalid_str)
  assert str(excinfo.value) == "Cold tank outdoor reset must be a Temperature instance or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  "K", "celsius", "farenheit", "", None
])
async def test_set_cold_tank_outdoor_reset_invalid_unit(sensorlinx_device_with_patch, invalid_unit):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(ValueError) as excinfo:
    temp = Temperature(10, invalid_unit)
    await device.set_cold_tank_outdoor_reset(temp)
  assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Cold tank outdoor reset must be a Temperature instance or 'off'."),
  (45.6, "Cold tank outdoor reset must be a Temperature instance or 'off'."),
  (True, "Cold tank outdoor reset must be a Temperature instance or 'off'."),
  (False, "Cold tank outdoor reset must be a Temperature instance or 'off'."),
  (["F", 100], "Cold tank outdoor reset must be a Temperature instance or 'off'."),
  ({"value": 100, "unit": "F"}, "Cold tank outdoor reset must be a Temperature instance or 'off'."),
  (None, "At least one optional parameter must be provided."),
])
async def test_set_cold_tank_outdoor_reset_invalid_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_outdoor_reset(invalid_input)
  assert str(excinfo.value) == expected_error
  

##################################################################################################
# Cold Tank Differential tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("fahrenheit,expected_json", [
  (2, {"clDif": 2}),
  (50, {"clDif": 50}),
  (100, {"clDif": 100}),
])
async def test_set_cold_tank_differential_valid_fahrenheit(sensorlinx_device_with_patch, fahrenheit, expected_json):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(fahrenheit, "F")
  await device.set_cold_tank_differential(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected_json

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (1.1, 34),    # 1.1°C ≈ 34°F (rounded)
  (10, 50),     # 10°C ≈ 50°F
  (37.7, 100),  # 37.7°C ≈ 100°F
])
async def test_set_cold_tank_differential_valid_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_cold_tank_differential(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"clDif": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_f", [1, 0, 101, 200, -10])
async def test_set_cold_tank_differential_invalid_fahrenheit(sensorlinx_device_with_patch, invalid_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_f, "F")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_differential(temp)
  assert str(excinfo.value) == "Cold tank differential must be between 2°F and 100°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_c", [-100, -17, 38, 100, 1000])
async def test_set_cold_tank_differential_invalid_celsius(sensorlinx_device_with_patch, invalid_c):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_c, "C")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_differential(temp)
  assert str(excinfo.value) == "Cold tank differential must be between 2°F and 100°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  "K", "celsius", "farenheit", "", None
])
async def test_set_cold_tank_differential_invalid_unit(sensorlinx_device_with_patch, invalid_unit):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(ValueError) as excinfo:
    temp = Temperature(10, invalid_unit)
    await device.set_cold_tank_differential(temp)
  assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Cold tank differential must be a Temperature instance."),
  (45.6, "Cold tank differential must be a Temperature instance."),
  (True, "Cold tank differential must be a Temperature instance."),
  (False, "Cold tank differential must be a Temperature instance."),
  ("100F", "Cold tank differential must be a Temperature instance."),
  ("180", "Cold tank differential must be a Temperature instance."),
  (["F", 100], "Cold tank differential must be a Temperature instance."),
  ({"value": 100, "unit": "F"}, "Cold tank differential must be a Temperature instance."),
  (None, "At least one optional parameter must be provided."),
])
async def test_set_cold_tank_differential_non_temperature_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_differential(invalid_input)
  assert str(excinfo.value) == expected_error


##################################################################################################
# Cold Tank Minimum Temperature tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("fahrenheit,expected_json", [
  (2, {"dst": 2}),
  (32, {"dst": 32}),
  (100, {"dst": 100}),
  (180, {"dst": 180}),
])
async def test_set_cold_tank_min_temp_valid_fahrenheit(sensorlinx_device_with_patch, fahrenheit, expected_json):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(fahrenheit, "F")
  await device.set_cold_tank_min_temp(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected_json

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (1.1, 34),    # 1.1°C ≈ 34°F (rounded)
  (37.8, 100),  # 37.8°C ≈ 100°F
  (82.2, 180),  # 82.2°C ≈ 180°F
])
async def test_set_cold_tank_min_temp_valid_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_cold_tank_min_temp(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"dst": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_f", [1, 0, 181, 200, -10])
async def test_set_cold_tank_min_temp_invalid_fahrenheit(sensorlinx_device_with_patch, invalid_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_f, "F")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_min_temp(temp)
  assert str(excinfo.value) == "Cold tank min temperature must be between 2°F and 180°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_c", [-100, -17, 82.3, 100, 1000])
async def test_set_cold_tank_min_temp_invalid_celsius(sensorlinx_device_with_patch, invalid_c):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_c, "C")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_min_temp(temp)
  assert str(excinfo.value) == "Cold tank min temperature must be between 2°F and 180°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  "K", "celsius", "farenheit", "", None
])
async def test_set_cold_tank_min_temp_invalid_unit(sensorlinx_device_with_patch, invalid_unit):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(ValueError) as excinfo:
    temp = Temperature(10, invalid_unit)
    await device.set_cold_tank_min_temp(temp)
  assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Cold tank min temperature must be a Temperature instance."),
  (45.6, "Cold tank min temperature must be a Temperature instance."),
  (True, "Cold tank min temperature must be a Temperature instance."),
  (False, "Cold tank min temperature must be a Temperature instance."),
  ("100F", "Cold tank min temperature must be a Temperature instance."),
  ("180", "Cold tank min temperature must be a Temperature instance."),
  (["F", 100], "Cold tank min temperature must be a Temperature instance."),
  ({"value": 100, "unit": "F"}, "Cold tank min temperature must be a Temperature instance."),
  (None, "At least one optional parameter must be provided."),
])
async def test_set_cold_tank_min_temp_non_temperature_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_min_temp(invalid_input)
  assert str(excinfo.value) == expected_error


##################################################################################################
# Cold Tank Maximum Temperature tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("fahrenheit,expected_json", [
  (2, {"mst": 2}),
  (32, {"mst": 32}),
  (100, {"mst": 100}),
  (180, {"mst": 180}),
])
async def test_set_cold_tank_max_temp_valid_fahrenheit(sensorlinx_device_with_patch, fahrenheit, expected_json):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(fahrenheit, "F")
  await device.set_cold_tank_max_temp(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected_json

@pytest.mark.asyncio
@pytest.mark.parametrize("celsius,expected_f", [
  (1.1, 34),    # 1.1°C ≈ 34°F (rounded)
  (37.8, 100),  # 37.8°C ≈ 100°F
  (82.2, 180),  # 82.2°C ≈ 180°F
])
async def test_set_cold_tank_max_temp_valid_celsius(sensorlinx_device_with_patch, celsius, expected_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(celsius, "C")
  await device.set_cold_tank_max_temp(temp)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == {"mst": expected_f}

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_f", [1, 0, 181, 200, -10])
async def test_set_cold_tank_max_temp_invalid_fahrenheit(sensorlinx_device_with_patch, invalid_f):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_f, "F")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_max_temp(temp)
  assert str(excinfo.value) == "Cold tank max temperature must be between 2°F and 180°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_c", [-100, -17, 82.3, 100, 1000])
async def test_set_cold_tank_max_temp_invalid_celsius(sensorlinx_device_with_patch, invalid_c):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  temp = Temperature(invalid_c, "C")
  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_max_temp(temp)
  assert str(excinfo.value) == "Cold tank max temperature must be between 2°F and 180°F."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_unit", [
  "K", "celsius", "farenheit", "", None
])
async def test_set_cold_tank_max_temp_invalid_unit(sensorlinx_device_with_patch, invalid_unit):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(ValueError) as excinfo:
    temp = Temperature(10, invalid_unit)
    await device.set_cold_tank_max_temp(temp)
  assert str(excinfo.value) == "Unit must be 'C' for Celsius or 'F' for Fahrenheit"
  
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input,expected_error", [
  (123, "Cold tank max temperature must be a Temperature instance."),
  (45.6, "Cold tank max temperature must be a Temperature instance."),
  (True, "Cold tank max temperature must be a Temperature instance."),
  (False, "Cold tank max temperature must be a Temperature instance."),
  (None, "At least one optional parameter must be provided."),
  ("100F", "Cold tank max temperature must be a Temperature instance."),
  ("180", "Cold tank max temperature must be a Temperature instance."),
  (["F", 100], "Cold tank max temperature must be a Temperature instance."),
  ({"value": 100, "unit": "F"}, "Cold tank max temperature must be a Temperature instance."),
])
async def test_set_cold_tank_max_temp_non_temperature_type(sensorlinx_device_with_patch, invalid_input, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_cold_tank_max_temp(invalid_input)
  assert str(excinfo.value) == expected_error
  

##################################################################################################
# Backup Lag Time tests
##################################################################################################

@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [
  (1, {"bkLag": 1}),
  (120, {"bkLag": 120}),
  (240, {"bkLag": 240}),
  ("off", {"bkLag": 0}),
  ("OFF", {"bkLag": 0}),
  ("Off", {"bkLag": 0}),
])
async def test_set_backup_lag_time_valid(sensorlinx_device_with_patch, value, expected):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  await device.set_backup_lag_time(value)

  assert sensorlinx._session.patch.call_count == 1
  _, kwargs = sensorlinx._session.patch.call_args
  assert kwargs["json"] == expected

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_value", [
  0, -1, 241, 1000,
  "invalid", "on", "OFFF", "of", "Offf"
])
async def test_set_backup_lag_time_invalid(sensorlinx_device_with_patch, invalid_value):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_backup_lag_time(invalid_value)
  assert str(excinfo.value) == "Backup lag time must be an integer between 1 and 240 or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_int", [
  0, -1, 241, 1000
])
async def test_set_backup_lag_time_invalid_int(sensorlinx_device_with_patch, invalid_int):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_backup_lag_time(invalid_int)
  assert str(excinfo.value) == "Backup lag time must be an integer between 1 and 240 or 'off'."

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_type,expected_error", [
  (12.5, "Backup lag time must be an integer between 1 and 240 or 'off'."),
  (True, "Backup lag time must be an integer between 1 and 240 or 'off'."),
  (False, "Backup lag time must be an integer between 1 and 240 or 'off'."),
  (None, "At least one optional parameter must be provided."),
  (["off"], "Backup lag time must be an integer between 1 and 240 or 'off'."),
  ({"value": 10}, "Backup lag time must be an integer between 1 and 240 or 'off'."),
])
async def test_set_backup_lag_time_invalid_type(sensorlinx_device_with_patch, invalid_type, expected_error):
  sensorlinx, device, mock_patch = sensorlinx_device_with_patch

  with pytest.raises(InvalidParameterError) as excinfo:
    await device.set_backup_lag_time(invalid_type)
  assert str(excinfo.value) == expected_error