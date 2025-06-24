import pytest
import os
from pysensorlinx import Sensorlinx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("SENSORLINX_EMAIL") or not os.getenv("SENSORLINX_PASSWORD"),
    reason="SENSORLINX_EMAIL or SENSORLINX_PASSWORD environment variable not set"
)
@pytest.mark.asyncio
async def test_live_login_and_fetch_data():
    sensorlinx = Sensorlinx()
    username = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")

    assert username is not None, "SENSORLINX_EMAIL is not set"
    assert password is not None, "SENSORLINX_PASSWORD is not set"

    result = await sensorlinx.login(username, password)
    assert result is True, "Login failed"

    await sensorlinx.close()
    
  
    
    
    
    