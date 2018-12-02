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

PYTHON3 = sys.version_info[0] >= 3

if PYTHON3:
    from urllib.request import urlopen
else:
    from urllib2 import urlopen

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.core import QgsMessageLog


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


def hat_names(month, day):
    day = str(day).zfill(2)
    month = str(month).zfill(2)
    dayname = "{0}-{1}.png".format(str(month), str(day))
    monthname = "{0}.png".format(str(month))
    fullpath = os.path.join(resolve(HATSDIR), dayname)
    monthonly = os.path.join(resolve(HATSDIR), monthname)
    return fullpath, monthonly, dayname, monthname


def not_wearing_enough(month, day):
    fullpath, monthonly, _, _ = hat_names(month, day)

    if os.path.exists(fullpath):
        QgsMessageLog.logMessage("Found hat at", "hats")
        QgsMessageLog.logMessage(fullpath, "hats")
        return fullpath
    else:
        QgsMessageLog.logMessage("Fetching hats", "hats")
        get_more_hats(month, day)

    QgsMessageLog.logMessage(monthonly, "hats")
    QgsMessageLog.logMessage(fullpath, "hats")

    if os.path.exists(fullpath):
        QgsMessageLog.logMessage("Found hat at", "hats")
        QgsMessageLog.logMessage(fullpath, "hats")
        return fullpath
    elif os.path.exists(monthonly):
        QgsMessageLog.logMessage("Found hat at", "hats")
        QgsMessageLog.logMessage(monthonly, "hats")
        return monthonly
    else:
        QgsMessageLog.logMessage("Can't find hat at {} or {}".format(fullpath, monthonly), "hats")
        return None


def get_more_hats(month, day):
    if not os.path.exists(HATSDIR):
        os.makedirs(HATSDIR)

    fullpath, monthonly, dayname, monthname = hat_names(month, day)

    try:
        url = URL.format(icon=dayname)
        QgsMessageLog.logMessage(url, "hats")
        response = urlopen(url)
        data = response.read()
        with open(fullpath, "wb") as f:
            f.write(data)
    except Exception as ex:
        pass

    try:
        url = URL.format(icon=monthname)
        QgsMessageLog.logMessage(url, "hats")
        response = urlopen(url)
        data = response.read()
        with open(monthonly, "wb") as f:
            f.write(data)
    except Exception as ex:
        pass


class HatsSoManyHats:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        current = QDateTime.currentDateTime()
        month = current.date().month()
        day = current.date().day()
        hat = not_wearing_enough(month, day)

        if hat:
            icon = QIcon(hat)
            QApplication.instance().setWindowIcon(icon)
            self.iface.mainWindow().setWindowIcon(icon)

    def unload(self):
        pass
