# -*- coding: utf-8 -*-
# Module: default
# Author: cache-sk
# Created on: 4.11.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import sys, os, io
from urlparse import parse_qsl
from urllib import urlencode
import xbmcaddon, xbmcgui, xbmcplugin
import traceback
import re
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
    xbmcplugin.addDirectoryItem(_handle, get_url(action='m3u'), xbmcgui.ListItem(label=_addon.getLocalizedString(30201)), True)
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
            if re.search('CODECS="(.*),(.*)"',adaptive):
                li = xbmcgui.ListItem(path=playable.adaptive+'|'+urlencode(headers))
                li.setProperty('inputstreamaddon','inputstream.adaptive')
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

def m3u():
    try:
        folder = xbmcgui.Dialog().browseSingle(3, _addon.getAddonInfo('name'), "local")
        if folder and os.path.exists(folder):
            with io.open(os.path.join(folder,'playlist.m3u'), 'w', encoding='utf8') as f:
                rtv = rebittv.RebitTv(_username, _password, _profile)
                channels = rtv.getChannels()
                f.write(u'#EXTM3U\n')
                for ch in channels:
                    f.write(u'#EXTINF:0 tvg-logo="{0}" tvg-name="{1}",{1}\n'.format(ch.icon,ch.title))
                    f.write(unicode(get_url(action='play', cid=ch.id) + '\n'))
                f.close()
            xbmcgui.Dialog().notification(_addon.getAddonInfo('name'), 'Playlist OK', icon=xbmcgui.NOTIFICATION_INFO, time=3000, sound=True)
    except Exception as e:
        xbmcgui.Dialog().notification(_addon.getAddonInfo('name'), str(e), icon=xbmcgui.NOTIFICATION_ERROR, time=3000, sound=True)
        traceback.print_exc()
    xbmcplugin.endOfDirectory(_handle)

def router(params):
    if params and 'action' in params:
        if params['action'] == 'play':
            play(params['cid'])
        elif params['action'] == 'm3u':
            m3u()
        else:
            root()
    else:
        root()


if __name__ == '__main__':
    router(dict(parse_qsl(sys.argv[2][1:])))
