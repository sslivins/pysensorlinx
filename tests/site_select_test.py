import os
import pytest
from aioresponses import aioresponses
from pyomnisense.omnisense import Omnisense, LOGIN_URL, SITE_LIST_URL

@pytest.mark.asyncio
async def test_get_site_list():
    site_file_path = os.path.join(os.path.dirname(__file__), "samples", "site_list.html")
    
    with open(site_file_path, "r", encoding="utf-8") as f:
        site_html = f.read()
    
    omnisense = Omnisense()
    
    # Use a single aioresponses context to fake both login and site select requests
    with aioresponses() as m:
        # Fake successful login response
        m.post(LOGIN_URL, status=200, body="Logged In!")
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