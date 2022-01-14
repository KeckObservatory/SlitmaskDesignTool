#!/usr/bin/env python3
"""
Main entry point for Slitmask design tool.

Created: 2021-11-18, skwok
"""
import os
import sys
import argparse

rpath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(rpath)

from slitmaskDesignServer import *
from smdtLibs import utils

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Slitmask design tool server", formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-c", "--config", dest="config_file", help="Configuration file", default="smdt.cfg", required=False)
    parser.add_argument("-H", "--host", dest="host", help="Manually specify host name", required=False, default=None)
    parser.add_argument("-b", "--browser", dest="browser", help="Start browser", action="store_true")
    parser.epilog = """
    Slitmask Design Tool.
    Starts a the server part of the Slitmask Design Tool. A user can connect to this server via a web-browser.
    """

    args = parser.parse_args()

    cfname = args.config_file
    cf = readConfig(cfname)

    SMDesignHandler.config = cf
    SMDesignHandler.setDocRoot(cf.getValue("docRoot", "docs"))
    SMDesignHandler.defaultFile = cf.getValue("defaultFile", "index.html")
    SMDesignHandler.logEnabled = cf.getValue("logEnabled", False)

    port = cf.getValue("serverPort", 50080)
    smd = SMDesignServer(args.host, port)
    smd.start()
    initSignals(smd)

    if args.browser:
        utils.launchBrowser(host=smd.host, portnr=port, path=SMDesignHandler.defaultFile + "?q=1")
