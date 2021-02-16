# -*- coding: utf-8 -*-
# Module: default
# Author: cache-sk
# Created on: 4.11.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import os
import io
import sys
import random
import requests
import json
import time, datetime
import _strptime
import xbmc, platform

HEADERS = {
    'Origin':'https://www.rebit.tv',
    'Referer':'https://www.rebit.tv',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'
}
try:
    client = "Kodi " + xbmc.getInfoLabel("System.BuildVersion").split(" ")[0] + "; " + platform.system() + " " + platform.release()
except:
    client = "Kodi"
CLIENT = {'title':client,'type':'computer','child-lock-code':'0000'}

API = 'https://bbxnet.api.iptv.rebit.sk/'

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

class FolderNotExistException(RebitTvException):
    def __init__(self):
        self.id = 30503

class RebitTvChannel:
    id = ''
    channel = None
    icon = ''
    title = ''
    guide = False

    def __init__(self, id, channel, icon, title, guide):
        self.id = id
        self.channel = channel
        self.icon = icon
        self.title = title
        self.guide = guide
    
class RebitTvPlay:
    id = ''
    cid = ''
    link = ''
    protocol = ''
    quality = ''

    def __init__(self, id, cid, link, protocol, quality):
        self.id = id
        self.cid = cid
        self.link = link
        self.protocol = protocol
        self.quality = quality
        
    def __str__(self):
        return "[id=%s, cid=%s, link=%s, protocol=%s, quality=%s]" % (self.id,self.cid,self.link,self.protocol,self.quality)
    
class RebitTvProgramme:
    id = ''
    title = ''
    subtitle = ''
    description = ''
    start = None
    stop = None

    def __init__(self, id, title, subtitle, description, start, stop):
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
        if self.is_populated():
            return time.time() < self.expire_in
        return False

    def clear(self):
        self.access_token = ''
        self.expire_in = None
        self.refresh_token = ''
        self.user_id = ''
        self.client_id = ''


class RebitTv:
    _username = ''
    _password = ''
    _remove_oldest = False
    _remove_oldest_kodi = False
    _choose_device = None
    _storage_path = ''
    _storage_file = ''
    _session = requests.Session()
    _data = RebitTvAuthData()

    def __init__(self, username, password, storage_dir, remove_oldest, remove_oldest_kodi, choose_device):
        self._username = username
        self._password = password
        self._remove_oldest = remove_oldest
        self._remove_oldest_kodi = remove_oldest_kodi
        self._choose_device = choose_device
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
        if self._data.is_populated():
            if self._data.is_valid():
                return
            else:
                self._refresh_token()
                if self._data.is_valid():
                    return

        if (self._username == '') or (self._password == ''):
            raise UserNotDefinedException

        self._data.clear()
        
        now = time.time()

        headers = {'Content-Type':'application/json;charset=utf-8'}
        headers.update(HEADERS)
        payload = {'password':self._password,'username':self._username}
        resp = self._session.post(API + 'auth/auth', json=payload, headers=headers)
        
        if resp.status_code != 200:
            raise UserInvalidException

        data = resp.json()['data']
        self._data.access_token = data['access_token']
        self._data.expire_in = now + int(data['expire_in'])
        self._data.refresh_token = data['refresh_token']
        self._data.user_id = data['user_id']

        del headers['Content-Type']
        headers.update({'Authorization':'Bearer ' + self._data.access_token})
        #need client ID, remove oldest clients until it works
        clientId = None
        
        while clientId is None:
            resp = self._session.post(API + 'television/client', json=CLIENT, headers=headers)
            try:
                #print(resp.content)
                data = resp.json()['data']
                clientId = data['id']
            except Exception as e:
                #too many devices?!
                resp = self._session.get(API + 'television/clients', headers=headers)
                clients = resp.json()['data']
                oldest = None
                if self._remove_oldest:
                    oldestKodi = None
                    for client in clients:
                        if oldest is None:
                            oldest = client
                        else:
                            ot = oldest['updated_at'] if 'updated_at' in oldest and oldest['updated_at'] else (oldest['created_at'] if 'created_at' in oldest and oldest['created_at'] else None)
                            ct = client['updated_at'] if 'updated_at' in client and client['updated_at'] else (client['created_at'] if 'created_at' in client and client['created_at'] else None)
                            if ct is not None:
                                ct = datetime.datetime.fromtimestamp(ct)
                                if ot is not None:
                                    ot = datetime.datetime.fromtimestamp(ot)
                                    if ct < ot:
                                        oldest = client
                                        if 'title' in client and 'Kodi' in client['title']:
                                            oldestKodi = client
                            else:
                                oldest = client
                                if 'title' in client and 'Kodi' in client['title']:
                                    oldestKodi = client
                    if self._remove_oldest_kodi and oldestKodi is not None:
                        oldest = oldestKodi
                else:
                    oldest = self._choose_device(clients)
                    
                resp = self._session.delete(API + 'television/clients/'+oldest['id'], json=CLIENT, headers=headers)
                time.sleep(1)

        self._data.client_id = clientId
        
        self._store_session()
        
    def _refresh_token(self):
        try:
            #print 'refreshing token'
            now = time.time()
            headers = {
                'Content-Type':'application/json;charset=utf-8',
                'Authorization':'Bearer ' + self._data.refresh_token
            }
            headers.update(HEADERS)
            resp = self._session.post(API + 'auth/auth', headers=headers)
            
            #if resp.status_code != 200:
            #    raise UserInvalidException
            
            data = resp.json()['data']
            self._data.access_token = data['access_token']
            self._data.expire_in = now + int(data['expire_in'])
            self._data.refresh_token = data['refresh_token']
            self._data.user_id = data['user_id']
            
            self._store_session()
        except:
            #probably 403, data not in response
            self._data.clear()
    
    def _reconnect(self):
        self._data.expire_in = 0
        self._auth()
    
    
    def _get(self, url, params={}, dheaders={}, slow=False):
        doIt = True
        while doIt:
            headers = {}
            headers.update(dheaders)
            headers.update(self.getHeaders())
            resp = self._session.get(url, params=params, headers=headers)
            #print(resp.content)
            data = resp.json()
            if 'message' in data and data['message'] == 'Too Many Attempts.':
                if slow:
                    time.sleep(random.randint(6,9) + random.random())
                else:
                    time.sleep(random.randint(1,2) + random.random())
            elif ('code' in data and data['code'] == 403) or ('message' in data and data['message'] == 'The access token is invalid.'):
                self._reconnect()
            else:
                return data

    def getHeaders(self):
        self._auth()
        headers = {'Authorization':'Bearer ' + self._data.access_token, 'x-television-client-id':self._data.client_id, 'x-child-lock-code':'0000'}
        headers.update(HEADERS)
        return headers
    
    def getRequestsSession(self):
        self._auth()
        return self._session
        
    def getChannels(self):
        self._auth()
        data = self._get(API + 'television/channels')
        if 'data' not in data and 'message' in data:
            #no channels
            return []
        data = data['data']
        channels = []
        for item in data:
            channel = RebitTvChannel(
                item['id'],
                int(item['channel']),
                item['icon'],
                item['title'],
                item['guide'])
            channels.append(channel)

        channels = sorted(channels, key = lambda i: i.channel)
        return channels

    def getPlay(self, channelId):
        self._auth()
        data = self._get(API + 'television/channels/'+channelId+'/play')
        data = data['data']
        play = RebitTvPlay(
            data['id'] if 'id' in data and data['id'] else '',
            data['channel_id'] if 'channel_id' in data and data['channel_id'] else '',
            data['link'] if 'link' in data and data['link'] else '',
            data['protocol'] if 'protocol' in data and data['protocol'] else '',
            data['quality'] if 'quality' in data and data['quality'] else '')
        return play

    def getChannelGuide(self, channelId, dfrom, dto):
        self._auth()
        data = self._get(API + 'television/channels/'+channelId+'/programmes', params={'filter[start][ge]':dfrom,'filter[start][le]':dto}, slow=True)
        data = data['data']
        programmes = []
        for item in data:
            programme = RebitTvProgramme(
                item['id'] if 'id' in item and item['id'] else '',
                item['title'] if 'title' in item and item['title'] else '',
                item['subtitle'] if 'subtitle' in item and item['subtitle'] else '',
                item['description'] if 'description' in item and item['description'] else '',
                datetime.datetime.fromtimestamp(item['start']) if 'start' in item and item['start'] else None,
                datetime.datetime.fromtimestamp(item['stop']) if 'stop' in item and item['stop'] else None)
            programmes.append(programme)
        return programmes

    def generate(self, playlist, guide, days=7):
        print('Generating rebit tv')
        dfrom = datetime.datetime.now() - datetime.timedelta(days=1)
        dto = dfrom + datetime.timedelta(days=days+1)
        sdfrom = dfrom.strftime('%Y-%m-%dT23:00:00.000Z')
        sdto = dto.strftime('%Y-%m-%dT01:00:00.000Z')
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
                    if c.guide:
                        programmes = self.getChannelGuide(c.id, sdfrom, sdto)
                        for e in programmes:
                            if e.start is not None and e.stop is not None:
                                xml.write(u'<programme channel="%s" start="%s" stop="%s">\n' % (c.id, e.start.strftime('%Y%m%d%H%M%S'), e.stop.strftime('%Y%m%d%H%M%S')))
                                xml.write(u'<title>%s</title>\n' % html_escape(e.title))
                                xml.write(u'<desc>%s</desc>\n' % html_escape(e.description
                                ))
                                xml.write(u'</programme>\n')
                m3u.write(u'#EXT-X-ENDLIST\n')
                xml.write(u'</tv>\n')
