# pysensorlinx

pysensorlinx is a Python library for accessing Sensor Linx sensor data directly from their webservice. It supports logging into the service, retrieving sites list, and setting and getting device data used to control devices such as heat pumps, etc.

## Features

- Login to sensor linx account
- retrieve the user profile
- get the list of buildings
- get the list of devices
- get and set device parameters for a specific device

## Install this repo

Clone the repository and install in editable mode:

```bash
git clone https://github.com/your_username/pysensorlinx.git
cd pysensorlinx
```

### Create and activate a virtual environment

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Once the virtual environment is activated, install the package in editable mode:

```bash
pip install -e .
```

## Install from pypi.org

```bash
pip install pysensorlinx
```

## Usage

```python
from pysensorlinx import Omnisense

async def main():
    sensorlinx = Sensorlinx()
    # Login with your credentials
    await sensorlinx.login("your_username", "your_password")
    

    
    # When done, close the session
    await sensorlinx.close()

import asyncio
asyncio.run(main())
```

Replace `"your_username"` and `"your_password"` with your actual Sensorlinx credentials. For more details, refer to the documentation or explore the source code.

## Testing
Tests are written using pytest and pytest-asyncio. You can run tests as follows:

```bash
pip install -e .[tests]

pytest
