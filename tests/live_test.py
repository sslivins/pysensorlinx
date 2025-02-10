import pytest
import os
from pyomnisense import Omnisense
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("OMNISENSE_USERNAME") or not os.getenv("OMNISENSE_PASSWORD"),
    reason="OMNISENSE_USERNAME or OMNISENSE_PASSWORD environment variable not set"
)
@pytest.mark.asyncio
async def test_live_login_and_fetch_data():
    omnisense = Omnisense()
    username = os.getenv("OMNISENSE_USERNAME")
    password = os.getenv("OMNISENSE_PASSWORD")

    assert username is not None, "OMNISENSE_USERNAME is not set"
    assert password is not None, "OMNISENSE_PASSWORD is not set"

    result = await omnisense.login(username, password)
    assert result is True, "Login failed"

    sites = await omnisense.get_site_list()
    expected_result = {'119345': 'Home', '143554': 'BDL'}
    assert sites == expected_result

    sensor_data = await omnisense.get_sensor_data()

    #verify there are 14 sensors and that the correct keys are there for each sensor but ignore the values
    assert len(sensor_data) == 14
    for key, data in sensor_data.items():
        for key in data.keys():
            assert len(data.keys()) == 12
            assert 'description' in data
            assert 'last_activity' in data
            assert 'status' in data
            assert 'temperature' in data
            assert 'relative_humidity' in data
            assert 'absolute_humidity' in data
            assert 'dew_point' in data
            assert 'wood_pct' in data
            assert 'battery_voltage' in data
            assert 'sensor_type' in data
            assert 'sensor_id' in data
            assert 'site_name' in data

    await omnisense.close()