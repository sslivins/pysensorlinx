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

    try:
        await sensorlinx.login(username, password)
        profile = await sensorlinx.get_profile()
        assert profile is not None, "Failed to fetch user profile"
        assert profile.get("user", {}).get("email") == username, "User email does not match"
        #pprint.pprint(profile)
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
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

    try:
        await sensorlinx.login(username, password)
        buildings = await sensorlinx.get_buildings()
        pprint.pprint(buildings)
        assert buildings is not None, "Failed to fetch buildings"
        assert isinstance(buildings, list), "Buildings response is not a list"
        assert len(buildings) == 1, "Expected exactly 1 building to be returned"
        assert buildings[0].get("location", {}).get("timezone") == "America/Vancouver", "Expected timezone to be America/Vancouver"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
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

    try:
        await sensorlinx.login(username, password)
        buildings = await sensorlinx.get_buildings(building_id)
        assert buildings is not None, "Failed to fetch building"
        assert isinstance(buildings, dict), "Building response is not a dict"
        assert buildings.get("id") == building_id, "Building ID does not match"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()
    

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

    try:
        await sensorlinx.login(username, password)
        devices = await sensorlinx.get_devices(building_id)
        pprint.pprint(devices)
        assert devices is not None, "Failed to fetch devices"
        assert isinstance(devices, list), "Devices response is not a list"
        assert len(devices) > 0, "Expected at least one device to be returned"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
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

    try:
        await sensorlinx.login(username, password)
        device = await sensorlinx.get_devices(building_id, device_id)
        assert device is not None, "Failed to fetch devices"
        assert isinstance(device, dict), "Devices response is not a dict"
        assert device.get("syncCode") == device_id, "Device ID does not match"
        pprint.pprint(device)
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()
    

# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_enable_permanent_cd():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
#         await sensorlinxdevice.set_permanent_cd(True)
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()
    

# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_enable_permanent_hd():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
#         await sensorlinxdevice.set_permanent_hd(True)
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()
    

# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_set_cold_weather_shutdown_off():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
#         # Test setting cold weather shutdown to 'off'
#         await sensorlinxdevice.set_cold_weather_shutdown("off")
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()
    
    
# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_set_cold_weather_shutdown_5c():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
#         # Test setting cold weather shutdown to 5C
#         await sensorlinxdevice.set_cold_weather_shutdown(Temperature(5, "C"))
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()
    
    
# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_set_warm_weather_shutdown_off():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
#         # Test setting warm weather shutdown to 'off'
#         await sensorlinxdevice.set_warm_weather_shutdown("off")
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()


# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_set_warm_weather_shutdown_30c():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
#         # Test setting warm weather shutdown to 30C
#         await sensorlinxdevice.set_warm_weather_shutdown(Temperature(30, "C"))
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()
    
    
# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_set_hvac_mode_priority_heat():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
#         await sensorlinxdevice.set_hvac_mode_priority("heat")
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()


# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_set_hvac_mode_priority_cool():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
#         await sensorlinxdevice.set_hvac_mode_priority("cool")
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()


# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_set_hvac_mode_priority_auto():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
#         await sensorlinxdevice.set_hvac_mode_priority("auto")
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()
    
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_all_temperatures():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        await sensorlinx.login(username, password)
        sensorlinxdevice = SensorlinxDevice(
            sensorlinx=sensorlinx,
            building_id=building_id,
            device_id=device_id
        )
        temperatures = await sensorlinxdevice.get_temperatures()
        pprint.pprint(temperatures)
        assert temperatures is not None, "Failed to fetch temperatures"
        assert isinstance(temperatures, dict), "Temperatures response is not a dict"
        for key, value in temperatures.items():
            actual = value.get("actual")
            target = value.get("target")
            if actual is not None:
                assert -40 <= actual.value <= 140, f"{key} actual temperature {actual.value}F out of range"
            if target is not None:
                assert -40 <= target.value <= 140, f"{key} target temperature {target.value}F out of range"
        #pprint.pprint(temperatures)
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()


@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_tank_temperature():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        await sensorlinx.login(username, password)
        sensorlinxdevice = SensorlinxDevice(
            sensorlinx=sensorlinx,
            building_id=building_id,
            device_id=device_id
        )
        temperatures = await sensorlinxdevice.get_temperatures("TANK")
        assert temperatures is not None, "Failed to fetch temperatures with title 'TANK'"
        assert isinstance(temperatures, dict), "Temperatures response is not a dict"
        actual = temperatures.get("actual")
        target = temperatures.get("target")
        if actual is not None:
            assert -40 <= actual.value <= 140, f"actual temperature {actual.value}F out of range"
        if target is not None:
            assert -40 <= target.value <= 140, f"target temperature {target.value}F out of range"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()
    
    
# @pytest.mark.live
# @pytest.mark.skipif(
#     not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
#     reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
# )
# @pytest.mark.asyncio
# async def test_live_set_weather_shutdown_lag_time_zero():
#     sensorlinx = Sensorlinx()
#     username = os.getenv("SENSORLINX_EMAIL")
#     password = os.getenv("SENSORLINX_PASSWORD")
#     building_id = os.getenv("SENSORLINX_BUILDING_ID")
#     device_id = os.getenv("SENSORLINX_DEVICE_ID")

#     try:
#         await sensorlinx.login(username, password)
        
#         sensorlinxdevice = SensorlinxDevice(
#             sensorlinx=sensorlinx,
#             building_id=building_id,
#             device_id=device_id
#         )
        
#         await sensorlinxdevice.set_weather_shutdown_lag_time(0)
#     except Exception as e:
#         print(f"Test failed due to exception: {type(e).__name__}: {e}")
#         pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
#     finally:
#         await sensorlinx.close()
        
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_firmware_version():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        await sensorlinx.login(username, password)
        sensorlinxdevice = SensorlinxDevice(
            sensorlinx=sensorlinx,
            building_id=building_id,
            device_id=device_id
        )
        version = await sensorlinxdevice.get_firmware_version()
        assert str(version) == "2.07", f"Expected firmware version '2.07', got '{version}'"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()
        
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_sync_code():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        await sensorlinx.login(username, password)
        sensorlinxdevice = SensorlinxDevice(
            sensorlinx=sensorlinx,
            building_id=building_id,
            device_id=device_id
        )
        sync_code = await sensorlinxdevice.get_sync_code()
        assert sync_code == device_id, f"Expected sync code '{device_id}', got '{sync_code}'"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()
        
        
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_device_pin():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        await sensorlinx.login(username, password)
        sensorlinxdevice = SensorlinxDevice(
            sensorlinx=sensorlinx,
            building_id=building_id,
            device_id=device_id
        )
        pin = await sensorlinxdevice.get_device_pin()
        assert isinstance(pin, str), "PIN should be a string"
        assert len(pin) > 0, "PIN should not be empty"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()
        
        
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_device_type():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        await sensorlinx.login(username, password)
        sensorlinxdevice = SensorlinxDevice(
            sensorlinx=sensorlinx,
            building_id=building_id,
            device_id=device_id
        )
        device_type = await sensorlinxdevice.get_device_type()
        assert device_type == "ECO", f"Expected device type 'ECO', got '{device_type}'"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()
        
@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_runtimes():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        await sensorlinx.login(username, password)
        sensorlinxdevice = SensorlinxDevice(
            sensorlinx=sensorlinx,
            building_id=building_id,
            device_id=device_id
        )
        runtimes = await sensorlinxdevice.get_runtimes()
        assert runtimes is not None, "Failed to fetch runtimes"
        assert isinstance(runtimes, dict), "Runtimes response is not a dict"
        stages = runtimes.get("stages")
        backup = runtimes.get("backup")
        assert isinstance(stages, list), "Stages should be a list"
        assert len(stages) == 2, f"Expected 2 stages, got {len(stages)}"
        assert backup is not None, "Backup should not be None"
        #pprint.pprint(runtimes)
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()
        

@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_heatpump_stages_state():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        await sensorlinx.login(username, password)
        sensorlinxdevice = SensorlinxDevice(
            sensorlinx=sensorlinx,
            building_id=building_id,
            device_id=device_id
        )
        stages_state = await sensorlinxdevice.get_heatpump_stages_state()
        pprint.pprint(stages_state)
        assert stages_state is not None, "Failed to fetch stages state"
        assert isinstance(stages_state, list), "Stages state response is not a list"
        assert len(stages_state) > 0, "Expected at least one stage"
        
        # Validate structure of each stage
        for stage in stages_state:
            assert isinstance(stage, dict), "Each stage should be a dict"
            assert 'activated' in stage, "Stage should have 'activated' key"
            assert 'enabled' in stage, "Stage should have 'enabled' key"
            assert 'title' in stage, "Stage should have 'title' key"
            assert 'device' in stage, "Stage should have 'device' key"
            assert 'index' in stage, "Stage should have 'index' key"
            assert 'runTime' in stage, "Stage should have 'runTime' key"
            assert isinstance(stage['activated'], bool), "'activated' should be a bool"
            assert isinstance(stage['enabled'], bool), "'enabled' should be a bool"
            assert isinstance(stage['title'], str), "'title' should be a string"
            assert isinstance(stage['device'], str), "'device' should be a string"
            assert isinstance(stage['index'], int), "'index' should be an int"
            assert isinstance(stage['runTime'], str), "'runTime' should be a string"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()


@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD") or not os.getenv("SENSORLINX_BUILDING_ID") or not os.getenv("SENSORLINX_DEVICE_ID"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD or SENSORLINX_BUILDING_ID or SENSORLINX_DEVICE_ID environment variable not set"
)
@pytest.mark.asyncio
async def test_live_get_backup_state():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    try:
        await sensorlinx.login(username, password)
        sensorlinxdevice = SensorlinxDevice(
            sensorlinx=sensorlinx,
            building_id=building_id,
            device_id=device_id
        )
        backup_state = await sensorlinxdevice.get_backup_state()
        pprint.pprint(backup_state)
        assert backup_state is not None, "Failed to fetch backup state"
        assert isinstance(backup_state, dict), "Backup state response is not a dict"
        
        # Validate structure of backup
        assert 'activated' in backup_state, "Backup should have 'activated' key"
        assert 'enabled' in backup_state, "Backup should have 'enabled' key"
        assert 'title' in backup_state, "Backup should have 'title' key"
        assert 'runTime' in backup_state, "Backup should have 'runTime' key"
        assert isinstance(backup_state['activated'], bool), "'activated' should be a bool"
        assert isinstance(backup_state['enabled'], bool), "'enabled' should be a bool"
        assert isinstance(backup_state['title'], str), "'title' should be a string"
        assert isinstance(backup_state['runTime'], str), "'runTime' should be a string"
    except Exception as e:
        print(f"Test failed due to exception: {type(e).__name__}: {e}")
        pytest.fail(f"Test failed due to exception: {type(e).__name__}: {e}")
    finally:
        await sensorlinx.close()
