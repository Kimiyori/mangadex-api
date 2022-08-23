
# import aiohttp
# import asyncio

# async def main():
#     #headers={"Authorization": "Basic bG9naW46cGFzcw=="}
#     async with aiohttp.ClientSession() as session:
#         async with session.get('https://api.mangadex.org/manga/34f72e29-1bda-40df-ae93-0e1c32d96ea6') as r:
#             print(r.status)
#             print(await r.text())

# asyncio.run(main())

from requests_toolbelt import sessions
import functools
import aiohttp
import asyncio
import json
import time as t
from requests.structures import CaseInsensitiveDict
from aiohttp import ClientSession


class ApiWrapper:
    """
    Class for handling login and and requests
    """
    _URL = 'https://api.mangadex.org'

    def __init__(self,
                 username: str,
                 email: str,
                 password: str):
        self.url = self._URL
        self.username = username
        self.email = email
        self.password = password
        self.token = None
        self.refresh_token = None
        self.session = aiohttp.ClientSession(
            base_url=self.url, raise_for_status=True)
        # self._get_token()

    async def _get_token(self) -> None:

        try:
            with open('token.json', 'r') as f:
                token = json.load(f)
                self.token = token["token"]["session"]
                self.refresh_token = token["token"]["refresh"]
                self.session.headers.update(
                    {"Authorization": self.token})
                check = await self._auth_check()
                if not check:
                    await self._refresh_token()
        except json.JSONDecodeError as e:
            raise e
            #await self._login()

    async def _auth_check(self) -> bool:
        async with self.session.get('/auth/check') as response:
            t = await response.json()
            print(t)
            r = t.get('isAuthenticated')
            return r

    def _logout(self):
        response = self.session.post(self.url+'/auth/logout')
        if response.status == 200:
            return True
        elif response.status == 503:
            return response.json()

    async def _refresh_token(self):
        url = self.url+'/auth/refresh'
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        kwargs = {
            'token': self.refresh_token
        }
        async with self.session.post(
                '/auth/refresh',
                headers=headers,
                data=json.dumps(kwargs)) as response:

            if response.status == 200:
                await self._store_token(response)
            elif response.status == 401:
                return self._login()
            else:
                return response.json()

    async def close(self) -> None:
        return await self.session.close()

    def _login(self):
        url = self.url+'/auth/login'
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        kwargs = {
            "username": self.username,
            "email": self.email,
            "password": self.password
        }

        response = self.session.post(
            url, headers=headers, data=json.dumps(kwargs))
        if response.status == 200:
            return self._store_token(response)
        else:
            return response.json()

    async def _store_token(self, response):
        resp = await response.json()
        with open('token.json', 'w') as f:
            f.write(json.dumps(resp))
        self.session.headers.update(
            {"Authorization": resp["token"]["session"]})

    async def _request(self, method: str, path: str, **params):
        await self._get_token()
        url = self._get_request_url(path)
        kwargs = {'params': params} if method == 'GET' else {'json': params}
        async with self.session.request(method, url, **kwargs) as response:
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                self._refresh_token()
                return self.session.request(method, url, **kwargs).json()
            elif response.status_code == 429:
                print('Please wait')
                t.sleep(30)
                return self.session.request(method, url, **kwargs)
            else:
                return response.json()

    async def _get_request_url(self, path):
        return self.url + path

    async def close(self) -> None:
        return await self._client.close()

    def get_api(self) -> 'ApiMethod':
        return ApiMethod(self)


class ApiMethod:
    """
    Api method for for call handling
    """
    _HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE']

    def __init__(self, session: ApiWrapper, path: str = '') -> None:
        self._session = session
        self._path = path

    def __call__(self, item: str):
        new_path = self._path + '/' + str(item)
        return ApiMethod(self._session, new_path)

    def __getattr__(self, item: str):
        if item in self._HTTP_METHODS:
            return functools.partial(self._session._request, item, self._path)
        new_path = self._path + '/' + item
        return ApiMethod(self._session, new_path)

# api=ApiWrapper('Kimiyori', 'maksimkalin@mail.ru', 'maxmax17').get_api()
# manga=api.manga('34f72e29-1bda-40df-ae93-0e1c32d96ea6').GET()


async def fetch():
    client = ApiWrapper('Kimiyori', 'maksimkalin@mail.ru',
                        'maxmax17')
    api=client.get_api()
    try:
        posts = await api.manga('34f72e29-1bda-40df-ae93-0e1c32d96ea6').GET()
        print(posts)
    finally:
        client.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(fetch())
