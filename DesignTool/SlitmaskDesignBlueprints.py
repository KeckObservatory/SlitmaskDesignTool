from flask import Blueprint
from flask import session, escape, redirect, url_for
from flask import render_template, request, make_response
from SlitmaskDesignGlobals import smd, _getData, _setData
from MaskDesignFile import MaskDesignFile
from SlitmaskDesignTool import SlitmaskDesignTool

import json


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

def intVal(params, key, default):
    return int(floatVal(params,key,default))

test = Blueprint('test', __name__)

@test.route('/test', methods=['GET'])
def test_api():
    print(main.sm)
    return 'OK'

smdt = Blueprint('smdt', __name__)

@smdt.route('/')
def welcome():
    if 'username' in session:
        print("You are already logged in as %s" % escape(session['username']))
    else:
        print("No user is logged in")
        return (redirect(url_for('login')))
    return render_template('DesignTool.html')


@smdt.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('welcome'))
    return '''
    <form method='POST'>
    Enter your name: <input type='text' name='username'>
    <input type='submit' value='Login'>
    </form>'''


@smdt.route('/logout')
def logout():
    session.pop('username', None)
    return (redirect(url_for('smdt.welcome')))


@smdt.route('/getConfigParams', methods=['GET'])
def getConfigParams():
    args = request.args
    sm = _getData('smdt')
    paramData = smd.config.get('params')
    # print("Returning the following parameters:")
    # for property in paramData.properties:
    #    print(paramData.properties[property])
    return json.dumps({'params': paramData.properties})  # , self.PlainTextType


@smdt.route('/getMaskLayout', methods=['GET'])
def getMaskLayout():
    sm = _getData('smdt')
    inst = request.args['instrument']
    return json.dumps(sm.getMaskLayout(inst))  # , self.PlainTextType


@smdt.route('/getDSSImage', methods=['GET'])
def getDSSImage():
    sm = _getData('smdt')
    return sm.drawDSSImage(), smd.PNGImage


@smdt.route('/sendTargets2Server', methods=['POST', 'GET', 'PUT'])
def sendTargets2Server():
    """
    Respond to the form action
    """
    content = request.files['targetList'].read()
    useDSS = intVal(request.form, 'formUseDSS', 0)
    _setData('smdt', SlitmaskDesignTool(content, useDSS, smd.config))
    return 'OK'


@smdt.route('/getTargetsAndInfo', methods=['GET'])
def getTargetsAndInfo():
    """
    Returns the targets that were loaded via loadParams()
    """
    sm = _getData('smdt')
    return sm.targetList.toJsonWithInfo()


@smdt.route('/getTargets', methods=['GET'])
def getTargets():
    """
    Returns the targets that were loaded via loadParams()
    """
    sm = _getData('smdt')
    return sm.targetList.toJson()


@smdt.route('/getROIInfo', methods=['GET'])
def getROIInfo():
    sm = _getData('smdt')
    out = sm.getROIInfo()
    return json.dumps(out)


@smdt.route('/recalculateMask', methods=['POST'])
def recalculateMask():
    sm = _getData('smdt')
    args = request.form
    # print(request.data)
    # print(request.args)
    # print(request.form)
    # print(request.values)
    # print(request.json)

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


@smdt.route('/setColumnValue', methods=['POST'])
def setColumnValue():
    sm = _getData('smdt')
    value = getDefValue(request.form, 'value', '')
    colName = getDefValue(request.form, 'colName', '')
    if colName != '':
        sm.targetList.targets[colName] = value
    return "[]"


@smdt.route('/updateTarget', methods=['POST'])
def updateTarget():
    sm = _getData('smdt')

    sm.targetList.updateTarget(getDefValue(request.form, 'values', ''))
    return "[]"


@smdt.route('/saveMaskDesignFile', methods=['GET', 'POST'])
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
        # self.send_error(500, repr(e))
        return None, 'application/fits'

    response = make_response(buf)
    response.headers.set('Content-Type', 'application/fits')
    response.headers.set(
        'Content-Disposition', 'attachment', filename=mdFile)
    return response
