import os
import pytest
from aioresponses import aioresponses
from pyomnisense.omnisense import Omnisense, LOGIN_URL, SITE_LIST_URL, SENSOR_LIST_URL

@pytest.mark.asyncio
async def test_get_site_and_sensor_list():
    # Load sample HTML content for the site list and sensor list from local files.
    site_file_path = os.path.join(os.path.dirname(__file__), "samples", "site_list.html")
    sensor_file_path = os.path.join(os.path.dirname(__file__), "samples", "sensor.html")
    
    with open(site_file_path, "r", encoding="utf-8") as f:
        site_html = f.read()
    
    with open(sensor_file_path, "r", encoding="utf-8") as f:
        sensor_html = f.read()
    
    omnisense = Omnisense()
    
    # Use aioresponses context to fake all external HTTP calls.
    with aioresponses() as m:
        # Fake successful login response.
        m.post(LOGIN_URL, status=200, body="Logged In!")
        # Fake site list GET request.
        m.get(SITE_LIST_URL, status=200, body=site_html)
        
        # Call login, which hits the faked LOGIN_URL.
        login_result = await omnisense.login("testuser", "testpass")
        assert login_result is True
        
        # Call get_site_list to hit the faked SITE_LIST_URL and obtain the site dictionary.
        site_result = await omnisense.get_site_list()
        # Expecting exactly this dictionary.
        expected_site_result = {'123456': 'MySite', '654321': 'FirstSite'}
        assert site_result == expected_site_result
        
        # Use the first site's number from the site list.
        first_site_nbr = list(site_result.keys())[0]
        
        # Construct expected sensor URL based on first site's number.
        sensor_url = f"{SENSOR_LIST_URL}?siteNbr={first_site_nbr}"
        # Fake sensor list GET request with the sample sensor HTML.
        m.get(sensor_url, status=200, body=sensor_html)
        
        # Call a (presumed) method get_sensor_list to fetch sensor data for the given site.
        sensor_result = await omnisense.get_site_sensor_list(first_site_nbr)
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {'2A000001': {'description': 'Dining Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000002': {'description': 'Basement', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000003': {'description': 'Gateway', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000004': {'description': 'Kitchen', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000005': {'description': 'Laundry Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '6BC00000': {'description': '<description not set>', 'sensor_type': 'S-100', 'site_name': 'MySite'}}
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()