# -*- coding: utf-8 -*-
# Module: default
# Author: cache-sk
# Created on: 4.11.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import os
import io
import sys
import requests
import json
import time, datetime

HEADERS = {
    'Origin':'https://www.rebit.tv',
    'Referer':'https://www.rebit.tv',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'
}
CLIENT = {'title':'Firefox 70.0 on Windows 10','type':'computer'}

API = 'https://api.client.rebit.sk/'

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}

def html_escape(text, table=html_escape_table):
    return "".join(table.get(c, c) for c in text)


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
    adaptive = ''
    best = ''

    def __init__(self, id, channel, icon, title, adaptive, best):
        self.id = id
        self.channel = channel
        self.icon = icon
        self.title = title
        self.adaptive = adaptive
        self.best = best
    
class RebitTvProgramme:
    #id = ''
    title = ''
    subtitle = ''
    description = ''
    start = None
    stop = None

    def __init__(self, title, subtitle, description, start, stop):
        #self.id = id
        self.title = title
        self.subtitle = subtitle
        self.description = description
        self.start = start
        self.stop = stop

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

        headers = {'Content-Type':'application/json;charset=utf-8'}
        headers.update(HEADERS)
        payload = {'password':self._password,'username':self._username}
        resp = self._session.post(API + 'auth/auth', json=payload, headers=headers)
        
        if resp.status_code != 200:
            raise UserInvalidException

        data = resp.json()['data']
        self._data.access_token = data['access_token']
        self._data.expire_in = data['expire_in']
        self._data.refresh_token = data['refresh_token']
        self._data.user_id = data['user_id']

        del headers['Content-Type']
        headers.update({'Authorization':'Bearer ' + self._data.access_token})
        
        resp = self._session.post(API + 'television/client', json=CLIENT, headers=headers)
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
    
    def getRequestsSession(self):
        self._login()
        return self._session
        
    def getChannels(self):
        self._login()
        resp = self._session.get(API + 'television/channels', headers=self.getHeaders())
        data = resp.json()['data']
        channels = []
        for item in data:
            adaptive = None
            best = None
            fhd = None
            hd = None
            sd = None
            other = None
            for s in item['streams']:
                if s['quality'] == 'dynamic':
                    adaptive = s['link']
                elif s['quality'] == '1080p':
                    fhd = s['link']
                elif s['quality'] == '720p':
                    hd = s['link']
                elif s['quality'] == '432p':
                    sd = s['link']
                else:
                    other = s['link']
            if fhd is not None:
                best = fhd
            elif hd is not None:
                best = hd
            elif sd is not None:
                best = sd
            elif other is not None:
                best = other
            if adaptive or best:
                channel = RebitTvChannel(
                    item['id'],
                    int(item['channel']),
                    item['icon'],
                    item['title'],
                    adaptive, best)
                channels.append(channel)

        channels = sorted(channels, key = lambda i: i.channel)
        return channels

    def getChannelGuide(self, channelId):
        self._login()
        resp = self._session.get(API + 'television/channels/'+channelId+'/programmes', headers=self.getHeaders())
        data = resp.json()['data']
        programmes = []
        for item in data:
            programme = RebitTvProgramme(
                item['title'] if 'title' in item and item['title'] else '',
                item['subtitle'] if 'subtitle' in item and item['subtitle'] else '',
                item['description'] if 'description' in item and item['description'] else '',
                datetime.datetime(*(time.strptime(item['start'], DATETIME_FORMAT)[0:6])) if 'start' in item and item['start'] else None,
                datetime.datetime(*(time.strptime(item['stop'], DATETIME_FORMAT)[0:6])) if 'stop' in item and item['stop'] else None)
                #datetime.datetime.strptime(item['stop'], DATETIME_FORMAT)
            programmes.append(programme)
        return programmes

    def generate(self, playlist, guide):
        print 'Generating rebit tv'
        after = datetime.datetime.now() - datetime.timedelta(days=1)
        before = after + datetime.timedelta(days=8)
        with io.open(playlist, 'w', encoding='utf8') as m3u:
            with io.open(guide, 'w', encoding='utf8') as xml:
                m3u.write(u'#EXTM3U\n')
                xml.write(u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
                xml.write(u'<tv>\n')
                
                channels = self.getChannels()
                for c in channels:
                    m3u.write(u'#EXTINF:-1 tvg-id="%s" tvg-logo="%s" tvg-name="%s",%s\n' % (c.id, c.icon, c.title, html_escape(c.title,{',':'-'})))
                    m3u.write(u'plugin://plugin.video.rebit.tv/?action=play&cid=%s\n' % (c.id))
                    xml.write(u'<channel id="%s">\n' % c.id)
                    xml.write(u'<display-name>%s</display-name>\n' % c.title)
                    xml.write(u'</channel>\n')
                for c in channels:
                    programmes = self.getChannelGuide(c.id)
                    for e in programmes:
                        if e.start is not None and e.stop is not None and e.start < before and e.stop > after:
                            xml.write(u'<programme channel="%s" start="%s" stop="%s">\n' % (c.id, e.start.strftime('%Y%m%d%H%M%S'), e.stop.strftime('%Y%m%d%H%M%S')))
                            xml.write(u'<title>%s</title>\n' % html_escape(e.title))
                            xml.write(u'<desc>%s</desc>\n' % html_escape(e.description
                            ))
                            xml.write(u'</programme>\n')
                m3u.write(u'#EXT-X-ENDLIST\n')
                xml.write(u'</tv>\n')
