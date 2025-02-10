import pytest
import aiohttp
from aioresponses import aioresponses
from pyomnisense.omnisense import Omnisense, LOGIN_URL

@pytest.mark.offline
@pytest.mark.asyncio
async def test_successful_login():
    omnisense = Omnisense()
    username = "testuser"
    password = "testpass"
    # Simulate a successful login returning text that does not indicate failure.
    with aioresponses() as m:
        m.post(LOGIN_URL, status=200, body="Welcome to your dashboard")
        result = await omnisense.login(username, password)
        assert result is True
        await omnisense.close()

@pytest.mark.offline
@pytest.mark.asyncio
async def test_failed_login_response_status():
    omnisense = Omnisense()
    username = "testuser"
    password = "wrongpass"
    # Simulate a failed login with non-200 status.
    with aioresponses() as m:
        m.post(LOGIN_URL, status=401, body="Unauthorized")
        with pytest.raises(Exception) as excinfo:
            await omnisense.login(username, password)
        assert "Login failed" in str(excinfo.value)

@pytest.mark.offline
@pytest.mark.asyncio
async def test_failed_login_invalid_text():
    omnisense = Omnisense()
    username = "testuser"
    password = "wrongpass"
    # Simulate a failed login with a 200 status but response text indicating failure.
    with aioresponses() as m:
        m.post(LOGIN_URL, status=200, body="User Log-In")
        with pytest.raises(Exception) as excinfo:
            await omnisense.login(username, password)
        assert "Login failed" in str(excinfo.value)

@pytest.mark.offline
@pytest.mark.asyncio
async def test_no_credentials_provided():
    omnisense = Omnisense()
    # Calling login without credentials should raise an Exception.
    with pytest.raises(Exception) as excinfo:
        await omnisense.login()
    assert "No username or password provided." in str(excinfo.value)

@pytest.mark.offline
@pytest.mark.asyncio
async def test_close_session():
    omnisense = Omnisense()
    # Manually create an aiohttp session to simulate an active session.
    omnisense._session = aiohttp.ClientSession()
    await omnisense.close()
    assert omnisense._session is None