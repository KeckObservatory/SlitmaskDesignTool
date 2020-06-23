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

from urllib.parse import quote
from threading import Thread

from smdtLibs import utils
from smdtLibs.easyHTTP import EasyHTTPHandler, EasyHTTPServer, EasyHTTPServerThreaded
from smdtLibs.configFile import ConfigFile
from SlitmaskDesignTool import SlitmaskDesignTool
from smdtLogger import SMDTLogger, infoLog
from MaskDesignFile import MaskDesignFile

GlobalData = {}


def _getData(_id):
    d = GlobalData.get(_id)
    if not d:
        d = SlitmaskDesignTool(b"", 0, None)
    return d


def _setData(_id, smdata):
    GlobalData[_id] = smdata


class SMDesignHandler(EasyHTTPHandler):
    PNGImage = "image/png"
    config = None

    def echo(self, req, qstr):
        return json.dumps(qstr), self.PlainTextType

    @utils.tryEx
    def sendTargets2Server(self, req, qstr):
        """
        Respond to the form action
        """
        content = qstr["targetList"][0]
        useDSS = self.intVal(qstr, "formUseDSS", 0)
        _setData("smdt", SlitmaskDesignTool(content, useDSS, self.config))
        return "OK", self.PlainTextType

    @utils.tryEx
    def getConfigParams(self, req, qstr):
        sm = _getData("smdt")
        paramData = self.config.get("params")
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
        return sm.drawDSSImage(), self.PNGImage

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
        inst = self.getDefValue(qstr, "instrument", "deimos")
        return json.dumps(sm.getMaskLayout(inst)), self.PlainTextType

    @utils.tryEx
    def recalculateMask(self, req, qstr):
        sm = _getData("smdt")
        vals = self.getDefValue(qstr, "insideTargets", "")
        currRaDeg = self.floatVal(qstr, "currRaDeg", 0)
        currDecDeg = self.floatVal(qstr, "currDecDeg", 0)
        currAngleDeg = self.floatVal(qstr, "currAngleDeg", 0)
        minSep = self.floatVal(qstr, "minSepAs", 0.5)
        minSlitLength = self.floatVal(qstr, "minSlitLengthAs", 8)
        boxSize = self.floatVal(qstr, "boxSize", 4)
        parts = vals.split(",")
        if len(parts):
            targetIdx = [int(x) for x in vals.split(",")]
            sm.recalculateMask(targetIdx, currRaDeg, currDecDeg, currAngleDeg, minSlitLength, minSep, boxSize)
            return sm.targetList.toJson(), self.PlainTextType
        return sm.targetList.toJson(), self.PlainTextType

    @utils.tryEx
    def setColumnValue(self, req, qstr):
        sm = _getData("smdt")
        value = self.getDefValue(qstr, "value", "")
        colName = self.getDefValue(qstr, "colName", "")
        if colName != "":
            sm.targetList.targets[colName] = value
        return "[]", self.PlainTextType

    @utils.tryEx
    def updateTarget(self, req, qstr):
        sm = _getData("smdt")

        sm.targetList.updateTarget(self.getDefValue(qstr, "values", ""))
        return "[]", self.PlainTextType

    def saveMaskDesignFile(self, req, qstr):
        sm = _getData("smdt")

        try:
            mdFile = self.getDefValue(qstr, "mdFile", "mask.fits")
            mdf = MaskDesignFile(sm.targetList)
            buf = mdf.asBytes()
        except Exception as e:
            self.send_error(500, repr(e))
            return None, "application/fits"

        self.send_response(200, "OK")
        self.send_header("Content-type", "application/fits")
        self.send_header("Content-Disposition", "attachment; filename=" + mdFile)
        self.end_headers()
        self.wfile.write(buf)
        self.wfile.flush()
        return None, "application/fits"

    @infoLog
    def quit(self, req, qstr):
        SMDTLogger.info("%s", "Terminated")
        os._exit(1)
        return self.response("[]", self.PlainTextType)

    def log_message(self, msg, *args):
        SMDTLogger.info(msg, *args)


class SWDesignServer:
    def __init__(self, host=None, portNr=50080):
        self.portNr = portNr
        if host is None:
            try:
                hostname = socket.gethostname()
            except:
                hostname = "localhost"
        else:
            hostname = host

        self.host = hostname
        try:
            self.hostip = socket.gethostbyaddr(socket.gethostbyname(hostname))
        except:
            self.hostip = ""

    def _start(self):
        try:
            httpd = EasyHTTPServerThreaded(("", self.portNr), SMDesignHandler)
            print("HTTPD started {} ({}), port {}".format(self.host, self.hostip, self.portNr))
            try:
                httpd.serve_forever()
                httpd.shutdown()
            except KeyboardException:
                pass
            except:
                print("HTTPD Terminated")
        except Exception as e:
            print("Failed to start HTTP Server", e)

    def start(self):
        thr = Thread(target=self._start)
        thr.start()


def readConfig(confName):
    print("Using config file ", confName)
    cf = ConfigFile(confName)
    pf = ConfigFile(cf.get("paramFile"), split=True)
    cf.properties["params"] = pf
    return cf


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Slitmask design tool server")
    parser.add_argument("-c", "--config", dest="config_file", help="Configuration file", default="smdt.cfg", required=False)
    parser.add_argument("-H", "--host", dest="host", help="Manually specify host name", required=False, default=None)
    parser.add_argument("-b", "--browser", dest="browser", help="Start browser", action="store_true")

    args = parser.parse_args()

    cf = readConfig(args.config_file)

    _setData("smdt", SlitmaskDesignTool(b"", False, cf))
    SMDesignHandler.config = cf
    SMDesignHandler.DocRoot = cf.get("docRoot", "docs")
    SMDesignHandler.defaultFile = cf.get("defaultFile", "index.html")
    SMDesignHandler.logEnabled = cf.get("logEnabled", False)

    port = cf.get("serverPort", 50080)
    smd = SWDesignServer(args.host, port)
    smd.start()

    if args.browser:
        utils.launchBrowser(host=smd.host, portnr=port, path=SMDesignHandler.defaultFile)
