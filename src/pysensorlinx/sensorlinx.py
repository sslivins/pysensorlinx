'''
    This file implements classes and methods to get and set parameters for the HBX ECO-0600 controller
    via the Sensorlinx API.
    It provides asynchronous methods for authentication, device and building management, and detailed
    parameter control for the ECO-0600, including temperature, staging, backup, and other operational
    settings.

    The latest documentation for the HBX ECO-0600 controller as of the writing of this file can be found here:
    https://admin.hbxcontrols.com/assets/Uploads/resources/ECO-0600-2.0.1.pdf

    Any bugs or issues should be reported at:
    https://github.com/sslivins/pysensorlinx/issues
'''

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
        wide_priority_differential: Optional[bool] = None,
        number_of_stages: Optional[int] = None,
        two_stage_heat_pump: Optional[bool] = None, 
        stage_on_lag_time: Optional[int] = None,
        stage_off_lag_time: Optional[int] = None,
        rotate_cycles: Optional[Union[int, str]] = None,
        rotate_time: Optional[Union[int, str]] = None,
        off_staging: Optional[bool] = None,
        heat_cool_switch_delay: Optional[int] = None,
        hot_tank_outdoor_reset: Optional[Union[int, str]] = None,
        heat_differential: Optional[Temperature] = None,
        hot_min_tank_temp: Optional[Temperature] = None,
        hot_max_tank_temp: Optional[Temperature] = None,
        cold_tank_outdoor_reset: Optional[Union[int, str]] = None,
        cold_differential: Optional[Temperature] = None,
        cold_min_tank_temp: Optional[Temperature] = None,
        cold_max_tank_temp: Optional[Temperature] = None,
        backup_time: Optional[int] = None,
        backup_temp: Optional[Temperature] = None,
        backup_differential: Optional[Temperature] = None,
        backup_only_outdoor_temp: Optional[Temperature] = None,
        backup_only_tank_temp: Optional[Temperature] = None
    ) -> None:
        """
        Set permanent heating and/or cooling demand for a specific device.

        Args:
            building_id (str): The ID of the building (required).
            device_id (str): The ID of the device (required).
            
            permanent_hd (Optional[bool]): If True, always maintain buffer tank target temperature (heating).
            permanent_cd (Optional[bool]): If True, always maintain buffer tank target temperature (cooling).
            hvac_mode_priority (Optional[str]): The HVAC mode priority to set (e.g., "cool", "heat", "auto").
            weather_shutdown_lag_time (Optional[int]): Lag time for warm/cold weather shutdown.
            wide_priority_differential (Optional[bool]): If True, enables wide priority differential for the device.
            number_of_stages (Optional[int]): Number of heat pump stages attached to the control (1-4).
            two_stage_heat_pump (Optional[bool]): If True, enables two-stage heat pump mode.
            stage_on_lag_time (Optional[int]): Lag time in minutes between heat pump stages (1-240).
            stage_off_lag_time (Optional[int]): Lag time in seconds between heat pump stages (0-240).
            rotate_cycles (Optional[Union[int, str]]): Number of cycles to rotate heat pumps, or 'off' to disable.
            rotate_time (Optional[Union[int, str]]): Time of rotation between heat pumps in hours, or 'off' to disable.
            off_staging (Optional[bool]): If True, enables Off Staging feature for the device.
            heat_cool_switch_delay (Optional[int]): Delay in seconds between switching from heat to cool (30-600).
            warm_weather_shutdown (Optional[Temperature or str]): when in heating mode shuts the heat pump off above this temperature, or 'off' to disable.
            hot_tank_outdoor_reset (Optional[Union[int, str]]): Design temperature for outdoor reset in °F (-40 to 127) or 'off' to disable.
            heat_differential (Optional[Temperature]): The heat differential to set for the device.
            hot_min_tank_temp (Optional[Temperature]): The minimum tank temperature for the hot tank (35°F to 200°F)
            hot_max_tank_temp (Optional[Temperature]): The maximum tank temperature for the hot tank (35°F to 200°F)
            cold_weather_shutdown (Optional[Temperature or str]): when in cooling mode shuts the heat pump off below this temperature, (32F to 119F) or 'off' to disable.
            cold_tank_outdoor_reset (Optional[Union[int, str]]): Design temperature for outdoor reset in (0F to 119F) or 'off' to disable.
            cold_differential (Optional[Temperature]): The cold differential to set for the device (2°F to 100°F)
            cold_min_tank_temp (Optional[Temperature]): The minimum tank temperature for the cold tank (35°F to 200°F)
            cold_max_tank_temp (Optional[Temperature]): The maximum tank temperature for the cold tank (35°F to 200°F)
            backup_time (Optional[int]): The time in minutes to wait before switching to backup mode.
            backup_temp (Optional[Temperature]): The outdoor temperature at which the backup mode is activated (2F to 100F) or 'off' to disable.
            backup_differential (Optional[Temperature]): The backup differential temperature to set for the device or 'off' to disable.
            backup_only_outdoor_temp (Optional[Temperature]): The outdoor temperature at which the backup mode is activated (-40F to 127F) or 'off' to disable.
            backup_only_tank_temp (Optional[Temperature]): The tank temperature at which the backup mode is activated (33F to 200F) or 'off' to disable.

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

        if wide_priority_differential is not None:
            payload["wPDif"] = wide_priority_differential
            
        if number_of_stages is not None:
            if isinstance(number_of_stages, int) and 1 <= number_of_stages <= 4:
                payload["numStg"] = number_of_stages
            else:
                _LOGGER.error("Number of stages must be an integer between 1 and 4.")
                raise InvalidParameterError("number_of_stages must be an integer between 1 and 4.")
        
        if two_stage_heat_pump is not None:
            if isinstance(two_stage_heat_pump, bool):
                payload["twoS"] = two_stage_heat_pump
            else:
                _LOGGER.error("two_stage_heat_pump must be a boolean value.")
                raise InvalidParameterError("two_stage_heat_pump must be a boolean value.")
            
        if stage_on_lag_time is not None:
            if isinstance(stage_on_lag_time, int) and 1 <= stage_on_lag_time <= 240:
                payload["lagT"] = stage_on_lag_time
            else:
                _LOGGER.error("Stage ON Lagtime must be an integer between 1 and 240 minutes.")
                raise InvalidParameterError("stage_on_lag_time must be an integer between 1 and 240 minutes.")
            
        if stage_off_lag_time is not None:
            if isinstance(stage_off_lag_time, int) and 0 <= stage_off_lag_time <= 240:
                payload["lagOff"] = stage_off_lag_time
            else:
                _LOGGER.error("Stage OFF Lagtime must be an integer between 0 and 240 seconds.")
                raise InvalidParameterError("stage_off_lag_time must be an integer between 0 and 240 seconds.")
            
        if rotate_cycles is not None:
            if isinstance(rotate_cycles, str) and rotate_cycles.lower() == "off":
                payload["rotCy"] = 0
            elif isinstance(rotate_cycles, int) and 1 <= rotate_cycles <= 240:
                payload["rotCy"] = rotate_cycles
            else:
                _LOGGER.error("Rotate cycles must be an integer between 1 and 240 or 'off'.")
                raise InvalidParameterError("rotate_cycles must be an integer between 1 and 240 or 'off'.")
            
        if rotate_time is not None:
            if isinstance(rotate_time, str) and rotate_time.lower() == "off":
                payload["rotTi"] = 0
            elif isinstance(rotate_time, int) and 1 <= rotate_time <= 240:
                payload["rotTi"] = rotate_time
            else:
                _LOGGER.error("Rotate time must be an integer between 1 and 240 or 'off'.")
                raise InvalidParameterError("rotate_time must be an integer between 1 and 240 or 'off'.")
            
        if off_staging is not None:
            if isinstance(off_staging, bool):
                payload["hpStg"] = off_staging
            else:
                _LOGGER.error("Off staging must be a boolean value.")
                raise InvalidParameterError("off_staging must be a boolean value.")
            
        if heat_cool_switch_delay is not None:
            if isinstance(heat_cool_switch_delay, int) and 30 <= heat_cool_switch_delay <= 600:
                payload["hpSw"] = heat_cool_switch_delay
            else:
                _LOGGER.error("Heat/Cool Switch Delay must be an integer between 30 and 600 seconds.")
                raise InvalidParameterError("heat_cool_switch_delay must be an integer between 30 and 600 seconds.")
            
        ###############################################################################################    
        # Hot Tank parameters
        ###############################################################################################     
        
        if warm_weather_shutdown is not None:
            if isinstance(warm_weather_shutdown, str) and warm_weather_shutdown.lower() == "off":
                payload["wwsd"] = 32
            elif isinstance(warm_weather_shutdown, Temperature):
                payload["wwsd"] = round(warm_weather_shutdown.to_fahrenheit())
            else:
                raise InvalidParameterError("warm_weather_shutdown must be a Temperature or 'off'")               
            
        if hot_tank_outdoor_reset is not None:
            if isinstance(hot_tank_outdoor_reset, str) and hot_tank_outdoor_reset.lower() == "off":
                payload["dot"] = -41
            elif isinstance(hot_tank_outdoor_reset, int) and -40 <= hot_tank_outdoor_reset <= 127:
                payload["dot"] = hot_tank_outdoor_reset
            else:
                _LOGGER.error("Outdoor reset must be an integer between -40 and 127 or 'off'.")
                raise InvalidParameterError("hot_tank_outdoor_reset must be an integer between -40 and 127 or 'off'.")
            
        if heat_differential is not None:
            if isinstance(heat_differential, Temperature):
                payload["htDif"] = round(heat_differential.to_fahrenheit())
            else:
                _LOGGER.error("heat_differential must be a Temperature instance.")
                raise InvalidParameterError("heat_differential must be a Temperature instance.")
            
        if hot_min_tank_temp is not None:
            if isinstance(hot_min_tank_temp, Temperature):
                temp_f = hot_min_tank_temp.to_fahrenheit()
                if not (35 <= temp_f <= 200):
                    _LOGGER.error("hot_min_tank_temp must be between 35°F and 200°F.")
                    raise InvalidParameterError("hot_min_tank_temp must be between 35°F and 200°F.")
                payload["dbt"] = round(temp_f)
            else:
                _LOGGER.error("hot_min_tank_temp must be a Temperature instance.")
                raise InvalidParameterError("hot_min_tank_temp must be a Temperature instance.")
            
        if hot_max_tank_temp is not None:
            if isinstance(hot_max_tank_temp, Temperature):
                temp_f = hot_max_tank_temp.to_fahrenheit()
                if not (35 <= temp_f <= 200):
                    _LOGGER.error("hot_max_tank_temp must be between 35°F and 200°F.")
                    raise InvalidParameterError("hot_max_tank_temp must be between 35°F and 200°F.")
                payload["mbt"] = round(temp_f)
            else:
                _LOGGER.error("hot_max_tank_temp must be a Temperature instance.")
                raise InvalidParameterError("hot_max_tank_temp must be a Temperature instance.")
        
        ###############################################################################################    
        # Cold Tank parameters
        ###############################################################################################
            
        if cold_weather_shutdown is not None:
            if isinstance(cold_weather_shutdown, str) and cold_weather_shutdown.lower() == "off":
                payload["cwsd"] = 32
            elif isinstance(cold_weather_shutdown, Temperature):
                payload["cwsd"] = round(cold_weather_shutdown.to_fahrenheit())
            else:
                raise InvalidParameterError("cold_weather_shutdown must be a Temperature or 'off'")            
            
        if cold_tank_outdoor_reset is not None:
            if isinstance(cold_tank_outdoor_reset, str) and cold_tank_outdoor_reset.lower() == "off":
                payload["cdot"] = -41
            elif isinstance(cold_tank_outdoor_reset, int) and 0 <= cold_tank_outdoor_reset <= 119:
                payload["cdot"] = cold_tank_outdoor_reset
            else:
                _LOGGER.error("cold_tank_outdoor_reset must be an integer between 0 and 119 or 'off'.")
                raise InvalidParameterError("cold_tank_outdoor_reset must be an integer between 0 and 119 or 'off'.")
            
        if cold_differential is not None:
            if isinstance(cold_differential, Temperature):
                temp_f = cold_differential.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("cold_differential must be between 2°F and 100°F.")
                    raise InvalidParameterError("cold_differential must be between 2°F and 100°F.")
                payload["clDif"] = round(temp_f)
            else:
                _LOGGER.error("cold_differential must be a Temperature instance.")
                raise InvalidParameterError("cold_differential must be a Temperature instance.")
            
        if cold_min_tank_temp is not None:
            if isinstance(cold_min_tank_temp, Temperature):
                temp_f = cold_min_tank_temp.to_fahrenheit()
                if not (35 <= temp_f <= 200):
                    _LOGGER.error("cold_min_tank_temp must be between 35°F and 200°F.")
                    raise InvalidParameterError("cold_min_tank_temp must be between 35°F and 200°F.")
                payload["dst"] = round(temp_f)
            else:
                _LOGGER.error("cold_min_tank_temp must be a Temperature instance.")
                raise InvalidParameterError("cold_min_tank_temp must be a Temperature instance.")
            
        if cold_max_tank_temp is not None:
            if isinstance(cold_max_tank_temp, Temperature):
                temp_f = cold_max_tank_temp.to_fahrenheit()
                if not (35 <= temp_f <= 200):
                    _LOGGER.error("cold_max_tank_temp must be between 35°F and 200°F.")
                    raise InvalidParameterError("cold_max_tank_temp must be between 35°F and 200°F.")
                payload["mst"] = round(temp_f)
            else:
                _LOGGER.error("cold_max_tank_temp must be a Temperature instance.")
                raise InvalidParameterError("cold_max_tank_temp must be a Temperature instance.")
            
        ###############################################################################################    
        # Domestic Hot Water Parameters
        ###############################################################################################        
        
        ###############################################################################################    
        # Backup Parameters
        ###############################################################################################          
            
        if backup_time is not None:
            if isinstance(backup_time, str):
                if backup_time.lower() != "off":
                    _LOGGER.error("Backup time must be an integer between 1 and 240 or 'off'.")
                    raise InvalidParameterError("Backup time must be an integer between 1 and 240 or 'off'.")
                payload["bkLag"] = 0
            elif isinstance(backup_time, int):
                if not (1 <= backup_time <= 240):
                    _LOGGER.error("Backup time must be an integer between 1 and 240.")
                    raise InvalidParameterError("Backup time must be an integer between 1 and 240.")
                payload["bkLag"] = backup_time
            else:
                _LOGGER.error("Backup time must be an integer between 1 and 240 or 'off'.")
                raise InvalidParameterError("Backup time must be an integer between 1 and 240 or 'off'.")
            
        if backup_temp is not None:
            if isinstance(backup_temp, str) and backup_temp.lower() == "off":
                payload["bkTemp"] = 0
            elif isinstance(backup_temp, Temperature):
                temp_f = backup_temp.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("Backup temperature must be between 2°F and 100°F.")
                    raise InvalidParameterError("backup_temp must be between 2°F and 100°F.")
                payload["bkTemp"] = round(temp_f)
            else:
                _LOGGER.error("backup_temp must be a Temperature instance or 'off'.")
                raise InvalidParameterError("backup_temp must be a Temperature instance or 'off'.")
            
        if backup_differential is not None:
            if isinstance(backup_differential, str) and backup_differential.lower() == "off":
                payload["bkDif"] = 0
            elif isinstance(backup_differential, Temperature):
                temp_f = backup_differential.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("Backup differential must be between 2°F and 100°F.")
                    raise InvalidParameterError("backup_differential must be between 2°F and 100°F.")
                payload["bkDif"] = round(temp_f)
            else:
                _LOGGER.error("backup_differential must be a Temperature instance or 'off'.")
                raise InvalidParameterError("backup_differential must be a Temperature instance or 'off'.")
            
        if backup_only_outdoor_temp is not None:
            if isinstance(backup_only_outdoor_temp, str) and backup_only_outdoor_temp.lower() == "off":
                payload["bkOd"] = -41
            elif isinstance(backup_only_outdoor_temp, Temperature):
                temp_f = backup_only_outdoor_temp.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("Backup only outdoor temperature must be between 2°F and 100°F.")
                    raise InvalidParameterError("backup_only_outdoor_temp must be between 2°F and 100°F.")
                payload["bkOd"] = round(temp_f)
            else:
                _LOGGER.error("backup_only_outdoor_temp must be a Temperature instance or 'off'.")
                raise InvalidParameterError("backup_only_outdoor_temp must be a Temperature instance or 'off'.")
            
        if backup_only_tank_temp is not None:
            if isinstance(backup_only_tank_temp, str) and backup_only_tank_temp.lower() == "off":
                payload["bkTk"] = 32
            elif isinstance(backup_only_tank_temp, Temperature):
                temp_f = backup_only_tank_temp.to_fahrenheit()
                if not (33 <= temp_f <= 200):
                    _LOGGER.error("Backup only tank temperature must be between 2°F and 100°F.")
                    raise InvalidParameterError("backup_only_tank_temp must be between 2°F and 100°F.")
                payload["bkTk"] = round(temp_f)
            else:
                _LOGGER.error("backup_only_tank_temp must be a Temperature instance or 'off'.")
                raise InvalidParameterError("backup_only_tank_temp must be a Temperature instance or 'off'.")
            
        ###############################################################################################
        #                       Pump Parameters
        ###############################################################################################
            
            
        ###############################################################################################
        # --- End of parameter processing, payload is ready ---
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
        
    async def set_wide_priority_differential(self, value: bool) -> None:
        """
        Enable or disable Wide Priority Differential for the device.

        When enabled, the tank target will exceed the setpoint by the configured differential before switching between heat and cool demands if both are present. When disabled, the tank target switches as soon as the setpoint is satisfied. This should not be used for single tank systems.

        Args:
            value (bool): True to enable, False to disable.

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, wide_priority_differential=value
        )


    async def set_permanent_hd(self, value: bool) -> None:
        """
        Set the permanent heating demand parameter for the device.

        This setting indicates that the ECO-0600 is in a permanent heat demand state. 
        It can be used instead of attaching a thermostat. 

        When enabled, the tank will always maintain the target temperature, even if there is no external demand.

        Args:
            value (bool): True to enable permanent heating demand (ON), False to disable (OFF).

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

        This setting indicates that the ECO-0600 is in a permanent cooling demand state.
        It can be used instead of attaching a thermostat.

        When enabled, the tank will always maintain the target temperature for cooling, even if there is no external demand.

        Args:
            value (bool): True to enable permanent cooling demand (ON), False to disable (OFF).

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, permanent_cd=value
        )

    #################################################################################################################################
    #                                               Heat Pump Setup Methods
    #################################################################################################################################

    async def set_number_of_stages(self, value: int) -> None:
        """
        Set the number of heat pump stages attached to the control.

        This setting allows you to select the number of heat pump stages that are attached to the control.
        If Backup is being used, you can only have a maximum of 3 stages. If Backup is being used with 4 stages of heat pumps,
        then Pump Output 1 will be used for the Backup. Allowed values: 1 to 4. Default: 1.

        Args:
            value (int): The number of stages (must be an integer between 1 and 4).

        Raises:
            InvalidParameterError: If the value is not between 1 and 4.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        if not isinstance(value, int) or not (1 <= value <= 4):
            _LOGGER.error("Number of stages must be an integer between 1 and 4.")
            raise InvalidParameterError("Number of stages must be an integer between 1 and 4.")
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, number_of_stages=value
        )
        
    async def set_two_stage_heat_pump(self, value: bool) -> None:
        """
        Set the two-stage heat pump parameter for the device.

        This setting will appear when the Number of Stages is set to an even value.
        This setting can be utilized when using dual stage heat pumps or pumps with 2 compressors per unit.

        Args:
            value (bool): True to enable two-stage heat pump mode, False to disable.

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, two_stage_heat_pump=value
        )
        
    async def set_stage_on_lag_time(self, value: int) -> None:
        """
        Set the Stage ON Lagtime for the device.

        When the heat pump is set for more than 1 stage, this setting specifies the minimum lagtime (in minutes) between heat pump stages. 
        This is a time delay between stages: even if the differential has been exceeded, this time must elapse before the next stage can 
        turn on. Allowed values: 1-240 minutes.

        Args:
            value (int): The lag time in minutes to wait before activating the next stage (must be between 1 and 240).

        Raises:
            InvalidParameterError: If the value is not between 1 and 240.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        if not isinstance(value, int) or not (1 <= value <= 240):
            _LOGGER.error("Stage ON Lagtime must be an integer between 1 and 240 minutes.")
            raise InvalidParameterError("Stage ON Lagtime must be an integer between 1 and 240 minutes.")
        
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, stage_on_lag_time=value
        )
        
    async def set_stage_off_lag_time(self, value: int) -> None:
        """
        Set the Stage OFF Lagtime for the device.

        When the heat pump is set for more than 1 stage, this setting specifies the minimum OFF lagtime (in seconds) between heat pump stages.
        Allowed values: 0-240 seconds.

        Args:
            value (int): The lag time in seconds to wait before deactivating the next stage (must be between 0 and 240).

        Raises:
            InvalidParameterError: If the value is not between 0 and 240.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        if not isinstance(value, int) or not (0 <= value <= 240):
            _LOGGER.error("Stage OFF Lagtime must be an integer between 0 and 240 seconds.")
            raise InvalidParameterError("Stage OFF Lagtime must be an integer between 0 and 240 seconds.")

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, stage_off_lag_time=value
        )
        
    async def set_rotate_cycles(self, value: Union[int, str]) -> None:
        """
        Set the number of cycles at which to rotate the heat pumps.

        One cycle is defined as the heat pump turning on and then off.
        Allowed values: "off" (to disable) or an integer between 1 and 240.

        Args:
            value (Union[int, str]): Number of cycles (1-240) or "off" to disable.

        Raises:
            InvalidParameterError: If the value is not "off" or an integer in range.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        if isinstance(value, str):
            if value.lower() != "off":
                _LOGGER.error("Rotate cycles must be an integer between 1 and 240 or 'off'.")
                raise InvalidParameterError("Rotate cycles must be an integer between 1 and 240 or 'off'.")
            cycles = 0
        elif isinstance(value, int):
            if not (1 <= value <= 240):
                _LOGGER.error("Rotate cycles must be an integer between 1 and 240.")
                raise InvalidParameterError("Rotate cycles must be an integer between 1 and 240.")
            cycles = value
        else:
            _LOGGER.error("Rotate cycles must be an integer between 1 and 240 or 'off'.")
            raise InvalidParameterError("Rotate cycles must be an integer between 1 and 240 or 'off'.")

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, rotate_cycles=cycles
        )
        
    async def set_rotate_time(self, value: Union[int, str]) -> None:
        """
        Set the rotate time between heat pumps.

        This setting determines the time of rotation between heat pumps, in hours of run time.
        The heat pumps will rotate when the first heat pump exceeds the second by the rotate time.
        Allowed values: "off" (to disable) or an integer between 1 and 240.

        Args:
            value (Union[int, str]): Number of hours (1-240) or "off" to disable.

        Raises:
            InvalidParameterError: If the value is not "off" or an integer in range.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, rotate_time=value
        )
        
    async def set_off_staging(self, value: bool) -> None:
        """
        Set the Off Staging feature for the device.

        If set to False (OFF), the heat pumps will stage off normally based on tank temperature,
        differential settings, or Stage OFF Lagtime settings.
        If set to True (ON), all heat pumps will stage off at the same time based on tank temperature
        and differential settings.

        Args:
            value (bool): True to enable Off Staging (ON), False to disable (OFF).

        Raises:
            InvalidParameterError: If the value is not a boolean.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, off_staging=value
        )
        
    async def set_heat_cool_switch_delay(self, value: int) -> None:
        """
        Set the delay between switching from heat to cool (and vice versa).

        This setting specifies the delay (in seconds) between the control switching between heat and cool calls.
        Allowed values: 30 to 600 seconds.

        Args:
            value (int): The delay in seconds (must be between 30 and 600).

        Raises:
            InvalidParameterError: If the value is not between 30 and 600.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, heat_cool_switch_delay=value
        )
        
    #################################################################################################################################
    #                                               Hot Tank Setup Methods
    #################################################################################################################################
    
    
    async def set_warm_weather_shutdown(self, value: Union[Temperature, str]) -> None:
        """
        Set the warm weather shutdown (WWSD) parameter for the device.

        WWSD is used to set the temperature at which the ECO-0600 will enter Warm Weather Shutdown.
        If the system rises above this temperature, the system will be shut off (heat pumps and backup boiler).
        Allowed values: "off" (to disable) or a Temperature between 34°F and 180°F (inclusive).

        Args:
            value (Temperature or str): The value to set for WWSD (Temperature instance or 'off').

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, warm_weather_shutdown=value
        )
        
    async def set_hot_tank_outdoor_reset(self, value: Union[int, str]) -> None:
        """
        Set the Outdoor Reset (Design Outdoor Temperature) parameter for the hot tank.

        This is used in the outdoor reset design calculation for the hot tank. Set to "off" if not using outdoor reset.
        With this enabled, the Tank Temperature setting will be replaced by Min Tank and Max Tank Temperature settings for the hot tank.

        Args:
            value (Union[int, str]): The design outdoor temperature in °F (-40 to 127) or "off" to disable.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, hot_tank_outdoor_reset=value
        )
        
    async def set_heat_differential(self, value: Temperature) -> None:
        """
        Set the heat differential for the hot tank.

        This temperature sets the desired hot tank differential. For example, a differential of 4°F will allow for 2 degrees above
        and/or 2 degrees below the desired temperature before a demand is present.

        Args:
            value (Temperature): The differential as a Temperature object.

        Raises:
            InvalidParameterError: If the value is not a Temperature instance.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, heat_differential=value
        )
        
    async def set_hot_min_tank_temp(self, value: Temperature) -> None:
        """
        Set the minimum tank temperature for the hot tank.

        This setting is the bottom of the heat curve. The target will hit this temperature as the
        Outdoor Temperature approaches the WWSD. Allowed values: 35°F to 200°F. Default: 80°F.

        Args:
            value (Temperature): The minimum tank temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, hot_min_tank_temp=value
        )
        
    async def set_hot_max_tank_temp(self, value: Temperature) -> None:
        """
        Set the maximum tank temperature for the hot tank.

        This setting is the top of the heat curve. The target will hit this temperature as the
        Outdoor Temperature approaches the Design Outdoor Temperature.
        Allowed values: 35°F to 200°F. Default: 115°F.

        Args:
            value (Temperature): The maximum tank temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (not a Temperature or out of range).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, hot_max_tank_temp=value
        )

    #################################################################################################################################
    #                                               Cold Tank Set Methods
    #################################################################################################################################

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
        
    async def set_cold_tank_outdoor_reset(self, value: Union[int, str]) -> None:
        """
        Set the Outdoor Reset (Design Outdoor Temperature) parameter for the cold tank.

        This is used in the outdoor reset design calculation for the cold tank. Set to "off" if not using outdoor reset.
        With this enabled, the Tank Temperature setting will be replaced by Min Tank and Max Tank Temperature settings for the cold tank.

        Args:
            value (Union[int, str]): The design outdoor temperature in °F (0 to 119) or "off" to disable.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, cold_tank_outdoor_reset=value
        )
        
    async def set_cold_differential(self, value: Temperature) -> None:
        """
        Set the cold tank differential for the device.

        This temperature sets the desired cold tank differential. For example, a differential of 4°F will allow for 2 degrees above
        and/or 2 degrees below the desired temperature before a demand is present.

        Args:
            value (Temperature): The differential as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, cold_differential=value
        )
        
    async def set_cold_min_tank_temp(self, value: Temperature) -> None:
        """
        Set the minimum tank temperature for the cold tank.

        This setting is the bottom of the cooling curve. The target will hit this temperature as the
        Outdoor Temperature approaches the Outdoor Design Temperature.
        Allowed values: 30°F to 200°F. Default: 45°F.

        Args:
            value (Temperature): The minimum tank temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, cold_min_tank_temp=value
        )
        
    async def set_cold_max_tank_temp(self, value: Temperature) -> None:
        """
        Set the maximum tank temperature for the cold tank.

        This setting is the top of the cooling curve. The target will hit this temperature as the
        Outdoor Temperature approaches the Cold Weather Shutdown (CWSD).
        Allowed values: 30°F to 200°F. Default: 60°F.

        Args:
            value (Temperature): The maximum tank temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, cold_max_tank_temp=value
        )
        
    #################################################################################################################################
    #                                               Domestic Hot Water Set Methods
    #################################################################################################################################
    
    #################################################################################################################################
    #                                               Backup Set Methods
    #################################################################################################################################  
        
    async def set_backup_time(self, value: Union[int, str]) -> None:
        """
        Set the backup time (lag time between heat pump stages and backup boiler).

        This is the minimum lag time (in minutes) between heat pump stages and the backup boiler.
        Allowed values: "off" (to disable) or an integer between 1 and 240.

        Args:
            value (Union[int, str]): Number of minutes (1-240) or "off" to disable.

        Raises:
            InvalidParameterError: If the value is not "off" or an integer in range.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, backup_time=value
        )
        
    async def set_backup_temp(self, value: Union[int, str]) -> None:
        """
        Set the backup temperature threshold for the device.

        When the outdoor temperature falls below this value, the backup will be allowed to come on.
        If set to "off", this feature is disabled.

        Args:
            value (Temperature or str): The temperature threshold as a Temperature object or "off" to disable.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled elsewhere).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, backup_temp=value
        )
        
    async def set_backup_differential(self, value: Union[Temperature, str]) -> None:
        """
        Set the backup differential for the device.

        This setting is used to set a differential on the tank at which you would like the backup to come on.
        This setting will override the backup time settings and bring the backup on instantaneously if the target is at or below the differential.
        (eg. Tank temperature of 115°F and a backup differential of 10°F. The backup boiler will come on at 105°F providing all of the heat pumps are already on)
        Allowed values: "off" (to disable) or a Temperature between 2°F and 100°F.

        Args:
            value (Temperature or str): The backup differential as a Temperature object or "off" to disable.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled elsewhere).        
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, backup_differential=value
        )
        
    async def set_backup_only_outdoor_temp(self, value: Temperature) -> None:
        """
        Set the Backup Only Outdoor temperature threshold for the device.

        When the outdoor temperature is below this value, only the backup will run for a Hot Tank or DHW call.
        The heat pumps will not run until the outdoor temperature rises above this setting.

        Args:
            value (Temperature): The temperature threshold as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled elsewhere). 
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, backup_only_outdoor_temp=value
        )
        
    async def set_backup_only_tank_temp(self, value: Temperature) -> None:
        """
        Set the Backup Only Tank temperature threshold for the device.

        When the tank temperature exceeds this value, only the backup will heat the tank to the target temperature.
        This should be set lower than the hot tank target temperature for proper operation.

        Args:
            value (Temperature): The maximum tank temperature for heat pumps to run at.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled elsewhere). 
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, backup_only_tank_temp=value
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
        
    
