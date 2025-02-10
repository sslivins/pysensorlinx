# pyomnisense

pyomnisense is a Python library for accessing Omnisense sensor data directly from the omnisense.com website. It supports logging into the service, retrieving site lists, and fetching sensor data.

## Features

- Login to the Omnisense website
- Retrieve a list of sites with sensor data
- Fetch detailed sensor data for a selected site
- Asynchronous methods using aiohttp

## Install this repo

Clone the repository and install in editable mode:

```bash
git clone https://github.com/your_username/pyomnisense.git
cd pyomnisense
pip install -e .
```

## Install from pypi.org

```bash
pip install pyomnisense
```

## Usage

```python
from pyomnisense import Omnisense

async def main():
    omnisense = Omnisense()
    # Login with your credentials
    await omnisense.login("your_username", "your_password")
    
    # Get list of sites
    sites = await omnisense.get_site_list()
    print("Available sites:", sites)

    sensor_data = await omnisense.get_sensor_data(sites)

    print("Sensor Data for Site:", sensor_data)
    
    # When done, close the session
    await omnisense.close()

import asyncio
asyncio.run(main())
```

Replace `"your_username"` and `"your_password"` with your actual Omnisense credentials. For more details, refer to the documentation or explore the source code.

## Testing
Tests are written using pytest and pytest-asyncio. You can run tests as follows:

pytest
