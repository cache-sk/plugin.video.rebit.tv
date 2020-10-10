# -*- coding: utf-8 -*-
# Module: default
# Author: cache-sk
# Created on: 4.11.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import sys, os, io
import xbmcaddon, xbmcgui, xbmcplugin
import traceback
import re
import rebittv

try:
    from urllib import urlencode
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import urlencode
    from urllib.parse import parse_qsl, urlparse


_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_profile = xbmc.translatePath( _addon.getAddonInfo('profile'))
try:
    _profile = _profile.decode("utf-8")
except AttributeError:
    pass

_username = xbmcplugin.getSetting(_handle, 'username')
_password = xbmcplugin.getSetting(_handle, 'password') 

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs, 'utf-8'))

def root():
    rtv = rebittv.RebitTv(_username, _password, _profile)
    channels = rtv.getChannels()
    for channel in channels:
        list_item = xbmcgui.ListItem(label=channel.title)
        list_item.setInfo('video', {'title': channel.title})
        list_item.setArt({'thumb': channel.icon})
        link = get_url(action='play', cid=channel.id)
        is_folder = False
        list_item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def play(cid):
    rtv = rebittv.RebitTv(_username, _password, _profile)
    channels = rtv.getChannels()
    for channel in channels:
        if channel.id == cid:
            playable = channel
            break
    if playable:
        headers = rtv.getHeaders()
        
        if playable.adaptive is not None:
            session = rtv.getRequestsSession()
            adaptive = session.get(playable.adaptive, headers=headers).content
            try:
                adaptive = adaptive.decode('utf-8')
            except AttributeError:
                pass
            if re.search('CODECS="(.*),(.*)"',adaptive):
                li = xbmcgui.ListItem(path=playable.adaptive+'|'+urlencode(headers))
                li.setProperty('inputstreamaddon','inputstream.adaptive') #kodi 18
                li.setProperty('inputstream','inputstream.adaptive') #kodi 19
                li.setProperty('inputstream.adaptive.manifest_type','hls')
            elif playable.best is not None:
                li = xbmcgui.ListItem(path=playable.best+'|'+urlencode(headers))
            else: #last resort
                li = xbmcgui.ListItem(path=playable.adaptive+'|'+urlencode(headers))
        else:
            li = xbmcgui.ListItem(path=playable.best+'|'+urlencode(headers))
        xbmcplugin.setResolvedUrl(_handle, True, li)
    else:
        xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())

def router(params):
    if params and 'action' in params:
        if params['action'] == 'play':
            play(params['cid'])
        else:
            root()
    else:
        root()


if __name__ == '__main__':
    router(dict(parse_qsl(sys.argv[2][1:])))
