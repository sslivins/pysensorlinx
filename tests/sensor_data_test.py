import os
import pytest
from aioresponses import aioresponses
from pyomnisense.omnisense import Omnisense, LOGIN_URL, SITE_LIST_URL, SENSOR_LIST_URL

@pytest.mark.asyncio
async def test_get_sensor_data_no_args():
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

        sensor_result = await omnisense.get_sensor_data()
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {
          '2A000001': {'description': 'Dining Room', 'last_activity': '24-12-30 10:57:44', 'status': 'A', 'temperature': 25.1, 'relative_humidity': '39.0', 'absolute_humidity': '7.7', 'dew_point': '10.2', 'wood_pct': '7.2', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000001', 'site_name': 'MySite'}, 
          '2A000002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000002', 'site_name': 'MySite'}, 
          '2A000003': {'description': 'Gateway', 'last_activity': '24-12-22 10:55:33', 'status': 'A', 'temperature': 11.8, 'relative_humidity': '78.4', 'absolute_humidity': '6.8', 'dew_point': '8.3', 'wood_pct': '13.0', 'battery_voltage': '3.1', 'sensor_type': 'S-11', 'sensor_id': '2A000003', 'site_name': 'MySite'}, 
          '2A000004': {'description': 'Kitchen', 'last_activity': '24-12-30 10:59:40', 'status': 'A', 'temperature': 24.7, 'relative_humidity': '42.1', 'absolute_humidity': '8.2', 'dew_point': '11.0', 'wood_pct': '7.8', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000004', 'site_name': 'MySite'}, 
          '2A000005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A000005', 'site_name': 'MySite'},
          '6BC00000': {'description': '<description not set>', 'last_activity': '24-12-30 10:59:28', 'status': 'A', 'temperature': 0.0, 'relative_humidity': '26', 'absolute_humidity': '0', 'dew_point': '60', 'wood_pct': '11', 'battery_voltage': '0.0', 'sensor_type': 'S-100', 'sensor_id': '6BC00000', 'site_name': 'MySite'}, 
          '2A001001': {'description': 'Dining Room', 'last_activity': '24-12-30 10:57:44', 'status': 'A', 'temperature': 25.1, 'relative_humidity': '39.0', 'absolute_humidity': '7.7', 'dew_point': '10.2', 'wood_pct': '7.2', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001001', 'site_name': 'FirstSite'}, 
          '2A001002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001002', 'site_name': 'FirstSite'}, 
          '2A001003': {'description': 'Gateway', 'last_activity': '24-12-22 10:55:33', 'status': 'A', 'temperature': 11.8, 'relative_humidity': '78.4', 'absolute_humidity': '6.8', 'dew_point': '8.3', 'wood_pct': '13.0', 'battery_voltage': '3.1', 'sensor_type': 'S-11', 'sensor_id': '2A001003', 'site_name': 'FirstSite'}, 
          '2A001004': {'description': 'Kitchen', 'last_activity': '24-12-30 10:59:40', 'status': 'A', 'temperature': 24.7, 'relative_humidity': '42.1', 'absolute_humidity': '8.2', 'dew_point': '11.0', 'wood_pct': '7.8', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001004', 'site_name': 'FirstSite'}, 
          '2A001005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A001005', 'site_name': 'FirstSite'}
          }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()

@pytest.mark.asyncio
async def test_get_sensor_data_pass_site_id_dict():
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

        sensor_result = await omnisense.get_sensor_data(site_ids)
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {
          '2A000001': {'description': 'Dining Room', 'last_activity': '24-12-30 10:57:44', 'status': 'A', 'temperature': 25.1, 'relative_humidity': '39.0', 'absolute_humidity': '7.7', 'dew_point': '10.2', 'wood_pct': '7.2', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000001', 'site_name': 'MySite'}, 
          '2A000002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000002', 'site_name': 'MySite'}, 
          '2A000003': {'description': 'Gateway', 'last_activity': '24-12-22 10:55:33', 'status': 'A', 'temperature': 11.8, 'relative_humidity': '78.4', 'absolute_humidity': '6.8', 'dew_point': '8.3', 'wood_pct': '13.0', 'battery_voltage': '3.1', 'sensor_type': 'S-11', 'sensor_id': '2A000003', 'site_name': 'MySite'}, 
          '2A000004': {'description': 'Kitchen', 'last_activity': '24-12-30 10:59:40', 'status': 'A', 'temperature': 24.7, 'relative_humidity': '42.1', 'absolute_humidity': '8.2', 'dew_point': '11.0', 'wood_pct': '7.8', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000004', 'site_name': 'MySite'}, 
          '2A000005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A000005', 'site_name': 'MySite'},
          '6BC00000': {'description': '<description not set>', 'last_activity': '24-12-30 10:59:28', 'status': 'A', 'temperature': 0.0, 'relative_humidity': '26', 'absolute_humidity': '0', 'dew_point': '60', 'wood_pct': '11', 'battery_voltage': '0.0', 'sensor_type': 'S-100', 'sensor_id': '6BC00000', 'site_name': 'MySite'}, 
          '2A001001': {'description': 'Dining Room', 'last_activity': '24-12-30 10:57:44', 'status': 'A', 'temperature': 25.1, 'relative_humidity': '39.0', 'absolute_humidity': '7.7', 'dew_point': '10.2', 'wood_pct': '7.2', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001001', 'site_name': 'FirstSite'}, 
          '2A001002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001002', 'site_name': 'FirstSite'}, 
          '2A001003': {'description': 'Gateway', 'last_activity': '24-12-22 10:55:33', 'status': 'A', 'temperature': 11.8, 'relative_humidity': '78.4', 'absolute_humidity': '6.8', 'dew_point': '8.3', 'wood_pct': '13.0', 'battery_voltage': '3.1', 'sensor_type': 'S-11', 'sensor_id': '2A001003', 'site_name': 'FirstSite'}, 
          '2A001004': {'description': 'Kitchen', 'last_activity': '24-12-30 10:59:40', 'status': 'A', 'temperature': 24.7, 'relative_humidity': '42.1', 'absolute_humidity': '8.2', 'dew_point': '11.0', 'wood_pct': '7.8', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001004', 'site_name': 'FirstSite'}, 
          '2A001005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A001005', 'site_name': 'FirstSite'}
          }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()
        
@pytest.mark.asyncio
async def test_get_sensor_data_pass_site_id_list():
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

        sensor_result = await omnisense.get_sensor_data(list(site_ids.keys()))
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {
          '2A000001': {'description': 'Dining Room', 'last_activity': '24-12-30 10:57:44', 'status': 'A', 'temperature': 25.1, 'relative_humidity': '39.0', 'absolute_humidity': '7.7', 'dew_point': '10.2', 'wood_pct': '7.2', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000001', 'site_name': 'MySite'}, 
          '2A000002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000002', 'site_name': 'MySite'}, 
          '2A000003': {'description': 'Gateway', 'last_activity': '24-12-22 10:55:33', 'status': 'A', 'temperature': 11.8, 'relative_humidity': '78.4', 'absolute_humidity': '6.8', 'dew_point': '8.3', 'wood_pct': '13.0', 'battery_voltage': '3.1', 'sensor_type': 'S-11', 'sensor_id': '2A000003', 'site_name': 'MySite'}, 
          '2A000004': {'description': 'Kitchen', 'last_activity': '24-12-30 10:59:40', 'status': 'A', 'temperature': 24.7, 'relative_humidity': '42.1', 'absolute_humidity': '8.2', 'dew_point': '11.0', 'wood_pct': '7.8', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000004', 'site_name': 'MySite'}, 
          '2A000005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A000005', 'site_name': 'MySite'},
          '6BC00000': {'description': '<description not set>', 'last_activity': '24-12-30 10:59:28', 'status': 'A', 'temperature': 0.0, 'relative_humidity': '26', 'absolute_humidity': '0', 'dew_point': '60', 'wood_pct': '11', 'battery_voltage': '0.0', 'sensor_type': 'S-100', 'sensor_id': '6BC00000', 'site_name': 'MySite'}, 
          '2A001001': {'description': 'Dining Room', 'last_activity': '24-12-30 10:57:44', 'status': 'A', 'temperature': 25.1, 'relative_humidity': '39.0', 'absolute_humidity': '7.7', 'dew_point': '10.2', 'wood_pct': '7.2', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001001', 'site_name': 'FirstSite'}, 
          '2A001002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001002', 'site_name': 'FirstSite'}, 
          '2A001003': {'description': 'Gateway', 'last_activity': '24-12-22 10:55:33', 'status': 'A', 'temperature': 11.8, 'relative_humidity': '78.4', 'absolute_humidity': '6.8', 'dew_point': '8.3', 'wood_pct': '13.0', 'battery_voltage': '3.1', 'sensor_type': 'S-11', 'sensor_id': '2A001003', 'site_name': 'FirstSite'}, 
          '2A001004': {'description': 'Kitchen', 'last_activity': '24-12-30 10:59:40', 'status': 'A', 'temperature': 24.7, 'relative_humidity': '42.1', 'absolute_humidity': '8.2', 'dew_point': '11.0', 'wood_pct': '7.8', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001004', 'site_name': 'FirstSite'}, 
          '2A001005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A001005', 'site_name': 'FirstSite'}
          }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()
        
@pytest.mark.asyncio
async def test_get_sensor_data_pass_single_site_id_string():
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
                
        sensor_result = await omnisense.get_sensor_data("123456")
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {
          '2A000001': {'description': 'Dining Room', 'last_activity': '24-12-30 10:57:44', 'status': 'A', 'temperature': 25.1, 'relative_humidity': '39.0', 'absolute_humidity': '7.7', 'dew_point': '10.2', 'wood_pct': '7.2', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000001', 'site_name': 'MySite'}, 
          '2A000002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000002', 'site_name': 'MySite'}, 
          '2A000003': {'description': 'Gateway', 'last_activity': '24-12-22 10:55:33', 'status': 'A', 'temperature': 11.8, 'relative_humidity': '78.4', 'absolute_humidity': '6.8', 'dew_point': '8.3', 'wood_pct': '13.0', 'battery_voltage': '3.1', 'sensor_type': 'S-11', 'sensor_id': '2A000003', 'site_name': 'MySite'}, 
          '2A000004': {'description': 'Kitchen', 'last_activity': '24-12-30 10:59:40', 'status': 'A', 'temperature': 24.7, 'relative_humidity': '42.1', 'absolute_humidity': '8.2', 'dew_point': '11.0', 'wood_pct': '7.8', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000004', 'site_name': 'MySite'}, 
          '2A000005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A000005', 'site_name': 'MySite'},
          '6BC00000': {'description': '<description not set>', 'last_activity': '24-12-30 10:59:28', 'status': 'A', 'temperature': 0.0, 'relative_humidity': '26', 'absolute_humidity': '0', 'dew_point': '60', 'wood_pct': '11', 'battery_voltage': '0.0', 'sensor_type': 'S-100', 'sensor_id': '6BC00000', 'site_name': 'MySite'}, 
          }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()
        
        
@pytest.mark.asyncio
async def test_get_sensor_data_single_sensor():
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
                
        sensor_result = await omnisense.get_sensor_data(sensor_ids="2A000005")
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {
          '2A000005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A000005', 'site_name': 'MySite'},
          }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()           
        
@pytest.mark.asyncio
async def test_get_sensor_data_sensor_id_list():
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
                
        sensor_result = await omnisense.get_sensor_data(sensor_ids=["2A000001", "2A000003", "2A000005", "6BC00000"])
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {
          '2A000001': {'description': 'Dining Room', 'last_activity': '24-12-30 10:57:44', 'status': 'A', 'temperature': 25.1, 'relative_humidity': '39.0', 'absolute_humidity': '7.7', 'dew_point': '10.2', 'wood_pct': '7.2', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000001', 'site_name': 'MySite'}, 
          '2A000003': {'description': 'Gateway', 'last_activity': '24-12-22 10:55:33', 'status': 'A', 'temperature': 11.8, 'relative_humidity': '78.4', 'absolute_humidity': '6.8', 'dew_point': '8.3', 'wood_pct': '13.0', 'battery_voltage': '3.1', 'sensor_type': 'S-11', 'sensor_id': '2A000003', 'site_name': 'MySite'}, 
          '2A000005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A000005', 'site_name': 'MySite'},
          '6BC00000': {'description': '<description not set>', 'last_activity': '24-12-30 10:59:28', 'status': 'A', 'temperature': 0.0, 'relative_humidity': '26', 'absolute_humidity': '0', 'dew_point': '60', 'wood_pct': '11', 'battery_voltage': '0.0', 'sensor_type': 'S-100', 'sensor_id': '6BC00000', 'site_name': 'MySite'}, 
          }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()
        
@pytest.mark.asyncio
async def test_get_sensor_data_sensor_id_list_multiple_sites():
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
                
        sensor_result = await omnisense.get_sensor_data(sensor_ids=["2A000002", "2A000003", "2A001002", "2A001005"])
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {
          '2A000002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000002', 'site_name': 'MySite'}, 
          '2A000003': {'description': 'Gateway', 'last_activity': '24-12-22 10:55:33', 'status': 'A', 'temperature': 11.8, 'relative_humidity': '78.4', 'absolute_humidity': '6.8', 'dew_point': '8.3', 'wood_pct': '13.0', 'battery_voltage': '3.1', 'sensor_type': 'S-11', 'sensor_id': '2A000003', 'site_name': 'MySite'}, 
          '2A001002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A001002', 'site_name': 'FirstSite'}, 
          '2A001005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A001005', 'site_name': 'FirstSite'}
          }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()
        
@pytest.mark.asyncio
async def test_get_sensor_data_sensor_id_list_multiple_sites_with_some_unknown_sensor_ids():
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
                
        sensor_result = await omnisense.get_sensor_data(sensor_ids=["2A000002", "2A008003", "2A008002", "2A001005"])
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {
          '2A000002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000002', 'site_name': 'MySite'}, 
          '2A001005': {'description': 'Laundry Room', 'last_activity': '24-12-22 10:51:17', 'status': 'A', 'temperature': 14.4, 'relative_humidity': '63.6', 'absolute_humidity': '6.5', 'dew_point': '7.6', 'wood_pct': '13.2', 'battery_voltage': '3.2', 'sensor_type': 'S-11', 'sensor_id': '2A001005', 'site_name': 'FirstSite'}
          }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()
        
@pytest.mark.asyncio
async def test_get_sensor_data_sensor_id_list_specific_site_and_sensor_id():
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
                
        sensor_result = await omnisense.get_sensor_data("123456", "2A000002")
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {
          '2A000002': {'description': 'Basement', 'last_activity': '24-12-30 10:59:04', 'status': 'A', 'temperature': 29.2, 'relative_humidity': '30.4', 'absolute_humidity': '7.7', 'dew_point': '10.1', 'wood_pct': '6.9', 'battery_voltage': '3.4', 'sensor_type': 'S-11', 'sensor_id': '2A000002', 'site_name': 'MySite'}, 
          }
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()           
        
@pytest.mark.asyncio
async def test_get_sensor_data_all_unknown_sensor_ids():
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
                
        sensor_result = await omnisense.get_sensor_data(sensor_ids="ABC0001")
        
        # Define the expected sensor result (adjust as necessary based on your parsing logic).
        expected_sensor_result = {}
        assert sensor_result == expected_sensor_result
        
        # Close the session to clean up.
        await omnisense.close()            