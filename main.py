# -*- coding: utf-8 -*-
# Module: default
# Author: cache-sk
# Created on: 4.11.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import sys
from urlparse import parse_qsl
from urllib import urlencode
import xbmcaddon, xbmcgui, xbmcplugin
import rebittv

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_profile = xbmc.translatePath( _addon.getAddonInfo('profile')).decode('utf-8')
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
        li = xbmcgui.ListItem(path=playable.stream+'|'+urlencode(headers))
        li.setProperty('inputstreamaddon','inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type','hls')
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
