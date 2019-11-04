# -*- coding: utf-8 -*-
# Module: default
# Author: cache-sk
# Created on: 4.11.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import os
import sys
import requests
import json

HEADERS = {
    'Origin':'https://www.rebit.tv',
    'Referer':'https://www.rebit.tv',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'
}
CLIENT = {'title':'Firefox 70.0 on Windows 10','type':'computer'}

API = 'https://api.client.rebit.sk/'

class RebitTvException(Exception):
    def __init__(self, id):
        self.id = id


class UserNotDefinedException(RebitTvException):
    def __init__(self):
        self.id = 30501

class UserInvalidException(RebitTvException):
    def __init__(self):
        self.id = 30502

class RebitTvChannel:
    id = ''
    channel = None
    icon = ''
    title = ''
    stream = ''

    def __init__(self, id, channel, icon, title, stream):
        self.id = id
        self.channel = channel
        self.icon = icon
        self.title = title
        self.stream = stream
    

class RebitTvAuthData:
    access_token = ''
    expire_in = None
    refresh_token = ''
    user_id = ''
    client_id = ''


    def is_populated(self):
        return (self.access_token != '' and
                self.refresh_token != '' and
                self.expire_in is not None and
                self.user_id != '' and
                self.client_id != '')

    def is_valid(self):
        return self.is_populated()
        #TODO refresh token!

    def clear(self):
        self.access_token = ''
        self.expire_in = None
        self.refresh_token = ''
        self.user_id = ''
        self.client_id = ''


class RebitTv:
    _username = ''
    _password = ''
    _storage_path = ''
    _storage_file = ''
    _session = requests.Session()
    _data = RebitTvAuthData()

    def __init__(self, username, password, storage_dir):
        self._username = username
        self._password = password
        self._storage_path = storage_dir
        self._storage_file = os.path.join(self._storage_path, '%s.session' % username.lower())
        self._load_session()

    def _store_session(self):
        if not os.path.exists(self._storage_path):
            os.makedirs(self._storage_path)
        with open(self._storage_file, 'w') as f:
            json.dump(self._data.__dict__, f)

    def _load_session(self):
        if os.path.exists(self._storage_file):
            with open(self._storage_file, 'r') as f:
                self._data.__dict__ = json.load(f)

    def _auth(self):

        if self._data.is_valid():
            return

        if (self._username == '') or (self._password == ''):
            raise UserNotDefinedException

        self._data.clear()

        session = requests.Session()
        headers = {'Content-Type':'application/json;charset=utf-8'}
        headers.update(HEADERS)
        payload = {'password':self._password,'username':self._username}
        resp = session.post(API + 'auth/auth', json=payload, headers=headers)
        
        if resp.status_code != 200:
            raise UserInvalidException

        data = resp.json()['data']
        self._data.access_token = data['access_token']
        self._data.expire_in = data['expire_in']
        self._data.refresh_token = data['refresh_token']
        self._data.user_id = data['user_id']

        del headers['Content-Type']
        headers.update({'Authorization':'Bearer ' + self._data.access_token})
        
        resp = session.post(API + 'television/client', json=CLIENT, headers=headers)
        data = resp.json()['data']
        self._data.client_id = data['id']

        self._store_session()
    
    def _login(self):
        if not self._data.is_valid():
            self._reconnect()

    def _reconnect(self):
        self._data.clear()
        self._auth()

    def getHeaders(self):
        self._login()
        headers = {'Authorization':'Bearer ' + self._data.access_token, 'X-Client-ID':self._data.client_id}
        headers.update(HEADERS)
        return headers

    def getChannels(self):
        self._login()
        resp = self._session.get(API + 'television/channels', headers=self.getHeaders())
        data = resp.json()['data']
        channels = []
        for item in data:
            for s in item['streams']:
                if s['quality'] == 'dynamic':
                    stream = s['link']
                    break
            if stream:
                channel = RebitTvChannel(
                    item['id'],
                    int(item['channel']),
                    item['icon'],
                    item['title'],
                    stream)
                channels.append(channel)

        channels = sorted(channels, key = lambda i: i.channel)
        return channels
