import logging
import aiohttp
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional, Union

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

CONF_SITE_NAME = "site_name"       # The name of the site (e.g., "home")
CONF_SENSOR_IDS = "sensor_ids"     # List of sensor IDs to extract (empty = all)
CONF_USERNAME = "username"         # Login username
CONF_PASSWORD = "password"         # Login password

LOGIN_URL = "https://www.omnisense.com/user_login.asp"
SITE_LIST_URL = "https://www.omnisense.com/site_select.asp"
SENSOR_LIST_URL = "https://www.omnisense.com/sensor_select.asp"


class Omnisense:

    def __init__(self): 
        self._username = None
        self._password = None
        self._session = None
    
    async def login(self, username: str=None, password: str=None) -> bool:

        #if username/password are not provided, use the stored credentials
        if not username or not password:
            if not self._username or not self._password:
                _LOGGER.error("No username or password provided.")
                raise Exception("No username or password provided.")
        else:
            self._username = username
            self._password = password

        payload = {
            "userId": self._username,
            "userPass": self._password,
            "btnAct": "Log-In",
            "target": ""
        }
        self._session = aiohttp.ClientSession()

        try:
            async with self._session.post(LOGIN_URL, data=payload, timeout=10) as response:
                if response.status != 200 or "User Log-In" in await response.text():
                    await self._session.close()  # Close the session if login fails
                    self._session = None
                    raise Exception("Login failed; check your credentials.")
        except Exception as err:
            _LOGGER.error("Error during login: %s", err)
            raise err
        
        _LOGGER.info("Login successful.")
        return True

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None        
        
    async def get_site_list(self) -> dict:
        """Fetch available sites using the provided credentials. this returns a dictionary of {site_id: site_name}"""
        if self._session is None:
            if not await self.login():
                return {}

        try:
            async with self._session.get(SITE_LIST_URL, timeout=10) as response:
                if response.status != 200:
                    raise Exception("Error fetching job sites page.")
                soup = BeautifulSoup(await response.text(), "html.parser")
        except Exception as err:
            _LOGGER.error("Error fetching site list: %s", err)
            return {}

        sites = {}
        for link in soup.find_all("a", onclick=True):
            onclick = link.get("onclick", "")
            match = re.search(r"ShowSiteDetail\('(\d+)'\)", onclick)
            if match:
                site_id = match.group(1)
                site_name = link.get_text(strip=True)
                sites[site_id] = site_name

        return sites
    
    async def get_site_sensor_list(self, site_ids: Union[str, List[str], Dict[str, str]] = None) -> Dict[str, Dict[str, str]]:
        '''  Fetch sensors for the selected site using the stored credentials.  
        
        Args:
            site_ids (Union[str, List[str], Dict[str, str]]) : can be a dictionary in the form {site_id : site_name} or a list of site_id strings or a single site_id string. 
                If not provided all sensors from all sites will be returned.
                
        Returns Dict[str, Dict[str, str, str]]: Returns a dictionary of Dict[sensor_id, Dict[description, sensor_type, site_name ]]'''

        if self._session is None:
            if not await self.login():
                return {}
            
        if not site_ids:
            site_ids = await self.get_site_list()
            
        if isinstance(site_ids, str):
            site_ids = [site_ids]
        elif isinstance(site_ids, list):
            #do nothing
            pass
        elif isinstance(site_ids, dict):
            site_ids = list(site_ids.keys())  # Extract only the keys as a list
        else:
            raise TypeError("Unsupported data type, expected str, list of str, or dict with str keys.")
                     
        sensors = {}

        try:
            sensor_data = await self.get_sensor_data(site_ids)

            #if there is no sensor data, return an empty dictionary
            if not sensor_data:
                return {}

            #only return a dictionary of sensor_id: description, sensor_type, site_name
            for sensor_id, sensor_info in sensor_data.items():
                sensors[sensor_id] = {"description" : sensor_info["description"], "sensor_type" : sensor_info["sensor_type"], "site_name" : sensor_info["site_name"]}

        except Exception as e:
            _LOGGER.error("Error fetching sensors: %s", e)
            return {}
        
        return sensors

    async def get_sensor_data(self, site_ids: Union[str, List[str]] = None, sensor_ids: Union[str, List[str]] = []) -> dict:
        """Fetch sensor data from Omnisense for specified sites and sensor_ids.  An empty sensor_ids list will return all sensors for the specified sites.
        Returns a dictionary of sensor data in the form of sensor_id: { description, last_activity, status, temperature, relative_humidity, absolute_humidity, dew_point, wood_pct, battery_voltage, sensor_type, site_name } """
        if self._session is None:
            if not await self.login():
                return {}

        if not site_ids:
            site_ids = await self.get_site_list()
        else:
            if isinstance(site_ids, str):
                site_ids = [site_ids]

        if isinstance(sensor_ids, str):
            sensor_ids = [sensor_ids]

        all_sensors = {}
        for site_id in site_ids:
            sensor_page_url = f"{SENSOR_LIST_URL}?siteNbr={site_id}"

            try:
                async with self._session.get(sensor_page_url, timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"Error fetching sensor data for site id '{site_id}'.")
                    soup = BeautifulSoup(await response.text(), "html.parser")

                    # Extract site name from the title
                    title_text = soup.find("title").get_text().strip()
                    # Use a regular expression to remove "Sensors for "
                    match = re.search(r"Sensors for\s+(.+)", title_text)
                    if match:
                        site_name = match.group(1)

                    #extract individual sensor data
                    for table in soup.select("table.sortable.table"):
                        sensor_type = None
                        table_id = table.get("id", "")
                        if table_id.startswith("sensorType"):
                            sensor_type = f"S-{table_id[len('sensorType'):]}"
                        if not sensor_type:
                            caption = table.find("caption")
                            if caption and caption.text:
                                m = re.search(r"Sensor Type\s*(\d+)", caption.text)
                                if m:
                                    sensor_type = f"S-{m.group(1)}"
                        for row in table.select("tr.sensorTable"):
                            tds = row.find_all("td")
                            if len(tds) >= 10:
                                sid = tds[0].get_text(strip=True)
                                if sensor_ids and sid not in sensor_ids:
                                    continue
                                try:
                                    temperature = float(tds[4].get_text(strip=True))
                                except ValueError:
                                    temperature = None

                                desc = tds[1].get_text(strip=True)
                                if desc == "~click to edit~":
                                    desc = "<description not set>"

                                all_sensors[sid] = {
                                    "description": desc,
                                    "last_activity": tds[2].get_text(strip=True),
                                    "status": tds[3].get_text(strip=True),
                                    "temperature": temperature,
                                    "relative_humidity": tds[5].get_text(strip=True),
                                    "absolute_humidity": tds[6].get_text(strip=True),
                                    "dew_point": tds[7].get_text(strip=True),
                                    "wood_pct": tds[8].get_text(strip=True),
                                    "battery_voltage": tds[9].get_text(strip=True),
                                    "sensor_type": sensor_type,
                                    "sensor_id": sid,
                                    "site_name": site_name,
                                }

            except Exception:
                _LOGGER.error(f"Error fetching/parsing sensor data for site id '{site_id}'.")
                continue

        return all_sensors


