import os
import pytest
from aioresponses import aioresponses
from pyomnisense.omnisense import Omnisense, LOGIN_URL, SITE_LIST_URL, SENSOR_LIST_URL

@pytest.mark.asyncio
async def test_get_sensor_list_no_args():
    # Load sample HTML content for the site list and sensor list from local files.
    site_file_path = os.path.join(os.path.dirname(__file__), "samples", "site_list.html")
    site_123456_sensors_file_path = os.path.join(os.path.dirname(__file__), "samples", "sensor_123456.html")
    site_654321_sensors_file_path = os.path.join(os.path.dirname(__file__), "samples", "sensor_654321.html")
    
    with open(site_file_path, "r", encoding="utf-8") as f:
        site_html = f.read()
    
    with open(site_123456_sensors_file_path, "r", encoding="utf-8") as f:
        site_123456_sensors_html = f.read()
        
    with open(site_654321_sensors_file_path, "r", encoding="utf-8") as f:
        site_654321_sensors_html = f.read()        
    
    omnisense = Omnisense()
    
    # Use aioresponses context to fake all external HTTP calls.
    with aioresponses() as m:
        # Fake successful login response.
        m.post(LOGIN_URL, status=200, body="Logged In!")
        
        # Call login, which hits the faked LOGIN_URL.
        login_result = await omnisense.login("testuser", "testpass")
        assert login_result is True
        
        # Call get_site_list to hit the faked SITE_LIST_URL and obtain the site dictionary.
        # Fake site list GET request.
        m.get(SITE_LIST_URL, status=200, body=site_html)
        
        # Construct expected sensor URL based on first site's number.
        site_123456_url = f"{SENSOR_LIST_URL}?siteNbr=123456"
        # Fake sensor list GET request with the sample sensor HTML.
        m.get(site_123456_url, status=200, body=site_123456_sensors_html)
                
        site_654321_url = f"{SENSOR_LIST_URL}?siteNbr=654321"
        # Fake sensor list GET request with the sample sensor HTML.
        m.get(site_654321_url, status=200, body=site_654321_sensors_html)

        sensor_result = await omnisense.get_site_sensor_list()
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {'2A000001': {'description': 'Dining Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000002': {'description': 'Basement', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000003': {'description': 'Gateway', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000004': {'description': 'Kitchen', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000005': {'description': 'Laundry Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '6BC00000': {'description': '<description not set>', 'sensor_type': 'S-100', 'site_name': 'MySite'},
                                  '2A001001': {'description': 'Dining Room', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001002': {'description': 'Basement', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001003': {'description': 'Gateway', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001004': {'description': 'Kitchen', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001005': {'description': 'Laundry Room', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}
                                }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()

@pytest.mark.asyncio
async def test_get_sensor_list_pass_site_id_dict():
    # Load sample HTML content for the site list and sensor list from local files.
    site_file_path = os.path.join(os.path.dirname(__file__), "samples", "site_list.html")
    site_123456_sensors_file_path = os.path.join(os.path.dirname(__file__), "samples", "sensor_123456.html")
    site_654321_sensors_file_path = os.path.join(os.path.dirname(__file__), "samples", "sensor_654321.html")
    
    with open(site_file_path, "r", encoding="utf-8") as f:
        site_html = f.read()
    
    with open(site_123456_sensors_file_path, "r", encoding="utf-8") as f:
        site_123456_sensors_html = f.read()
        
    with open(site_654321_sensors_file_path, "r", encoding="utf-8") as f:
        site_654321_sensors_html = f.read()        
    
    omnisense = Omnisense()
    
    # Use aioresponses context to fake all external HTTP calls.
    with aioresponses() as m:
        # Fake successful login response.
        m.post(LOGIN_URL, status=200, body="Logged In!")
        
        # Call login, which hits the faked LOGIN_URL.
        login_result = await omnisense.login("testuser", "testpass")
        assert login_result is True
        
        # Call get_site_list to hit the faked SITE_LIST_URL and obtain the site dictionary.
        # Fake site list GET request.
        m.get(SITE_LIST_URL, status=200, body=site_html)
        
        # Construct expected sensor URL based on first site's number.
        site_123456_url = f"{SENSOR_LIST_URL}?siteNbr=123456"
        # Fake sensor list GET request with the sample sensor HTML.
        m.get(site_123456_url, status=200, body=site_123456_sensors_html)
                
        site_654321_url = f"{SENSOR_LIST_URL}?siteNbr=654321"
        # Fake sensor list GET request with the sample sensor HTML.
        m.get(site_654321_url, status=200, body=site_654321_sensors_html)
        
        site_ids = await omnisense.get_site_list()

        sensor_result = await omnisense.get_site_sensor_list(site_ids)
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {'2A000001': {'description': 'Dining Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000002': {'description': 'Basement', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000003': {'description': 'Gateway', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000004': {'description': 'Kitchen', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000005': {'description': 'Laundry Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '6BC00000': {'description': '<description not set>', 'sensor_type': 'S-100', 'site_name': 'MySite'},
                                  '2A001001': {'description': 'Dining Room', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001002': {'description': 'Basement', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001003': {'description': 'Gateway', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001004': {'description': 'Kitchen', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001005': {'description': 'Laundry Room', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}
                                }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()
        
@pytest.mark.asyncio
async def test_get_sensor_list_pass_site_id_list():
    # Load sample HTML content for the site list and sensor list from local files.
    site_file_path = os.path.join(os.path.dirname(__file__), "samples", "site_list.html")
    site_123456_sensors_file_path = os.path.join(os.path.dirname(__file__), "samples", "sensor_123456.html")
    site_654321_sensors_file_path = os.path.join(os.path.dirname(__file__), "samples", "sensor_654321.html")
    
    with open(site_file_path, "r", encoding="utf-8") as f:
        site_html = f.read()
    
    with open(site_123456_sensors_file_path, "r", encoding="utf-8") as f:
        site_123456_sensors_html = f.read()
        
    with open(site_654321_sensors_file_path, "r", encoding="utf-8") as f:
        site_654321_sensors_html = f.read()        
    
    omnisense = Omnisense()
    
    # Use aioresponses context to fake all external HTTP calls.
    with aioresponses() as m:
        # Fake successful login response.
        m.post(LOGIN_URL, status=200, body="Logged In!")
        
        # Call login, which hits the faked LOGIN_URL.
        login_result = await omnisense.login("testuser", "testpass")
        assert login_result is True
        
        # Call get_site_list to hit the faked SITE_LIST_URL and obtain the site dictionary.
        # Fake site list GET request.
        m.get(SITE_LIST_URL, status=200, body=site_html)
        
        # Construct expected sensor URL based on first site's number.
        site_123456_url = f"{SENSOR_LIST_URL}?siteNbr=123456"
        # Fake sensor list GET request with the sample sensor HTML.
        m.get(site_123456_url, status=200, body=site_123456_sensors_html)
                
        site_654321_url = f"{SENSOR_LIST_URL}?siteNbr=654321"
        # Fake sensor list GET request with the sample sensor HTML.
        m.get(site_654321_url, status=200, body=site_654321_sensors_html)
        
        site_ids = await omnisense.get_site_list()

        sensor_result = await omnisense.get_site_sensor_list(list(site_ids.keys()))
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {'2A000001': {'description': 'Dining Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000002': {'description': 'Basement', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000003': {'description': 'Gateway', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000004': {'description': 'Kitchen', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000005': {'description': 'Laundry Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '6BC00000': {'description': '<description not set>', 'sensor_type': 'S-100', 'site_name': 'MySite'},
                                  '2A001001': {'description': 'Dining Room', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001002': {'description': 'Basement', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001003': {'description': 'Gateway', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001004': {'description': 'Kitchen', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}, 
                                  '2A001005': {'description': 'Laundry Room', 'sensor_type': 'S-11', 'site_name': 'FirstSite'}
                                }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()
        
@pytest.mark.asyncio
async def test_get_sensor_list_pass_single_site_id_string():
    # Load sample HTML content for the site list and sensor list from local files.
    site_file_path = os.path.join(os.path.dirname(__file__), "samples", "site_list.html")
    site_123456_sensors_file_path = os.path.join(os.path.dirname(__file__), "samples", "sensor_123456.html")
    site_654321_sensors_file_path = os.path.join(os.path.dirname(__file__), "samples", "sensor_654321.html")
    
    with open(site_file_path, "r", encoding="utf-8") as f:
        site_html = f.read()
    
    with open(site_123456_sensors_file_path, "r", encoding="utf-8") as f:
        site_123456_sensors_html = f.read()
        
    with open(site_654321_sensors_file_path, "r", encoding="utf-8") as f:
        site_654321_sensors_html = f.read()        
    
    omnisense = Omnisense()
    
    # Use aioresponses context to fake all external HTTP calls.
    with aioresponses() as m:
        # Fake successful login response.
        m.post(LOGIN_URL, status=200, body="Logged In!")
        
        # Call login, which hits the faked LOGIN_URL.
        login_result = await omnisense.login("testuser", "testpass")
        assert login_result is True
        
        # Call get_site_list to hit the faked SITE_LIST_URL and obtain the site dictionary.
        # Fake site list GET request.
        m.get(SITE_LIST_URL, status=200, body=site_html)
        
        # Construct expected sensor URL based on first site's number.
        site_123456_url = f"{SENSOR_LIST_URL}?siteNbr=123456"
        # Fake sensor list GET request with the sample sensor HTML.
        m.get(site_123456_url, status=200, body=site_123456_sensors_html)
                
        sensor_result = await omnisense.get_site_sensor_list("123456")
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {'2A000001': {'description': 'Dining Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000002': {'description': 'Basement', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000003': {'description': 'Gateway', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000004': {'description': 'Kitchen', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '2A000005': {'description': 'Laundry Room', 'sensor_type': 'S-11', 'site_name': 'MySite'}, 
                                  '6BC00000': {'description': '<description not set>', 'sensor_type': 'S-100', 'site_name': 'MySite'},
                                }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()         