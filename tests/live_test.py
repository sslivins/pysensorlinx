import pytest
import os
from pysensorlinx import Sensorlinx
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

    await sensorlinx.login(username, password)

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

    await sensorlinx.login(username, password)

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

    await sensorlinx.login(username, password)

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

    await sensorlinx.login(username, password)

    devices = await sensorlinx.get_devices(building_id, device_id)
    assert devices is not None, "Failed to fetch devices"
    assert isinstance(devices, dict), "Devices response is not a dict"
    assert devices.get("syncCode") == device_id, "Device ID does not match"

    await sensorlinx.close()  
