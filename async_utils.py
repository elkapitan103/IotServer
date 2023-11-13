import asyncio
from data_ops import connect_to_gateway

def run_async(func, *args):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        result = new_loop.run_until_complete(func(*args))
        new_loop.close()
    else:
        result = loop.run_until_complete(func(*args))
    return result

# Usage in services.py
from async_utils import run_async
# ... other imports ...

def get_sensor_data():
    return run_async(connect_to_gateway)
