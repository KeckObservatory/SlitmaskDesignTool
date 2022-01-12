"""
Created on Mar 20, 2018

The request sequence is:
- Browser starts with loadConfigParams -> getConfigParams
- Browser calls loadMaskLayout -> getMaskLayout returns mask and reducedMask layouts
- Browser calls loadBackgroundImage -> loads DSS image into canvas background

- Browser loads the targetlist via sendTargets2Server via form submit ('loadTargets')
- Server responds OK

- Browser onload calls loadAll(), which includes loadMaskLayout, loadBackgroundImage, loadTargets()
- Server loadTargets -> getTargetsAndInfo loads target list and info, such as center RA/DEC, sky PA and scales

@author: skwok
"""

import socket
import json
import sys
import os
import argparse
import time
import signal
import traceback
import matplotlib

matplotlib.use("Agg")

from threading import Thread

from smdtLibs import utils
from smdtLibs import drawUtils
from smdtLibs.easyHTTP import EasyHTTPHandler, EasyHTTPServer, EasyHTTPServerThreaded
from smdtLibs.configFile import ConfigFile
from slitmaskDesignTool import SlitmaskDesignTool
from smdtLogger import SMDTLogger, infoLog
from maskDesignFile import MaskDesignOutputFitsFile, getListAsBytes

GlobalData = {}


def _getData(_id):
    d = GlobalData.get(_id)
    if not d:
        d = SlitmaskDesignTool(None, "deimos", config=None)
    return d


def _setData(_id, smdata):
    GlobalData[_id] = smdata


class SMDesignHandler(EasyHTTPHandler):
    PNGImage = "image/png"
    config = None

    @classmethod
    def setDocRoot(cls, docRoot):
        if not os.path.exists(docRoot):
            rpath = os.path.dirname(os.path.realpath(__file__))
            docRoot = f"{rpath}/{docRoot}"
        cls.DocRoot = docRoot

    def echo(self, req, qstr):
        return json.dumps(qstr), self.PlainTextType

    def _updateConfigParams(self, qstr):
        params = self.config.getValue("params")
        for k in qstr.keys():
            k1 = k.replace("fd", "")
            v = params.getValue(k1, None)
            if v is not None:
                v1, v2, v3, v4 = v
                # print("setting ", k1, qstr[k][0])
                params.setValue(k1, (utils.asType(qstr[k][0]), v2, v3, v4))

    @utils.tryEx
    def sendTargets2Server(self, req, qstr):
        """
        Respond to the form action
        """
        content = self.getDefValue(qstr, "targetList", None)
        self._updateConfigParams(qstr)
        if content is not None:
            _setData("smdt", SlitmaskDesignTool(content, "deimos", self.config))
        return "OK", self.PlainTextType

    @utils.tryEx
    def getConfigParams(self, req, qstr):
        sm = _getData("smdt")
        paramData = self.config.getValue("params")
        return json.dumps({"params": paramData.properties}), self.PlainTextType

    @utils.tryEx
    def getTargets(self, req, qstr):
        """
        Returns the targets that were loaded via loadParams()
        """
        sm = _getData("smdt")
        return sm.targetList.toJson(), self.PlainTextType

    @utils.tryEx
    def getDSSImage(self, req, qstr):
        sm = _getData("smdt")
        return drawUtils.img2Bitmap(sm.targetList.dssData), self.PNGImage

    @utils.tryEx
    def getROIInfo(self, req, qstr):
        sm = _getData("smdt")
        out = sm.getROIInfo()
        return json.dumps(out), self.PlainTextType

    @utils.tryEx
    def getTargetsAndInfo(self, req, qstr):
        """
        Returns the targets that were loaded via loadParams()
        """
        sm = _getData("smdt")
        # targets = sm.targetList.toJson()
        # roi = sm.getROIInfo()
        # return "{'info':" + json.dumps(roi) + ',' + "'targets':" + targets + "}", self.PlainTextType
        return sm.targetList.toJsonWithInfo(), self.PlainTextType

    @utils.tryEx
    def getMaskLayout(self, req, qstr):
        sm = _getData("smdt")
        return json.dumps(sm.getMaskLayout()), self.PlainTextType

    @utils.tryEx
    def recalculateMask(self, req, qstr):
        """
        Selects targets that are inside the mask and are not overlapping
        Recalculates the slit lengths (length1 and lenght2).
        Updates selected flag.
        """
        sm = _getData("smdt")
        currRaDeg = self.floatVal(qstr, "currRaDeg", 0)
        currDecDeg = self.floatVal(qstr, "currDecDeg", 0)
        currAngleDeg = self.floatVal(qstr, "currAngleDeg", 0)
        minSep = self.floatVal(qstr, "minSepAs", 0.5)
        minSlitLength = self.floatVal(qstr, "minSlitLengthAs", 8)
        extentSlits = self.intVal(qstr, "extendSlits", 1)
        try:
            sm.recalculateMask(currRaDeg, currDecDeg, currAngleDeg, minSlitLength, minSep, ext=extentSlits)
            return sm.targetList.toJsonWithInfo(), self.PlainTextType
        except Exception as e:
            print("Failed in recalculateMask", e)
            traceback.print_exc()
            pass

        return None, None

    @utils.tryEx
    def setColumnValue(self, req, qstr):
        sm = _getData("smdt")
        value = self.getDefValue(qstr, "value", "")
        colName = self.getDefValue(qstr, "colName", "")
        avalue = self.getDefValue(qstr, "avalue", "")
        if colName != "":
            sm.setColumnValue(colName, utils.asType(value), utils.asType(avalue))
            # sm.targetList.targets[colName] = utils.asType (value)
        return self.response("[]", self.PlainTextType)

    @utils.tryEx
    def updateTarget(self, req, qstr):
        sm = _getData("smdt")

        idx = sm.targetList.updateTarget(self.getDefValue(qstr, "values", ""))
        return self.response(f"[{idx}]", self.PlainTextType)

    @utils.tryEx
    def deleteTarget(self, req, qstr):
        sm = _getData("smdt")

        sm.targetList.deleteTarget(self.intVal(qstr, "idx", -1))
        return self.response("[]", self.PlainTextType)

    def saveMaskDesignFile(self, req, qstr):
        sm = _getData("smdt")
        mdFile = self.getDefValue(qstr, "mdFile", "mask.fits")
        try:
            prefix = os.path.splitext(mdFile)[0]
            # make sure extension is fits
            fitsname = os.path.realpath(prefix + ".fits")
            listname = os.path.realpath(prefix + ".out")
            fbase = os.path.basename(fitsname)
            lbase = os.path.basename(listname)
            dname = os.path.dirname(fitsname)
            fname, fbackupName = sm.saveDesignAsFits(fitsname)
            lname, lbackupName = sm.saveDesignAsList(listname)
            out = {
                "fitsname": fbase,
                "listname": lbase,
                "path": dname,
                "errstr": "OK",
                "fbackup": fbackupName,
                "lbackup": lbackupName,
            }
        except Exception as e:
            out = {"errstr": repr(e)}
        return self.response(json.dumps(out), self.PlainTextType)

    def quit(self, req, qstr):
        time.sleep(1)
        SMDTLogger.info("%s", "Terminated")
        os._exit(1)
        return self.response("[]", self.PlainTextType)

    def log_message(self, msg, *args):
        SMDTLogger.info(msg, *args)


class SMDesignServer:
    def __init__(self, host=None, portNr=50080):
        self.portNr = portNr
        if host is None:
            try:
                hostname = socket.gethostname()
            except:
                hostname = "localhost"
        else:
            # If the host has multiple network addresses, use the giving host name
            hostname = host

        self.host = hostname
        try:
            self.hostip = socket.gethostbyaddr(socket.gethostbyname(hostname))
        except:
            self.hostip = ""

    def _start(self):
        try:
            self.httpd = httpd = EasyHTTPServerThreaded(("", self.portNr), SMDesignHandler)
            print("HTTPD started {} ({}), port {}".format(self.host, self.hostip, self.portNr))
            try:
                httpd.serve_forever()
                httpd.shutdown()
            # except (KeyboardException, KeyboardInterrupt):
            #    pass
            except:
                print("HTTPD Terminated")
        except Exception as e:
            print("Failed to start HTTP Server", e)

    def start(self):
        thr = Thread(target=self._start)
        thr.start()


def readConfig(confName):
    def getPath(rpath, fname):
        if not os.path.isfile(fname):
            fname = f"{rpath}/{fname}"
            return fname
        return fname

    rpath = os.path.dirname(os.path.realpath(__file__))
    confName = getPath(rpath, confName)
    SMDTLogger.info(f"Loading config {confName}")
    cf = ConfigFile(confName)
    pf = ConfigFile(getPath(rpath, cf.paramFile))
    cf.properties["params"] = pf
    return cf


def initSignals(smd):
    def reallyQuit(signum, frame):
        try:
            smd.httpd.shutdown()
            os._exit(0)
        except Exception as e:
            pass
        return True

    def handler(signum, frame):
        for s in sigList:
            signal.signal(s, reallyQuit)
        print("\nPress Ctrl-C again to quit")
        time.sleep(2)
        print("Resuming ...")
        signal.signal(signal.SIGINT, handler)
        return False

    sigList = signal.SIGINT, signal.SIGQUIT, signal.SIGABRT
    for s in sigList:
        signal.signal(s, handler)

