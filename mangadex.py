# -*- coding: utf8 -*-
from requests_toolbelt import sessions
import functools
import aiohttp
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
        self.session = sessions.BaseUrlSession(base_url=self.url)
        self._get_token()

    def _get_token(self) -> None:

        try:
            with open('token.json', 'r') as f:
                token = json.load(f)
                self.token = token["token"]["session"]
                self.refresh_token = token["token"]["refresh"]
                self.session.headers.update(
                    {"Authorization": self.token})
                if not self._auth_check():
                    self._refresh_token()
        except json.JSONDecodeError:
            self._login()

    def _auth_check(self) -> bool:
        response = self.session.get(self.url+'/auth/check')
        return response.json().get('isAuthenticated')

    def _logout(self):
        response = self.session.post(self.url+'/auth/logout')
        if response.status_code == 200:
            return True
        elif response.status_code == 503:
            return response.json()

    def _refresh_token(self):
        url = self.url+'/auth/refresh'
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        kwargs = {
            'token': self.refresh_token
        }
        response = self.session.post(
            url, headers=headers, data=json.dumps(kwargs))
        if response.status_code == 200:
            return self._store_token(response)
        elif response.status_code == 401:
            return self._login()
        else:
            return response.json()

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
        if response.status_code == 200:
            return self._store_token(response)
        else:
            return response.json()

    def _store_token(self, response):
        resp = response.json()
        with open('token.json', 'w') as f:
            f.write(json.dumps(resp))
        self.session.headers.update(
            {"Authorization": resp["token"]["session"]})

    def _request(self, method: str, path: str, **params):
        url = self._get_request_url(path)
        kwargs = {'params': params} if method == 'GET' else {'json': params}
        response = self.session.request(method, url, **kwargs)
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

    def _get_request_url(self, path):
        return self.url + path

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


