from urllib.parse import urljoin
import time

import aiohttp


class Client:
    def __init__(self, api_url, username, password):
        self._session = aiohttp.ClientSession()
        self._token = None
        self._info = None
        self._api_url = api_url
        self._username = username
        self._password = password

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        await self._session.close()
        self._session = None

    async def get_info(self):
        if not self._info:
            response = await self._session.get(urljoin(self._api_url, 'v2/info'))
            self._info = await response.json()

        return self._info

    async def authenticate(self):
        """ Request a token from service """
        headers = {
            'accept': 'application/json',
            'authorization': 'Basic Y2Y6',
        }

        params = {
            'username': self._username,
            'password': self._password,
            'grant_type': 'password'
        }

        token_endpoint = (await self.get_info())['token_endpoint']

        response = await self._session.post(
            urljoin(token_endpoint, '/oauth/token'),
            headers=headers,
            params=params
        )

        self._token = await response.json()
        self._token['time_stamp'] = time.time()

    async def ensure_valid_token(self):
        if not self._token or time.time() - self._token['time_stamp'] > self._token['expires_in']:
            await self.authenticate()

    def get_auth_headers(self):
        return {
            'authorization': 'bearer ' + self._token['access_token']
        }

    async def get_json(self, path, params):
        await self.ensure_valid_token()

        response = await self._session.get(urljoin(self._api_url, path), params=params, headers=self.get_auth_headers())
        return await response.json()

    async def get_events(self, filters=None):
        return await self.get_json('/v2/events', filters)
