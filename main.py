import os
import asyncio
from cf_client import Client

from dotenv import load_dotenv
load_dotenv()

CF_USERNAME = os.getenv('CF_USERNAME')
CF_PASSWORD = os.getenv('CF_PASSWORD')
CF_ENDPOINT = os.getenv('CF_ENDPOINT')

async def main():
    loop = asyncio.get_event_loop()

    async with Client(CF_ENDPOINT, CF_USERNAME, CF_PASSWORD) as client:
        events = await client.get_events()
        import pdb; pdb.set_trace()
        print(events)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    loop.run_until_complete(task)
    loop.close()
