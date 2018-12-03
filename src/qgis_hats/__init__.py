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

WIN = os.name == "nt"

PYTHON3 = sys.version_info[0] >= 3

if PYTHON3:
    from urllib.request import urlopen
else:
    from urllib2 import urlopen

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.core import QgsMessageLog

if WIN:
    from PyQt5.QtWinExtras import QWinTaskbarButton


def classFactory(iface):
    return HatsSoManyHats(iface)


def resolve(name):
    filename = __file__
    f = os.path.join(os.path.dirname(filename), name)
    return f


if PYTHON3:
    HATSDIR = resolve("SoManyMoreHats")
    URL = "https://raw.githubusercontent.com/NathanW2/qgis_hats/master/SoManyMoreHats/{icon}"
else:
    HATSDIR = resolve("SoManyHats")
    URL = "https://raw.githubusercontent.com/NathanW2/qgis_hats/master/SoManyHats/{icon}"


def hat_names(month, day, overlay=False):
    day = str(day).zfill(2)
    month = str(month).zfill(2)
    if overlay:
        dayname = "{0}-{1}-overlay.png".format(str(month), str(day))
        monthname = "{0}-overlay.png".format(str(month))
    else:
        dayname = "{0}-{1}.png".format(str(month), str(day))
        monthname = "{0}.png".format(str(month))
    fullpath = os.path.join(resolve(HATSDIR), dayname)
    monthonly = os.path.join(resolve(HATSDIR), monthname)
    return fullpath, monthonly, dayname, monthname


def not_wearing_enough(month, day):
    fullpath, monthonly, _, _ = hat_names(month, day)
    overlay_fullpath, overlay_monthonly, _, _ = hat_names(month, day, overlay=True)

    get_more_hats(month, day)

    overlay = None
    if os.path.exists(overlay_fullpath):
        QgsMessageLog.logMessage("Found overlay at", "hats")
        QgsMessageLog.logMessage(overlay_fullpath, "hats")
        overlay = overlay_fullpath
    elif os.path.exists(overlay_monthonly):
        QgsMessageLog.logMessage("Found overlay at", "hats")
        QgsMessageLog.logMessage(overlay_monthonly, "hats")
        overlay = overlay_monthonly

    path = None
    if os.path.exists(fullpath):
        QgsMessageLog.logMessage("Found hat at", "hats")
        QgsMessageLog.logMessage(fullpath, "hats")
        path = fullpath
    elif os.path.exists(monthonly):
        QgsMessageLog.logMessage("Found hat at", "hats")
        QgsMessageLog.logMessage(monthonly, "hats")
        path = monthonly
    else:
        QgsMessageLog.logMessage("Can't find hat at {} or {}".format(fullpath, monthonly), "hats")

    return path, overlay


def get_more_hats(month, day):
    def fetch_more(name, outpath):
        try:
            url = URL.format(icon=name)
            response = urlopen(url)
            data = response.read()
            with open(outpath, "wb") as f:
                f.write(data)
        except Exception as ex:
            pass

    if not os.path.exists(HATSDIR):
        os.makedirs(HATSDIR)

    fullpath, monthonly, dayname, monthname = hat_names(month, day)
    overlay_fullpath, overlay_monthonly, overlay_dayname, overlay_monthname = hat_names(month, day, overlay=True)

    fetch_more(dayname, fullpath)
    fetch_more(monthname, monthonly)
    fetch_more(overlay_dayname, overlay_fullpath)
    fetch_more(overlay_monthname, overlay_monthonly)


class HatsSoManyHats(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.iface.mainWindow().installEventFilter(self)

    def eventFilter(self, object, event):
        if self.iface.mainWindow().windowHandle() and self.iface.mainWindow().windowHandle().title():
            self.show_the_hats()

        return super().eventFilter(object, event)

    def initGui(self):
        pass

    def show_the_hats(self):
        self.iface.mainWindow().removeEventFilter(self)
        current = QDateTime.currentDateTime()
        month = current.date().month()
        day = current.date().day()
        hat, overlay = not_wearing_enough(month, day)
        if hat:
            icon = QIcon(hat)
            QApplication.instance().setWindowIcon(icon)
            self.iface.mainWindow().setWindowIcon(icon)

        if overlay and WIN:
            QgsMessageLog.logMessage("Set overlay", "hats")
            self.button = QWinTaskbarButton()
            QgsMessageLog.logMessage(self.iface.mainWindow().windowHandle().title(), "hats")
            self.button.setWindow(self.iface.mainWindow().windowHandle())
            self.button.setOverlayIcon(QIcon(overlay))
        else:
            QgsMessageLog.logMessage("No overlay set", "hats")

    def unload(self):
        pass
