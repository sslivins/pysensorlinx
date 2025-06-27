import pytest
from unittest.mock import AsyncMock, MagicMock
from pysensorlinx import Sensorlinx, SensorlinxDevice, InvalidParameterError

@pytest.mark.asyncio
async def test_set_hvac_mode_priority_to_heat():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id="building123",
        device_id="device456"
    )

    # Prepare a mock session and patch method
    sensorlinx._session = MagicMock()
    mock_patch = MagicMock()
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_patch.return_value = mock_response
    sensorlinx._session.patch = mock_patch

    await device.set_hvac_mode_priority("heat")

    # Now inspect the call to patch
    assert sensorlinx._session.patch.call_count == 1
    _, kwargs = sensorlinx._session.patch.call_args
    assert kwargs["json"] == {"prior": 0}
    
@pytest.mark.asyncio
async def test_set_hvac_mode_priority_to_cold():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id="building123",
        device_id="device456"
    )

    # Prepare a mock session and patch method
    sensorlinx._session = MagicMock()
    mock_patch = MagicMock()
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_patch.return_value = mock_response
    sensorlinx._session.patch = mock_patch

    await device.set_hvac_mode_priority("cool")

    # Now inspect the call to patch
    assert sensorlinx._session.patch.call_count == 1
    _, kwargs = sensorlinx._session.patch.call_args
    assert kwargs["json"] == {"prior": 1}    
    
@pytest.mark.asyncio
async def test_set_hvac_mode_priority_to_auto():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id="building123",
        device_id="device456"
    )

    # Prepare a mock session and patch method
    sensorlinx._session = MagicMock()
    mock_patch = MagicMock()
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_patch.return_value = mock_response
    sensorlinx._session.patch = mock_patch

    await device.set_hvac_mode_priority("auto")

    # Now inspect the call to patch
    assert sensorlinx._session.patch.call_count == 1
    _, kwargs = sensorlinx._session.patch.call_args
    assert kwargs["json"] == {"prior": 2}
    
@pytest.mark.asyncio
async def test_set_hvac_mode_priority_invalid_value():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id="building123",
        device_id="device456"
    )

    with pytest.raises(InvalidParameterError) as excinfo:
        await device.set_hvac_mode_priority("invalid_value")
        
    assert str(excinfo.value) == "Invalid HVAC mode priority. Must be 'cool', 'heat' or 'auto'."
    
@pytest.mark.asyncio
async def test_set_permanent_hd_on():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id="building123",
        device_id="device456"
    )

    # Prepare a mock session and patch method
    sensorlinx._session = MagicMock()
    mock_patch = MagicMock()
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_patch.return_value = mock_response
    sensorlinx._session.patch = mock_patch

    await device.set_permanent_hd(True)

    # Now inspect the call to patch
    assert sensorlinx._session.patch.call_count == 1
    _, kwargs = sensorlinx._session.patch.call_args
    assert kwargs["json"] == {"permHD": 1}
    
@pytest.mark.asyncio
async def test_set_permanent_hd_off():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id="building123",
        device_id="device456"
    )

    # Prepare a mock session and patch method
    sensorlinx._session = MagicMock()
    mock_patch = MagicMock()
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_patch.return_value = mock_response
    sensorlinx._session.patch = mock_patch

    await device.set_permanent_hd(False)

    # Now inspect the call to patch
    assert sensorlinx._session.patch.call_count == 1
    _, kwargs = sensorlinx._session.patch.call_args
    assert kwargs["json"] == {"permHD": 0}
    
@pytest.mark.asyncio
async def test_set_permanent_cd_on():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(
      sensorlinx=sensorlinx,
      building_id="building123",
      device_id="device456"
    )

    # Prepare a mock session and patch method
    sensorlinx._session = MagicMock()
    mock_patch = MagicMock()
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_patch.return_value = mock_response
    sensorlinx._session.patch = mock_patch

    await device.set_permanent_cd(True)

    # Now inspect the call to patch
    assert sensorlinx._session.patch.call_count == 1
    _, kwargs = sensorlinx._session.patch.call_args
    assert kwargs["json"] == {"permCD": 1}
  
@pytest.mark.asyncio
async def test_set_permanent_cd_off():
    sensorlinx = Sensorlinx()
    device = SensorlinxDevice(
      sensorlinx=sensorlinx,
      building_id="building123",
      device_id="device456"
    )

    # Prepare a mock session and patch method
    sensorlinx._session = MagicMock()
    mock_patch = MagicMock()
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_patch.return_value = mock_response
    sensorlinx._session.patch = mock_patch

    await device.set_permanent_cd(False)

    # Now inspect the call to patch
    assert sensorlinx._session.patch.call_count == 1
    _, kwargs = sensorlinx._session.patch.call_args
    assert kwargs["json"] == {"permCD": 0}