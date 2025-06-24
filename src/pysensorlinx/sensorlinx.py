import logging
import aiohttp
import re
from typing import List, Dict, Optional, Union
from urllib.parse import urlencode
from http.cookies import SimpleCookie

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

CONF_SITE_NAME = "site_name"       # The name of the site (e.g., "home")
CONF_SENSOR_IDS = "sensor_ids"     # List of sensor IDs to extract (empty = all)
CONF_USERNAME = "username"         # Login username
CONF_PASSWORD = "password"         # Login password

HOST_URL = "https://mobile.sensorlinx.co"
LOGIN_ENDPOINT = "account/login"
PROFILE_ENDPOINT = "account/me"
BUILDINGS_ENDPOINT = "buildings"
DEVICES_ENDPOINT_TEMPLATE = "buildings/{building_id}/devices"

class Sensorlinx:

    def __init__(self): 
        self._username = None
        self._password = None
        self._session = None
        self._bearer_token = None
        self._refresh_token = None
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 "
                        "Mobile Safari/537.36 Edg/138.0.0.0",
        }
        
        #self.proxy_url = "http://127.0.0.1:8888"
        self.proxy_url = None  # Set to None to disable proxy, or provide a valid proxy URL if needed
                        
        
    
    async def login(self, username: str=None, password: str=None) -> bool:
        if not username or not password:
            if not self._username or not self._password:
                _LOGGER.error("No username or password provided.")
                raise Exception("No username or password provided.")
        else:
            self._username = username
            self._password = password

        self._session = aiohttp.ClientSession()

        login_url = f"{HOST_URL}/{LOGIN_ENDPOINT}"
        payload = {
            "email": self._username,
            "password": self._password
        }
        try:
            async with self._session.post(
                login_url,
                json=payload,
                headers={**self.headers, "Content-Type": "application/json"},
                proxy=self.proxy_url,
                timeout=10
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(f"Login failed with status {resp.status}")
                    return False
                data = await resp.json()
                self._bearer_token = data.get("token")
                self._refresh_token = data.get("refresh")
                if not self._bearer_token:
                    _LOGGER.error("No bearer token received during login.")
                    return False
                # Add Authorization header for future requests
                self.headers["Authorization"] = f"Bearer {self._bearer_token}"
                
                return True
        except Exception as e:
            _LOGGER.error(f"Exception during login: {e}")
            return False
        
    async def get_profile(self) -> Optional[Dict[str, str]]:
        ''' Fetch the user profile information
        
        Returns: Optional[Dict[str, str]]: Returns a dictionary with user profile information or None if not logged in.
        '''
        
        if self._session is None:
            if not await self.login():
                return None

        profile_url = f"{HOST_URL}/{PROFILE_ENDPOINT}"
        try:
            async with self._session.get(
                profile_url,
                headers=self.headers,
                proxy=self.proxy_url,
                timeout=10
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(f"Failed to fetch profile with status {resp.status}")
                    return None
                data = await resp.json()
                return data
        except Exception as e:
            _LOGGER.error(f"Exception fetching profile: {e}")
            return None

    async def get_buildings(self, building_id: Optional[str] = None) -> Optional[Union[List[Dict[str, str]], Dict[str, str]]]:
        ''' Fetch the list of buildings or a specific building by ID
        
        Args:
            building_id (Optional[str]): If provided, fetches the building with this ID. Otherwise, fetches all buildings.
        
        Returns: 
            Optional[Union[List[Dict[str, str]], Dict[str, str]]]: 
                - If building_id is None, returns a list of building dicts or None if not logged in.
                - If building_id is provided, returns a dict for the building or None if not found.
        '''
        if self._session is None:
            if not await self.login():
                return None

        if building_id:
            buildings_url = f"{HOST_URL}/{BUILDINGS_ENDPOINT}/{building_id}"
        else:
            buildings_url = f"{HOST_URL}/{BUILDINGS_ENDPOINT}"

        try:
            async with self._session.get(
                buildings_url,
                headers=self.headers,
                proxy=self.proxy_url,
                timeout=10
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(f"Failed to fetch building(s) with status {resp.status}")
                    return None
                data = await resp.json()
                return data
        except Exception as e:
            _LOGGER.error(f"Exception fetching building(s): {e}")
            return None
        
    async def get_devices(self, building_id: str, device_id: Optional[str] = None) -> Optional[Union[List[Dict[str, str]], Dict[str, str]]]:
        ''' Fetch devices for a given building, or a specific device if device_id is provided

        Args:
            building_id (str): The ID of the building.
            device_id (Optional[str]): The ID of the device. If not provided, fetches all devices for the building.

        Returns:
            Optional[Union[List[Dict[str, str]], Dict[str, str]]]: 
                - If device_id is None, returns a list of device dicts or None if not found or error.
                - If device_id is provided, returns a dict for the device or None if not found or error.
        '''
        if self._session is None:
            if not await self.login():
                return None

        if device_id:
            url = f"{HOST_URL}/{DEVICES_ENDPOINT_TEMPLATE.format(building_id=building_id)}/{device_id}"
        else:
            url = f"{HOST_URL}/{DEVICES_ENDPOINT_TEMPLATE.format(building_id=building_id)}"

        try:
            async with self._session.get(
                url,
                headers=self.headers,
                proxy=self.proxy_url,
                timeout=10
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(f"Failed to fetch device(s) with status {resp.status}")
                    return None
                data = await resp.json()
                return data
        except Exception as e:
            _LOGGER.error(f"Exception fetching device(s): {e}")
            return None


    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None        
        
    # async def get_site_list(self) -> dict:
    #     ''' fetch the available sites
        
    #     Returns: dict: Returns a dictionary of {site_id: site_name}

    #     '''
        
    #     if self._session is None:
    #         if not await self.login():
    #             return {}

    #     try:
    #         async with self._session.get(SITE_LIST_URL, proxy=self.proxy_url, headers=self.headers, timeout=10) as response:
    #             if response.status != 200:
    #                 raise Exception("Error fetching job sites page.")
    #             soup = BeautifulSoup(await response.text(), "html.parser")
    #     except Exception as err:
    #         _LOGGER.error("Error fetching site list: %s", err)
    #         return {}

    #     sites = {}
    #     for link in soup.find_all("a", onclick=True):
    #         onclick = link.get("onclick", "")
    #         match = re.search(r"ShowSiteDetail\('(\d+)'\)", onclick)
    #         if match:
    #             site_id = match.group(1)
    #             site_name = link.get_text(strip=True)
    #             sites[site_id] = site_name

    #     return sites
    
    # async def get_site_sensor_list(self, site_ids: Union[str, List[str], Dict[str, str]] = None) -> Dict[str, Dict[str, str]]:
    #     '''  Fetch sensors for the selected site using the stored credentials.  
        
    #     Args:
    #         site_ids (Union[str, List[str], Dict[str, str]]) : can be a dictionary in the form {site_id : site_name} or a list of site_id strings or a single site_id string. 
    #             If not provided all sensors from all sites will be returned.
                
    #     Returns: Dict[str, Dict[str, str, str]]: Returns a dictionary of Dict[sensor_id, Dict[description, sensor_type, site_name ]]'''

    #     if self._session is None:
    #         if not await self.login():
    #             return {}
            
    #     if not site_ids:
    #         site_ids = await self.get_site_list()
            
    #     if isinstance(site_ids, str):
    #         site_ids = [site_ids]
    #     elif isinstance(site_ids, list):
    #         #do nothing
    #         pass
    #     elif isinstance(site_ids, dict):
    #         site_ids = list(site_ids.keys())  # Extract only the keys as a list
    #     else:
    #         raise TypeError("Unsupported data type, expected str, list of str, or dict with str keys.")
                     
    #     sensors = {}

    #     try:
    #         sensor_data = await self.get_sensor_data(site_ids)

    #         #if there is no sensor data, return an empty dictionary
    #         if not sensor_data:
    #             return {}

    #         #only return a dictionary of sensor_id: description, sensor_type, site_name
    #         for sensor_id, sensor_info in sensor_data.items():
    #             sensors[sensor_id] = {
    #                 "description" : sensor_info["description"], 
    #                 "sensor_type" : sensor_info["sensor_type"], 
    #                 "site_name" : sensor_info["site_name"]
    #             }

    #     except Exception as e:
    #         _LOGGER.error("Error fetching sensors: %s", e)
    #         return {}
        
    #     return sensors

    # async def get_sensor_data(self, site_ids: Union[str, List[str], Dict[str, str]] = None, sensor_ids: Union[str, List[str]] = []) -> dict:
    #     ''' Fetch the sensor data
        
    #     Args: 
    #         site_ids (Union[str, List[str], Dict[str, str]]): A single site_id string or a list of site_id strings. If not provided, all sites will be searched.
    #         sensor_ids (Union[str, List[str]]): A single sensor_id string or a list of sensor_id strings. If not provided, all sensors will be returned from all site(s).
            
    #     Returns: dict: Returns a dictionary of sensor data in the form of sensor_id: { description, last_activity, status, temperature, relative_humidity, absolute_humidity, dew_point, wood_pct, battery_voltage, sensor_type, site_name }
    #     '''
        
    #     if self._session is None:
    #         if not await self.login():
    #             return {}
            
    #     if not site_ids:
    #         site_ids = await self.get_site_list()
            
    #     if isinstance(site_ids, str):
    #         site_ids = [site_ids]
    #     elif isinstance(site_ids, list):
    #         #do nothing
    #         pass
    #     elif isinstance(site_ids, dict):
    #         site_ids = list(site_ids.keys())  # Extract only the keys as a list
    #     else:
    #         raise TypeError("Unsupported data type, expected str, list of str, or dict with str keys.")

    #     if isinstance(sensor_ids, str):
    #         sensor_ids = [sensor_ids]

    #     all_sensors = {}
    #     for site_id in site_ids:
    #         sensor_page_url = f"{SENSOR_LIST_URL}?siteNbr={site_id}"

    #         try:
    #             async with self._session.get(sensor_page_url, proxy=self.proxy_url, headers=self.headers, timeout=10) as response:
    #                 if response.status != 200:
    #                     raise Exception(f"Error fetching sensor data for site id '{site_id}'.")
    #                 soup = BeautifulSoup(await response.text(), "html.parser")

    #                 # Extract site name from the title
    #                 title_text = soup.find("title").get_text().strip()
    #                 # Use a regular expression to remove "Sensors for "
    #                 match = re.search(r"Sensors for\s+(.+)", title_text)
    #                 if match:
    #                     site_name = match.group(1)

    #                 #extract individual sensor data
    #                 for table in soup.select("table.sortable.table"):
    #                     sensor_type = None
    #                     table_id = table.get("id", "")
    #                     if table_id.startswith("sensorType"):
    #                         sensor_type = f"S-{table_id[len('sensorType'):]}"
    #                     if not sensor_type:
    #                         caption = table.find("caption")
    #                         if caption and caption.text:
    #                             m = re.search(r"Sensor Type\s*(\d+)", caption.text)
    #                             if m:
    #                                 sensor_type = f"S-{m.group(1)}"
    #                     for row in table.select("tr.sensorTable"):
    #                         tds = row.find_all("td")
    #                         if len(tds) >= 10:
    #                             sid = tds[0].get_text(strip=True)
    #                             if sensor_ids and sid not in sensor_ids:
    #                                 continue
    #                             try:
    #                                 temperature = float(tds[4].get_text(strip=True))
    #                             except ValueError:
    #                                 temperature = None

    #                             desc = tds[1].get_text(strip=True)
    #                             if desc == "~click to edit~":
    #                                 desc = "<description not set>"

    #                             all_sensors[sid] = {
    #                                 "description": desc,
    #                                 "last_activity": tds[2].get_text(strip=True),
    #                                 "status": tds[3].get_text(strip=True),
    #                                 "temperature": temperature,
    #                                 "relative_humidity": tds[5].get_text(strip=True),
    #                                 "absolute_humidity": tds[6].get_text(strip=True),
    #                                 "dew_point": tds[7].get_text(strip=True),
    #                                 "wood_pct": tds[8].get_text(strip=True),
    #                                 "battery_voltage": tds[9].get_text(strip=True),
    #                                 "sensor_type": sensor_type,
    #                                 "sensor_id": sid,
    #                                 "site_name": site_name,
    #                             }

    #         except Exception:
    #             _LOGGER.error(f"Error fetching/parsing sensor data for site id '{site_id}'.")
    #             continue

    #     return all_sensors


