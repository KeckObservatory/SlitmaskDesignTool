from flask import Blueprint
from flask import session, escape, redirect, url_for
from flask import render_template, request, make_response
from SlitmaskDesignGlobals import smd, _get_data, _set_data
from MaskDesignFile import MaskDesignFile
from SlitmaskDesignTool import SlitmaskDesignTool

import json


def get_def_value(params, key, default):
    try:
        return params[key]
    except KeyError:
        return default


def float_val(params, key, default):
    try:
        return float(params[key])
    except KeyError:
        return float(default)


def int_val(params, key, default):
    return int(float_val(params, key, default))


smdt = Blueprint('smdt', __name__)


@smdt.route('/')
def welcome():
    if 'username' in session:
        print("You are already logged in as %s" % escape(session['username']))
        return render_template('DesignTool.html')
    else:
        print("No user is logged in")
        return redirect(url_for('smdt.login'))



@smdt.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('smdt.welcome'))
    return '''
    <form method='POST'>
    Enter your name: <input type='text' name='username'>
    <input type='submit' value='Login'>
    </form>'''


@smdt.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('smdt.welcome'))


@smdt.route('/getConfigParams', methods=['GET'])
def get_config_params():
    args = request.args
    sm = _get_data('smdt')
    paramData = smd.config.get('params')
    # print("Returning the following parameters:")
    # for property in paramData.properties:
    #    print(paramData.properties[property])
    return json.dumps({'params': paramData.properties})  # , self.PlainTextType


@smdt.route('/getMaskLayout', methods=['GET'])
def get_mask_layout():
    sm = _get_data('smdt')
    inst = request.args['instrument']
    return json.dumps(sm.getMaskLayout(inst))  # , self.PlainTextType


@smdt.route('/getDSSImage', methods=['GET'])
def get_dss_image():
    sm = _get_data('smdt')
    return sm.drawDSSImage(), smd.PNGImage


@smdt.route('/sendTargets2Server', methods=['POST', 'GET', 'PUT'])
def send_targets_2server():
    """
    Respond to the form action
    """
    content = request.files['targetList'].read()
    useDSS = int_val(request.form, 'formUseDSS', 0)
    _set_data('smdt', SlitmaskDesignTool(content, useDSS, smd.config))
    return 'OK'


@smdt.route('/getTargetsAndInfo', methods=['GET'])
def get_targets_and_info():
    """
    Returns the targets that were loaded via loadParams()
    """
    sm = _get_data('smdt')
    return sm.targetList.toJsonWithInfo()


@smdt.route('/getTargets', methods=['GET'])
def get_targets():
    """
    Returns the targets that were loaded via loadParams()
    """
    sm = _get_data('smdt')
    return sm.targetList.toJson()


@smdt.route('/getROIInfo', methods=['GET'])
def getROIInfo():
    sm = _get_data('smdt')
    out = sm.getROIInfo()
    return json.dumps(out)


@smdt.route('/recalculateMask', methods=['POST'])
def recalculate_mask():
    sm = _get_data('smdt')
    args = request.form
    # print(request.data)
    # print(request.args)
    # print(request.form)
    # print(request.values)
    # print(request.json)

    vals = get_def_value(args, 'insideTargets', '')
    curr_ra_deg = float_val(args, 'currRaDeg', 0)
    curr_dec_deg = float_val(args, 'currDecDeg', 0)
    curr_angle_deg = float_val(args, 'currAngleDeg', 0)
    min_sep = float_val(args, 'minSepAs', 0.5)
    min_slit_length = float_val(args, "minSlitLengthAs", 8)
    box_size = float_val(args, "boxSize", 4)
    parts = vals.split(',')
    if len(parts):
        target_idx = [int(x) for x in vals.split(',')]
        sm.recalculateMask(target_idx, curr_ra_deg, curr_dec_deg, curr_angle_deg, min_slit_length, min_sep, box_size)
        return sm.targetList.toJson()
    return sm.targetList.toJson()


@smdt.route('/setColumnValue', methods=['POST'])
def set_column_value():
    sm = _get_data('smdt')
    value = get_def_value(request.form, 'value', '')
    col_name = get_def_value(request.form, 'colName', '')
    if col_name != '':
        sm.targetList.targets[col_name] = value
    return "[]"


@smdt.route('/updateTarget', methods=['POST'])
def update_target():
    sm = _get_data('smdt')

    sm.targetList.updateTarget(get_def_value(request.form, 'values', ''))
    return "[]"


@smdt.route('/saveMaskDesignFile', methods=['GET', 'POST'])
def save_mask_design_file():
    """
    THIS IS NOT COMPLETE OR CORRECT
    :return:
    """
    sm = _get_data('smdt')

    try:
        md_file = get_def_value(request.form, 'mdFile', 'mask.fits')
        mdf = MaskDesignFile(sm.targetList)
        buf = mdf.asBytes()
    except Exception as e:
        # self.send_error(500, repr(e))
        return None, 'application/fits'

    response = make_response(buf)
    response.headers.set('Content-Type', 'application/fits')
    response.headers.set(
        'Content-Disposition', 'attachment', filename=md_file)
    return response
