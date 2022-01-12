#!/usr/bin/env python
# Test running MaskDesignFile
#
# Created: 2020-06-26, skwok
#
import sys
import os
import numpy as np
import logging
import argparse

rpath = os.path.dirname(os.path.realpath(__file__))
sys.path.extend((rpath + "/smdtLibs",))

from configFile import ConfigFile
from targets import TargetList
from slitmaskDesignTool import SlitmaskDesignTool

logging.disable()


class TestSlitmask:
    def __init__(self, inFile, config):
        self.inFile = inFile
        self.config = config
        self.targetList = TargetList(inFile, config)
        instrument = self.config.getValue("instrument", "deimos").lower()
        self.sdt = SlitmaskDesignTool(self.targetList, instrument, config)

    def runDesign(self, slitLength, boxLength, slitWidth, minSep, ext):
        tlist = self.targetList.targets
        self.minSep = minSep
        self.minSlitLength = slitLength
        self.minABoxLength = boxLength
        self.slitWidth = slitWidth
        self.sdt.setColumnValue("length1", self.minSlitLength / 2, self.minABoxLength / 2)
        self.sdt.setColumnValue("length2", self.minSlitLength / 2, self.minABoxLength / 2)
        self.sdt.setColumnValue("slitWidth", self.slitWidth, self.minABoxLength)

        tlist = tlist[tlist.selected == 1].copy()

        self.targetList.targets = tlist
        targets = self.targetList

        raDeg, decDeg = targets.centerRADeg, targets.centerDEC
        paDeg = targets.positionAngle
        tlist.loc[tlist.pcode > 0, "slitLPA"] = paDeg

        self.sdt.recalculateMask(raDeg, decDeg, paDeg, self.minSlitLength, self.minSep, ext)
        tlist = self.targetList.targets
        self.targetList.targets = tlist[tlist.selected == 1].copy()

    def saveDesignAsFits(self, outName):
        self.sdt.saveDesignAsFits(fname=outName)


def testMaskDesign(inFile, outName, slitLength, boxLength, slitWidth, minSep, ext, overw):
    config = ConfigFile(rpath + "/smdt.cfg")
    config.properties["params"] = ConfigFile(rpath + "/params.cfg")

    tester = TestSlitmask(inFile, config)
    tester.runDesign(slitLength, boxLength, slitWidth, minSep, ext)
    if outName is not None:
        if overw:
            try:
                os.unlink(outName)
            except:
                pass
        tester.saveDesignAsFits(outName)
    return tester, tester.targetList


if __name__ == "__main__":
    epilog = """
    Use the output file from DSIM as input,
    and generate the slitmask FITS and output file.
    The output should match the input.
    """
    parser = argparse.ArgumentParser(description="Slitmask design tool Tester", epilog=epilog)
    parser.add_argument(dest="input_file", help="Input file", nargs=1)
    parser.add_argument("-o", "--output_file", help="Output Fits file", type=str)
    parser.add_argument("-l", "--slitLength", help="Slit length in arcsec", default=1)
    parser.add_argument("-a", "--boxLength", help="Alignment box size in arcsec", default=4)
    parser.add_argument("-w", "--slitWidth", help="Slit width in arcsec", default=0.7)
    parser.add_argument("-s", "--minSep", help="Min. separation in arcsec", default=0.35)
    parser.add_argument("-e", "--extend", help="Extend slits", default=True)
    parser.add_argument("-c", "--clobber", help="Overwrite output file", action="store_true", default=False)

    args = parser.parse_args()
    inFile = args.input_file[0]
    outFile = args.output_file

    testMaskDesign(inFile, outFile, args.slitLength, \
        args.boxLength, args.slitWidth, args.minSep, args.extend, args.clobber)
    sys.exit(0)
