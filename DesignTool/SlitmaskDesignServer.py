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
import argparse

from urllib.parse import quote

from smdtLibs import utils
from smdtLibs.easyHTTP import EasyHTTPHandler, EasyHTTPServer, EasyHTTPServerThreaded
from smdtLibs.configFile import ConfigFile
from SlitmaskDesignTool import SlitmaskDesignTool
from smdtLogger import SMDTLogger, infoLog
from MaskDesignFile import MaskDesignFile

GlobalData = {}

from flask import Flask
from flask import render_template, request

def _getData(_id):
    d = GlobalData.get(_id)
    if not d:
        d = SlitmaskDesignTool(b'', 0, None)
    return d

    
def _setData(_id, smdata):
    GlobalData[_id] = smdata

class SMDesign():
    PNGImage = "image/png"

    def __init__(self):
        self.sm = _getData('smdt')
        self.config = None




class SMDesignHandler (EasyHTTPHandler):    
    PNGImage = "image/png"
    config = None

    def echo (self, req, qstr):
        return json.dumps(qstr), self.PlainTextType

    def log_message (self, msg, *args):
        SMDTLogger.info (msg, *args)

    
class SWDesignServer:

    def __init__(self):
        pass

    def start(self, port=50080, host='Auto'):
        if host=="Auto":
            hostname=socket.gethostname()
        else:
            hostname=host
        try:
            httpd = EasyHTTPServerThreaded (("", port), SMDesignHandler)
            #hostname = socket.gethostname()
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

# Flask conversion
app = Flask(__name__)

@app.route('/')
def welcome():
    return render_template('DesignTool.html')

@app.route('/getConfigParams', methods=['GET'])
def getConfigParams ():
    args = request.args
    sm = _getData('smdt')
    paramData = smd.config.get('params')
    return json.dumps({'params': paramData.properties}) #, self.PlainTextType

@app.route('/getMaskLayout', methods=['GET'])
def getMaskLayout ():
    sm = _getData('smdt')
    inst = request.args['instrument']
    return json.dumps(sm.getMaskLayout(inst)) #, self.PlainTextType

@app.route('/getDSSImage', methods=['GET'])
def getDSSImage ():
    sm = _getData('smdt')
    return sm.drawDSSImage(), smd.PNGImage

@app.route('/sendTargets2Server', methods=['POST', 'GET', 'PUT'])
def sendTargets2Server():
    """
    Respond to the form action
    """
    content = request.files['targetList'].read()
    useDSS = request.values['formUseDSS']
    _setData('smdt', SlitmaskDesignTool(content, useDSS, smd.config))
    return 'OK'

@app.route('/getTargetsAndInfo', methods=['GET'])
def getTargetsAndInfo():
    """
    Returns the targets that were loaded via loadParams()
    """
    sm = _getData('smdt')
    #targets = sm.targetList.toJson()
    #roi = sm.getROIInfo()
    #return "{'info':" + json.dumps(roi) + ',' + "'targets':" + targets + "}", self.PlainTextType
    return sm.targetList.toJsonWithInfo()

@app.route('/getTargets', methods=['GET'])
def getTargets():
    """
    Returns the targets that were loaded via loadParams()
    """
    sm = _getData('smdt')
    return sm.targetList.toJson()

@app.route('/getROIInfo', methods=['GET'])
def getROIInfo():
    sm = _getData('smdt')
    out = sm.getROIInfo()
    return json.dumps(out)

def getDefValue(params, key, default):
    try:
        return params[key]
    except:
        return default

def floatVal(params, key, default):
    try:
        return float(params[key])
    except:
        return float(default)
    

@app.route('/recalculateMask', methods=['POST'])
def recalculateMask():
    sm = _getData('smdt')
    args = request.form
    #print(request.data)
    #print(request.args)
    #print(request.form)
    #print(request.values)
    #print(request.json)

    vals = getDefValue(args, 'insideTargets', '')
    currRaDeg = floatVal(args, 'currRaDeg', 0)
    currDecDeg = floatVal(args, 'currDecDeg', 0)
    currAngleDeg = floatVal(args, 'currAngleDeg', 0)
    minSep = floatVal(args, 'minSepAs', 0.5)
    minSlitLength = floatVal(args, "minSlitLengthAs", 8)
    boxSize = floatVal(args, "boxSize", 4)
    parts = vals.split(',')
    if len(parts):
        targetIdx = [int(x) for x in vals.split(',')]
        sm.recalculateMask(targetIdx, currRaDeg, currDecDeg, currAngleDeg, minSlitLength, minSep, boxSize)
        return sm.targetList.toJson()
    return sm.targetList.toJson()

@app.route('/setColumnValue', methods=['POST'])
def setColumnValue():
    sm = _getData('smdt')
    value = getDefValue(request.form, 'value', '')
    colName = getDefValue(request.form, 'colName', '')
    if colName != '':
        sm.targetList.targets[colName] = value
    return "[]"


@app.route('/updateTarget', methods=['POST'])
def updateTarget():
    sm = _getData('smdt')

    sm.targetList.updateTarget(getDefValue(request.form, 'values', ''))
    return "[]"

@app.route('/saveMaskDesignFile', methods=['POST'])
def saveMaskDesignFile():
    """
    THIS IS NOT COMPLETE OR CORRECT
    :return:
    """
    sm = _getData('smdt')

    try:
        mdFile = getDefValue(request.form, 'mdFile', 'mask.fits')
        mdf = MaskDesignFile(sm.targetList)
        buf = mdf.asBytes()
    except Exception as e:
        self.send_error(500, repr(e))
        return None, 'application/fits'

    self.send_response(200, 'OK')
    self.send_header('Content-type', 'application/fits')
    self.send_header('Content-Disposition', 'attachment; filename=' + mdFile)
    self.end_headers()
    self.wfile.write(buf)
    self.wfile.flush()
    return None, 'application/fits'



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Slitmask design tool server")
    parser.add_argument('-c', dest="config_file", help='Configuration file', default='smdt.cfg', required=False)
    parser.add_argument('-host', dest="host", help='Manually specify host name', required=False, default="Auto")

    args = parser.parse_args()

    configName = args.config_file
    #smd = SWDesignServer()
    cf = readConfig (configName)

    _setData('smdt', SlitmaskDesignTool(b'', False, cf))
    #SMDesignHandler.config = cf
    #SMDesignHandler.DocRoot = cf.get('docRoot', 'docs')
    #SMDesignHandler.defaultFile = cf.get('defaultFile', 'index.html')
    #SMDesignHandler.logEnabled = cf.get('logEnabled', False)
    host = args.host
    #smd.start(cf.get('serverPort', 50080), host)

    smd = SMDesign()
    smd.config = cf

    app.run(debug=True)
        
