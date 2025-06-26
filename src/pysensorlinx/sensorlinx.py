import logging
import re
from typing import List, Dict, Optional, Union
from urllib.parse import urlencode
from http.cookies import SimpleCookie
import asyncio
import aiohttp
import datetime


_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class LoginError(Exception):
    """Base exception for login failures."""

class LoginTimeoutError(LoginError):
    """Raised when login times out."""

class InvalidCredentialsError(LoginError):
    """Raised when credentials are invalid."""

class NoTokenError(LoginError):
    """Raised when no token is received after login."""
    
class InvalidParameterError(Exception):
    """Raised when an invalid parameter is provided."""


CONF_SITE_NAME = "site_name"       # The name of the site (e.g., "home")
CONF_SENSOR_IDS = "sensor_ids"     # List of sensor IDs to extract (empty = all)
CONF_USERNAME = "username"         # Login username
CONF_PASSWORD = "password"         # Login password

HOST_URL = "https://mobile.sensorlinx.co"
LOGIN_ENDPOINT = "account/login"
PROFILE_ENDPOINT = "account/me"
BUILDINGS_ENDPOINT = "buildings"
DEVICES_ENDPOINT_TEMPLATE = "buildings/{building_id}/devices"



class Temperature:
    def __init__(self, value: float, unit: str = "C"):
        unit = unit.upper()
        if unit not in ("C", "F"):
            raise ValueError("Unit must be 'C' for Celsius or 'F' for Fahrenheit")
        self.value = float(value)
        self.unit = unit

    def to_celsius(self) -> float:
        if self.unit == "C":
            return self.value
        return (self.value - 32) * 5.0 / 9.0

    def to_fahrenheit(self) -> float:
        if self.unit == "F":
            return self.value
        return self.value * 9.0 / 5.0 + 32

    def as_celsius(self):
        return Temperature(self.to_celsius(), "C")

    def as_fahrenheit(self):
        return Temperature(self.to_fahrenheit(), "F")

    def __repr__(self):
        return f"Temperature({self.value:.2f}, '{self.unit}')"

    def __str__(self):
        symbol = "°C" if self.unit == "C" else "°F"
        return f"{self.value:.2f}{symbol}"

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
                        
        
    
    async def login(self, username: str=None, password: str=None) -> None:
        """
        Attempt to log in to the Sensorlinx service.

        Args:
            username (str, optional): The username to use for login.
            password (str, optional): The password to use for login.

        Raises:
            InvalidCredentialsError: If the credentials are missing or invalid.
            LoginTimeoutError: If the login request times out.
            NoTokenError: If no bearer token is received after login.
            LoginError: For other login-related errors.
        """
        if not username or not password:
            if not self._username or not self._password:
                _LOGGER.error("No username or password provided.")
                raise InvalidCredentialsError("No username or password provided.")
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
                if resp.status == 401:
                    _LOGGER.error("Invalid credentials.")
                    raise InvalidCredentialsError("Invalid username or password.")
                if resp.status != 200:
                    _LOGGER.error(f"Login failed with status {resp.status}")
                    raise LoginError(f"Login failed with status {resp.status}")
                data = await resp.json()
                self._bearer_token = data.get("token")
                self._refresh_token = data.get("refresh")
                if not self._bearer_token:
                    _LOGGER.error("No bearer token received during login.")
                    raise NoTokenError("No bearer token received during login.")
                self.headers["Authorization"] = f"Bearer {self._bearer_token}"
        except asyncio.TimeoutError:
            _LOGGER.error("Login request timed out.")
            raise LoginTimeoutError("Login request timed out.")
        except Exception as e:
            _LOGGER.exception(f"Exception during login: {e}")
            raise LoginError(f"Exception during login: {e}")
        
    async def close(self):
        """Close the aiohttp session if it exists."""
        if self._session:
            await self._session.close()
            self._session = None
            self._bearer_token = None
            self._refresh_token = None
            _LOGGER.debug("Session closed successfully.")
        else:
            _LOGGER.debug("No session to close.")
        
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
            _LOGGER.debug(f"Fetching URL: {url}")
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



    async def set_device_parameter(
        self,
        building_id: str,
        device_id: str,
        permanent_hd: Optional[bool] = None,
        permanent_cd: Optional[bool] = None,
        cold_weather_shutdown: Optional[Union[Temperature, str]] = None,
        warm_weather_shutdown: Optional[Union[Temperature, str]] = None,
        hvac_mode_priority: Optional[str] = None,
        weather_shutdown_lag_time: Optional[int] = None,
    ) -> None:
        """
        Set permanent heating and/or cooling demand for a specific device.

        Args:
            building_id (str): The ID of the building (required).
            device_id (str): The ID of the device (required).
            permanent_hd (Optional[bool]): If True, always maintain buffer tank target temperature (heating).
            permanent_cd (Optional[bool]): If True, always maintain buffer tank target temperature (cooling).
            cold_weather_shutdown (Optional[Temperature or str]): when in cooling mode shuts the heat pump off below this temperature, or 'off' to disable.
            warm_weather_shutdown (Optional[Temperature or str]): when in heating mode shuts the heat pump off above this temperature, or 'off' to disable.
            hvac_mode_priority (Optional[str]): The HVAC mode priority to set (e.g., "cool", "heat", "auto").
            weather_shutdown_lag_time (Optional[int]): Lag time for warm/cold weather shutdown.

        Raises:
            InvalidParameterError: If required parameters are missing or invalid.
            LoginError: If login fails or session is not established.
            RuntimeError: If the API call fails for other reasons.
        """
        if not building_id or not device_id:
            _LOGGER.error("Both building_id and device_id must be provided.")
            raise InvalidParameterError("Both building_id and device_id must be provided.")

        if self._session is None:
            await self.login()

        url = f"{HOST_URL}/{DEVICES_ENDPOINT_TEMPLATE.format(building_id=building_id)}/{device_id}"
        payload = {}
        if permanent_hd is not None:
            payload["permHD"] = permanent_hd
        if permanent_cd is not None:
            payload["permCD"] = permanent_cd
        if cold_weather_shutdown is not None:
            if isinstance(cold_weather_shutdown, str) and cold_weather_shutdown.lower() == "off":
                payload["cwsd"] = 32
            elif isinstance(cold_weather_shutdown, Temperature):
                payload["cwsd"] = round(cold_weather_shutdown.to_fahrenheit())
            else:
                raise InvalidParameterError("cold_weather_shutdown must be a Temperature or 'off'")
        if warm_weather_shutdown is not None:
            if isinstance(warm_weather_shutdown, str) and warm_weather_shutdown.lower() == "off":
                payload["wwsd"] = 32
            elif isinstance(warm_weather_shutdown, Temperature):
                payload["wwsd"] = round(warm_weather_shutdown.to_fahrenheit())
            else:
                raise InvalidParameterError("warm_weather_shutdown must be a Temperature or 'off'")
        if hvac_mode_priority is not None:
            if hvac_mode_priority == "heat":
                payload["prior"] = 0
            elif hvac_mode_priority == "cool":
                payload["prior"] = 1
            elif hvac_mode_priority == "auto":
                payload["prior"] = 2
            else:
                _LOGGER.error("Invalid HVAC mode priority. Must be 'cool', 'heat', or 'auto'.")
                raise InvalidParameterError("Invalid HVAC mode priority. Must be 'cool', 'heat', or 'auto'.")
        if weather_shutdown_lag_time is not None:
            if isinstance(weather_shutdown_lag_time, int) and weather_shutdown_lag_time >= 0:
                payload["wwTime"] = weather_shutdown_lag_time
            else:
                _LOGGER.error("Invalid value for warm or cold weather shutdown time. Must be a non-negative integer.")
                raise InvalidParameterError("weather_shutdown_lag_time must be a non-negative integer.")

        if not payload:
            _LOGGER.error("At least one optional parameter must be provided")
            raise InvalidParameterError("At least one optional parameter must be provided.")

        try:
            async with self._session.patch(
                url,
                json=payload,
                headers={**self.headers, "Content-Type": "application/json"},
                proxy=self.proxy_url,
                timeout=10
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(f"Failed to set device parameter(s) with status {resp.status}")
                    raise RuntimeError(f"Failed to set device parameter(s) with status {resp.status}")
                _LOGGER.debug(f"Response from setting device parameter(s): {await resp.json()}")
        except Exception as e:
            _LOGGER.error(f"Exception setting device parameter(s): {e}")
            raise RuntimeError(f"Exception setting device parameter(s): {e}")

           
class SensorlinxDevice:
    """
    Represents a device managed by the Sensorlinx system, providing methods to set various device parameters.

    Args:
        sensorlinx (Sensorlinx): An instance of the Sensorlinx API client used to communicate with the backend.
        building_id (str): The unique identifier for the building where the device is located.
        device_id (str): The unique identifier for the device within the building.
    """

    def __init__(self, sensorlinx: Sensorlinx, building_id: str, device_id: str):
        """
        Initialize a SensorlinxDevice.

        Args:
            sensorlinx (Sensorlinx): The Sensorlinx API client.
            building_id (str): The building's unique identifier.
            device_id (str): The device's unique identifier.
        """
        self.sensorlinx = sensorlinx
        self.building_id = building_id
        self.device_id = device_id
        
    '''
        #################################################################################################################################
        #
        #                                               Device Settings - Set Methods
        # 
        #################################################################################################################################   
    '''
    async def set_hvac_mode_priority(self, value: str) -> None:
        """
        Set the HVAC mode priority for the device.

        Args:
            value (str): The HVAC mode priority to set (e.g., "heat", "cool" or "auto").

        Raises:
            InvalidParameterError: If value is not one of "cool", "heat" or "auto".
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        if value not in ["cool", "heat", "auto"]:
            _LOGGER.error("Invalid HVAC mode priority. Must be 'cool', 'heat' or 'auto'.")
            raise InvalidParameterError("Invalid HVAC mode priority. Must be 'cool', 'heat' or 'auto'.")
        
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, hvac_mode_priority=value
        )
        
    
    async def set_weather_shutdown_lag_time(self, value: int) -> None:
        """
        Sets the lag time (in hours) for Warm Weather Shutdown (WWSD) or Cold Weather Shutdown (CWSD).

        Args:
            value (int): The lag time in hours to wait before entering WWSD or CWSD after the temperature threshold is met.

        Raises:
            InvalidParameterError: If value is not a non-negative integer.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        if not isinstance(value, int) or value < 0:
            _LOGGER.error("Invalid value for warm or cold weather shutdown time. Must be a non-negative integer.")
            raise InvalidParameterError("Value must be a non-negative integer.")

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, weather_shutdown_lag_time=value
        )


    async def set_permanent_hd(self, value: bool) -> None:
        """
        Set the permanent heating demand parameter for the device.

        Args:
            value (bool): True to enable permanent heating demand, False to disable.

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, permanent_hd=value
        )

    async def set_permanent_cd(self, value: bool) -> None:
        """
        Set the permanent cooling demand parameter for the device.

        Args:
            value (bool): True to enable permanent cooling demand, False to disable.

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, permanent_cd=value
        )

    async def set_cold_weather_shutdown(self, value) -> None:
        """
        Set the cold weather shutdown parameter for the device.

        Args:
            value (Temperature or str): The value to set for cold weather shutdown (Temperature instance or 'off').

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, cold_weather_shutdown=value
        )

    async def set_warm_weather_shutdown(self, value) -> None:
        """
        Set the warm weather shutdown parameter for the device.

        Args:
            value (Temperature or str): The value to set for warm weather shutdown (Temperature instance or 'off').

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, warm_weather_shutdown=value
        )

    '''
        #################################################################################################################################
                                                METHODS TO GET PARAMETERS
        #################################################################################################################################

    '''
    
    async def _get_device_info_value(self, key: str, device_info: Optional[Dict] = None, *, parent: Optional[str] = None) -> str:
        """
        Helper to get a value from device_info by key, optionally from a parent dict.

        Args:
            key (str): The key to retrieve.
            device_info (Optional[Dict]): The device info dict.
            parent (Optional[str]): If provided, look for the key inside this parent dict.

        Returns:
            str: The value found.

        Raises:
            RuntimeError: If the device info or key is not found.
        """
        if device_info is None:
            device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
        if not device_info:
            raise RuntimeError("Device info not found.")
        if parent:
            parent_dict = device_info.get(parent)
            if not (parent_dict and isinstance(parent_dict, dict)):
                raise RuntimeError(f"{parent.capitalize()} info not found.")
            value = parent_dict.get(key)
        else:
            value = device_info.get(key)
        if value is None:
            raise RuntimeError(f"{key.replace('_', ' ').capitalize()} not found.")
        return value    
    
    #################################################################################################################################
    #                                               General Device Get Methods
    #################################################################################################################################

    async def get_firmware_version(self, device_info: Optional[Dict] = None) -> str:
        """
        Get the firmware version of the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            str: The firmware version string.

        Raises:
            RuntimeError: If the device or firmware version is not found.
        """
        return await self._get_device_info_value("firmVer", device_info)

    async def get_sync_code(self, device_info: Optional[Dict] = None) -> str:
        """
        Get the sync code of the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            str: The sync code string.

        Raises:
            RuntimeError: If the device or sync code is not found.
        """
        return await self._get_device_info_value("syncCode", device_info)

    async def get_device_pin(self, device_info: Optional[Dict] = None) -> str:
        """
        Get the device PIN.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            str: The device PIN string.

        Raises:
            RuntimeError: If the device or PIN is not found.
        """
        return await self._get_device_info_value("pin", device_info, parent="production")
    
    async def get_device_type(self, device_info: Optional[Dict] = None) -> str:
        """
        Get the device type.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            str: The device type string.

        Raises:
            RuntimeError: If the device or device type is not found.
        """
        return await self._get_device_info_value("deviceType", device_info)

    async def get_temperatures(
        self, 
        temp_name: Optional[str] = None, 
        device_info: Optional[Dict] = None
    ) -> Union[Dict[str, Dict[str, Optional[Temperature]]], Dict[str, Optional[Temperature]]]:
        """
        Get the current temperatures for the device.

        Args:
            temp_name (Optional[str]): The name of the temperature sensor to retrieve. If None, retrieves all.
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Dict[str, Dict[str, Optional[Temperature]]]: 
                A dictionary with sensor titles as keys and dicts with 'actual' and 'target' Temperature instances as values,
                or a single dict for the requested sensor if temp_name is provided.

        Raises:
            RuntimeError: If the device or temperature data is not found.
        """
        if device_info is None:
            device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
        if not device_info or "temps" not in device_info:
            raise RuntimeError("Device or temperature data not found.")

        result = {}
        for temp_key, temp_info in device_info["temps"].items():
            sensor_title = temp_info.get("title")
            if sensor_title is None:
                continue  # Skip entries with null titles
            if temp_name and sensor_title != temp_name:
                continue
            actual = temp_info.get("actual")
            target = temp_info.get("target")
            result[sensor_title] = {
                "actual": Temperature(actual, "F") if actual is not None else None,
                "target": Temperature(target, "F") if target is not None else None
            }
        if temp_name:
            if temp_name not in result:
                raise RuntimeError(f"Temperature sensor '{temp_name}' not found.")
            return result[temp_name]
        if not result:
            raise RuntimeError("No matching temperature sensors found.")
        return result
    
    async def get_runtimes(self, device_info: Optional[Dict] = None) -> Dict[str, Union[list, str]]:
        """
        Retrieve runtimes for heat pump stages and backup heater.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Dict[str, Union[list, str]]: Dictionary with 'stages' as a list of timedelta objects and 'backup' as a string.

        Raises:
            RuntimeError: If required runtime data is not found.
        """
        if device_info is None:
            device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
        if not device_info:
            raise RuntimeError("Device info not found.")

        stg_run = device_info.get("stgRun")
        num_stg = device_info.get("numStg")
        bk_run = device_info.get("bkRun")

        if stg_run is None or num_stg is None:
            raise RuntimeError("Stage runtime data not found.")

        def parse_runtime(runtime_str):
            # Expects format "H:MM"
            hours, minutes = map(int, runtime_str.split(":"))
            return datetime.timedelta(hours=hours, minutes=minutes)

        stages = []
        for i in range(num_stg):
            value = stg_run[i] if i < len(stg_run) else "0:00"
            stages.append(parse_runtime(value))

        result = {"stages": stages}
        if bk_run is not None:
            result["backup"] = parse_runtime(bk_run)  # You could also parse this if it's in the same format

        return result
        
    
