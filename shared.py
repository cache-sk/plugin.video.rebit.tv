# -*- coding: utf-8 -*-
# Module: default
# Author: cache-sk
# Created on: 28.12.2020
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import xbmc, xbmcaddon, xbmcgui
import datetime

try:
    from xbmc import translatePath
except ImportError:
    from xbmcvfs import translatePath

_addon = xbmcaddon.Addon()
_profile = translatePath( _addon.getAddonInfo('profile'))

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
