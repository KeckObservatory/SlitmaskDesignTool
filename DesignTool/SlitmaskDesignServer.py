'''
Created on Mar 20, 2018

The request sequence is:
- Browser sendTargets2Server via form submit ('loadParams')
- Server responds OK
- Browser onload calls loadAll(), which includes loadMaskLayout, loadBackgroundImage, loadTargets()
- Server loadMaskLayout -> getMaskLayout returns mask and reducedMask layouts
- server lackBackgroundImage -> loads DSS image into canvas background
- Server loadTargets -> getTargetsAndInfo loads target list and info, such as center RA/DEC, sky PA and scales

@author: skwok
'''

import socket
import json
import sys
import os

from smdtLibs import utils
from smdtLibs.easyHTTP import EasyHTTPHandler, EasyHTTPServer, EasyHTTPServerThreaded
from smdtLibs.configFile import ConfigFile
from SlitmaskDesignTool import SlitmaskDesignTool
from smdtLogger import SMDTLogger, infoLog
#from anaconda_navigator.config import value

GlobalData = {}


def _getData(_id):
    d = GlobalData.get(_id)
    if not d:
        d = SlitmaskDesignTool(b'', 0, None)
    return d
    
def _setData(_id, smdata):
    GlobalData[_id] = smdata

class SMDesignHandler (EasyHTTPHandler):    
    PNGImage = "image/png"
    config = None

    def echo (self, req, qstr):
        return json.dumps(qstr), self.PlainTextType
    
    @utils.tryEx
    def sendTargets2Server (self, req, qstr):
        """
        Respond to the form action
        """        
        content = qstr['targetList'][0]    
        useDSS = self.intVal(qstr, 'formUseDSS', 0) 
        _setData('smdt', SlitmaskDesignTool(content, useDSS, self.config))
        return 'OK', self.PlainTextType
    
    @utils.tryEx 
    def getConfigParams (self, req, qstr):
        sm = _getData('smdt')
        paramData = self.config.get('params')
        return json.dumps({'params': paramData.properties}), self.PlainTextType
        
    @utils.tryEx   
    def getTargets (self, req, qstr):
        """
        Returns the targets that were loaded via loadParams()
        """
        sm = _getData('smdt')
        return sm.targetList.toJson(), self.PlainTextType       
    
    
    @utils.tryEx 
    def getDSSImage (self, req, qstr):
        sm = _getData('smdt')  
        return sm.drawDSSImage(), self.PNGImage
    
    @utils.tryEx 
    def getROIInfo (self, req, qstr):
        sm = _getData('smdt')        
        out = sm.getROIInfo() 
        return json.dumps(out), self.PlainTextType
    
    @utils.tryEx 
    def getTargetsAndInfo (self, req, qstr):        
        """
        Returns the targets that were loaded via loadParams()
        """
        sm = _getData('smdt')
        #targets = sm.targetList.toJson()             
        #roi = sm.getROIInfo()
        #return "{'info':" + json.dumps(roi) + ',' + "'targets':" + targets + "}", self.PlainTextType
        return sm.targetList.toJsonWithInfo(), self.PlainTextType 
    
    @utils.tryEx
    def getMaskLayout (self, req, qstr):        
        sm = _getData('smdt')        
        inst = self.getDefValue (qstr, 'instrument', 'deimos')
        return json.dumps(sm.getMaskLayout(inst)), self.PlainTextType
    
    @utils.tryEx 
    def recalculateMask (self, req, qstr):
        sm = _getData('smdt')
        vals = self.getDefValue(qstr, 'insideTargets', '')
        currRaDeg = self.floatVal(qstr, 'currRaDeg', 0)
        currDecDeg = self.floatVal(qstr, 'currDecDeg', 0)
        currAngleDeg = self.floatVal(qstr, 'currAngleDeg', 0)
        minSep = self.floatVal(qstr, 'minSepAs', 0.5)
        minSlitLength = self.floatVal (qstr, "minSlitLengthAs", 8)
        boxSize = self.floatVal (qstr, "boxSize", 4)
        parts = vals.split(',')
        if len(parts):
            targetIdx = [int(x) for x in vals.split(',')]        
            sm.recalculateMask (targetIdx, currRaDeg, currDecDeg, currAngleDeg, minSlitLength, minSep, boxSize)
            return sm.targetList.toJson(), self.PlainTextType
        return sm.targetList.toJson(), self.PlainTextType
    
    @utils.tryEx 
    def setColumnValue (self, req, qstr):
        sm = _getData('smdt')
        value = self.getDefValue(qstr, 'value', '')
        colName = self.getDefValue(qstr, 'colName', '')
        if colName != '':
            sm.targetList.targets[colName] = value
        return  "[]", self.PlainTextType
        
    @utils.tryEx 
    def updateTarget (self, req, qstr):
        sm = _getData('smdt')
        
        sm.targetList.updateTarget(self.getDefValue(qstr, 'values', ''))
        return "[]", self.PlainTextType
    
    @infoLog
    def quit (self, req, qstr):        
        SMDTLogger.info ("%s", "Terminated")
        os._exit(1)
        return self.response('[]', self.PlainTextType)

    def log_message (self, msg, *args):
        SMDTLogger.info (msg, *args)
    
class SWDesignServer:

    def __init__(self):
        pass

    def start(self, port=50080):
        try:
            httpd = EasyHTTPServerThreaded (("", port), SMDesignHandler)
            hostname = socket.gethostname()
            print ("HTTPD started %s %d" % (socket.gethostbyaddr(socket.gethostbyname(hostname)), port))
            try:
                httpd.serve_forever()
                httpd.shutdown()
            except:
                print ("HTTPD Terminated")
        except Exception as e:
            print ("Failed to start HTTP Server", e)
    

def readConfig (confName):
    print ("Using config file ", confName)
    cf = ConfigFile(confName)
    pf = ConfigFile(cf.get('paramFile'), split=True)
    cf.properties['params'] = pf
    return cf
    
if __name__ == "__main__":
    def printUsage():
        print("\nUsage: %s configFile" % sys.argv[0])        
        os._exit(1)
        
    try:
        configName = 'smdt.cfg'
        smd = SWDesignServer() 
        if len(sys.argv) > 1:
            fn = sys.argv[1]
            if os.path.isfile(fn):
                configName = fn
        
        cf = readConfig (configName)
        
        _setData('smdt', SlitmaskDesignTool(b'', False, cf))
        SMDesignHandler.config = cf
        SMDesignHandler.DocRoot = cf.get('docRoot', 'docs')
        SMDesignHandler.defaultFile = cf.get('defaultFile', 'index.html')
        SMDesignHandler.logEnabled = cf.get('logEnabled', False)       
        smd.start(cf.get('serverPort', 50080))
        
    except Exception as e:
        print(e, file=sys.stderr)
        printUsage()
