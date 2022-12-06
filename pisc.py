# -*- coding: utf-8 -*-
# Author: cache-sk
# Created on: 09.10.2020

import os
import io
import xbmcgui
import xbmcaddon
import rebittv

try:
    from xbmc import translatePath
except ImportError:
    from xbmcvfs import translatePath

def set_pisc():
    _self = xbmcaddon.Addon(id='plugin.video.rebit.tv')
    try:
        _pisc = xbmcaddon.Addon(id='pvr.iptvsimple')
    except:
        xbmcgui.Dialog().ok(_self.getAddonInfo('name'), _self.getLocalizedString(30202))
        return

    if not xbmcgui.Dialog().yesno(_self.getAddonInfo('name'), _self.getLocalizedString(30203)):
        return
        
    if 'true' == _self.getSetting('gentoaddon'):
        _workdir = translatePath(_self.getAddonInfo('profile'))
    else:
        _workdir = _self.getSetting('gentofolder')
    try:
        _workdir = _workdir.decode("utf-8")
    except AttributeError:
        pass
        
    if "" == _workdir:
        raise rebittv.FolderNotExistException
        
    if not os.path.exists(_workdir):
        os.makedirs(_workdir)
    
    playlist = os.path.join(_workdir, 'playlist.m3u')
    guide = os.path.join(_workdir, 'epg.xml')
    
    if not os.path.exists(playlist) or not os.path.exists(guide):
        with io.open(playlist, 'w', encoding='utf8') as m3u:
            m3u.write(u'#EXTM3U\n')
        with io.open(guide, 'w', encoding='utf8') as xml:
            xml.write(u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
            xml.write(u'<tv>\n')
            xml.write(u'</tv>\n')

    _pisc.setSetting('m3uPathType','0')
    _pisc.setSetting('m3uPath',playlist)
    _pisc.setSetting('startNum','1')
    _pisc.setSetting('epgPath',guide)
    _pisc.setSetting('epgCache','false')
    _pisc.setSetting('epgPathType','0')
    _pisc.setSetting('epgTimeShift','0')
    _pisc.setSetting('epgTSOverride','false')
    _pisc.setSetting('logoPathType','1')
    _pisc.setSetting('logoBaseUrl','')
    _pisc.setSetting('logoFromEpg','2')
    xbmcgui.Dialog().ok(_self.getAddonInfo('name'), _self.getLocalizedString(30204))

set_pisc()