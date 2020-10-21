"""
Created on Mar 20, 2018

@author: skwok
"""
import math
import numpy as np
import webbrowser
import traceback


def tryEx(f):
    def ff(*args, **kargs):
        try:
            return f(*args, **kargs)
        except:
            traceback.print_exc()

    return ff


def as2Radian(arcsec):
    return math.radians(arcsec / 3600.0)


def toSexagecimal(deg, plus=" "):
    """Converts deg to dd:mm:ss """
    sign = plus
    if deg < 0:
        t = -deg
        sign = "-"
    else:
        t = deg
    hh = int(t)
    t = (t - hh) * 60
    mm = int(t)
    ss = (t - mm) * 60

    ssStr = "%05.2f" % ss

    return "%s%02d:%02d:%s" % (sign, hh, mm, ssStr)


def sexg2Float(str0):
    """ Input str as dd:mm:ss
        output as decimal
    """
    sign = 1.0
    str0 = str0.strip()
    if str0.startswith("-"):
        str0 = str0.replace("-", "")
        sign = -1.0
    str0 = str0.replace(":", " ")
    s1 = str0.split(" ")
    hh = mm = ss = 0
    try:
        hh = float(s1[0])
        mm = float(s1[1]) / 60.0
        ss = float(s1[2]) / 3600.0
    except Exception as e:
        raise Exception("Failed to convert to float " + str(e))
    return sign * (hh + mm + ss)


def sec2hour(sec):
    isec = int(sec)
    hh = isec / 3600
    mm = (isec % 3600) / 60
    ss = (isec % 60) + (sec - isec)
    ssStr = "%05.2f" % ss
    # if ss < 10:
    #    ssStr = '0' + ssStr
    return "%02d:%02d:%s" % (hh, mm, ssStr)


def norm360Angle(ang):
    while ang > 360:
        ang -= 360
    while ang < 0:
        ang += 360
    return ang


def norm180Angle(ang):
    ang = norm360Angle(ang)
    if ang > 180:
        return ang - 360
    return ang


def julianDay(y, m, d):
    """ Returns Julian day, a decimal number.
    """
    if m <= 2:
        m += 12
        y -= 1
    A = int(y / 100)
    B = int(2 - A + A / 4)

    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
    return jd
    # JulianDay


def transpose(arr):
    return list(map(list, zip(*arr)))


def launchBrowser(host, portnr, path):
    webbrowser.open(f"http://{host}:{portnr}/{path}", new=1)


def rotate(xs, ys, rotDeg):
    rotRad = math.radians(rotDeg)
    sina = math.sin(rotRad)
    cosa = math.cos(rotRad)
    outxs = xs * cosa - ys * sina
    outys = xs * sina + ys * cosa
    return outxs, outys


MM2AS = math.degrees(1.0 / 149583) * 3600

