import logging
import aiohttp
from bs4 import BeautifulSoup
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

HOST_URL = "https://www.omnisense.com"
LOGIN_URL = "https://www.omnisense.com/user_login.asp"
SITE_LIST_URL = "https://www.omnisense.com/site_select.asp"
SENSOR_LIST_URL = "https://www.omnisense.com/sensor_select.asp"

class Omnisense:

    def __init__(self): 
        self._username = None
        self._password = None
        self._session = None
        
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
            
       
        payload = {
            "userId": self._username,
            "userPass": self._password,
            "target": "",
            "btnAct": "Log-In",
        }
        
        self._session = aiohttp.ClientSession()
        
        # 1. POST login (no redirects)
        async with self._session.post(LOGIN_URL, data=payload, proxy=self.proxy_url, headers=self.headers, allow_redirects=False) as resp:
            _LOGGER.debug("POST %s status: %s", LOGIN_URL, resp.status)
            _LOGGER.debug("POST response headers: %s", dict(resp.headers))
            _LOGGER.debug("POST response cookies: %s", resp.cookies)
            # 2. Build manual Cookie header (no quotes)
            set_cookie_headers = resp.headers.getall('Set-Cookie', [])
            _LOGGER.debug("Set-Cookie headers: %s", set_cookie_headers)
            cookies = SimpleCookie()
            for h in set_cookie_headers:
                _LOGGER.debug(f"Processing Set-Cookie header: {h}")
                if h.startswith("userPNSToken=login+failed;"):
                    _LOGGER.error("Login failed: userPNSToken=login+failed detected in cookies.")
                    await self._session.close()
                    self._session = None
                    return False
                cookies.load(h)
            _LOGGER.debug("Parsed cookies: %s", {k: v.value for k, v in cookies.items()})

            # --- IMPORTANT WORKAROUND ---
            # aiohttp (and the Python standard library) will quote cookie values containing special characters,
            # which breaks compatibility with legacy classic ASP and some ASP.NET applications.
            # These servers expect unquoted cookie values—even if the value contains '=' or other special chars.
            # The fix: manually build the Cookie header and add this to the headers rather than relying on aiohttp's cookie handling.
            cookie_header = "; ".join(f"{key}={m.value}" for key, m in cookies.items())
            _LOGGER.debug("Manual Cookie header: %s", cookie_header)
            # --- END WORKAROUND ---

            # 3. Get the redirect location
            location = resp.headers.get('Location')
            _LOGGER.debug("Redirect location: %s", location)
            if not location:
                _LOGGER.error("No redirect location after login.")
                return False
            if not location.startswith("http"):
                location = HOST_URL + location
                _LOGGER.debug("Full redirect location: %s", location)

            # 4. Clear session cookies so aiohttp doesn't interfere
            self._session.cookie_jar.clear()
            _LOGGER.debug("Session cookies cleared.")

            # 5. Make GET to redirect target with manual Cookie header
            self.headers['Cookie'] = cookie_header
            _LOGGER.debug("GET %s with headers: %s", location, self.headers)
            async with self._session.get(location, proxy=self.proxy_url, headers=self.headers) as resp2:
                final_url = str(resp2.url)
                _LOGGER.debug("GET response status: %s", resp2.status)
                _LOGGER.debug("GET response URL: %s", final_url)
                # Optionally, check resp2.status and/or content for further validation

            # 6. Return True if we landed on the intended URL
            _LOGGER.debug("Final URL after login: %s (success=%s)", final_url, final_url == location)
            return final_url == location
                

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None        
        
    async def get_site_list(self) -> dict:
        ''' fetch the available sites
        
        Returns: dict: Returns a dictionary of {site_id: site_name}

        '''
        
        if self._session is None:
            if not await self.login():
                return {}

        try:
            async with self._session.get(SITE_LIST_URL, proxy=self.proxy_url, headers=self.headers, timeout=10) as response:
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
                
        Returns: Dict[str, Dict[str, str, str]]: Returns a dictionary of Dict[sensor_id, Dict[description, sensor_type, site_name ]]'''

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
                sensors[sensor_id] = {
                    "description" : sensor_info["description"], 
                    "sensor_type" : sensor_info["sensor_type"], 
                    "site_name" : sensor_info["site_name"]
                }

        except Exception as e:
            _LOGGER.error("Error fetching sensors: %s", e)
            return {}
        
        return sensors

    async def get_sensor_data(self, site_ids: Union[str, List[str], Dict[str, str]] = None, sensor_ids: Union[str, List[str]] = []) -> dict:
        ''' Fetch the sensor data
        
        Args: 
            site_ids (Union[str, List[str], Dict[str, str]]): A single site_id string or a list of site_id strings. If not provided, all sites will be searched.
            sensor_ids (Union[str, List[str]]): A single sensor_id string or a list of sensor_id strings. If not provided, all sensors will be returned from all site(s).
            
        Returns: dict: Returns a dictionary of sensor data in the form of sensor_id: { description, last_activity, status, temperature, relative_humidity, absolute_humidity, dew_point, wood_pct, battery_voltage, sensor_type, site_name }
        '''
        
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

        if isinstance(sensor_ids, str):
            sensor_ids = [sensor_ids]

        all_sensors = {}
        for site_id in site_ids:
            sensor_page_url = f"{SENSOR_LIST_URL}?siteNbr={site_id}"

            try:
                async with self._session.get(sensor_page_url, proxy=self.proxy_url, headers=self.headers, timeout=10) as response:
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


