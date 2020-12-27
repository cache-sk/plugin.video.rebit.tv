# -*- coding: utf-8 -*-
# Module: default
# Author: cache-sk
# Created on: 4.11.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import sys, os, io
import xbmcaddon, xbmcgui, xbmcplugin
import traceback
import re
import time, datetime
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
_remove_oldest = 'true' == xbmcplugin.getSetting(_handle, 'remove_oldest_device')
_remove_oldest_kodi = 'true' == xbmcplugin.getSetting(_handle, 'remove_oldest_kodi')

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs, 'utf-8'))

def getRtv():
    def chooseDevice(devices):
        def nameDevice(device):
            anyDTI = device['updated_at'] if 'updated_at' in device and device['updated_at'] else (device['created_at'] if 'created_at' in device and device['created_at'] else None)
            anyDTI = ('; ' + datetime.datetime.fromtimestamp(anyDTI).strftime("%d.%m.%Y, %H:%M:%S")) if anyDTI is not None else ''
            return device['title'] + anyDTI if 'title' in device else _addon.getLocalizedString(30302)
        dialog = xbmcgui.Dialog()
        opts = ['%s' % (nameDevice(device)) for device in devices]
        index = dialog.select(_addon.getLocalizedString(30301), opts)
        if index != -1:
            return devices[index]
        else:
            return chooseDevice(devices)
    return rebittv.RebitTv(_username, _password, _profile, _remove_oldest, _remove_oldest_kodi, chooseDevice)

def root():
    rtv = getRtv()
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
    rtv = getRtv()
    print 'have rtv'
    stream = rtv.getPlay(cid)
    print 'have stream'
    if stream.link != '':
        headers = rtv.getHeaders()
        li = xbmcgui.ListItem(path=stream.link+'|'+urlencode(headers))
        if 'adaptive' == stream.quality:
            li.setProperty('inputstreamaddon','inputstream.adaptive') #kodi 18
            li.setProperty('inputstream','inputstream.adaptive') #kodi 19
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
