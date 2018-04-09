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

GlobalData = {}


def _getData(_id):
    d = GlobalData.get(_id)
    return SlitmaskDesignTool(b'') if not d else d 

def _setData(_id, smdata):
    GlobalData[_id] = smdata


class SMDesignHandler (EasyHTTPHandler):    
    PNGImage = "image/png"

    def echo (self, req, qstr):
        return self.response(json.dumps(qstr), self.PlainTextType)
    
    @utils.tryEx
    def loadParams (self, req, qstr):        
        content = qstr['targetList'][0]
        _setData('smdt', SlitmaskDesignTool(content))
        print ("uploaded")
        return self.response('OK', self.PlainTextType)
    
    @utils.tryEx
    def getTargets (self, req, qstr):
        sm = _getData('smdt')
        return self.response(sm.targetList.toJson(), self.PNGImage)        
    
    @utils.tryEx 
    def getDSSImage (self, req, qstr):
        sm = _getData('smdt')        
        return self.response(sm.drawDSSImage(), self.PNGImage)
    
    @utils.tryEx 
    def getROIInfo (self, req, qstr):
        sm = _getData('smdt')
        
            
        out = sm.getDSSInfo()    
            
        """
        return tl.dssSizeDeg, hdr.platescl, hdr.xpsize, hdr.ypsize, \
            hdr.getHeader('NAXIS1', 0), hdr.getHeader('NAXIS2', 0)
            
        dssSize, pltScale, xpsize, ypsize, xsize, ysize = sm.getDSSInfo ()
        
        out = {'dssSize': dssSize, 'dssPlatescale': pltScale,
            'xpsize': xpsize, 'ypsize': ypsize,
            'xsize': xsize, 'ysize': ysize }
        """
        return self.response(json.dumps(out), self.PlainTextType)
        
    def quit (self, req, qstr):
        print("req", req, qstr)
        self.log_message("%s", "Terminated")
        os._exit(1)
        return self.response('[]', self.PlainTextType)

    
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
        SMDesignHandler.DocRoot = cf.get('docRoot', 'docs')
        SMDesignHandler.logEnabled = cf.get('logEnabled', False)       
        smd.start(cf.get('port', 50080))
        
    except Exception as e:
        print(e, file=sys.stderr)
        printUsage()
