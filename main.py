import os
import asyncio
import datetime as dt
import logging
import json

from aiohttp import web
from aioprometheus import Counter, Gauge, Service, Summary, timer

from raven import Client
from raven_aiohttp import AioHttpTransport

from cf_client import Client

from dotenv import load_dotenv
load_dotenv()


CF_USERNAME = os.getenv('CF_USERNAME')
CF_PASSWORD = os.getenv('CF_PASSWORD')
CF_ENDPOINT = os.getenv('CF_ENDPOINT')
SENTRY_DSN = os.getenv('SENTRY_DSN')
SCRAPE_DELAY = int(os.getenv('SCRAPE_DELAY', 10))
PORT = os.getenv('PORT', 3000)

PROM_CLOUDFOUNDRY_EVENT = Counter('cf_event', 'a count of the number of cloudfoundry events')

logger = logging.getLogger('event-log-proxy')


async def start_webapp(port):
    prometheus_service = Service()
    prometheus_service.register(PROM_CLOUDFOUNDRY_EVENT)

    app = web.Application()
    app.add_routes([web.get('/check', lambda _: web.Response(text='OK')),
                    web.get('/metrics', prometheus_service.handle_metrics)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()


async def main():
    from_time = dt.datetime.utcnow() - dt.timedelta(minutes=10)

    async with Client(CF_ENDPOINT, CF_USERNAME, CF_PASSWORD) as client:
        while True:
            logger.debug('Checking for events ...')

            curr_time = dt.datetime.utcnow()

            filters = {
                'results-per-page': 20,
                'q': f'timestamp>{from_time}'
            }

            async for event in client.get_events(filters):
                print(json.dumps(event))
                PROM_CLOUDFOUNDRY_EVENT.inc({'type': event['entity']['type']})

            from_time = curr_time
            await asyncio.sleep(10)


def custom_exception_handler(loop, context):
    loop.default_exception_handler(context)

    print(context)
    loop.stop()


if __name__ == '__main__':
    if SENTRY_DSN:
        sentry_client = Client(SENTRY_DSN, ransport=AioHttpTransport)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        loop.create_task(main()),
        loop.create_task(start_webapp(PORT))
    ))
    loop.close()
