import os
import pytest
from aioresponses import aioresponses
from pyomnisense.omnisense import Omnisense, LOGIN_URL, SITE_LIST_URL, HOST_URL

@pytest.mark.offline
@pytest.mark.asyncio
async def test_get_site_list():
    site_file_path = os.path.join(os.path.dirname(__file__), "samples", "site_list.html")
    
    with open(site_file_path, "r", encoding="utf-8") as f:
        site_html = f.read()
    
    omnisense = Omnisense()
    
    set_cookie_value = "ASP.NET_SessionId=abc123; Path=/; HttpOnly"
    redirect_location = "/site_select.asp"    
    
    # Use aioresponses context to fake all external HTTP calls.
    with aioresponses() as m:
        # Mock the POST to LOGIN_URL with Set-Cookie and Location headers
        m.post(
            LOGIN_URL,
            status=302,
            headers={
                "Set-Cookie": set_cookie_value,
                "Location": redirect_location,
            },
            body="",
        )
        # Mock the GET to the redirect location with the manual Cookie header
        m.get(
            f"{HOST_URL}{redirect_location}",
            status=200,
            body="Welcome to your dashboard",
        )
        # Fake site list GET request response with the sample HTML content
        m.get(SITE_LIST_URL, status=200, body=site_html)
        
        # Call login, which will hit the faked LOGIN_URL endpoint
        login_result = await omnisense.login("testuser", "testpass")
        assert login_result is True

        # Now call get_site_list which will hit the faked SITE_LIST_URL endpoint
        result = await omnisense.get_site_list()
        
        # Close the session to clean up
        await omnisense.close()
        
        # Assert that the result matches the expected dict
        expected_result = {'123456': 'MySite', '654321': 'FirstSite'}
        assert result == expected_result