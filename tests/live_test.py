import pytest
import os
from pysensorlinx import Sensorlinx, Temperature, SensorlinxDevice, InvalidCredentialsError, LoginTimeoutError, LoginError
from dotenv import load_dotenv
import pprint

# Load environment variables from .env file
load_dotenv()

@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD environment variable not set"
)
@pytest.mark.asyncio
async def test_live_login_and_user_profile():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")

    assert username is not None, "SENSORLINX_EMAIL is not set"
    assert password is not None, "SENSORLINX_PASSWORD is not set"

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"

    profile = await sensorlinx.get_profile()
    assert profile is not None, "Failed to fetch user profile"
    assert profile.get("user", {}).get("email") == username, "User email does not match"
    
    #print user profile fopr debugging
    pprint.pprint(profile)

    await sensorlinx.close()
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_all_buildings():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"

    buildings = await sensorlinx.get_buildings()
    assert buildings is not None, "Failed to fetch buildings"
    assert isinstance(buildings, list), "Buildings response is not a list"
    assert len(buildings) == 1, "Expected exactly 1 building to be returned"
    assert buildings[0].get("location", {}).get("timezone") == "America/Vancouver", "Expected timezone to be America/Vancouver"

    await sensorlinx.close()
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_specific_building():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"

    buildings = await sensorlinx.get_buildings(building_id)
    assert buildings is not None, "Failed to fetch building"
    assert isinstance(buildings, dict), "Building response is not a dict"
    assert buildings.get("id") == building_id, "Building ID does not match"

    await sensorlinx.close() 
    
#test to get all devices in a building
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_all_devices():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"

    devices = await sensorlinx.get_devices(building_id)
    assert devices is not None, "Failed to fetch devices"
    assert isinstance(devices, list), "Devices response is not a list"
    assert len(devices) > 0, "Expected at least one device to be returned"

    await sensorlinx.close()
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_specific_device():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"

    device = await sensorlinx.get_devices(building_id, device_id)
    assert device is not None, "Failed to fetch devices"
    assert isinstance(device, dict), "Devices response is not a dict"
    assert device.get("syncCode") == device_id, "Device ID does not match"

    pprint.pprint(device)

    await sensorlinx.close()
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_enable_permanent_cd():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"
    
    
    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )
    
    result = await sensorlinxdevice.set_permanent_cd(True)

    assert result is True, "Failed to enable permanent cooling demand"
    
    await sensorlinx.close()
    

@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_enable_permanent_hd():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"
    
    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )
    
    result = await sensorlinxdevice.set_permanent_hd(True)

    assert result is True, "Failed to enable permanent heating demand"
    
    await sensorlinx.close()
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_set_cold_weather_shutdown_off():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"
    
    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )

    # Test setting cold weather shutdown to 'off'
    result = await sensorlinxdevice.set_cold_weather_shutdown("off")
    assert result is True, "Failed to set cold weather shutdown to 'off'"

    await sensorlinx.close()
    
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_set_cold_weather_shutdown_5c():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"
    
    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )

    # Test setting cold weather shutdown to 5C
    result = await sensorlinxdevice.set_cold_weather_shutdown(Temperature(5, "C"))
    assert result is True, "Failed to set cold weather shutdown to 5C"

    await sensorlinx.close()
    
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_set_warm_weather_shutdown_off():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"    
    
    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )

    # Test setting warm weather shutdown to 'off'
    result = await sensorlinxdevice.set_warm_weather_shutdown("off")
    assert result is True, "Failed to set warm weather shutdown to 'off'"

    await sensorlinx.close()


@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_set_warm_weather_shutdown_30c():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"    
    
    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )

    # Test setting warm weather shutdown to 30C
    result = await sensorlinxdevice.set_warm_weather_shutdown(Temperature(30, "C"))
    assert result is True, "Failed to set warm weather shutdown to 30C"

    await sensorlinx.close()
    
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_set_hvac_mode_priority_heat():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"    
    
    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )

    result = await sensorlinxdevice.set_hvac_mode_priority("heat")
    assert result is True, "Failed to set HVAC mode priority to 'heat'"

    await sensorlinx.close()


@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_set_hvac_mode_priority_cool():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"

    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )

    result = await sensorlinxdevice.set_hvac_mode_priority("cool")
    assert result is True, "Failed to set HVAC mode priority to 'cool'"

    await sensorlinx.close()


@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_set_hvac_mode_priority_auto():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"

    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )

    result = await sensorlinxdevice.set_hvac_mode_priority("auto")
    assert result is True, "Failed to set HVAC mode priority to 'auto'"

    await sensorlinx.close()
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_temperatures():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"

    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )

    temperatures = await sensorlinxdevice.get_temperatures()
    assert temperatures is not None, "Failed to fetch temperatures"
    assert isinstance(temperatures, dict), "Temperatures response is not a dict"
    pprint.pprint(temperatures)

    await sensorlinx.close()


@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_temperatures_with_title_tank():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        result = await sensorlinx.login(username, password)
        assert result is True, "Login failed"
    except Exception as e:
        print(f"Login error: {e}")
        assert False, f"Login raised an exception: {e}"

    sensorlinxdevice = SensorlinxDevice(
        sensorlinx=sensorlinx,
        building_id=building_id,
        device_id=device_id
    )

    temperatures = await sensorlinxdevice.get_temperatures("TANK")
    assert temperatures is not None, "Failed to fetch temperatures with title 'TANK'"
    assert isinstance(temperatures, dict), "Temperatures response is not a dict"
    pprint.pprint(temperatures)

    await sensorlinx.close()



    
