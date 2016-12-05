#-----------------------------------------------------------
# Copyright (C) 2015 Martin Dobias
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import os
import urllib2
from urllib.error import HTTPError

from PyQt4.QtGui import *
from PyQt4.QtCore import *

def classFactory(iface):
    return HatsSoManyHats(iface)

def resolve(name):
    filename = __file__
    f = os.path.join(os.path.dirname(filename), name)
    return f

HATSDIR = resolve("SoManyHats")
URL =  "https://raw.githubusercontent.com/NathanW2/qgis_hats/master/SoManyHats/{icon}"


def not_wearing_enough(month, day):
    day = str(day).zfill(2)
    month = str(month).zfill(2)
    fullpath = resolve(HATSDIR + "\{0}-{1}.png".format(str(month), str(day)))
    monthonly = resolve(HATSDIR + "\{0}.png".format(str(month)))
    if os.path.exists(fullpath):
        return fullpath
    elif os.path.exists(monthonly):
        return monthonly
    return None


def get_more_hats(month, day):
    if not os.path.exists(HATSDIR):
        os.makedirs(HATSDIR)
    day = str(day).zfill(2)
    month = str(month).zfill(2)
    fullname = "{0}-{1}.png".format(str(month), str(day))
    monthonlyname = "{0}.png".format(str(month))
    fullpath = resolve(HATSDIR + "\\" + fullname)
    monthonly = resolve(HATSDIR + "\\" + monthonlyname)
    data = None
    try:
        url = URL.format(icon=fullname)
        response = urllib2.urlopen(url)
        data = response.read()
        with open(fullpath, "wb") as f:
            f.write(data)
        return fullpath
    except Exception as ex:
        pass

    try:
        url = URL.format(icon=monthonlyname)
        print url
        response = urllib2.urlopen(url)
        data = response.read()
        with open(monthonly, "wb") as f:
            f.write(data)
        return monthonly
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
        if not hat:
            hat = get_more_hats(month, day)

        if hat:
            icon = QIcon(hat)
            QApplication.instance().setWindowIcon(icon)
            self.iface.mainWindow().setWindowIcon(icon)

    def unload(self):
        pass
