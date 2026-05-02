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
from glom import glom, PathAccessError

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


PERMANENT_HEAT_DEMAND = "permHD"
PERMANENT_COOL_DEMAND = "permCD"
HVAC_MODE_PRIORITY = "prior"
WEATHER_SHUTDOWN_LAG_TIME = "wwTime"
HEAT_COOL_SWITCH_DELAY = "hpSw"
WIDE_PRIORITY_DIFFERENTIAL = "wPDif"
NUMBER_OF_STAGES = "numStg"
TWO_STAGE_HEAT_PUMP = "twoS"
STAGE_ON_LAG_TIME = "lagT"
STAGE_OFF_LAG_TIME = "lagOff"
ROTATE_CYCLES = "rotCy"
ROTATE_TIME = "rotTi"
OFF_STAGING = "hpStg"
WARM_WEATHER_SHUTDOWN = "wwsd"
HOT_TANK_OUTDOOR_RESET = "dot"
HOT_TANK_DIFFERENTIAL = "htDif"
HOT_TANK_MIN_TEMP = "mbt"
HOT_TANK_MAX_TEMP = "dbt"
COLD_WEATHER_SHUTDOWN = "cwsd"
COLD_TANK_OUTDOOR_RESET = "cdot"
COLD_TANK_DIFFERENTIAL = "clDif"
COLD_TANK_MIN_TEMP = "mst"
COLD_TANK_MAX_TEMP = "dst"
BACKUP_LAG_TIME = "bkLag"
BACKUP_TEMP = "bkTemp"
BACKUP_DIFFERENTIAL = "bkDif"
BACKUP_ONLY_OUTDOOR_TEMP = "bkOd"
BACKUP_ONLY_TANK_TEMP = "bkTk"
FIRMWARE_VERSION = "firmVer"
SYNC_CODE = "syncCode"
DEVICE_PIN = "production.pin"
DEVICE_TYPE = "deviceType"  # The type of device (e.g., "ECO", "THM", "ZON")

# Known deviceType values returned by the HBX cloud
DEVICE_TYPE_ECO = "ECO"  # ECO-0600 heat-pump controller
DEVICE_TYPE_THM = "THM"  # THM-0600 thermostat
DEVICE_TYPE_ZON = "ZON"  # ZON-0600 zone controller
HEATPUMP_STAGE_RUNTIMES = "stgRun"
HEATPUMP_STAGES_STATE = "stages"
BACKUP_STATE = "backup"
BACKUP_RUNTIME = "bkRun"
TEMPERATURE_SENSORS = "temps"
DHW_ENABLED = "dhwOn"
DHW_TARGET_TEMP = "dhwT"
DHW_DIFFERENTIAL = "auxDif"
DEMANDS = "demands"
PUMPS = "pumps"
PUMP_1_MODE = "pmp1Set"
PUMP_2_MODE = "pmp2Set"
REVERSING_VALVE = "reversingValve"
WEATHER_SHUTDOWN_STATUS = "wsd"
TEMPERATURES_ENHANCED = "temperatures"

PUMP_MODES = {
    0: "system",
    1: "heating",
    2: "cooling",
    3: "dhw",
    4: "app",
    5: "none",
}

# THM/ZON device-specific raw field names (HBX cloud short keys).
# Confirmed via paired before/after device dumps from a live install
# (THM-0600 firmware 1.22, ZON-0600 firmware 1.32) on 2026-04-26.
THM_CHANGEOVER = "cngOvr"      # 0=Auto, 1=Heat, 2=Cool, 3=Off
THM_AWAY = "away"              # 0=off, 1=on
THM_FAN_MODE = "fnMode"        # 0=Off, 1=On, 2=Intermittent
THM_HEAT_SETPOINT = "rmT"      # int °F — heat-mode room setpoint
THM_COOL_SETPOINT = "rmCT"     # int °F — cool-mode room setpoint
# Away-mode setpoints live in a nested object under `awayMode`. Unlike rmT/rmCT,
# these are only the active setpoints when the THM Away preset is on. Field
# paths confirmed via paired before/after dumps from a live THM-0600 on
# 2026-05-01: in away mode, baseline awayMode.heatTarget.value=53 / coolTarget=87,
# then +5°F each via the app popup → 58 / 92.
THM_AWAY_MODE = "awayMode"
THM_AWAY_HEAT_TARGET = "heatTarget"
THM_AWAY_COOL_TARGET = "coolTarget"
THM_AWAY_TARGET_VALUE = "value"
THM_SCHEDULE_ENABLE = "pgmble" # 0=schedule disabled, 1=schedule enabled
THM_HUMIDITY_MODE = "useHum"   # 0=off, 1=on, 2=auto
THM_HUMIDITY_TARGET = "hmT"    # int % relative humidity (0-100)
THM_DEMAND = "dmd"             # bitfield: heat=0x02, cool=0x40, fan=0x80
# `dmd` bit assignments confirmed via paired dumps from a live THM-0600
# (Stairway thermostat) on 2026-04-30: dmd=2 with active heat call, dmd=64
# with active cool call, dmd=128 with fan-only operation. The cloud's
# `isHeating`/`isCooling` flags are unreliable (`isCooling` was observed
# false even with cooling demand active); `dmd` is the reliable source.
THM_DMD_HEAT_BIT = 0x02
THM_DMD_COOL_BIT = 0x40
THM_DMD_FAN_BIT = 0x80
ZON_APP_BUTTON = "aBut"        # 0=off, 1=on
ZON_DHW_TARGET = "dhwT"        # int °F (auxiliary heat / DHW setpoint)
# ZON aux setpoint reuses the same `dhwT` key as ECO DHW target (see DHW_TARGET_TEMP).

THM_CHANGEOVER_VALUES = {
    "auto": 0,
    "heat": 1,
    "cool": 2,
    "off": 3,
}

THM_FAN_MODE_VALUES = {
    "off": 0,
    "on": 1,
    "intermittent": 2,
}

THM_HUMIDITY_MODE_VALUES = {
    "off": 0,
    "on": 1,
    "auto": 2,
}

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
        if unit is None:
            raise ValueError("Unit must be 'C' for Celsius or 'F' for Fahrenheit")
        unit = unit.upper()
        if unit not in ("C", "F"):
            raise ValueError("Unit must be 'C' for Celsius or 'F' for Fahrenheit")
        try:
            self.value = float(value)
        except (TypeError, ValueError):
            raise ValueError("Temperature value must be a float or convertible to float")
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


class TemperatureDelta:
    """
    Represents a temperature difference (delta) rather than an absolute temperature.
    
    Unlike absolute temperatures, deltas convert without the +32/-32 offset:
    - Absolute: °F = °C × 9/5 + 32
    - Delta:    ΔF = ΔC × 9/5 (no offset)
    
    Example: A 4°F differential equals a 2.22°C differential (not -15.56°C).
    """
    def __init__(self, value: float, unit: str = "C"):
        if unit is None:
            raise ValueError("Unit must be 'C' for Celsius or 'F' for Fahrenheit")
        unit = unit.upper()
        if unit not in ("C", "F"):
            raise ValueError("Unit must be 'C' for Celsius or 'F' for Fahrenheit")
        try:
            self.value = float(value)
        except (TypeError, ValueError):
            raise ValueError("Temperature delta value must be a float or convertible to float")
        self.unit = unit

    def to_celsius(self) -> float:
        """Convert delta to Celsius. ΔC = ΔF × 5/9 (no offset)."""
        if self.unit == "C":
            return self.value
        return self.value * 5.0 / 9.0

    def to_fahrenheit(self) -> float:
        """Convert delta to Fahrenheit. ΔF = ΔC × 9/5 (no offset)."""
        if self.unit == "F":
            return self.value
        return self.value * 9.0 / 5.0

    def as_celsius(self):
        return TemperatureDelta(self.to_celsius(), "C")

    def as_fahrenheit(self):
        return TemperatureDelta(self.to_fahrenheit(), "F")

    def __repr__(self):
        return f"TemperatureDelta({self.value:.2f}, '{self.unit}')"

    def __str__(self):
        symbol = "Δ°C" if self.unit == "C" else "Δ°F"
        return f"{self.value:.2f}{symbol}"


class Sensorlinx:

    def __init__(self): 
        self._username = None
        self._password = None
        self._session = None
        self._bearer_token = None
        self._refresh_token = None
        # Serializes login / cleanup / 401-driven reauth so concurrent
        # callers (HA coordinator + service calls) cannot race on the
        # session object.
        self._auth_lock = asyncio.Lock()

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 "
                        "Mobile Safari/537.36 Edg/138.0.0.0",
        }
        
        #self.proxy_url = "http://127.0.0.1:8888"
        self.proxy_url = None  # Set to None to disable proxy, or provide a valid proxy URL if needed
                        
        
    @property
    def is_logged_in(self) -> bool:
        """True iff there is an open session AND a bearer token."""
        return self._session is not None and not self._session.closed and bool(self._bearer_token)

    async def _cleanup_session(self) -> None:
        """Close the aiohttp session and clear auth tokens.

        Cached credentials (``_username`` / ``_password``) are *not* cleared
        here so that a subsequent ``login()`` call can transparently
        reauthenticate. Use :meth:`close` for an explicit shutdown that
        also forgets credentials.
        """
        if self._session is not None:
            try:
                if not self._session.closed:
                    await self._session.close()
            except Exception:  # pragma: no cover - close shouldn't raise
                _LOGGER.exception("Error closing session during cleanup")
        self._session = None
        self._bearer_token = None
        self._refresh_token = None
        self.headers.pop("Authorization", None)

    async def login(self, username: str=None, password: str=None) -> None:
        """
        Attempt to log in to the Sensorlinx service.

        Idempotent: if the client is already logged in and no new
        credentials are supplied, this is a no-op. On any failure the
        client is left in a clean, not-logged-in state.

        Args:
            username (str, optional): The username to use for login.
            password (str, optional): The password to use for login.

        Raises:
            InvalidCredentialsError: If the credentials are missing or invalid.
            LoginTimeoutError: If the login request times out.
            NoTokenError: If no bearer token is received after login.
            LoginError: For other login-related errors.
        """
        async with self._auth_lock:
            await self._login_locked(username, password)

    async def _login_locked(self, username: str=None, password: str=None) -> None:
        new_creds_supplied = bool(username and password)
        new_creds_match_cached = (
            new_creds_supplied
            and username == self._username
            and password == self._password
        )

        # Idempotent fast-path: already authenticated, and either no
        # fresh credentials were supplied or they match the cached ones.
        # Check this BEFORE mutating cached creds so a true rotation
        # (different new creds) is not mistaken for a no-op.
        if self.is_logged_in and (not new_creds_supplied or new_creds_match_cached):
            return

        if new_creds_supplied:
            # Cache eagerly so that a first-ever transient failure can
            # still self-heal on the next call (the failed attempt at
            # least leaves us with the user's intended credentials).
            self._username = username
            self._password = password
        elif not (self._username and self._password):
            _LOGGER.error("No username or password provided.")
            raise InvalidCredentialsError("No username or password provided.")

        # Replace any prior session before opening a new one so we never
        # leak a ClientSession across login attempts.
        if self._session is not None:
            await self._cleanup_session()

        self._session = aiohttp.ClientSession()

        login_url = f"{HOST_URL}/{LOGIN_ENDPOINT}"
        payload = {
            "email": self._username,
            "password": self._password,
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
                    body = await resp.text()
                    _LOGGER.error(f"Login failed with status {resp.status}: {body}")
                    raise LoginError(f"Login failed with status {resp.status}: {body}")
                data = await resp.json()
                bearer = data.get("token")
                if not bearer:
                    _LOGGER.error("No bearer token received during login.")
                    raise NoTokenError("No bearer token received during login.")
                self._bearer_token = bearer
                self._refresh_token = data.get("refresh")
                self.headers["Authorization"] = f"Bearer {self._bearer_token}"
        except asyncio.TimeoutError:
            _LOGGER.error("Login request timed out.")
            await self._cleanup_session()
            raise LoginTimeoutError("Login request timed out.")
        except LoginError:
            await self._cleanup_session()
            raise
        except Exception as e:
            _LOGGER.exception(f"Exception during login: {e}")
            await self._cleanup_session()
            raise LoginError(f"Exception during login: {e}")
        
    async def close(self):
        """Close the aiohttp session and forget cached credentials.

        Use this for an explicit shutdown (e.g. HA's ``async_unload_entry``).
        For internal failure cleanup that needs to preserve credentials so
        the next call can reauthenticate, see :meth:`_cleanup_session`.
        """
        async with self._auth_lock:
            had_session = self._session is not None
            await self._cleanup_session()
            self._username = None
            self._password = None
            if had_session:
                _LOGGER.debug("Session closed successfully.")
            else:
                _LOGGER.debug("No session to close.")

    async def _authenticated_request(self, method: str, url: str, *, retry_on_401: bool = True, **kwargs):
        """Issue an authenticated request, transparently reauthenticating on 401.

        Args:
            method: HTTP method (``GET``, ``PATCH``, ...).
            url: Fully-qualified request URL.
            retry_on_401: When True (default) and the server responds 401
                Unauthorized, clear auth state, log in again with cached
                credentials, and retry the request once. A second 401
                raises :class:`InvalidCredentialsError`. Network errors
                and timeouts are *never* retried because their semantics
                (especially for writes) are ambiguous.
            **kwargs: Forwarded to ``aiohttp.ClientSession.request``. The
                authorization header is injected automatically; callers
                should not supply ``headers["Authorization"]``.

        Returns:
            Parsed JSON body when ``Content-Type`` is JSON, otherwise the
            raw response text.

        Raises:
            InvalidCredentialsError: After a second consecutive 401.
            LoginError / LoginTimeoutError / aiohttp errors: Propagated
                unchanged from the underlying calls.
        """
        if not self.is_logged_in:
            await self.login()

        attempt = 0
        while True:
            attempt += 1
            req_headers = {**self.headers, **(kwargs.pop("headers", {}) if attempt == 1 else {})}
            req_kwargs = dict(kwargs)
            req_kwargs.setdefault("timeout", 10)
            req_kwargs.setdefault("proxy", self.proxy_url)
            session_method = getattr(self._session, method.lower())
            async with session_method(url, headers=req_headers, **req_kwargs) as resp:
                if resp.status == 401 and retry_on_401 and attempt == 1:
                    body_preview = await resp.text()
                    _LOGGER.info(
                        "Got 401 on %s %s; re-authenticating once. Body: %s",
                        method, url, body_preview[:200],
                    )
                    # Force a clean reauth: drop the (likely-expired)
                    # token but keep the session/creds for the relogin.
                    self._bearer_token = None
                    self.headers.pop("Authorization", None)
                    await self.login()  # uses cached creds; raises if they are now bad
                    continue
                if resp.status == 401:
                    body = await resp.text()
                    raise InvalidCredentialsError(
                        f"Authentication rejected after retry on {method} {url}: {body}"
                    )
                if resp.status >= 400:
                    body = await resp.text()
                    raise RuntimeError(f"{method} {url} failed with status {resp.status}: {body}")
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await resp.json()
                return await resp.text()

    async def get_profile(self) -> Optional[Dict[str, str]]:
        ''' Fetch the user profile information
        
        Returns: Optional[Dict[str, str]]: Returns a dictionary with user profile information or None if not logged in.
        '''
        profile_url = f"{HOST_URL}/{PROFILE_ENDPOINT}"
        try:
            return await self._authenticated_request("GET", profile_url)
        except LoginError:
            # Auth failures must reach the caller so HA can route them
            # to ConfigEntryAuthFailed / UpdateFailed appropriately.
            raise
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
        if building_id:
            buildings_url = f"{HOST_URL}/{BUILDINGS_ENDPOINT}/{building_id}"
        else:
            buildings_url = f"{HOST_URL}/{BUILDINGS_ENDPOINT}"

        try:
            return await self._authenticated_request("GET", buildings_url)
        except LoginError:
            raise
        except Exception as e:
            _LOGGER.error(f"Exception fetching building(s): {e}")
            return None
        
    async def get_devices(self, building_id: str, device_id: Optional[str] = None) -> Union[List[Dict[str, str]], Dict[str, str]]:
        ''' Fetch devices for a given building, or a specific device if device_id is provided

        Args:
            building_id (str): The ID of the building.
            device_id (Optional[str]): The ID of the device. If not provided, fetches all devices for the building.

        Returns:
            Union[List[Dict[str, str]], Dict[str, str]]: 
                - If device_id is None, returns a list of device dicts.
                - If device_id is provided, returns a dict for the device.

        Raises:
            RuntimeError: If the request fails or the device(s) are not found.
        '''
        if device_id:
            url = f"{HOST_URL}/{DEVICES_ENDPOINT_TEMPLATE.format(building_id=building_id)}/{device_id}"
            _LOGGER.debug(f"Fetching URL: {url}")
        else:
            url = f"{HOST_URL}/{DEVICES_ENDPOINT_TEMPLATE.format(building_id=building_id)}"

        try:
            data = await self._authenticated_request("GET", url)
        except LoginError:
            raise
        except Exception as e:
            _LOGGER.error(f"Exception fetching device(s): {e}")
            raise RuntimeError(f"Exception fetching device(s): {e}")
        if not data:
            raise RuntimeError("No device data found.")
        return data

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
        hot_tank_outdoor_reset: Optional[Union[Temperature, str]] = None,
        hot_tank_differential: Optional[TemperatureDelta] = None,
        hot_tank_min_temp: Optional[Temperature] = None,
        hot_tank_max_temp: Optional[Temperature] = None,
        cold_tank_outdoor_reset: Optional[Union[Temperature, str]] = None,
        cold_tank_differential: Optional[TemperatureDelta] = None,
        cold_tank_min_temp: Optional[Temperature] = None,
        cold_tank_max_temp: Optional[Temperature] = None,
        backup_lag_time: Optional[Union[int, str]] = None,
        backup_temp: Optional[Union[Temperature, str]] = None,
        backup_differential: Optional[Union[TemperatureDelta, str]] = None,
        backup_only_outdoor_temp: Optional[Union[Temperature, str]] = None,
        backup_only_tank_temp: Optional[Union[Temperature, str]] = None,
        dhw_enabled: Optional[bool] = None,
        dhw_target_temp: Optional[Temperature] = None,
        dhw_differential: Optional[TemperatureDelta] = None,
    ) -> None:
        """
        Set permanent heating and/or cooling demand for a specific device.

        Args:
            building_id (str): The ID of the building (required).
            device_id (str): The ID of the device (required).
            
            permanent_hd (Optional[bool]): If True, always maintain buffer tank target temperature (heating).
            permanent_cd (Optional[bool]): If True, always maintain buffer tank target temperature (cooling).
            hvac_mode_priority (Optional[str]): The HVAC mode priority to set (e.g., "cool", "heat", "auto").
            weather_shutdown_lag_time (Optional[int]): Lag time for warm/cold weather shutdown (0-240 hours)
            wide_priority_differential (Optional[bool]): If True, enables wide priority differential for the device.
            number_of_stages (Optional[int]): Number of heat pump stages attached to the control (1-4).
            two_stage_heat_pump (Optional[bool]): If True, enables two-stage heat pump mode.
            stage_on_lag_time (Optional[int]): Lag time in minutes between heat pump stages (1-240).
            stage_off_lag_time (Optional[int]): Lag time in seconds between heat pump stages (1-240).
            rotate_cycles (Optional[Union[int, str]]): Number of cycles to rotate heat pumps (1-240) or 'off' to disable.
            rotate_time (Optional[Union[int, str]]): Time of rotation between heat pumps in hours (1-240) or 'off' to disable.
            off_staging (Optional[bool]): If True, enables Off Staging feature for the device.
            heat_cool_switch_delay (Optional[int]): Delay in seconds between switching from heat to cool (30-600).
            warm_weather_shutdown (Optional[Temperature or str]): when in heating mode shuts the heat pump off above this temperature (34 to 180F) or 'off' to disable.
            hot_tank_outdoor_reset (Optional[Union[Temperature, str]]): temperature for outdoor reset in °F (-40 to 127) or 'off' to disable.
            hot_tank_differential (Optional[TemperatureDelta]): controlling how far above or below the target temperature a demand is triggered. (2-100F)
            hot_tank_min_temp (Optional[Temperature]): The minimum tank temperature for the hot tank (35°F to 200°F)
            hot_tank_max_temp (Optional[Temperature]): The maximum tank temperature for the hot tank (35°F to 200°F)
            cold_weather_shutdown (Optional[Temperature or str]): when in cooling mode shuts the heat pump off below this temperature, (33F to 119F) or 'off' to disable.
            cold_tank_outdoor_reset (Optional[Union[Temperature, str]]): Design temperature for outdoor reset in (0F to 119F) or 'off' to disable.
            cold_tank_differential (Optional[TemperatureDelta]): The cold differential to set for the device (2°F to 100°F)
            cold_tank_min_temp (Optional[Temperature]): The minimum tank temperature for the cold tank (35°F to 200°F)
            cold_tank_max_temp (Optional[Temperature]): The maximum tank temperature for the cold tank (35°F to 200°F)
            backup_lag_time (Optional[Union[int, str]]): Minimum lag time between heat pump stages and backup boiler; accepts "off" or integer 1–240 (minutes). Default: "off".
            backup_temp (Optional[Union[Temperature, str]]): The outdoor temperature at which the backup mode is activated (2F to 100F) or 'off' to disable.
            backup_differential (Optional[Union[TemperatureDelta, str]]): Tank temperature difference below target at which backup boiler activates, overriding backup time if needed. Use "off" to disable, or a TemperatureDelta between 2°F and 100°F.
            backup_only_outdoor_temp (Optional[Union[Temperature, str]]): The outdoor temperature below which the backup will only run (-40F to 127F) or 'off' to disable.
            backup_only_tank_temp (Union[Temperature, str]): The maximum tank temperature for heat pumps to run at. Once exceeded, only the backup will heat the tank to the target temperature. Should be set lower than the hot tank target temperature (33°F to 200°F or "off" to disable)
            dhw_enabled (Optional[bool]): If True, enables the Domestic Hot Water demand channel. If False, disables it.
            dhw_target_temp (Optional[Temperature]): The DHW tank target temperature (33°F to 180°F).
            dhw_differential (Optional[TemperatureDelta]): DHW tank differential — how far below the target the tank must drop before DHW demand is triggered (2°F to 100°F).

        Raises:
            InvalidParameterError: If required parameters are missing or invalid.
            LoginError: If login fails or session is not established.
            RuntimeError: If the API call fails for other reasons.
        """
        if not building_id or not device_id:
            _LOGGER.error("Both building_id and device_id must be provided.")
            raise InvalidParameterError("Both building_id and device_id must be provided.")

        url = f"{HOST_URL}/{DEVICES_ENDPOINT_TEMPLATE.format(building_id=building_id)}/{device_id}"
        payload = {}
        
        if permanent_hd is not None:
            payload[PERMANENT_HEAT_DEMAND] = permanent_hd
            
        if permanent_cd is not None:
            payload[PERMANENT_COOL_DEMAND] = permanent_cd
            
        if hvac_mode_priority is not None:
            if hvac_mode_priority == "heat":
                payload[HVAC_MODE_PRIORITY] = 0
            elif hvac_mode_priority == "cool":
                payload[HVAC_MODE_PRIORITY] = 1
            elif hvac_mode_priority == "auto":
                payload[HVAC_MODE_PRIORITY] = 2
            else:
                _LOGGER.error("Invalid HVAC mode priority. Must be 'cool', 'heat', or 'auto'.")
                raise InvalidParameterError("Invalid HVAC mode priority. Must be 'cool', 'heat', or 'auto'.")
        
        if weather_shutdown_lag_time is not None:
            if isinstance(weather_shutdown_lag_time, int) and 0 <= weather_shutdown_lag_time <= 240:
                payload[WEATHER_SHUTDOWN_LAG_TIME] = weather_shutdown_lag_time
            else:
                _LOGGER.error("Invalid value for warm or cold weather shutdown time. Must be an integer between 0 and 240.")
                raise InvalidParameterError("Invalid weather shutdown lag time. Must be an integer between 0 and 240.")
        
        if heat_cool_switch_delay is not None:
            if isinstance(heat_cool_switch_delay, int) and 30 <= heat_cool_switch_delay <= 600:
                payload[HEAT_COOL_SWITCH_DELAY] = heat_cool_switch_delay
            else:
                _LOGGER.error("Heat/Cool Switch Delay must be an integer between 30 and 600 seconds.")
                raise InvalidParameterError("Heat/Cool Switch Delay must be an integer between 30 and 600 seconds.")            

        if wide_priority_differential is not None:
            if isinstance(wide_priority_differential, bool):
                payload[WIDE_PRIORITY_DIFFERENTIAL] = wide_priority_differential
            else:
                _LOGGER.error("Wide priority differential value must be a boolean.")
                raise InvalidParameterError("Wide priority differential value must be a boolean.")
        
        # Heat Pump Setup
        if number_of_stages is not None:
            if isinstance(number_of_stages, int) and 1 <= number_of_stages <= 4:
                payload[NUMBER_OF_STAGES] = number_of_stages
            else:
                _LOGGER.error("Number of stages must be an integer between 1 and 4.")
                raise InvalidParameterError("Number of stages must be an integer between 1 and 4.")
        
        if two_stage_heat_pump is not None:
            if isinstance(two_stage_heat_pump, bool):
                payload[TWO_STAGE_HEAT_PUMP] = two_stage_heat_pump
            else:
                _LOGGER.error("Two stage heat pump value must be a boolean.")
                raise InvalidParameterError("Two stage heat pump value must be a boolean.")
            
        if stage_on_lag_time is not None:
            if isinstance(stage_on_lag_time, int) and 1 <= stage_on_lag_time <= 240:
                payload[STAGE_ON_LAG_TIME] = stage_on_lag_time
            else:
                _LOGGER.error("Stage ON Lagtime value must be an integer between 1 and 240 minutes.")
                raise InvalidParameterError("Stage ON Lagtime value must be an integer between 1 and 240 minutes.")
            
        if stage_off_lag_time is not None:
            if isinstance(stage_off_lag_time, int) and 1 <= stage_off_lag_time <= 240:
                payload[STAGE_OFF_LAG_TIME] = stage_off_lag_time
            else:
                _LOGGER.error("Stage OFF lag time value must be an integer between 1 and 240 seconds.")
                raise InvalidParameterError("Stage OFF lag time value must be an integer between 1 and 240 seconds.")
            
        if rotate_cycles is not None:
            if isinstance(rotate_cycles, str) and rotate_cycles.lower() == "off":
                payload[ROTATE_CYCLES] = 0
            elif isinstance(rotate_cycles, int) and 1 <= rotate_cycles <= 240:
                payload[ROTATE_CYCLES] = rotate_cycles
            else:
                _LOGGER.error("Rotate cycles value must be an integer between 1 and 240 or 'off'.")
                raise InvalidParameterError("Rotate cycles value must be an integer between 1 and 240 or 'off'.")
            
        if rotate_time is not None:
            if isinstance(rotate_time, str) and rotate_time.lower() == "off":
                payload[ROTATE_TIME] = 0
            elif isinstance(rotate_time, int) and 1 <= rotate_time <= 240:
                payload[ROTATE_TIME] = rotate_time
            else:
                _LOGGER.error("Rotate time must be an integer between 1 and 240 or 'off'.")
                raise InvalidParameterError("Rotate time must be an integer between 1 and 240 or 'off'.")
            
        if off_staging is not None:
            if isinstance(off_staging, bool):
                payload[OFF_STAGING] = off_staging
            else:
                _LOGGER.error("Off staging must be a boolean value.")
                raise InvalidParameterError("Off staging must be a boolean value.")
            
        # Hot Tank parameters
        if warm_weather_shutdown is not None:
            if isinstance(warm_weather_shutdown, str) and warm_weather_shutdown.lower() == "off":
                payload[WARM_WEATHER_SHUTDOWN] = 32
            elif isinstance(warm_weather_shutdown, Temperature):
                temp_f = warm_weather_shutdown.to_fahrenheit()
                if not (34 <= temp_f <= 180):
                    _LOGGER.error("Warm weather shutdown must be between 34°F and 180°F or 'off'.")
                    raise InvalidParameterError("Warm weather shutdown must be between 34°F and 180°F or 'off'.")
                payload[WARM_WEATHER_SHUTDOWN] = round(temp_f)
            else:
                _LOGGER.error("Invalid type for warm weather shutdown. Must be a Temperature or 'off'.")
                raise InvalidParameterError("Invalid type for warm weather shutdown. Must be a Temperature or 'off'.")
            
        if hot_tank_outdoor_reset is not None:
            if isinstance(hot_tank_outdoor_reset, str) and hot_tank_outdoor_reset.lower() == "off":
                payload[HOT_TANK_OUTDOOR_RESET] = -41
            elif isinstance(hot_tank_outdoor_reset, Temperature):
                temp_f = hot_tank_outdoor_reset.to_fahrenheit()
                if not (-40 <= temp_f <= 127):
                    _LOGGER.error(f"Hot tank outdoor reset must be between -40°F and 127°F or 'off': Got {temp_f}°F")
                    raise InvalidParameterError("Hot tank outdoor reset must be between -40°F and 127°F or 'off'.")
                payload[HOT_TANK_OUTDOOR_RESET] = round(temp_f)
            else:
                _LOGGER.error("Hot tank outdoor reset must be a Temperature instance or 'off'.")
                raise InvalidParameterError("Hot tank outdoor reset must be a Temperature instance or 'off'.")
            
        if hot_tank_differential is not None:
            if isinstance(hot_tank_differential, TemperatureDelta):
                temp_f = hot_tank_differential.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("Hot tank differential must be between 2°F and 100°F.")
                    raise InvalidParameterError("Hot tank differential must be between 2°F and 100°F.")
                payload[HOT_TANK_DIFFERENTIAL] = round(temp_f)
            else:
                _LOGGER.error("Hot tank differential must be a TemperatureDelta instance.")
                raise InvalidParameterError("Hot tank differential must be a TemperatureDelta instance.")
            
        if hot_tank_min_temp is not None:
            if isinstance(hot_tank_min_temp, Temperature):
                temp_f = hot_tank_min_temp.to_fahrenheit()
                if not (2 <= temp_f <= 180):
                    _LOGGER.error("Minimum tank temperature for the hot tank must be between 2°F and 180°F.")
                    raise InvalidParameterError("Minimum tank temperature for the hot tank must be between 2°F and 180°F.")
                payload[HOT_TANK_MIN_TEMP] = round(temp_f)
            else:
                _LOGGER.error("Minimum tank temperature for the hot tank must be a Temperature instance.")
                raise InvalidParameterError("Minimum tank temperature for the hot tank must be a Temperature instance.")
            
        if hot_tank_max_temp is not None:
            if isinstance(hot_tank_max_temp, Temperature):
                temp_f = hot_tank_max_temp.to_fahrenheit()
                if not (2 <= temp_f <= 180):
                    _LOGGER.error("Maximum tank temperature for the hot tank must be between 2°F and 180°F.")
                    raise InvalidParameterError("Maximum tank temperature for the hot tank must be between 2°F and 180°F.")
                payload[HOT_TANK_MAX_TEMP] = round(temp_f)
            else:
                _LOGGER.error("Maximum tank temperature for the hot tank must be a Temperature instance.")
                raise InvalidParameterError("Maximum tank temperature for the hot tank must be a Temperature instance.")
            
        # Cold Tank parameters
        if cold_weather_shutdown is not None:
            if isinstance(cold_weather_shutdown, str) and cold_weather_shutdown.lower() == "off":
                payload[COLD_WEATHER_SHUTDOWN] = 32
            elif isinstance(cold_weather_shutdown, Temperature):
                temp_f = cold_weather_shutdown.to_fahrenheit()
                if not (33 <= temp_f <= 119):
                    _LOGGER.error("Cold weather shutdown must be between 33°F and 119°F or 'off'.")
                    raise InvalidParameterError("Cold weather shutdown must be between 33°F and 119°F or 'off'.")
                payload[COLD_WEATHER_SHUTDOWN] = round(temp_f)
            else:
                _LOGGER.error("Cold weather shutdown must be a Temperature instance or 'off'.")
                raise InvalidParameterError("Cold weather shutdown must be a Temperature instance or 'off'.")
            
        if cold_tank_outdoor_reset is not None:
            if isinstance(cold_tank_outdoor_reset, str) and cold_tank_outdoor_reset.lower() == "off":
                payload[COLD_TANK_OUTDOOR_RESET] = -41
            elif isinstance(cold_tank_outdoor_reset, Temperature):
                temp_f = cold_tank_outdoor_reset.to_fahrenheit()
                if not (0 <= temp_f <= 119):
                    _LOGGER.error("Cold tank outdoor reset must be between 0°F and 119°F or 'off'.")
                    raise InvalidParameterError("Cold tank outdoor reset must be between 0°F and 119°F or 'off'.")
                payload[COLD_TANK_OUTDOOR_RESET] = round(temp_f)
            else:
                _LOGGER.error("Cold tank outdoor reset must be a Temperature instance or 'off'.")
                raise InvalidParameterError("Cold tank outdoor reset must be a Temperature instance or 'off'.")
            
        if cold_tank_differential is not None:
            if isinstance(cold_tank_differential, TemperatureDelta):
                temp_f = cold_tank_differential.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("Cold tank differential must be between 2°F and 100°F.")
                    raise InvalidParameterError("Cold tank differential must be between 2°F and 100°F.")
                payload[COLD_TANK_DIFFERENTIAL] = round(temp_f)
            else:
                _LOGGER.error("Cold tank differential must be a TemperatureDelta instance.")
                raise InvalidParameterError("Cold tank differential must be a TemperatureDelta instance.")
            
        if cold_tank_min_temp is not None:
            if isinstance(cold_tank_min_temp, Temperature):
                temp_f = cold_tank_min_temp.to_fahrenheit()
                if not (2 <= temp_f <= 180):
                    _LOGGER.error("Cold tank min temperature must be between 2°F and 180°F.")
                    raise InvalidParameterError("Cold tank min temperature must be between 2°F and 180°F.")
                payload[COLD_TANK_MIN_TEMP] = round(temp_f)
            else:
                _LOGGER.error("Cold tank min temperature must be a Temperature instance.")
                raise InvalidParameterError("Cold tank min temperature must be a Temperature instance.")
            
        if cold_tank_max_temp is not None:
            if isinstance(cold_tank_max_temp, Temperature):
                temp_f = cold_tank_max_temp.to_fahrenheit()
                if not (2 <= temp_f <= 180):
                    _LOGGER.error("Cold tank max temperature must be between 2°F and 180°F.")
                    raise InvalidParameterError("Cold tank max temperature must be between 2°F and 180°F.")
                payload[COLD_TANK_MAX_TEMP] = round(temp_f)
            else:
                _LOGGER.error("Cold tank max temperature must be a Temperature instance.")
                raise InvalidParameterError("Cold tank max temperature must be a Temperature instance.")
            
        # Backup Parameters
        if backup_lag_time is not None:
            if isinstance(backup_lag_time, str):
                if backup_lag_time.lower() != "off":
                    _LOGGER.error("Backup lag time must be an integer between 1 and 240 or 'off'.")
                    raise InvalidParameterError("Backup lag time must be an integer between 1 and 240 or 'off'.")
                payload[BACKUP_LAG_TIME] = 0
            elif isinstance(backup_lag_time, int) and not isinstance(backup_lag_time, bool):
                if not (1 <= backup_lag_time <= 240):
                    _LOGGER.error("Backup lag time must be an integer between 1 and 240.")
                    raise InvalidParameterError("Backup lag time must be an integer between 1 and 240 or 'off'.")
                payload[BACKUP_LAG_TIME] = backup_lag_time
            else:
                _LOGGER.error("Backup lag time must be an integer between 1 and 240 or 'off'.")
                raise InvalidParameterError("Backup lag time must be an integer between 1 and 240 or 'off'.")
            
        if backup_temp is not None:
            if isinstance(backup_temp, str) and backup_temp.lower() == "off":
                payload[BACKUP_TEMP] = 0
            elif isinstance(backup_temp, Temperature):
                temp_f = backup_temp.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("Backup temp must be between 2°F and 100°F.")
                    raise InvalidParameterError("Backup temp must be between 2°F and 100°F.")
                payload[BACKUP_TEMP] = round(temp_f)
            else:
                _LOGGER.error("Backup temp must be a Temperature instance or 'off'.")
                raise InvalidParameterError("Backup temp must be a Temperature instance or 'off'.")
            
        if backup_differential is not None:
            if isinstance(backup_differential, str) and backup_differential.lower() == "off":
                payload[BACKUP_DIFFERENTIAL] = 0
            elif isinstance(backup_differential, TemperatureDelta):
                temp_f = backup_differential.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("Backup differential must be between 2°F and 100°F.")
                    raise InvalidParameterError("Backup differential must be between 2°F and 100°F.")
                payload[BACKUP_DIFFERENTIAL] = round(temp_f)
            else:
                _LOGGER.error("Backup differential must be a TemperatureDelta instance or 'off'.")
                raise InvalidParameterError("Backup differential must be a TemperatureDelta instance or 'off'.")
            
        if backup_only_outdoor_temp is not None:
            if isinstance(backup_only_outdoor_temp, str) and backup_only_outdoor_temp.lower() == "off":
                payload[BACKUP_ONLY_OUTDOOR_TEMP] = -41
            elif isinstance(backup_only_outdoor_temp, Temperature):
                temp_f = backup_only_outdoor_temp.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("Backup only outdoor temperature must be between 2°F and 100°F.")
                    raise InvalidParameterError("Backup only outdoor temperature must be between 2°F and 100°F.")
                payload[BACKUP_ONLY_OUTDOOR_TEMP] = round(temp_f)
            else:
                _LOGGER.error("Backup only outdoor temperature must be a Temperature instance or 'off'.")
                raise InvalidParameterError("Backup only outdoor temperature must be a Temperature instance or 'off'.")
            
        if backup_only_tank_temp is not None:
            if isinstance(backup_only_tank_temp, str) and backup_only_tank_temp.lower() == "off":
                payload[BACKUP_ONLY_TANK_TEMP] = 32
            elif isinstance(backup_only_tank_temp, Temperature):
                temp_f = backup_only_tank_temp.to_fahrenheit()
                if not (33 <= temp_f <= 200):
                    _LOGGER.error("Backup only tank temperature must be between 33°F and 200°F.")
                    raise InvalidParameterError("Backup only tank temperature must be between 33°F and 200°F.")
                payload[BACKUP_ONLY_TANK_TEMP] = round(temp_f)
            else:
                _LOGGER.error("Backup only tank temperature must be a Temperature instance or 'off'.")
                raise InvalidParameterError("Backup only tank temperature must be a Temperature instance or 'off'.")
            
        # DHW Parameters
        if dhw_enabled is not None:
            payload[DHW_ENABLED] = dhw_enabled

        if dhw_target_temp is not None:
            if isinstance(dhw_target_temp, Temperature):
                temp_f = dhw_target_temp.to_fahrenheit()
                if not (33 <= temp_f <= 180):
                    _LOGGER.error("DHW target temperature must be between 33°F and 180°F.")
                    raise InvalidParameterError("DHW target temperature must be between 33°F and 180°F.")
                payload[DHW_TARGET_TEMP] = round(temp_f)
            else:
                _LOGGER.error("DHW target temperature must be a Temperature instance.")
                raise InvalidParameterError("DHW target temperature must be a Temperature instance.")

        if dhw_differential is not None:
            if isinstance(dhw_differential, TemperatureDelta):
                temp_f = dhw_differential.to_fahrenheit()
                if not (2 <= temp_f <= 100):
                    _LOGGER.error("DHW differential must be between 2°F and 100°F.")
                    raise InvalidParameterError("DHW differential must be between 2°F and 100°F.")
                payload[DHW_DIFFERENTIAL] = round(temp_f)
            else:
                _LOGGER.error("DHW differential must be a TemperatureDelta instance.")
                raise InvalidParameterError("DHW differential must be a TemperatureDelta instance.")

        if not payload:
            _LOGGER.error("At least one optional parameter must be provided")
            raise InvalidParameterError("At least one optional parameter must be provided.")

        try:
            response = await self._authenticated_request(
                "PATCH",
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            _LOGGER.debug(f"Response from setting device parameter(s): {response}")
        except LoginError:
            raise
        except Exception as e:
            _LOGGER.error(f"Exception setting device parameter(s): {e}")
            raise RuntimeError(f"Exception setting device parameter(s): {e}")

    async def patch_device(
        self,
        building_id: str,
        device_id: str,
        **fields,
    ) -> None:
        """
        Send a low-level PATCH to the device-parameter endpoint with arbitrary
        raw HBX field names.

        Used for THM/ZON device-specific fields that aren't covered by the
        typed signature of :py:meth:`set_device_parameter`. Reuses the same
        URL and authentication path (including 401 retry).

        Args:
            building_id (str): The ID of the building (required).
            device_id (str): The ID of the device (required).
            **fields: Raw HBX field name -> value pairs. Example:
                ``patch_device(b, d, cngOvr=1)`` to set THM changeover to Heat.

        Raises:
            InvalidParameterError: If ``building_id``/``device_id`` are missing
                or no fields were supplied.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        if not building_id or not device_id:
            _LOGGER.error("Both building_id and device_id must be provided.")
            raise InvalidParameterError(
                "Both building_id and device_id must be provided."
            )
        if not fields:
            _LOGGER.error("At least one field must be provided to patch_device.")
            raise InvalidParameterError(
                "At least one field must be provided to patch_device."
            )

        url = f"{HOST_URL}/{DEVICES_ENDPOINT_TEMPLATE.format(building_id=building_id)}/{device_id}"
        try:
            response = await self._authenticated_request(
                "PATCH",
                url,
                json=dict(fields),
                headers={"Content-Type": "application/json"},
            )
            _LOGGER.debug(f"Response from patch_device: {response}")
        except LoginError:
            raise
        except Exception as e:
            _LOGGER.error(f"Exception in patch_device: {e}")
            raise RuntimeError(f"Exception in patch_device: {e}")

           
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
        
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, stage_on_lag_time=value
        )
        
    async def set_stage_off_lag_time(self, value: int) -> None:
        """
        Set the Stage OFF Lagtime for the device.

        When the heat pump is set for more than 1 stage, this setting specifies the minimum OFF lagtime (in seconds) between heat pump stages.
        Allowed values: 1-240 seconds.

        Args:
            value (int): The lag time in seconds to wait before deactivating the next stage (must be between 1 and 240).

        Raises:
            InvalidParameterError: If the value is not between 1 and 240.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """

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

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, rotate_cycles=value
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
        
    async def set_hot_tank_outdoor_reset(self, value: Union[Temperature, str]) -> None:
        """
        Set the Outdoor Reset (Design Outdoor Temperature) parameter for the hot tank.

        This is used in the outdoor reset design calculation for the hot tank. Set to "off" if not using outdoor reset.
        With this enabled, the Tank Temperature setting will be replaced by Min Tank and Max Tank Temperature settings for the hot tank.

        Args:
            value (Union[Temperature, str]): The design outdoor temperature as a Temperature object (in °F or °C) or "off" to disable.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, hot_tank_outdoor_reset=value
        )
        
    async def set_hot_tank_differential(self, value: TemperatureDelta) -> None:
        """
        Set the heat differential for the hot tank.

        This temperature delta sets the desired hot tank differential. For example, a differential of 4°F will allow for 2 degrees above
        and/or 2 degrees below the desired temperature before a demand is present.

        Args:
            value (TemperatureDelta): The differential as a TemperatureDelta object.

        Raises:
            InvalidParameterError: If the value is not a TemperatureDelta instance.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, hot_tank_differential=value
        )
        
    async def set_hot_tank_target_temp(self, value: Temperature) -> None:
        """
        Set the hot tank target temperature for heating.

        Note:
            This method is functionally identical to set_hot_tank_min_temp and uses the same parameter.
            It is provided as a helper for clarity and code readability.

        When a heat demand is present and the control is not in WWSD, the control will target this temperature for heating.
        Allowed values: 2°F to 180°F. Default: 115°F.

        Args:
            value (Temperature): The target temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.set_hot_tank_min_temp(value)
        
    async def set_hot_tank_min_temp(self, value: Temperature) -> None:
        """
        Set the minimum tank temperature for the hot tank.

        This setting is the bottom of the heat curve. The target will hit this temperature as the
        Outdoor Temperature approaches the WWSD. Allowed values: 2°F to 180°F. Default: 80°F.

        Note:
            This option is only used when hot tank outdoor reset is enabled.

        Args:
            value (Temperature): The minimum tank temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, hot_tank_min_temp=value
        )
        
    async def set_hot_tank_max_temp(self, value: Temperature) -> None:
        """
        Set the maximum tank temperature for the hot tank.

        This setting is the top of the heat curve. The target will hit this temperature as the
        Outdoor Temperature approaches the Design Outdoor Temperature.
        Allowed values: 2°F to 180°F. Default: 115°F.

        Note:
            This option is only used when hot tank outdoor reset is enabled.

        Args:
            value (Temperature): The maximum tank temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (not a Temperature or out of range).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, hot_tank_max_temp=value
        )

    #################################################################################################################################
    #                                               Cold Tank Set Methods
    #################################################################################################################################

    async def set_cold_weather_shutdown(self, value) -> None:
        """
        Set the Cold Weather Shutdown (CWSD) parameter for the device.

        CWSD is used to set the outdoor temperature at which the ECO-0600 will enter Cold Weather Shutdown.
        If the outdoor temperature drops below this value, the system (heat pumps) will be shut off.
        Allowed values: "off" (to disable, sets to 32°F) or a Temperature between 33°F and 119°F (inclusive).
        Default: 75°F.

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
        
    async def set_cold_tank_outdoor_reset(self, value: Union[Temperature, str]) -> None:
        """
        Set the Outdoor Reset (Design Outdoor Temperature) parameter for the cold tank.

        This is used in the outdoor reset design calculation for the cold tank. Set to "off" if not using outdoor reset.
        With this enabled, the Tank Temperature setting will be replaced by Min Tank and Max Tank Temperature settings for the cold tank.

        Args:
            value (Union[Temperature, str]): The design outdoor temperature as a Temperature object (in °F or °C) or "off" to disable.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, cold_tank_outdoor_reset=value
        )
        
    async def set_cold_tank_differential(self, value: TemperatureDelta) -> None:
        """
        Set the cold tank differential for the device.

        This temperature delta sets the desired cold tank differential. For example, a differential of 4°F will allow for 2 degrees above
        and/or 2 degrees below the desired temperature before a demand is present. Default 8F

        Args:
            value (TemperatureDelta): The differential as a TemperatureDelta object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, cold_tank_differential=value
        )
        
    async def set_cold_tank_target_temp(self, value: Temperature) -> None:
        """
        Set the cold tank target temperature for cooling.

        Note:
            This method is functionally identical to set_cold_tank_min_temp and uses the same parameter.
            It is provided as a helper for clarity and code readability.

        When a cool demand is present and the control is not in CWSD, the control will target this temperature for cooling.
        Allowed values: 2°F to 180°F. Default: 45°F.

        Args:
            value (Temperature): The target temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.set_cold_tank_min_temp(value)
        
    async def set_cold_tank_min_temp(self, value: Temperature) -> None:
        """
        Set the minimum tank temperature for the cold tank.

        This setting is the bottom of the cooling curve. The target will hit this temperature as the
        Outdoor Temperature approaches the Outdoor Design Temperature.
        Allowed values: 2°F to 180°F. Default: 45°F.

        Args:
            value (Temperature): The minimum tank temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, cold_tank_min_temp=value
        )
        
    async def set_cold_tank_max_temp(self, value: Temperature) -> None:
        """
        Set the maximum tank temperature for the cold tank.

        This setting is the top of the cooling curve. The target will hit this temperature as the
        Outdoor Temperature approaches the Cold Weather Shutdown (CWSD).
        Allowed values: 2°F to 180°F. Default: 60°F.

        Args:
            value (Temperature): The maximum tank temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled in set_device_parameter).
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, cold_tank_max_temp=value
        )
        
    #################################################################################################################################
    #                                               Domestic Hot Water Set Methods
    #################################################################################################################################

    async def set_dhw_enabled(self, value: bool) -> None:
        """
        Enable or disable the Domestic Hot Water (DHW) demand channel.

        When enabled, the controller will maintain the DHW tank target temperature.
        This can be used instead of an external DHW thermostat.

        Args:
            value (bool): True to enable DHW demand, False to disable.

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, dhw_enabled=value
        )

    async def set_dhw_target_temp(self, value: Temperature) -> None:
        """
        Set the Domestic Hot Water (DHW) tank target temperature.

        This is the temperature the controller will maintain in the DHW tank
        when the DHW demand channel is active. Allowed values: 33°F to 180°F.

        Args:
            value (Temperature): The target temperature as a Temperature object.

        Raises:
            InvalidParameterError: If the value is out of range or the wrong type.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, dhw_target_temp=value
        )

    async def set_dhw_differential(self, value: TemperatureDelta) -> None:
        """
        Set the Domestic Hot Water (DHW) tank differential.

        This controls how far below the target temperature the DHW tank must drop
        before a DHW demand is triggered. Allowed values: 2°F to 100°F.

        Args:
            value (TemperatureDelta): The differential as a TemperatureDelta object.

        Raises:
            InvalidParameterError: If the value is out of range or the wrong type.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, dhw_differential=value
        )

    #################################################################################################################################
    #                                               Backup Set Methods
    #################################################################################################################################  
        
    async def set_backup_lag_time(self, value: Union[int, str]) -> None:
        """
        Set the backup time (lag time between heat pump stages and backup boiler).

        This is the minimum lag time (in minutes) between heat pump stages and the backup boiler.
        Allowed values: "off" (to disable) or an integer between 1 and 240.

        Args:
            value (Temperature or str): Number of minutes (1-240) or "off" to disable.

        Raises:
            InvalidParameterError: If the value is not "off" or an integer in range.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """

        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, backup_lag_time=value
        )
        
    async def set_backup_temp(self, value: Union[Temperature, str]) -> None:
        """
        Set the backup temperature threshold for the device.

        When the outdoor temperature falls below this value, the backup will be allowed to come on.
        If set to "off", this feature is disabled.

        Args:
            value (Temperature or str): The temperature threshold as a Temperature object with a valid range of 2F to 100F or "off" to disable.

        Raises:
            InvalidParameterError: If the value is invalid.
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, backup_temp=value
        )
        
    async def set_backup_differential(self, value: Union[TemperatureDelta, str]) -> None:
        """
        Set the backup differential for the device.

        This setting is used to set a differential on the tank at which you would like the backup to come on.
        This setting will override the backup time settings and bring the backup on instantaneously if the target is at or below the differential.
        (eg. Tank temperature of 115°F and a backup differential of 10°F. The backup boiler will come on at 105°F providing all of the heat pumps are already on)
        Allowed values: "off" (to disable) or a TemperatureDelta between 2°F and 100°F.

        Args:
            value (TemperatureDelta or str): The backup differential as a TemperatureDelta object with a valid range of 2 to 100F or "off" to disable.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled elsewhere).        
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, backup_differential=value
        )
        
    async def set_backup_only_outdoor_temp(self, value: Union[Temperature, str]) -> None:
        """
        Set the Backup Only Outdoor temperature threshold for the device.

        When the outdoor temperature is below this value, only the backup will run for a Hot Tank or DHW call.
        The heat pumps will not run until the outdoor temperature rises above this setting.

        Args:
            value (Union[Temperature, str]): The temperature threshold as a Temperature object (-40°F to 127°F) or 'off' to disable.

        Raises:
            InvalidParameterError: If the value is invalid (validation is handled elsewhere). 
            LoginError: If the API call fails for login reasons.
            RuntimeError: If the API call fails for other reasons.
        """
        await self.sensorlinx.set_device_parameter(
            self.building_id, self.device_id, backup_only_outdoor_temp=value
        )
        
    async def set_backup_only_tank_temp(self, value: Union[Temperature, str]) -> None:
        """
        Set the Backup Only Tank temperature threshold for the device.

        When the tank temperature exceeds this value, only the backup will heat the tank to the target temperature.
        This should be set lower than the hot tank target temperature for proper operation.

        Args:
            value (Temperature or str): The maximum tank temperature for heat pumps to run at.
                Valid range is 33 to 200°F. Use the string 'off' to disable this feature.

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
    
    async def _get_device_info_value(self, key: str, device_info: Optional[Dict] = None) -> str:
        """
        Helper to get a value from device_info by key, supporting dotted paths using glom.

        Args:
            key (str): The dotted key path to retrieve (e.g., "parent.child.value").
            device_info (Optional[Dict]): The device info dict.

        Returns:
            str: The value found.

        Raises:
            RuntimeError: If the device info or key is not found.
        """

        if device_info is None:
            try:
                device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
            except Exception as e:
                _LOGGER.error(f"Exception fetching device info: {e}")
                raise RuntimeError(f"Failed to fetch device info: {e}")
        if not device_info:
            raise RuntimeError("Device info not found.")
        
        
        try:
            value = glom(device_info, key)
        except PathAccessError:
            raise RuntimeError(f"{key} not found.")
        if value is None:
            raise RuntimeError(f"{key} not found.")
        return value
    
    #################################################################################################################################
    #                                               General Device Get Methods
    #################################################################################################################################
    
    async def get_permanent_heat_demand(self, device_info: Optional[Dict] = None):
        """
        Get the permanent heat demand setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The permanent heat demand value.

        Raises:
            RuntimeError: If the device or permanent heat demand is not found.
        """
        return await self._get_device_info_value(PERMANENT_HEAT_DEMAND, device_info)

    async def get_permanent_cool_demand(self, device_info: Optional[Dict] = None):
        """
        Get the permanent cool demand setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The permanent cool demand value.

        Raises:
            RuntimeError: If the device or permanent cool demand is not found.
        """
        return await self._get_device_info_value(PERMANENT_COOL_DEMAND, device_info)

    async def get_hvac_mode_priority(self, device_info: Optional[Dict] = None):
        """
        Get the HVAC mode priority for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The HVAC mode priority value.

        Raises:
            RuntimeError: If the device or HVAC mode priority is not found.
        """
        return await self._get_device_info_value(HVAC_MODE_PRIORITY, device_info)

    async def get_weather_shutdown_lag_time(self, device_info: Optional[Dict] = None):
        """
        Get the weather shutdown lag time for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The weather shutdown lag time value.

        Raises:
            RuntimeError: If the device or weather shutdown lag time is not found.
        """
        return await self._get_device_info_value(WEATHER_SHUTDOWN_LAG_TIME, device_info)

    async def get_heat_cool_switch_delay(self, device_info: Optional[Dict] = None):
        """
        Get the heat/cool switch delay for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The heat/cool switch delay value.

        Raises:
            RuntimeError: If the device or heat/cool switch delay is not found.
        """
        return await self._get_device_info_value(HEAT_COOL_SWITCH_DELAY, device_info)

    async def get_wide_priority_differential(self, device_info: Optional[Dict] = None):
        """
        Get the wide priority differential setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The wide priority differential value.

        Raises:
            RuntimeError: If the device or wide priority differential is not found.
        """
        return await self._get_device_info_value(WIDE_PRIORITY_DIFFERENTIAL, device_info)

    async def get_number_of_stages(self, device_info: Optional[Dict] = None):
        """
        Get the number of stages for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The number of stages value.

        Raises:
            RuntimeError: If the device or number of stages is not found.
        """
        return await self._get_device_info_value(NUMBER_OF_STAGES, device_info)

    async def get_two_stage_heat_pump(self, device_info: Optional[Dict] = None):
        """
        Get the two-stage heat pump setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The two-stage heat pump value.

        Raises:
            RuntimeError: If the device or two-stage heat pump is not found.
        """
        return await self._get_device_info_value(TWO_STAGE_HEAT_PUMP, device_info)

    async def get_stage_on_lag_time(self, device_info: Optional[Dict] = None):
        """
        Get the stage ON lag time for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The stage ON lag time value.

        Raises:
            RuntimeError: If the device or stage ON lag time is not found.
        """
        return await self._get_device_info_value(STAGE_ON_LAG_TIME, device_info)

    async def get_stage_off_lag_time(self, device_info: Optional[Dict] = None):
        """
        Get the stage OFF lag time for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The stage OFF lag time value.

        Raises:
            RuntimeError: If the device or stage OFF lag time is not found.
        """
        return await self._get_device_info_value(STAGE_OFF_LAG_TIME, device_info)

    async def get_rotate_cycles(self, device_info: Optional[Dict] = None) -> Union[int, str]:
        """
        Get the rotate cycles setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[int, str]: The rotate cycles value, or 'off' if disabled (value is 0).

        Raises:
            RuntimeError: If the device or rotate cycles is not found.
        """
        value = await self._get_device_info_value(ROTATE_CYCLES, device_info)
        if value == 0:
            return 'off'
        return value

    async def get_rotate_time(self, device_info: Optional[Dict] = None) -> Union[int, str]:
        """
        Get the rotate time setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[int, str]: The rotate time value, or 'off' if disabled (value is 0).

        Raises:
            RuntimeError: If the device or rotate time is not found.
        """
        value = await self._get_device_info_value(ROTATE_TIME, device_info)
        if value == 0:
            return 'off'
        return value

    async def get_off_staging(self, device_info: Optional[Dict] = None):
        """
        Get the off staging setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            The off staging value.

        Raises:
            RuntimeError: If the device or off staging is not found.
        """
        return await self._get_device_info_value(OFF_STAGING, device_info)

    async def get_warm_weather_shutdown(self, device_info: Optional[Dict] = None) -> Union[Temperature, str]:
        """
        Get the warm weather shutdown setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[Temperature, str]: The warm weather shutdown as a Temperature (in Fahrenheit),
                or 'off' if the feature is disabled (value is 32).

        Raises:
            RuntimeError: If the device or warm weather shutdown is not found.
        """
        value = await self._get_device_info_value(WARM_WEATHER_SHUTDOWN, device_info)
        if value == 32:
            return 'off'
        return Temperature(value, 'F')

    async def get_hot_tank_outdoor_reset(self, device_info: Optional[Dict] = None) -> Union[Temperature, str]:
        """
        Get the hot tank outdoor reset setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[Temperature, str]: The hot tank outdoor reset as a Temperature (in Fahrenheit),
                or 'off' if the feature is disabled (value is -41).

        Raises:
            RuntimeError: If the device or hot tank outdoor reset is not found.
        """
        value = await self._get_device_info_value(HOT_TANK_OUTDOOR_RESET, device_info)
        if value == -41:
            return 'off'
        return Temperature(value, 'F')

    async def get_hot_tank_differential(self, device_info: Optional[Dict] = None) -> TemperatureDelta:
        """
        Get the hot tank differential setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            TemperatureDelta: The hot tank differential value as a TemperatureDelta (stored in °F).

        Raises:
            RuntimeError: If the device or hot tank differential is not found.
        """
        value = await self._get_device_info_value(HOT_TANK_DIFFERENTIAL, device_info)
        return TemperatureDelta(value, 'F')

    async def get_hot_tank_min_temp(self, device_info: Optional[Dict] = None) -> Temperature:
        """
        Get the hot tank minimum temperature for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Temperature: The hot tank minimum temperature value as a Temperature (stored in °F).

        Raises:
            RuntimeError: If the device or hot tank minimum temperature is not found.
        """
        value = await self._get_device_info_value(HOT_TANK_MIN_TEMP, device_info)
        return Temperature(value, 'F')

    async def get_hot_tank_max_temp(self, device_info: Optional[Dict] = None) -> Temperature:
        """
        Get the hot tank maximum temperature for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Temperature: The hot tank maximum temperature value as a Temperature (stored in °F).

        Raises:
            RuntimeError: If the device or hot tank maximum temperature is not found.
        """
        value = await self._get_device_info_value(HOT_TANK_MAX_TEMP, device_info)
        return Temperature(value, 'F')

    async def get_cold_weather_shutdown(self, device_info: Optional[Dict] = None) -> Union[Temperature, str]:
        """
        Get the cold weather shutdown setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[Temperature, str]: The cold weather shutdown as a Temperature (in Fahrenheit),
                or 'off' if the feature is disabled (value is 32).

        Raises:
            RuntimeError: If the device or cold weather shutdown is not found.
        """
        value = await self._get_device_info_value(COLD_WEATHER_SHUTDOWN, device_info)
        if value == 32:
            return 'off'
        return Temperature(value, 'F')

    async def get_cold_tank_outdoor_reset(self, device_info: Optional[Dict] = None) -> Union[Temperature, str]:
        """
        Get the cold tank outdoor reset setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[Temperature, str]: The cold tank outdoor reset as a Temperature (in Fahrenheit),
                or 'off' if the feature is disabled (value is -41).

        Raises:
            RuntimeError: If the device or cold tank outdoor reset is not found.
        """
        value = await self._get_device_info_value(COLD_TANK_OUTDOOR_RESET, device_info)
        if value == -41:
            return 'off'
        return Temperature(value, 'F')

    async def get_cold_tank_differential(self, device_info: Optional[Dict] = None) -> TemperatureDelta:
        """
        Get the cold tank differential setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            TemperatureDelta: The cold tank differential value as a TemperatureDelta (stored in °F).

        Raises:
            RuntimeError: If the device or cold tank differential is not found.
        """
        value = await self._get_device_info_value(COLD_TANK_DIFFERENTIAL, device_info)
        return TemperatureDelta(value, 'F')

    async def get_cold_tank_min_temp(self, device_info: Optional[Dict] = None) -> Temperature:
        """
        Get the cold tank minimum temperature for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Temperature: The cold tank minimum temperature value as a Temperature (stored in °F).

        Raises:
            RuntimeError: If the device or cold tank minimum temperature is not found.
        """
        value = await self._get_device_info_value(COLD_TANK_MIN_TEMP, device_info)
        return Temperature(value, 'F')

    async def get_cold_tank_max_temp(self, device_info: Optional[Dict] = None) -> Temperature:
        """
        Get the cold tank maximum temperature for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Temperature: The cold tank maximum temperature value as a Temperature (stored in °F).

        Raises:
            RuntimeError: If the device or cold tank maximum temperature is not found.
        """
        value = await self._get_device_info_value(COLD_TANK_MAX_TEMP, device_info)
        return Temperature(value, 'F')

    async def get_dhw_enabled(self, device_info: Optional[Dict] = None) -> bool:
        """
        Get the Domestic Hot Water (DHW) enabled state for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            bool: True if DHW demand is enabled, False otherwise.

        Raises:
            RuntimeError: If the device or DHW enabled state is not found.
        """
        return bool(await self._get_device_info_value(DHW_ENABLED, device_info))

    async def get_dhw_target_temp(self, device_info: Optional[Dict] = None) -> Temperature:
        """
        Get the Domestic Hot Water (DHW) tank target temperature for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Temperature: The DHW target temperature (stored in °F).

        Raises:
            RuntimeError: If the device or DHW target temperature is not found.
        """
        value = await self._get_device_info_value(DHW_TARGET_TEMP, device_info)
        return Temperature(value, 'F')

    async def get_dhw_differential(self, device_info: Optional[Dict] = None) -> TemperatureDelta:
        """
        Get the Domestic Hot Water (DHW) tank differential for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            TemperatureDelta: The DHW differential (stored in °F).

        Raises:
            RuntimeError: If the device or DHW differential is not found.
        """
        value = await self._get_device_info_value(DHW_DIFFERENTIAL, device_info)
        return TemperatureDelta(value, 'F')

    async def get_demands(self, device_info: Optional[Dict] = None) -> List[Dict[str, Union[bool, str]]]:
        """
        Retrieve the state of all demand channels (heat, cool, DHW).

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            List[Dict[str, Union[bool, str]]]: A list of dictionaries, each containing:
                - 'activated' (bool): Whether this demand is currently active
                - 'enabled' (bool): Whether this demand channel is enabled
                - 'name' (str): The demand channel identifier ('hd', 'cd', 'dhw')
                - 'title' (str): The display title (e.g., "Heat", "Cool", "DHW")

        Raises:
            RuntimeError: If device info or demands data is not found.
        """
        if device_info is None:
            try:
                device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
            except Exception as e:
                raise RuntimeError(f"Failed to fetch device info: {e}")
        if not device_info:
            raise RuntimeError("Device info not found.")

        try:
            demands = await self._get_device_info_value(DEMANDS, device_info)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve demands data: {e}")

        if not isinstance(demands, list):
            raise RuntimeError("Demands data must be a list.")

        return [
            {
                'activated': d.get('activated', False),
                'enabled': d.get('enabled', False),
                'name': d.get('name', ''),
                'title': d.get('title', ''),
            }
            for d in demands
        ]

    async def get_dhw_state(self, device_info: Optional[Dict] = None) -> Dict[str, Union[bool, str]]:
        """
        Retrieve the runtime state of the Domestic Hot Water (DHW) demand channel.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Dict[str, Union[bool, str]]: A dictionary containing:
                - 'activated' (bool): Whether DHW demand is currently active
                - 'enabled' (bool): Whether the DHW channel is enabled
                - 'title' (str): The display title (e.g., "DHW")

        Raises:
            RuntimeError: If device info or DHW demand data is not found.
        """
        all_demands = await self.get_demands(device_info)
        dhw = next((d for d in all_demands if d.get('name') == 'dhw'), None)
        if dhw is None:
            raise RuntimeError("DHW demand not found.")

        return {
            'activated': dhw['activated'],
            'enabled': dhw['enabled'],
            'title': dhw['title'],
        }

    async def get_system_state(self, device_info: Optional[Dict] = None) -> Dict:
        """
        Retrieve the complete runtime state of the system in a single API call.

        Bundles demands, temperatures, heat pump stages, backup, pumps,
        reversing valve, and weather shutdown status into one response.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Dict containing:
                - 'demands' (list): Demand channels with 'activated', 'enabled', 'name', 'title'
                - 'temperatures' (list): Enabled sensors with 'title', 'type', 'current', 'target',
                  'activated', 'activatedState', 'enabled'
                - 'stages' (list): Heat pump stages with 'activated', 'enabled', 'title', 'device',
                  'index', 'runTime'
                - 'backup' (dict): Backup state with 'activated', 'enabled', 'title', 'runTime'
                - 'pumps' (list): Pump states with 'activated', 'title', 'mode'
                - 'reversingValve' (dict): Reversing valve with 'activated', 'title'
                - 'weatherShutdown' (dict): WWSD/CWSD status dicts with 'activated', 'title'

            Any section that cannot be parsed returns None instead of raising.

        Raises:
            RuntimeError: If device info cannot be fetched.
        """
        if device_info is None:
            try:
                device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
            except Exception as e:
                raise RuntimeError(f"Failed to fetch device info: {e}")
        if not device_info:
            raise RuntimeError("Device info not found.")

        # Demands — delegate to existing method
        try:
            demands = await self.get_demands(device_info)
        except Exception:
            demands = None

        # Temperatures — use the enhanced 'temperatures' array
        try:
            temps_data = await self._get_device_info_value(TEMPERATURES_ENHANCED, device_info)
            temperatures = []
            for t in temps_data:
                if not t.get('enabled', False):
                    continue
                current = t.get('current')
                target = t.get('target')
                temperatures.append({
                    'title': t.get('title'),
                    'type': t.get('type'),
                    'current': Temperature(current, 'F') if current is not None else None,
                    'target': Temperature(target, 'F') if target is not None else None,
                    'activated': t.get('activated', False),
                    'activatedState': t.get('activatedState'),
                    'enabled': True,
                })
        except Exception:
            temperatures = None

        # Stages — delegate to existing method
        try:
            stages = await self.get_heatpump_stages_state(device_info)
        except Exception:
            stages = None

        # Backup — delegate to existing method
        try:
            backup = await self.get_backup_state(device_info)
        except Exception:
            backup = None

        # Pumps — merge state array with mode config
        try:
            pumps_data = await self._get_device_info_value(PUMPS, device_info)
            pump_mode_keys = [PUMP_1_MODE, PUMP_2_MODE]
            pumps = []
            for i, p in enumerate(pumps_data):
                mode_value = None
                if i < len(pump_mode_keys):
                    try:
                        mode_value = await self._get_device_info_value(pump_mode_keys[i], device_info)
                    except Exception:
                        pass
                pumps.append({
                    'activated': p.get('activated', False),
                    'title': p.get('title', ''),
                    'mode': PUMP_MODES.get(mode_value, f"unknown ({mode_value})") if mode_value is not None else None,
                })
        except Exception:
            pumps = None

        # Reversing Valve
        try:
            rv_data = await self._get_device_info_value(REVERSING_VALVE, device_info)
            reversing_valve = {
                'activated': rv_data.get('activated', False),
                'title': rv_data.get('title', 'Reversing Valve'),
            }
        except Exception:
            reversing_valve = None

        # Weather Shutdown Status
        try:
            wsd_data = await self._get_device_info_value(WEATHER_SHUTDOWN_STATUS, device_info)
            weather_shutdown = {}
            for key in ('wwsd', 'cwsd'):
                entry = wsd_data.get(key, {})
                weather_shutdown[key] = {
                    'activated': entry.get('activated', False),
                    'title': entry.get('title', key.upper()),
                }
        except Exception:
            weather_shutdown = None

        return {
            'demands': demands,
            'temperatures': temperatures,
            'stages': stages,
            'backup': backup,
            'pumps': pumps,
            'reversingValve': reversing_valve,
            'weatherShutdown': weather_shutdown,
        }

    async def get_backup_lag_time(self, device_info: Optional[Dict] = None) -> Union[int, str]:
        """
        Get the backup lag time setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[int, str]: The backup lag time value, or 'off' if disabled (value is 0).

        Raises:
            RuntimeError: If the device or backup lag time is not found.
        """
        value = await self._get_device_info_value(BACKUP_LAG_TIME, device_info)
        if value == 0:
            return 'off'
        return value

    async def get_backup_temp(self, device_info: Optional[Dict] = None) -> Union[Temperature, str]:
        """
        Get the backup temperature setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[Temperature, str]: The backup temperature value as a Temperature (stored in °F), or 'off' if disabled (value is 0).

        Raises:
            RuntimeError: If the device or backup temperature is not found.
        """
        value = await self._get_device_info_value(BACKUP_TEMP, device_info)
        if value == 0:
            return 'off'
        return Temperature(value, 'F')

    async def get_backup_differential(self, device_info: Optional[Dict] = None) -> Union[TemperatureDelta, str]:
        """
        Get the backup differential setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[TemperatureDelta, str]: The backup differential value as a TemperatureDelta, or 'off' if disabled (value is 0).

        Raises:
            RuntimeError: If the device or backup differential is not found.
        """
        value = await self._get_device_info_value(BACKUP_DIFFERENTIAL, device_info)
        if value == 0:
            return 'off'
        return TemperatureDelta(value, 'F')

    async def get_backup_only_outdoor_temp(self, device_info: Optional[Dict] = None) -> Union[Temperature, str]:
        """
        Get the backup only outdoor temperature setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[Temperature, str]: The backup only outdoor temperature value as a Temperature (stored in °F), or 'off' if disabled (value is -41).

        Raises:
            RuntimeError: If the device or backup only outdoor temperature is not found.
        """
        value = await self._get_device_info_value(BACKUP_ONLY_OUTDOOR_TEMP, device_info)
        if value == -41:
            return 'off'
        return Temperature(value, 'F')

    async def get_backup_only_tank_temp(self, device_info: Optional[Dict] = None) -> Union[Temperature, str]:
        """
        Get the backup only tank temperature setting for the device.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Union[Temperature, str]: The backup only tank temperature value as a Temperature (stored in °F), or 'off' if disabled (value is 32).

        Raises:
            RuntimeError: If the device or backup only tank temperature is not found.
        """
        value = await self._get_device_info_value(BACKUP_ONLY_TANK_TEMP, device_info)
        if value == 32:
            return 'off'
        return Temperature(value, 'F')    

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
        return await self._get_device_info_value(FIRMWARE_VERSION, device_info)

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
        return await self._get_device_info_value(SYNC_CODE, device_info)

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
        return await self._get_device_info_value(DEVICE_PIN, device_info)
    
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
        return await self._get_device_info_value(DEVICE_TYPE, device_info)

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
            try:
                device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
            except Exception as e:
                _LOGGER.error(f"Exception fetching device info: {e}")
                raise RuntimeError(f"Failed to fetch device info: {e}")
        if not device_info:
            raise RuntimeError("Device info not found.")

        result = {}
        
        try:
            sensors = await self._get_device_info_value(TEMPERATURE_SENSORS, device_info)
        except Exception as e:
            _LOGGER.error(f"Failed to retrieve temperature sensors: {e}")
            raise RuntimeError(f"Failed to retrieve temperature sensors: {e}")
        
        if not isinstance(sensors, dict):
            raise RuntimeError("Temperature sensors data is not in expected format.")
        
        for temp_key, temp_info in sensors.items():
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
            Dict[str, Union[list, str]]: Dictionary with 'stages' as a list of timedelta objects and 'backup' as a single timedelta object.

        Raises:
            RuntimeError: If required runtime data is not found.
        """
        if device_info is None:
            try:
                device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
            except Exception as e:
                raise RuntimeError(f"Failed to fetch device info: {e}")
        if not device_info:
            raise RuntimeError("Device info not found.")
        
        try:
            stg_run = await self._get_device_info_value(HEATPUMP_STAGE_RUNTIMES, device_info)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve heat pump stage runtimes: {e}")

        try:
            num_stg = int(await self._get_device_info_value(NUMBER_OF_STAGES, device_info))
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve number of stages: {e}")

        try:
            bk_run = await self._get_device_info_value(BACKUP_RUNTIME, device_info)
        except Exception:
            bk_run = None  # Backup runtime is optional

        if not isinstance(stg_run, list):
            raise RuntimeError("Stage runtimes must be a list.")

        if not (1 <= num_stg <= 16):
            raise RuntimeError("Number of stages must be between 1 and 16.")

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
    
    
    async def get_heatpump_stages_state(self, device_info: Optional[Dict] = None) -> List[Dict[str, Union[bool, str, int]]]:
        """
        Retrieve the state of all heat pump stages.

        Each stage contains information about whether it's activated (currently running),
        enabled, its title/name, associated device, index, and runtime.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            List[Dict[str, Union[bool, str, int]]]: A list of dictionaries, each containing:
                - 'activated' (bool): Whether the stage is currently running
                - 'enabled' (bool): Whether the stage is enabled
                - 'title' (str): The name/title of the stage (e.g., "Stage 1")
                - 'device' (str): The device identifier associated with the stage
                - 'index' (int): The index of the stage
                - 'runTime' (str): The runtime of the stage in "H:MM" format

        Raises:
            RuntimeError: If device info or stages data is not found.
        """
        if device_info is None:
            try:
                device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
            except Exception as e:
                raise RuntimeError(f"Failed to fetch device info: {e}")
        if not device_info:
            raise RuntimeError("Device info not found.")

        try:
            stages_data = await self._get_device_info_value(HEATPUMP_STAGES_STATE, device_info)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve stages data: {e}")

        if not isinstance(stages_data, list):
            raise RuntimeError("Stages data must be a list.")

        result = []
        for stage in stages_data:
            stage_info = {
                'activated': stage.get('activated', False),
                'enabled': stage.get('enabled', False),
                'title': stage.get('title', ''),
                'device': stage.get('device', ''),
                'index': stage.get('index', 0),
                'runTime': stage.get('runTime', '0:00')
            }
            result.append(stage_info)

        return result

    async def get_backup_state(self, device_info: Optional[Dict] = None) -> Dict[str, Union[bool, str]]:
        """
        Retrieve the state of the backup heater (e.g., electric or gas boiler).

        The backup heater runs when heat pumps cannot keep up or are shut off
        due to cold temperatures.

        Args:
            device_info (Optional[Dict]): If provided, use this device_info dict instead of fetching from API.

        Returns:
            Dict[str, Union[bool, str]]: A dictionary containing:
                - 'activated' (bool): Whether the backup is currently running
                - 'enabled' (bool): Whether the backup is enabled
                - 'title' (str): The name/title of the backup (e.g., "Backup")
                - 'runTime' (str): The runtime of the backup in "H:MM" format

        Raises:
            RuntimeError: If device info or backup data is not found.
        """
        if device_info is None:
            try:
                device_info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
            except Exception as e:
                raise RuntimeError(f"Failed to fetch device info: {e}")
        if not device_info:
            raise RuntimeError("Device info not found.")

        try:
            backup_data = await self._get_device_info_value(BACKUP_STATE, device_info)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve backup data: {e}")

        if not isinstance(backup_data, dict):
            raise RuntimeError("Backup data must be a dictionary.")

        return {
            'activated': backup_data.get('activated', False),
            'enabled': backup_data.get('enabled', False),
            'title': backup_data.get('title', 'Backup'),
            'runTime': backup_data.get('runTime', '0:00')
        }

    async def get_current_weather(self, building_info: Optional[Dict] = None) -> Dict:
        """
        Retrieve the current weather conditions for the building.

        Weather data is attached to the building, not the device.

        Args:
            building_info (Optional[Dict]): If provided, use this building dict instead of fetching from API.

        Returns:
            Dict containing:
                - 'temp' (Temperature): Current outdoor temperature
                - 'feelsLike' (Temperature): Feels-like temperature
                - 'min' (Temperature): Today's minimum temperature
                - 'max' (Temperature): Today's maximum temperature
                - 'pressure' (int): Atmospheric pressure in hPa
                - 'humidity' (int): Relative humidity in %
                - 'wind' (float): Wind speed
                - 'windDir' (int): Wind direction in degrees
                - 'clouds' (int): Cloud cover in %
                - 'snow' (float): Snow amount
                - 'rain' (float): Rain amount
                - 'description' (str): Weather description (e.g., "mist")
                - 'icon' (str): Weather icon code
                - 'weatherId' (int): OpenWeatherMap condition ID

        Raises:
            RuntimeError: If building info or weather data is not found.
        """
        if building_info is None:
            try:
                building_info = await self.sensorlinx.get_buildings(self.building_id)
            except Exception as e:
                raise RuntimeError(f"Failed to fetch building info: {e}")
        if not building_info:
            raise RuntimeError("Building info not found.")

        if isinstance(building_info, list):
            building_info = building_info[0]

        weather_data = building_info.get('weather', {}).get('weather')
        if not weather_data:
            raise RuntimeError("Current weather data not found.")

        return {
            'temp': Temperature(weather_data['temp'], 'F'),
            'feelsLike': Temperature(weather_data['feelsLike'], 'F'),
            'min': Temperature(weather_data['min'], 'F'),
            'max': Temperature(weather_data['max'], 'F'),
            'pressure': weather_data.get('pressure'),
            'humidity': weather_data.get('humidity'),
            'wind': weather_data.get('wind'),
            'windDir': weather_data.get('windDir'),
            'clouds': weather_data.get('clouds'),
            'snow': weather_data.get('snow', 0),
            'rain': weather_data.get('rain', 0),
            'description': weather_data.get('description'),
            'icon': weather_data.get('icon'),
            'weatherId': weather_data.get('weatherId'),
        }

    async def get_forecast(self, building_info: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve the weather forecast for the building.

        Weather data is attached to the building, not the device.

        Args:
            building_info (Optional[Dict]): If provided, use this building dict instead of fetching from API.

        Returns:
            List of forecast period dicts, each containing:
                - 'time' (datetime): Forecast period start time (UTC)
                - 'pop' (int): Probability of precipitation in %
                - 'snow' (float): Snow amount
                - 'temp' (Temperature): Forecast temperature
                - 'min' (Temperature): Minimum temperature for the period
                - 'max' (Temperature): Maximum temperature for the period
                - 'description' (str): Weather description
                - 'icon' (str): Weather icon code

        Raises:
            RuntimeError: If building info or forecast data is not found.
        """
        if building_info is None:
            try:
                building_info = await self.sensorlinx.get_buildings(self.building_id)
            except Exception as e:
                raise RuntimeError(f"Failed to fetch building info: {e}")
        if not building_info:
            raise RuntimeError("Building info not found.")

        if isinstance(building_info, list):
            building_info = building_info[0]

        forecast_data = building_info.get('weather', {}).get('forecast')
        if forecast_data is None:
            raise RuntimeError("Forecast data not found.")
        if not isinstance(forecast_data, list):
            raise RuntimeError("Forecast data must be a list.")

        result = []
        for period in forecast_data:
            result.append({
                'time': datetime.datetime.fromisoformat(period['time'].replace('Z', '+00:00')),
                'pop': period.get('pop', 0),
                'snow': period.get('snow', 0),
                'temp': Temperature(period['temp'], 'F'),
                'min': Temperature(period['min'], 'F'),
                'max': Temperature(period['max'], 'F'),
                'description': period.get('description'),
                'icon': period.get('icon'),
                'weatherId': period.get('weatherId'),
            })
        return result


class ThmDevice(SensorlinxDevice):
    """
    Parser for HBX THM-style thermostats (e.g. THM-0600).

    The THM JSON payload has a different shape than an ECO controller:
    no ``temps`` dict, no tank parameters. Instead it exposes a small
    set of pre-decoded blocks (``temperature``, ``target``, ``thmMode``,
    ``changeover``, ``fanModes``, ``awayMode``, ``demands``, ``schedules``)
    plus raw fields like ``rm`` (room °F), ``flr`` (floor °F), and
    ``hm`` (humidity %).

    Most accessors are read-only; a small set of setters
    (:meth:`set_hvac_mode`, :meth:`set_target_temperature`,
    :meth:`set_away_mode`, :meth:`set_fan_mode`) cover the surfaces validated
    against a live install.
    """

    async def get_name(self, device_info: Optional[Dict] = None) -> str:
        """Return the user-assigned thermostat name (e.g. ``"Garage"``)."""
        return await self._get_device_info_value("name", device_info)

    async def get_room_temperature(
        self, device_info: Optional[Dict] = None
    ) -> Optional[Temperature]:
        """Current room temperature in °F, or ``None`` if not reported."""
        info = await self._resolve_device_info(device_info)
        # Prefer the pre-decoded ``temperature`` block when present.
        block = info.get("temperature")
        if isinstance(block, dict) and block.get("type") == "room":
            value = block.get("value")
            if value is not None:
                return Temperature(value, "F")
        raw = info.get("rm")
        return Temperature(raw, "F") if raw is not None else None

    async def get_floor_temperature(
        self, device_info: Optional[Dict] = None
    ) -> Optional[Temperature]:
        """Current floor temperature in °F, or ``None`` if not reported."""
        info = await self._resolve_device_info(device_info)
        raw = info.get("flr")
        return Temperature(raw, "F") if raw is not None else None

    async def get_humidity(
        self, device_info: Optional[Dict] = None
    ) -> Optional[float]:
        """Current relative humidity in percent, or ``None`` if not reported."""
        info = await self._resolve_device_info(device_info)
        raw = info.get("hm")
        return float(raw) if raw is not None else None

    async def get_target_temperature(
        self, device_info: Optional[Dict] = None
    ) -> Optional[Temperature]:
        """
        The active setpoint in °F.

        Returns ``None`` when the thermostat reports ``target.isOff`` (i.e.
        the changeover is in the Off position) so callers can distinguish
        "no setpoint" from a real temperature.
        """
        info = await self._resolve_device_info(device_info)
        block = info.get("target")
        if not isinstance(block, dict):
            return None
        if block.get("isOff"):
            return None
        value = block.get("value")
        return Temperature(value, "F") if value is not None else None

    async def get_target_type(
        self, device_info: Optional[Dict] = None
    ) -> Optional[str]:
        """The kind of setpoint currently shown (``"heat"`` or ``"cool"``)."""
        info = await self._resolve_device_info(device_info)
        block = info.get("target")
        if isinstance(block, dict):
            return block.get("type")
        return None

    async def is_off(self, device_info: Optional[Dict] = None) -> bool:
        """Return ``True`` when the thermostat changeover is in the Off position."""
        info = await self._resolve_device_info(device_info)
        block = info.get("target")
        if isinstance(block, dict):
            return bool(block.get("isOff"))
        return False

    async def is_heating(self, device_info: Optional[Dict] = None) -> bool:
        """Return ``True`` when a heat demand is currently active."""
        info = await self._resolve_device_info(device_info)
        return bool(info.get("isHeating"))

    async def is_cooling(self, device_info: Optional[Dict] = None) -> bool:
        """Return ``True`` when a cool demand is currently active."""
        info = await self._resolve_device_info(device_info)
        return bool(info.get("isCooling"))

    async def get_hvac_mode(
        self, device_info: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Active changeover mode as a lowercase string.

        Reads the ``changeover`` array and returns the ``key`` of the entry
        flagged ``activated``: typically one of ``"auto"``, ``"heat"``,
        ``"cool"``, ``"off"``. Returns ``None`` if no entry is activated.
        """
        info = await self._resolve_device_info(device_info)
        for entry in info.get("changeover", []) or []:
            if isinstance(entry, dict) and entry.get("activated"):
                return entry.get("key")
        return None

    async def get_thm_mode(
        self, device_info: Optional[Dict] = None
    ) -> Optional[str]:
        """The thermostat mode label (e.g. ``"Air"``, ``"Floor"``)."""
        info = await self._resolve_device_info(device_info)
        block = info.get("thmMode")
        if isinstance(block, dict):
            return block.get("title")
        return None

    async def get_fan_mode(
        self, device_info: Optional[Dict] = None
    ) -> Optional[str]:
        """Active fan mode key (``"off"``/``"on"``/``"intermittent"``)."""
        info = await self._resolve_device_info(device_info)
        for entry in info.get("fanModes", []) or []:
            if isinstance(entry, dict) and entry.get("activated"):
                return entry.get("key")
        return None

    async def get_away_mode(
        self, device_info: Optional[Dict] = None
    ) -> Dict:
        """Full ``awayMode`` block (activated flag + heat/cool targets)."""
        info = await self._resolve_device_info(device_info)
        block = info.get("awayMode")
        return block if isinstance(block, dict) else {}

    async def get_demands(
        self, device_info: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Return the THM ``demands`` array as a list of dicts.

        Each entry has ``key``, ``title``, ``enabled``, ``activated``.
        Overrides the ECO-specific ``get_demands`` to use the THM schema.
        """
        info = await self._resolve_device_info(device_info)
        block = info.get("demands")
        return list(block) if isinstance(block, list) else []

    async def get_schedules(
        self, device_info: Optional[Dict] = None
    ) -> List[Dict]:
        """Return the ``schedules`` array (weekday/weekend periods)."""
        info = await self._resolve_device_info(device_info)
        block = info.get("schedules")
        return list(block) if isinstance(block, list) else []

    async def get_temperatures(
        self,
        temp_name: Optional[str] = None,
        device_info: Optional[Dict] = None,
    ) -> Union[Dict[str, Dict[str, Optional[Temperature]]], Dict[str, Optional[Temperature]]]:
        """
        Override the ECO-shaped reader to expose THM temperature sensors.

        Returns a dict keyed by sensor title with ``actual``/``target``
        Temperature values, mirroring :meth:`SensorlinxDevice.get_temperatures`
        so callers expecting the ECO shape get a usable result.
        """
        info = await self._resolve_device_info(device_info)
        actual_room = await self.get_room_temperature(info)
        target = await self.get_target_temperature(info)
        floor = await self.get_floor_temperature(info)

        result: Dict[str, Dict[str, Optional[Temperature]]] = {}
        if actual_room is not None or target is not None:
            result["Room"] = {"actual": actual_room, "target": target}
        if floor is not None:
            result["Floor"] = {"actual": floor, "target": None}

        if temp_name:
            if temp_name not in result:
                raise RuntimeError(f"Temperature sensor '{temp_name}' not found.")
            return result[temp_name]
        if not result:
            raise RuntimeError("No matching temperature sensors found.")
        return result

    # ------------------------------------------------------------------
    # Setters
    #
    # Field names confirmed via paired before/after device dumps from a live
    # THM-0600 (firmware 1.22) on 2026-04-26. ``set_target_temperature`` is
    # the only setter whose payload shape is inferred (the change surfaced
    # only in the derived ``target.value`` block in read-side data); all
    # others write the raw integer field that demonstrably changed in the
    # diffs.
    # ------------------------------------------------------------------

    async def set_hvac_mode(self, mode: str) -> None:
        """
        Set the THM changeover (HVAC mode).

        Args:
            mode: One of ``"auto"``, ``"heat"``, ``"cool"``, ``"off"``.

        Raises:
            InvalidParameterError: If ``mode`` is not recognised.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        key = mode.lower() if isinstance(mode, str) else None
        if key not in THM_CHANGEOVER_VALUES:
            _LOGGER.error(
                "Invalid THM HVAC mode %r. Must be one of %s.",
                mode, list(THM_CHANGEOVER_VALUES),
            )
            raise InvalidParameterError(
                "Invalid THM HVAC mode. Must be 'auto', 'heat', 'cool' or 'off'."
            )
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_CHANGEOVER: THM_CHANGEOVER_VALUES[key]},
        )

    async def set_away_mode(self, enabled: bool) -> None:
        """
        Enable or disable the THM Away preset.

        Args:
            enabled: ``True`` to turn Away mode on; ``False`` to turn it off.

        Raises:
            InvalidParameterError: If ``enabled`` is not a bool.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        if not isinstance(enabled, bool):
            _LOGGER.error("THM away mode must be a boolean (got %r).", type(enabled))
            raise InvalidParameterError("THM away mode must be a boolean.")
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_AWAY: 1 if enabled else 0},
        )

    async def set_fan_mode(self, mode: str) -> None:
        """
        Set the THM fan mode.

        Args:
            mode: One of ``"off"``, ``"on"``, ``"intermittent"``.

        Raises:
            InvalidParameterError: If ``mode`` is not recognised.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        key = mode.lower() if isinstance(mode, str) else None
        if key not in THM_FAN_MODE_VALUES:
            _LOGGER.error(
                "Invalid THM fan mode %r. Must be one of %s.",
                mode, list(THM_FAN_MODE_VALUES),
            )
            raise InvalidParameterError(
                "Invalid THM fan mode. Must be 'off', 'on' or 'intermittent'."
            )
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_FAN_MODE: THM_FAN_MODE_VALUES[key]},
        )

    async def set_target_temperature(self, value: Temperature) -> None:
        """
        Set the THM target setpoint for the active changeover (heat or cool).

        Inspects the device's current ``target.type`` and writes either the
        ``rmT`` (heat) or ``rmCT`` (cool) field accordingly. The HBX cloud
        rejects setpoint writes when the THM is in Off mode.

        Args:
            value: A :class:`Temperature` in the 35°F–99°F range.

        Raises:
            InvalidParameterError: If ``value`` is not a Temperature or is
                outside the safe range, or if the THM is currently Off.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.

        Note:
            Field mapping (``rmT`` / ``rmCT``) was confirmed via paired
            before/after device dumps from a live THM-0600 (firmware 1.22)
            on 2026-04-26: changing the heat setpoint moved ``rmT``;
            changing the cool setpoint moved ``rmCT``. The previously-used
            ``target.value`` was a derived read-only block.
        """
        if not isinstance(value, Temperature):
            _LOGGER.error(
                "THM target temperature must be a Temperature instance (got %r).",
                type(value),
            )
            raise InvalidParameterError(
                "THM target temperature must be a Temperature instance."
            )
        temp_f = value.to_fahrenheit()
        if not (35 <= temp_f <= 99):
            _LOGGER.error(
                "THM target temperature must be between 35°F and 99°F (got %s°F).",
                temp_f,
            )
            raise InvalidParameterError(
                "THM target temperature must be between 35°F and 99°F."
            )
        info = await self._resolve_device_info(None)
        target = info.get("target") or {}
        target_type = target.get("type")
        if target.get("isOff") or target_type not in ("heat", "cooling"):
            _LOGGER.error(
                "Cannot set THM target temperature while changeover is Off "
                "(target.type=%r, target.isOff=%r).",
                target_type, target.get("isOff"),
            )
            raise InvalidParameterError(
                "Cannot set THM target temperature while changeover is Off."
            )
        field = THM_HEAT_SETPOINT if target_type == "heat" else THM_COOL_SETPOINT
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{field: int(round(temp_f))},
        )

    async def set_schedule_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the THM's on-device program/schedule.

        Writes the ``pgmble`` field. When the schedule is disabled, the THM
        ignores its weekday/weekend program and holds the manual setpoint;
        when enabled, the program drives the active setpoint.

        Args:
            enabled: ``True`` to enable the schedule; ``False`` to disable it.

        Raises:
            InvalidParameterError: If ``enabled`` is not a bool.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.

        Note:
            Field name confirmed via paired before/after device dumps
            from a live THM-0600 on 2026-04-28: toggling the schedule
            moved ``pgmble`` between 0 and 1.
        """
        if not isinstance(enabled, bool):
            _LOGGER.error(
                "THM schedule enabled must be a boolean (got %r).", type(enabled)
            )
            raise InvalidParameterError("THM schedule enabled must be a boolean.")
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_SCHEDULE_ENABLE: 1 if enabled else 0},
        )

    async def set_humidity_mode(self, mode: str) -> None:
        """
        Set the THM humidity control mode.

        Writes the ``useHum`` field. ``"off"`` disables humidity control,
        ``"on"`` runs continuously toward :attr:`humidity target <set_humidity_target>`,
        and ``"auto"`` lets the THM choose based on outdoor conditions.

        Args:
            mode: One of ``"off"``, ``"on"``, ``"auto"``.

        Raises:
            InvalidParameterError: If ``mode`` is not recognised.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.

        Note:
            Field mapping confirmed via paired before/after dumps from
            a live THM-0600 on 2026-04-28: off→on moved ``useHum`` 0→1,
            on→auto moved it 1→2.
        """
        key = mode.lower() if isinstance(mode, str) else None
        if key not in THM_HUMIDITY_MODE_VALUES:
            _LOGGER.error(
                "Invalid THM humidity mode %r. Must be one of %s.",
                mode, list(THM_HUMIDITY_MODE_VALUES),
            )
            raise InvalidParameterError(
                "Invalid THM humidity mode. Must be 'off', 'on' or 'auto'."
            )
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_HUMIDITY_MODE: THM_HUMIDITY_MODE_VALUES[key]},
        )

    async def set_humidity_target(self, value: int) -> None:
        """
        Set the THM humidity target (relative humidity, percent).

        Writes the ``hmT`` field as an integer percent in the 0-100 range.

        Args:
            value: Target relative humidity, 0-100 (integer).

        Raises:
            InvalidParameterError: If ``value`` is not an int or is out of range.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.

        Note:
            Field mapping confirmed via paired before/after dumps from a
            live THM-0600 on 2026-04-28: changing the humidity target
            from 40% to 45% moved ``hmT`` 40→45.
        """
        # Reject bool because bool is a subclass of int in Python.
        if isinstance(value, bool) or not isinstance(value, int):
            _LOGGER.error("THM humidity target must be an int (got %r).", type(value))
            raise InvalidParameterError("THM humidity target must be an int.")
        if not (0 <= value <= 100):
            _LOGGER.error(
                "THM humidity target must be between 0 and 100 (got %s).", value
            )
            raise InvalidParameterError(
                "THM humidity target must be between 0 and 100."
            )
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_HUMIDITY_TARGET: value},
        )

    async def get_heat_setpoint(
        self, device_info: Optional[Dict] = None
    ) -> Optional[Temperature]:
        """
        Return the heat-side setpoint (``rmT``) in °F.

        This is the dedicated heat-mode setpoint and is independent of the
        active changeover mode: it always reports the heat target, even
        when the thermostat is in Auto or Cool. Prefer this over
        :py:meth:`get_target_temperature` which reads the display-only
        ``target.value`` field that is biased to one side in Auto mode.

        Returns:
            ``Temperature`` in °F, or ``None`` when the field is missing.
        """
        info = await self._resolve_device_info(device_info)
        value = info.get(THM_HEAT_SETPOINT)
        if value is None:
            return None
        return Temperature(value, "F")

    async def get_cool_setpoint(
        self, device_info: Optional[Dict] = None
    ) -> Optional[Temperature]:
        """
        Return the cool-side setpoint (``rmCT``) in °F.

        Mirror of :py:meth:`get_heat_setpoint` for the cool side. Always
        reports the cool target regardless of changeover mode. The HBX
        cloud's ``target`` block does NOT expose the cool setpoint when in
        Auto mode (``target.type`` is permanently ``"heat"`` in Auto), so
        this is the only reliable way to read the cool target.

        Returns:
            ``Temperature`` in °F, or ``None`` when the field is missing.
        """
        info = await self._resolve_device_info(device_info)
        value = info.get(THM_COOL_SETPOINT)
        if value is None:
            return None
        return Temperature(value, "F")

    @staticmethod
    def _validate_setpoint(value: Temperature, label: str) -> int:
        """Validate a setpoint Temperature and return its integer °F value."""
        if not isinstance(value, Temperature):
            _LOGGER.error(
                "THM %s setpoint must be a Temperature instance (got %r).",
                label, type(value),
            )
            raise InvalidParameterError(
                f"THM {label} setpoint must be a Temperature instance."
            )
        temp_f = value.to_fahrenheit()
        if not (35 <= temp_f <= 99):
            _LOGGER.error(
                "THM %s setpoint must be between 35°F and 99°F (got %s°F).",
                label, temp_f,
            )
            raise InvalidParameterError(
                f"THM {label} setpoint must be between 35°F and 99°F."
            )
        return int(round(temp_f))

    async def set_heat_setpoint(self, value: Temperature) -> None:
        """
        Set the heat-side setpoint (``rmT``) directly.

        Works in any changeover mode (Auto/Heat/Cool). Use this instead of
        :py:meth:`set_target_temperature` when you need to be explicit
        about which side you're writing — particularly important in Auto
        mode where the legacy method's ``target.type`` lookup is biased
        to the heat side and cannot disambiguate.

        Args:
            value: A :class:`Temperature` in the 35°F–99°F range.

        Raises:
            InvalidParameterError: If ``value`` is not a Temperature or is
                outside the safe range.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        temp_int = self._validate_setpoint(value, "heat")
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_HEAT_SETPOINT: temp_int},
        )

    async def set_cool_setpoint(self, value: Temperature) -> None:
        """
        Set the cool-side setpoint (``rmCT``) directly.

        Mirror of :py:meth:`set_heat_setpoint`. Works in any changeover
        mode. Required for adjusting the cool side while in Auto mode,
        which the legacy :py:meth:`set_target_temperature` cannot do.

        Args:
            value: A :class:`Temperature` in the 35°F–99°F range.

        Raises:
            InvalidParameterError: If ``value`` is not a Temperature or is
                outside the safe range.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        temp_int = self._validate_setpoint(value, "cool")
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_COOL_SETPOINT: temp_int},
        )

    async def set_heat_cool_setpoints(
        self, heat: Temperature, cool: Temperature
    ) -> None:
        """
        Set both heat (``rmT``) and cool (``rmCT``) setpoints in a single PATCH.

        Use this for HEAT_COOL / Auto-mode dual-setpoint writes to avoid
        the transient inconsistent state that two sequential PATCHes would
        produce.

        Args:
            heat: Heat-side ``Temperature`` (35°F–99°F).
            cool: Cool-side ``Temperature`` (35°F–99°F). Must be strictly
                greater than ``heat`` so the deadband is non-zero.

        Raises:
            InvalidParameterError: If either value is invalid or if
                ``heat >= cool``.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        heat_int = self._validate_setpoint(heat, "heat")
        cool_int = self._validate_setpoint(cool, "cool")
        if heat_int >= cool_int:
            _LOGGER.error(
                "THM heat setpoint (%s°F) must be lower than cool setpoint (%s°F).",
                heat_int, cool_int,
            )
            raise InvalidParameterError(
                "THM heat setpoint must be lower than cool setpoint."
            )
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{
                THM_HEAT_SETPOINT: heat_int,
                THM_COOL_SETPOINT: cool_int,
            },
        )

    async def get_away_heat_setpoint(
        self, device_info: Optional[Dict] = None
    ) -> Optional[Temperature]:
        """
        Return the away-mode heat setpoint in °F.

        Reads the nested ``awayMode.heatTarget.value`` field. This is the
        active heat target only while the THM Away preset is on; in Home
        mode the active heat target is ``rmT`` (see
        :py:meth:`get_heat_setpoint`).

        Returns:
            ``Temperature`` in °F, or ``None`` when the field is missing.

        Note:
            Field path confirmed via paired before/after dumps from a
            live THM-0600 on 2026-05-01: changing the away heat setpoint
            in the HBX app's away-temps popup moved
            ``awayMode.heatTarget.value`` from 53 to 58.
        """
        info = await self._resolve_device_info(device_info)
        block = info.get(THM_AWAY_MODE) or {}
        target = block.get(THM_AWAY_HEAT_TARGET) or {}
        value = target.get(THM_AWAY_TARGET_VALUE)
        if value is None:
            return None
        return Temperature(value, "F")

    async def get_away_cool_setpoint(
        self, device_info: Optional[Dict] = None
    ) -> Optional[Temperature]:
        """
        Return the away-mode cool setpoint in °F.

        Mirror of :py:meth:`get_away_heat_setpoint` for the cool side,
        reading ``awayMode.coolTarget.value``.

        Returns:
            ``Temperature`` in °F, or ``None`` when the field is missing.
        """
        info = await self._resolve_device_info(device_info)
        block = info.get(THM_AWAY_MODE) or {}
        target = block.get(THM_AWAY_COOL_TARGET) or {}
        value = target.get(THM_AWAY_TARGET_VALUE)
        if value is None:
            return None
        return Temperature(value, "F")

    async def _load_away_mode_block(self) -> Dict:
        """Fetch the current ``awayMode`` block for read-modify-write.

        The cloud silently rejects partial-nested PATCHes that don't
        include the full block (title/activated/pgm/heatTarget/
        coolTarget), so every away-setpoint setter has to splice into a
        complete copy. Returns a deep-ish copy of the existing block,
        or a sane default if the device hasn't seeded one yet.
        """
        info = await self.sensorlinx.get_devices(self.building_id, self.device_id)
        if not isinstance(info, dict):
            info = {}
        block = info.get(THM_AWAY_MODE)
        if not isinstance(block, dict):
            block = {}
        # Shallow copy of the top-level block plus copies of the nested
        # heatTarget/coolTarget so we can mutate them safely.
        result = dict(block)
        for key in (THM_AWAY_HEAT_TARGET, THM_AWAY_COOL_TARGET):
            target = result.get(key)
            result[key] = dict(target) if isinstance(target, dict) else {"enabled": True}
        return result

    async def set_away_heat_setpoint(self, value: Temperature) -> None:
        """
        Set the away-mode heat setpoint (``awayMode.heatTarget.value``).

        Performs a read-modify-write of the entire ``awayMode`` block:
        the cloud silently rejects partial-nested PATCHes that omit
        ``title``/``activated``/``pgm``/``coolTarget``, so the existing
        block is fetched first and the new value spliced in.

        Args:
            value: A :class:`Temperature` in the 35°F–99°F range.

        Raises:
            InvalidParameterError: If ``value`` is invalid.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        temp_int = self._validate_setpoint(value, "away heat")
        block = await self._load_away_mode_block()
        block[THM_AWAY_HEAT_TARGET][THM_AWAY_TARGET_VALUE] = temp_int
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_AWAY_MODE: block},
        )

    async def set_away_cool_setpoint(self, value: Temperature) -> None:
        """
        Set the away-mode cool setpoint (``awayMode.coolTarget.value``).

        Mirror of :py:meth:`set_away_heat_setpoint` — uses the same
        read-modify-write strategy on the full ``awayMode`` block.

        Args:
            value: A :class:`Temperature` in the 35°F–99°F range.

        Raises:
            InvalidParameterError: If ``value`` is invalid.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        temp_int = self._validate_setpoint(value, "away cool")
        block = await self._load_away_mode_block()
        block[THM_AWAY_COOL_TARGET][THM_AWAY_TARGET_VALUE] = temp_int
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_AWAY_MODE: block},
        )

    async def set_away_heat_cool_setpoints(
        self, heat: Temperature, cool: Temperature
    ) -> None:
        """
        Set both away-mode heat and cool setpoints in a single PATCH.

        Use this for atomic dual-setpoint writes to the away preset to
        avoid the transient inconsistent state two sequential PATCHes
        would produce. Read-modify-write on the full ``awayMode`` block.

        Args:
            heat: Away-side heat ``Temperature`` (35°F–99°F).
            cool: Away-side cool ``Temperature`` (35°F–99°F). Must be
                strictly greater than ``heat``.

        Raises:
            InvalidParameterError: If either value is invalid or
                ``heat >= cool``.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        heat_int = self._validate_setpoint(heat, "away heat")
        cool_int = self._validate_setpoint(cool, "away cool")
        if heat_int >= cool_int:
            _LOGGER.error(
                "THM away heat setpoint (%s°F) must be lower than away cool "
                "setpoint (%s°F).",
                heat_int, cool_int,
            )
            raise InvalidParameterError(
                "THM away heat setpoint must be lower than away cool setpoint."
            )
        block = await self._load_away_mode_block()
        block[THM_AWAY_HEAT_TARGET][THM_AWAY_TARGET_VALUE] = heat_int
        block[THM_AWAY_COOL_TARGET][THM_AWAY_TARGET_VALUE] = cool_int
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{THM_AWAY_MODE: block},
        )

    async def get_active_demands(
        self, device_info: Optional[Dict] = None
    ) -> List[str]:
        """
        Return the active demand flags decoded from the ``dmd`` bitfield.

        Returns a list whose elements are a subset of
        ``["heating", "cooling", "fan"]``. Multiple flags can be set at
        once (e.g. fan plus heating). Prefer this over the cloud's
        ``isHeating`` / ``isCooling`` booleans, which were observed to be
        unreliable: ``isCooling`` reads ``False`` even when the cool-side
        demand is active.

        The bitfield mapping (heat=0x02, cool=0x40, fan=0x80) was
        confirmed against five paired before/after device dumps from a
        live THM-0600 on 2026-04-30.
        """
        info = await self._resolve_device_info(device_info)
        dmd = info.get(THM_DEMAND)
        if not isinstance(dmd, int):
            return []
        active: List[str] = []
        if dmd & THM_DMD_HEAT_BIT:
            active.append("heating")
        if dmd & THM_DMD_COOL_BIT:
            active.append("cooling")
        if dmd & THM_DMD_FAN_BIT:
            active.append("fan")
        return active

    async def _resolve_device_info(
        self, device_info: Optional[Dict] = None
    ) -> Dict:
        """Resolve a passed-in device dict or fetch it from the API."""
        if device_info is not None:
            return device_info
        try:
            fetched = await self.sensorlinx.get_devices(self.building_id, self.device_id)
        except Exception as e:
            _LOGGER.error(f"Exception fetching device info: {e}")
            raise RuntimeError(f"Failed to fetch device info: {e}")
        if not fetched:
            raise RuntimeError("Device info not found.")
        return fetched


class ZonDevice(SensorlinxDevice):
    """
    Parser for HBX ZON-style zone controllers (e.g. ZON-0600).

    A ZON device aggregates one or more THM thermostats and drives 16
    zone relays, plus pumps/fancoil/demands. It does not report room or
    floor temperatures of its own, so :meth:`get_temperatures` is not
    available; use the linked :class:`ThmDevice` instances instead
    (see :meth:`get_thermostat_sync_codes`).

    Most accessors are read-only; setters :meth:`set_app_button` and
    :meth:`set_aux_setpoint` cover the surfaces validated against a live
    install.
    """

    async def get_name(self, device_info: Optional[Dict] = None) -> str:
        """Return the user-assigned controller name (e.g. ``"AZON-0224"``)."""
        return await self._get_device_info_value("name", device_info)

    async def get_relays(
        self, device_info: Optional[Dict] = None
    ) -> List[bool]:
        """Return the 16-element relay state array (booleans)."""
        info = await self._resolve_device_info(device_info)
        block = info.get("relays")
        return [bool(x) for x in block] if isinstance(block, list) else []

    async def get_relay_types(
        self, device_info: Optional[Dict] = None
    ) -> List[int]:
        """Return the ``relType`` configuration array (integers)."""
        info = await self._resolve_device_info(device_info)
        block = info.get("relType")
        return [int(x) for x in block] if isinstance(block, list) else []

    async def get_demands(
        self, device_info: Optional[Dict] = None
    ) -> List[Dict]:
        """ZON demand entries (HD/CD2/APP). Overrides the ECO version."""
        info = await self._resolve_device_info(device_info)
        block = info.get("demands")
        return list(block) if isinstance(block, list) else []

    async def get_pumps(
        self, device_info: Optional[Dict] = None
    ) -> List[Dict]:
        """Pump configuration list (each entry has key/title/value/activated)."""
        info = await self._resolve_device_info(device_info)
        block = info.get("pumps")
        return list(block) if isinstance(block, list) else []

    async def get_fancoil(
        self, device_info: Optional[Dict] = None
    ) -> List[Dict]:
        """Fancoil capability list (heating/cooling/fan/humidity)."""
        info = await self._resolve_device_info(device_info)
        block = info.get("fancoil")
        return list(block) if isinstance(block, list) else []

    async def get_app_button(
        self, device_info: Optional[Dict] = None
    ) -> Dict:
        """Return the ``appButton`` block (enabled/activated/text)."""
        info = await self._resolve_device_info(device_info)
        block = info.get("appButton")
        return block if isinstance(block, dict) else {}

    async def get_aux_setpoint(
        self, device_info: Optional[Dict] = None
    ) -> Dict:
        """Return the ``auxSetpoint`` block."""
        info = await self._resolve_device_info(device_info)
        block = info.get("auxSetpoint")
        return block if isinstance(block, dict) else {}

    async def get_thermostat_sync_codes(
        self, device_info: Optional[Dict] = None
    ) -> List[str]:
        """
        Return the syncCodes of THM devices linked to this zone controller.

        Reads the ``thmInfo`` array and filters out null/empty entries.
        Useful for wiring HA ``via_device`` so child thermostats show up
        underneath their parent zone controller.
        """
        info = await self._resolve_device_info(device_info)
        block = info.get("thmInfo")
        if not isinstance(block, list):
            return []
        return [str(x) for x in block if x]

    async def get_zone_id(
        self, device_info: Optional[Dict] = None
    ) -> Optional[int]:
        """Return the integer ``znID`` zone identifier."""
        info = await self._resolve_device_info(device_info)
        raw = info.get("znID")
        return int(raw) if raw is not None else None

    async def get_sequence(
        self, device_info: Optional[Dict] = None
    ) -> int:
        """
        Return the zone-block sequence offset for this controller.

        The HBX system supports stacking up to five ZON controllers per
        installation: one Primary (zones 1-4) plus up to four Secondary
        units (zones 5-8, 9-12, 13-16, 17-20). Each device's place in
        that stack is reported as an integer 0-4 in the ``sequence``
        block (or, equivalently, as ``znSeq`` at the top level).

        Multiplied by four and added to the relay slot index, this value
        produces the absolute "zone number" the HBX mobile app shows to
        the end user. For a Secondary unit at sequence 1 with relays at
        idx 0/1/2 active, the app calls those Zone 5/6/7.

        Returns 0 (Primary) when the field is absent or unparseable.
        """
        info = await self._resolve_device_info(device_info)
        block = info.get("sequence")
        if isinstance(block, dict):
            raw = block.get("value")
            if isinstance(raw, (int, float)):
                return int(raw)
        raw = info.get("znSeq")
        if isinstance(raw, (int, float)):
            return int(raw)
        return 0

    async def get_temperatures(
        self,
        temp_name: Optional[str] = None,
        device_info: Optional[Dict] = None,
    ) -> Dict:
        """
        ZON controllers do not carry their own temperature sensors.

        Raises :class:`RuntimeError` so callers fall back to reading
        temperatures from the linked :class:`ThmDevice` instances.
        """
        raise RuntimeError(
            "ZON devices do not expose temperatures directly; "
            "use the linked THM devices via get_thermostat_sync_codes()."
        )

    # ------------------------------------------------------------------
    # Setters
    #
    # Field names confirmed via paired before/after device dumps from a live
    # ZON-0600 (firmware 1.32) on 2026-04-26. Toggling ``aBut`` was observed
    # to flip the 12th element of the relay state arrays as a hardware
    # side-effect — that's a server-derived consequence and is not written.
    # ``dhwT`` is the same field used by :class:`SensorlinxDevice` (ECO) for
    # the DHW target setpoint.
    # ------------------------------------------------------------------

    async def set_app_button(self, enabled: bool) -> None:
        """
        Toggle the ZON "app button" (which drives relay 12).

        Args:
            enabled: ``True`` to activate the app button (and relay 12);
                ``False`` to deactivate.

        Raises:
            InvalidParameterError: If ``enabled`` is not a bool.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        if not isinstance(enabled, bool):
            _LOGGER.error("ZON app button must be a boolean (got %r).", type(enabled))
            raise InvalidParameterError("ZON app button must be a boolean.")
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{ZON_APP_BUTTON: 1 if enabled else 0},
        )

    async def set_aux_setpoint(self, value: Temperature) -> None:
        """
        Set the ZON auxiliary heat setpoint.

        Args:
            value: A :class:`Temperature` in the 33°F–180°F range.

        Raises:
            InvalidParameterError: If ``value`` is not a Temperature or is
                outside the safe range.
            LoginError: If authentication fails.
            RuntimeError: If the API call fails for other reasons.
        """
        if not isinstance(value, Temperature):
            _LOGGER.error(
                "ZON aux setpoint must be a Temperature instance (got %r).",
                type(value),
            )
            raise InvalidParameterError(
                "ZON aux setpoint must be a Temperature instance."
            )
        temp_f = value.to_fahrenheit()
        if not (33 <= temp_f <= 180):
            _LOGGER.error(
                "ZON aux setpoint must be between 33°F and 180°F (got %s°F).",
                temp_f,
            )
            raise InvalidParameterError(
                "ZON aux setpoint must be between 33°F and 180°F."
            )
        await self.sensorlinx.patch_device(
            self.building_id,
            self.device_id,
            **{ZON_DHW_TARGET: int(round(temp_f))},
        )

    async def _resolve_device_info(
        self, device_info: Optional[Dict] = None
    ) -> Dict:
        """Resolve a passed-in device dict or fetch it from the API."""
        if device_info is not None:
            return device_info
        try:
            fetched = await self.sensorlinx.get_devices(self.building_id, self.device_id)
        except Exception as e:
            _LOGGER.error(f"Exception fetching device info: {e}")
            raise RuntimeError(f"Failed to fetch device info: {e}")
        if not fetched:
            raise RuntimeError("Device info not found.")
        return fetched


def device_for(
    sensorlinx: Sensorlinx,
    building_id: str,
    device_info: Dict,
) -> SensorlinxDevice:
    """
    Build the appropriate device wrapper for a raw device payload.

    Inspects ``deviceType`` in the payload and returns a :class:`ThmDevice`,
    :class:`ZonDevice`, or :class:`SensorlinxDevice` (the historical ECO
    parser). Unknown device types fall back to :class:`SensorlinxDevice`
    so callers still get firmware/sync_code/name accessors.

    Args:
        sensorlinx: The authenticated API client.
        building_id: The parent building id (used for nested API calls).
        device_info: A device dict as returned by
            :meth:`Sensorlinx.get_devices` (must contain ``deviceType`` and
            either ``syncCode`` or ``id``/``_id``).

    Returns:
        A :class:`SensorlinxDevice` (or subclass) bound to the device id.
    """
    if not isinstance(device_info, dict):
        raise TypeError("device_info must be a dict from get_devices().")
    device_id = (
        device_info.get("syncCode")
        or device_info.get("id")
        or device_info.get("_id")
    )
    if not device_id:
        raise ValueError("device_info is missing syncCode/id/_id.")
    dtype = (device_info.get(DEVICE_TYPE) or "").upper()
    if dtype == DEVICE_TYPE_THM:
        return ThmDevice(sensorlinx, building_id, device_id)
    if dtype == DEVICE_TYPE_ZON:
        return ZonDevice(sensorlinx, building_id, device_id)
    return SensorlinxDevice(sensorlinx, building_id, device_id)

