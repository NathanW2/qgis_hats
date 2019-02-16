# -----------------------------------------------------------
# Copyright (C) 2018 Nathan Woodrow
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
import shutil

WIN = os.name == "nt"

PYTHON3 = sys.version_info[0] >= 3

if PYTHON3:
    import urllib.request
    import json

    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen
else:
    from urllib2 import urlopen, HTTPError

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMessageLog, Qgis, QgsSettings, QgsApplication


def classFactory(iface):
    return HatsSoManyHats(iface)


def resolve(name):
    filename = __file__
    f = os.path.join(os.path.dirname(filename), name)
    return f


def log(message):
    QgsMessageLog.logMessage(message, "hats")


if __name__ == "__main__":
    log = print

if WIN:
    from PyQt5.QtWinExtras import QWinTaskbarButton

versiondata = Qgis.QGIS_VERSION.split(".")
QGIS_VERSION = versiondata[0] + "." + versiondata[1]

if PYTHON3:
    HATSDIRNAME = "SoManyMoreHats"
else:
    HATSDIRNAME = "SoManyHats"

HATSDIR = resolve(HATSDIRNAME)
SPLASHDIRNAME = "SoManySplashes"
SPLASHPATH = resolve(os.path.join(SPLASHDIRNAME, QGIS_VERSION))
ACTIVESPLASH = resolve(os.path.join(SPLASHDIRNAME, "active"))
SUNFILE = resolve("sun.json")

pathlib.Path(ACTIVESPLASH).mkdir(parents=True, exist_ok=True)

SUNURL = "https://api.sunrise-sunset.org/json?lat={latitude}&lng={longitude}&formatted=0"
URL = "https://raw.githubusercontent.com/NathanW2/qgis_hats/master/{folder}/{icon}"
SPLASH_URL = "https://raw.githubusercontent.com/NathanW2/qgis_hats/master/{folder}/{version}/{icon}"
SETTINGKEY = "qgis_hats"
TIMEKEY = "{}/time_enabled_splash".format(SETTINGKEY)

qgssettings = QgsSettings()

time_is_enabled = qgssettings.value(TIMEKEY, False)


def _get_sun_data():
    # TODO: Add 30 day time out on sun data
    if os.path.exists(SUNFILE):
        with open(SUNFILE) as f:
            return json.load(f)
    else:
        if not time_is_enabled:
            log("Fetching sun data online disabled")
            return {}

        log("Fetching location info")
        try:
            with urllib.request.urlopen("https://geoip-db.com/json") as url:
                data = json.loads(url.read().decode())
                log("Fetching sun data")
                with urllib.request.urlopen(SUNURL.format(**data)) as sunurl:
                    sundata = json.loads(sunurl.read().decode())
                    with open(SUNFILE, "w") as f:
                        json.dump(sundata, f)
                    return sundata
        except URLError as ex:
            log("Error fetching location and sun data")
            log(str(ex))
            return {}


def is_nighttime():
    sundata = _get_sun_data()
    if not sundata:
        return False

    sunrise = sundata["results"]["sunrise"]
    sunset = sundata["results"]["sunset"]
    sunrise = QDateTime.fromString(sunrise, Qt.ISODate)
    sunset = QDateTime.fromString(sunset, Qt.ISODate)
    now = QTime.currentTime()
    sunrisetime=sunrise.time()
    sunsettime=sunset.time()
    if sunrisetime < now < sunsettime:
        log("Day")
        return False
    else:
        log("Night")
        return True


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
    """
    Return the names and paths for the splash screens based on the month and day.
    :param month: Month
    :param day: Day
    :return: Paths and names of splash screens.
    """
    day = str(day).zfill(2)
    month = str(month).zfill(2)
    modestr = "-night" if is_nighttime() else ""
    dayname = "{0}-{1}{2}.png".format(str(month), str(day), modestr)
    monthname = "{0}{1}.png".format(str(month), modestr)
    fullpath = os.path.join(resolve(SPLASHPATH), dayname)
    monthonly = os.path.join(resolve(SPLASHPATH), monthname)
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

    return path, overlay, splash


def set_splash_active(splash):
    """
    Set the splash to active by moving it to the active folder.
    :param splash:
    :return:
    """
    log("Setting {} to active".format(splash))
    newname = os.path.join(ACTIVESPLASH, "splash.png")
    shutil.copy(splash, newname)
    return os.path.dirname(newname)


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


class AboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        loadUi(resolve("about.ui"), self)

    @property
    def time_enabled(self):
        return self.setting_timesplash.isChecked()

    @time_enabled.setter
    def time_enabled(self, value):
        self.setting_timesplash.setChecked(value)


class HatsSoManyHats(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.about_action = QAction(QIcon(resolve("icon.png")), "About QGIS Hats!")
        self.about_action.triggered.connect(self.show_about)

    def show_about(self):
        dlg = AboutDialog(self.iface.mainWindow())
        dlg.time_enabled = qgssettings.value(TIMEKEY, False, type=bool)
        if dlg.exec_():
            timeenabled = dlg.time_enabled
            qgssettings.setValue(TIMEKEY, timeenabled)

    def initGui(self):
        self.iface.addPluginToMenu("QGIS Hats", self.about_action)
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

        key = "Customization/splashpath"
        activekey = "{}/active_splash".format(SETTINGKEY)
        path = os.path.join(QgsApplication.qgisSettingsDirPath(), "QGIS", "QGISCUSTOMIZATION3.ini")
        settings = QSettings(path, QSettings.IniFormat)
        activesplash = qgssettings.value(activekey, None)
        if splash:
            splashname = os.path.basename(splash)
            if splashname != activesplash or not settings.value(key, None):
                activepath = set_splash_active(splash)
                value = activepath + os.sep
                settings.setValue(key, value)

                qgssettings.setValue("UI/Customization/enabled", True)
                qgssettings.setValue(activekey, splashname)
                self.iface.messageBar().pushMessage("Splash", "Yay! New splash. Restart QGIS to check it out.")
        else:
            settings.remove(key)

    def unload(self):
        pass


if __name__ == "__main__":
    current = QDateTime.currentDateTime()
    month = current.date().month()
    day = current.date().day()
    hat, overlay, splash = not_wearing_enough(month, day)
    set_splash_active(splash)
