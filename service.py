# -*- coding: utf-8 -*-
# Module: default
# Author: cache-sk
# Created on: 09.10.2020
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import datetime
import time
import io
import os
import rebittv
import xbmc
import xbmcaddon
import traceback
import string
import random
import shared

class RebbitMonitor(xbmc.Monitor):
    _addon = None
    _workdir = ''
    _next_update = 0
    
    def _setWorkdir(self):
        if 'true' == self._addon.getSetting('gentoaddon'):
            self._workdir = xbmc.translatePath(self._addon.getAddonInfo('profile'))
        else:
            self._workdir = self._addon.getSetting('gentofolder')
            
        try:
            self._workdir = self._workdir.decode("utf-8")
        except AttributeError:
            pass
            
        if "" == self._workdir:
            raise rebittv.FolderNotExistException

    def __init__(self):
        xbmc.Monitor.__init__(self)
        self._addon = xbmcaddon.Addon()
        self._setWorkdir()
        
        ts = self._addon.getSetting('genall_next_update')
        self._next_update = datetime.datetime.fromtimestamp(0) if ts == '' else datetime.datetime.fromtimestamp(float(ts))
        #cleanup
        if os.path.exists(self._workdir):
            files_to_remove = [f for f in os.listdir(self._workdir) if os.path.isfile(os.path.join(self._workdir, f)) and (f.endswith('.work.xml') or f.endswith('.work.m3u'))]
            for f in files_to_remove:
                os.unlink(os.path.join(self._workdir, f))

    def __del__(self):
        print('rebit.tv service destroyed')

    def notify(self, text, error=False):
        try:
            text = text.encode("utf-8") if type(text) is unicode else text
        except NameError:
            pass
        icon = 'DefaultIconError.png' if error else ''
        xbmc.executebuiltin('Notification("%s","%s",5000,%s)' % (self._addon.getAddonInfo('name'), text, icon))

    def onSettingsChanged(self):
        self._addon = xbmcaddon.Addon()  # refresh for updated settings!
        self._setWorkdir()
        if not self.abortRequested():
            self._next_update = datetime.datetime.fromtimestamp(0)
            self.tick()

    def schedule_next(self, seconds):
        dt = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        print('Next rebit.tv update %s' % dt)
        self._next_update = dt

    def update(self):
        gse = 'true' == self._addon.getSetting('genall')
        if not gse:
            return False

        print('Updating rebit.tv')

        if not os.path.exists(self._workdir):
            os.makedirs(self._workdir)
        
        epg_workpath = os.path.join(self._workdir, get_random_string(8) + '.work.xml')
        epg_path = os.path.join(self._workdir, 'epg.xml')
        playlist_workpath = os.path.join(self._workdir, get_random_string(8) + '.work.m3u')
        playlist_path = os.path.join(self._workdir, 'playlist.m3u')

        _username = self._addon.getSetting('username')
        _password = self._addon.getSetting('password')
        _remove_oldest = 'true' == self._addon.getSetting('remove_oldest_device')
        _remove_oldest_kodi = 'true' == self._addon.getSetting('remove_oldest_kodi')
        rtv = rebittv.RebitTv(_username, _password, self._workdir, _remove_oldest, _remove_oldest_kodi, shared.chooseDevice)
        rtv.generate(playlist_workpath,epg_workpath,int(self._addon.getSetting('gen_days')))
        
        if os.path.isfile(epg_path):
            os.unlink(epg_path)
        os.rename(epg_workpath, epg_path)

        if os.path.isfile(playlist_path):
            os.unlink(playlist_path)
        os.rename(playlist_workpath, playlist_path)
        
        self.notify(self._addon.getLocalizedString(30201))
        
        if "true" == self._addon.getSetting('restartpisc'):
            try:
                pisc = xbmcaddon.Addon(id='pvr.iptvsimple') #existance
                xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":1,"params":{"addonid": "pvr.iptvsimple","enabled":false}}')
                time.sleep(1)
                xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":1,"params":{"addonid": "pvr.iptvsimple","enabled":true}}')
            except:
                pass

        return True

    def tick(self):
        if datetime.datetime.now() > self._next_update:
            try:
                self.schedule_next(int(self._addon.getSetting('gen_delay')) * 60 * 60)
                self.update()
            except Exception as e:
                traceback.print_exc()
                self.notify(str(e), True)

    def save(self):
        self._addon.setSetting('genall_next_update', str(time.mktime(self._next_update.timetuple())))
        print('Saving rebit.tv next update %s' % self._next_update)

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

if __name__ == '__main__':
    monitor = RebbitMonitor()
    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            monitor.save()
            break
        monitor.tick()
