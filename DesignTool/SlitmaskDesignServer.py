'''
Created on Mar 20, 2018

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
        return self.response(json.dumps(qstr), self.PlainTextType)
    
    @utils.tryEx
    def loadParams (self, req, qstr):
        """
        Respond to the form action
        """        
        content = qstr['targetList'][0]    
        useDSS = self.intVal(qstr, 'formUseDSS', 0) 
        _setData('smdt', SlitmaskDesignTool(content, useDSS, self.config))
        return self.response('OK', self.PlainTextType)
    
    @utils.tryEx   
    def getTargets (self, req, qstr):
        """
        Returns the targets that were loaded via loadParams()
        """
        sm = _getData('smdt')
        return self.response(sm.targetList.toJson(), self.PlainTextType)        
    
    @utils.tryEx 
    @infoLog
    def getDSSImage (self, req, qstr):
        sm = _getData('smdt')  
        return self.response(sm.drawDSSImage(), self.PNGImage)
    
    @utils.tryEx 
    def getROIInfo (self, req, qstr):
        sm = _getData('smdt')        
        out = sm.getDSSInfo() 
        return self.response(json.dumps(out), self.PlainTextType)
    
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
    

if __name__ == "__main__":
    """
    Param1: port number
    """

    def printUsage():
        print("\nUsage: %s configFile" % sys.argv[0])        
        os._exit(1)
        
    try:
        defConfigName = 'smdt.cfg'
        smd = SWDesignServer() 
        if len(sys.argv) > 1:
            fn = sys.argv[1]
            if os.path.isfile(fn):
                defConfigName = fn
        print ("Using config file ", defConfigName)
        cf = ConfigFile(defConfigName)
        SMDesignHandler.config = cf
        SMDesignHandler.DocRoot = cf.get('docRoot', 'docs')
        SMDesignHandler.logEnabled = cf.get('logEnabled', False)       
        smd.start(cf.get('port', 50080))
        
    except Exception as e:
        print(e, file=sys.stderr)
        printUsage()
