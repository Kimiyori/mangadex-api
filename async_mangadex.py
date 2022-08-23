
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
import time

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
            base_url=self.url)

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
        except json.JSONDecodeError:
            await self._login()

    async def _auth_check(self) -> bool:
        response= await self.session.get('/auth/check') 
        t = await response.json()
        r = t.get('isAuthenticated')
        return r

    async def _logout(self):
        response = await self.session.post(self.url+'/auth/logout')
        if response.status == 200:
            return True
        elif response.status == 503:
            return response.json()

    async def _refresh_token(self):
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        kwargs = {
            'token': self.refresh_token
        }
        response= await self.session.post(
                '/auth/refresh',
                headers=headers,
                data=json.dumps(kwargs)) 

        if response.status == 200:
            await self._store_token(response)
        elif response.status == 401:
            return self._login()
        else:
            return response.json()

    async def close(self) -> None:
        return await self.session.close()

    async def _login(self):
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        kwargs = {
            "username": self.username,
            "email": self.email,
            "password": self.password
        }

        response= await self.session.post(
            '/auth/login', headers=headers, data=json.dumps(kwargs))
        if response.status == 200:
            await self._store_token(response)
        else:
            return response

    async def _store_token(self, response):
        resp = await response.json()
        with open('token.json', 'w') as f:
            f.write(json.dumps(resp))
        self.session.headers.update(
            {"Authorization": resp["token"]["session"]})

    async def _request(self, method: str, path: str, **params):
        kwargs = {'params': params} if method == 'GET' else {'json': params}
        response= await self.session.request(method, path, **kwargs)
        status = response.status
        if status == 200:
            json=await response.json()
            return json
        elif status == 401:
            await self._refresh_token()
            return await self._request(method, path, **params)
        elif status == 429:
            print('Please wait')
            await asyncio.sleep(30)
            return await self._request(method, path, **params)
        else:
            return response

    async def _get_request_url(self, path):
        return self.url + path

    async def close(self) -> None:
        return await self.session.close()

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



