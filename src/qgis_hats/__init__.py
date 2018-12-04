# -----------------------------------------------------------
# Copyright (C) 2015 Martin Dobias
# -----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# ---------------------------------------------------------------------

import os
import sys
import pathlib

WIN = os.name == "nt"

PYTHON3 = sys.version_info[0] >= 3

if PYTHON3:
    from urllib.error import HTTPError
    from urllib.request import urlopen
else:
    from urllib2 import urlopen, HTTPError

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.core import QgsMessageLog, Qgis, QgsSettings, QgsApplication

def log(message):
    QgsMessageLog.logMessage(message, "hats")

if __name__ == "__main__":
    log = print



if WIN:
    from PyQt5.QtWinExtras import QWinTaskbarButton


def classFactory(iface):
    return HatsSoManyHats(iface)


def resolve(name):
    filename = __file__
    f = os.path.join(os.path.dirname(filename), name)
    return f


versiondata = Qgis.QGIS_VERSION.split(".")
QGIS_VERSION = versiondata[0] + "." + versiondata[1]

if PYTHON3:
    HATSDIRNAME = "SoManyMoreHats"
else:
    HATSDIRNAME = "SoManyHats"

HATSDIR = resolve(HATSDIRNAME)
SPLASHDIRNAME = "SoManySplashes"
SPLASHPATH = resolve(os.path.join(SPLASHDIRNAME, QGIS_VERSION))

URL = "https://raw.githubusercontent.com/NathanW2/qgis_hats/master/{folder}/{icon}"
SPLASH_URL = "https://raw.githubusercontent.com/NathanW2/qgis_hats/master/{folder}/{version}/{icon}"


def hat_names(month, day, overlay=False, folder=HATSDIR):
    day = str(day).zfill(2)
    month = str(month).zfill(2)
    if overlay:
        dayname = "{0}-{1}-overlay.png".format(str(month), str(day))
        monthname = "{0}-overlay.png".format(str(month))
    else:
        dayname = "{0}-{1}.png".format(str(month), str(day))
        monthname = "{0}.png".format(str(month))
    fullpath = os.path.join(resolve(folder), dayname)
    monthonly = os.path.join(resolve(folder), monthname)
    return fullpath, monthonly, dayname, monthname


def splash_names(month, day):
    day = str(day).zfill(2)
    month = str(month).zfill(2)
    dayname = "{0}-{1}.png".format(str(month), str(day))
    monthname = "{0}.png".format(str(month))
    fullpath = os.path.join(resolve(SPLASHPATH), str(month), str(day), "splash.png")
    monthonly = os.path.join(resolve(SPLASHPATH), str(month), "splash.png")
    return fullpath, monthonly, dayname, monthname


def not_wearing_enough(month, day):
    def get_final_path(*paths):
        for path in paths:
            if os.path.exists(path):
                log("Found {}".format(path))
                return path
        log("Can't find any paths from {}".format("|".join(paths)))
        return None

    fullpath, monthonly, _, _ = hat_names(month, day, folder=HATSDIR)
    overlay_fullpath, overlay_monthonly, _, _ = hat_names(month, day, overlay=True, folder=HATSDIR)
    splash_fullpath, splash_monthonly, _, _ = splash_names(month, day)

    get_more_hats(month, day)

    overlay = get_final_path(overlay_fullpath, overlay_monthonly)
    path = get_final_path(fullpath, monthonly)
    splash = get_final_path(splash_fullpath, splash_monthonly)

    if splash:
        splash = os.path.dirname(splash)
    return path, overlay, splash


def get_more_hats(month, day):
    def fetch_more(url, folder, name, outpath, **kwargs):
        # If it's there already just skip over it.
        if os.path.exists(outpath):
            log("Found {} skipping request for more".format(outpath))
            return

        try:
            url = url.format(folder=folder, icon=name, **kwargs)
            log(url)
            response = urlopen(url)
            data = response.read()
            pathlib.Path(os.path.dirname(outpath)).mkdir(parents=True, exist_ok=True)
            with open(outpath, "wb") as f:
                f.write(data)
        except HTTPError as ex:
            if ex.code == 404:
                pass
            log(str(ex))

    fullpath, monthonly, dayname, monthname = hat_names(month, day, folder=HATSDIR)
    overlay_fullpath, overlay_monthonly, overlay_dayname, overlay_monthname = hat_names(month, day, overlay=True,
                                                                                        folder=HATSDIR)
    splash_fullpath, splash_monthonly, splash_dayname, splash_monthname = splash_names(month, day)

    fetch_more(URL, HATSDIRNAME, dayname, fullpath)
    fetch_more(URL, HATSDIRNAME, monthname, monthonly)
    fetch_more(URL, HATSDIRNAME, overlay_dayname, overlay_fullpath)
    fetch_more(URL, HATSDIRNAME, overlay_monthname, overlay_monthonly)

    fetch_more(SPLASH_URL, SPLASHDIRNAME, splash_dayname, splash_fullpath, version=QGIS_VERSION)
    fetch_more(SPLASH_URL, SPLASHDIRNAME, splash_monthname, splash_monthonly, version=QGIS_VERSION)


class HatsSoManyHats(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        # self.iface.mainWindow().installEventFilter(self)

    # def eventFilter(self, object, event):
    #     if self.iface.mainWindow().windowHandle() and self.iface.mainWindow().windowHandle().title():
    #         self.show_the_hats()
    #
    #     return super().eventFilter(object, event)

    def initGui(self):
        self.show_the_hats()

    def show_the_hats(self):
        # self.iface.mainWindow().removeEventFilter(self)
        current = QDateTime.currentDateTime()
        month = current.date().month()
        day = current.date().day()
        hat, overlay, splash = not_wearing_enough(month, day)
        if hat:
            icon = QIcon(hat)
            QApplication.instance().setWindowIcon(icon)
            self.iface.mainWindow().setWindowIcon(icon)

        if splash:
            path = os.path.join(QgsApplication.qgisSettingsDirPath(), "QGIS", "QGISCUSTOMIZATION3.ini")
            settings = QSettings(path, QSettings.IniFormat)
            key = "Customization/splashpath"
            value = splash + "\\"
            currentvalue = settings.value(key)
            if currentvalue != value:
                log("Setting splash to {}".format(splash))
                settings.setValue(key, value)
                qgssettings = QgsSettings()
                qgssettings.setValue("UI/Customization/enabled", True)
                self.iface.messageBar().pushMessage("Splash updated! Yay. Restart QGIS to check it out!")

        # if overlay and WIN:
        #     log("Set overlay", "hats")
        #     self.button = QWinTaskbarButton()
        #     self.button.setWindow(self.iface.mainWindow().windowHandle())
        #     self.button.setOverlayIcon(QIcon(overlay))
        # else:
        #     log("No overlay set", "hats")

    def unload(self):
        pass


if __name__ == "__main__":
    t = HatsSoManyHats(None)
    t.initGui()
