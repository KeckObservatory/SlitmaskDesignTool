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


import argparse
from SlitmaskDesignGlobals import smd, _set_data, _get_data
from SlitmaskDesignTool import SlitmaskDesignTool
from smdtLibs.configFile import ConfigFile
from flask import Flask
from SlitmaskDesignBlueprints import smdt

import logging
logging.config.fileConfig('logger.conf')


def read_config (confName):
    print ("Using config file ", confName)
    cf = ConfigFile(confName)
    pf = ConfigFile(cf.get('paramFile'), split=True)
    cf.properties['params'] = pf
    return cf


app = Flask(__name__)
app.config['SECRET_KEY'] = 'Your Secret Key'

app.register_blueprint(smdt)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Slitmask design tool server")
    parser.add_argument('-c', dest="config_file", help='Configuration file', default='smdt.cfg', required=False)

    args = parser.parse_args()
    cf = read_config(args.config_file)

    _set_data('smdt', SlitmaskDesignTool(b'', False, cf))

    smd.logger = app.logger
    smd.config = cf

    app.run(debug=True)
