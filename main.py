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
import shared

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

def dec_utf8(str):
    try:
        return str.decode("utf-8")  # Python 2.x
    except AttributeError:
        return str  # Python 3.x

def getRtv():
    return rebittv.RebitTv(_username, _password, _profile, _remove_oldest, _remove_oldest_kodi, shared.chooseDevice)

def channelList():
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
    stream = rtv.getPlay(cid)
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

def archiveList():
    rtv = getRtv()
    channels = rtv.getChannels()
    for channel in channels:
        if channel.archive is not None:
            list_item = xbmcgui.ListItem(label=channel.title)
            list_item.setInfo('video', {'title': channel.title})
            list_item.setArt({'thumb': channel.icon})
            link = get_url(action='archiveDays', cid=channel.id, days=channel.archive)
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def archiveDays(cid, days):
    now = datetime.datetime.now()
    for day in range(0, days+1):
        d = now - datetime.timedelta(days=day) if day > 0 else now
        #print(day)
        title = _addon.getLocalizedString(30611) if day == 0 else _addon.getLocalizedString(30612) if day == 1 else dec_utf8(d.strftime('%d. %m.'))
        title = _addon.getLocalizedString(int('3062' + str(d.weekday()))) + ', ' + title
        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'icon': 'DefaultAddonPVRClient.png'})
        link = get_url(action='archivePrograms', cid=cid, days=days, day=day, first=True)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def archivePrograms(cid, days, day, first):
    today = day == 0
    lastday = day == days+1
    now = datetime.datetime.now()
    if today:
        from_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = now
        start_date = from_date
    elif lastday:
        then = now - datetime.timedelta(days=day)
        start_date = then.replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = then + datetime.timedelta(seconds=REPLAY_LAST_GAP)
        to_date = start_date + datetime.timedelta(days=1)
    else: #other days
        from_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=day)
        to_date = from_date + datetime.timedelta(days=1)
        start_date = from_date

    if day < days:
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30606))
        list_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        list_item.setInfo('video', {'title': _addon.getLocalizedString(30606),'sorttitle':'00000'})
        link = get_url(action='archivePrograms', cid=cid, days=days, day=day+1)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    rtv = getRtv()
    programmes = rtv.getChannelGuide(cid,start_date,to_date)
    for programme in programmes:
        title = dec_utf8(programme.start.strftime('%H:%M'))
        title += ' - '
        title += programme.title
        list_item = xbmcgui.ListItem(label=title)
        list_item.setInfo('video', {'title': title,'sorttitle':title})
        list_item.setArt({'icon': 'DefaultAddonPVRClient.png'})
        link = get_url(action='archivePlay', cid=programme.cid, pid=programme.id)
        is_folder = False
        list_item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    if day > 0:
        list_item = xbmcgui.ListItem(label='9999 - '+_addon.getLocalizedString(30605))
        list_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        list_item.setInfo('video', {'title': _addon.getLocalizedString(30605),'sorttitle':'99999'})
        link = get_url(action='archivePrograms', cid=cid, days=days, day=day-1)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)


    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE) #SORT_METHOD_LABEL
    xbmcplugin.endOfDirectory(_handle, updateListing=not first)
        
def archivePlay(cid,pid):
    rtv = getRtv()
    stream = rtv.getPlay(cid,pid)
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

def menu():
    xbmcplugin.addDirectoryItem(_handle, get_url(action='channelList'), xbmcgui.ListItem(label=_addon.getLocalizedString(30601)), True)
    xbmcplugin.addDirectoryItem(_handle, get_url(action='archiveList'), xbmcgui.ListItem(label=_addon.getLocalizedString(30602)), True)
    xbmcplugin.endOfDirectory(_handle)

def router(params):
    if params and 'action' in params:
        if params['action'] == 'play':
            play(params['cid'])
        elif params['action'] == 'channelList':
            channelList()
        elif params['action'] == 'archiveList':
            archiveList()
        elif params['action'] == 'archiveDays':
            archiveDays(params['cid'],int(params['days']))
        elif params['action'] == 'archivePrograms':
            archivePrograms(params['cid'],int(params['days']),int(params['day']),'first' in params)
        elif params['action'] == 'archivePlay':
            archivePlay(params['cid'],params['pid'])
        else:
            menu()
    else:
        menu()

if __name__ == '__main__':
    router(dict(parse_qsl(sys.argv[2][1:])))
