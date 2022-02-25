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
from diffSlitMask import DiffSlitMask

logging.disable()


class TestSlitmask:
    def __init__(self, inFile):

        config = ConfigFile(rpath + "/smdt.cfg")
        config.properties["params"] = ConfigFile(rpath + "/params.cfg")
        
        self.inFile = inFile
        self.config = config
        self.targetList = TargetList(inFile, config)
        instrument = self.config.getValue("instrument", "deimos").lower()
        self.sdt = SlitmaskDesignTool(self.targetList, instrument, config)

    def runDesign(self, slitLength, boxLength, slitWidth, minSep, ext):
        @np.vectorize
        def toFixed (x, m=8):
            return float(f"{x:.{m}f}")

        tlist = self.sdt.targetList.targets
        self.minSep = minSep
        self.minSlitLength = slitLength
        self.minABoxLength = boxLength
        self.slitWidth = slitWidth
        self.sdt.setColumnValue("TopDist", self.minSlitLength / 2, self.minABoxLength / 2)
        self.sdt.setColumnValue("BotDist", self.minSlitLength / 2, self.minABoxLength / 2)
        self.sdt.setColumnValue("slitWidth", self.slitWidth, self.minABoxLength)
        
        tlist = tlist[tlist.selected == 1].copy()
        
        self.targetList.targets = tlist
        targets = self.targetList

        raDeg, decDeg = targets.centerRADeg, targets.centerDEC
        paDeg = targets.positionAngle
        #tlist.loc[tlist.pcode > 0, "slitLPA"] = paDeg

        self.sdt.recalculateMask(raDeg, decDeg, paDeg, self.minSlitLength, self.minSep, ext)
        
        tlist = self.targetList.targets        
        tlist["RA_OBJ"] = toFixed(np.degrees(tlist.raRad))
        tlist["DEC_OBJ"] = toFixed(np.degrees(tlist.decRad))
        tlist['pcode'] = [min(1, x) for x in tlist.pcode]
        self.targetList.targets = tlist

def testMaskDesign(args):
    def checkNRemove (fname):    
        if os.path.exists(fname):
            if args.clobber:
                try: os.unlink(fname)
                except: pass
                return True
            else:
                print (f"File {fname} exists, will not overwrite")
                return False
        return True

    tester = TestSlitmask(args.input_file[0])
    tester.runDesign(args.slitLength, args.boxLength, args.slitWidth, args.minSep, args.extend)
    
    if args.output_file is not None:
        checkNRemove (args.output_file) and tester.sdt.saveDesignAsFits(args.output_file)

    if args.output_list is not None:
        checkNRemove(args.output_list) and tester.sdt.saveDesignAsList(args.output_list)

    diffFits = args.diffFits
    if diffFits is not None:
        output = args.output_file
        if output is None:
            output = tester.sdt.targetList.targets
            output = output[output.selected == 1]
        dsm = DiffSlitMask (diffFits, output)
        diffs = dsm.calcDiffs()
        dsm.plotDiffs (diffs)

    return tester, tester.targetList


if __name__ == "__main__":
    epilog = """
    Use the output file from DSIM as input,
    and generate the slitmask FITS and output file.
    The output should match the input.
    """
    parser = argparse.ArgumentParser(description="Slitmask design tool Tester", epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(dest="input_file", help="Input file", nargs=1)
    parser.add_argument("-o", "--output_file", help="Output Fits file", type=str)
    parser.add_argument("-t", "--output_list", help="Output list file", type=str)
    parser.add_argument("-l", "--slitLength", help="Slit length in arcsec", type=float, default=1)
    parser.add_argument("-a", "--boxLength", help="Alignment box size in arcsec", type=float, default=4)
    parser.add_argument("-w", "--slitWidth", help="Slit width in arcsec", type=float, default=0.7)
    parser.add_argument("-s", "--minSep", help="Min. separation in arcsec", type=float, default=0.35)
    parser.add_argument("-E", "--extend", help="Do not extend slits", action="store_false", default=True)
    parser.add_argument("-c", "--clobber", help="Overwrite output file", action="store_true", default=False)
    parser.add_argument("-d", "--diffFits", help="FITS file to compare with", type=str)
    
    try:
        args = parser.parse_args()
    except:
        sys.exit(0)

    if os.path.exists(args.input_file[0]):
        bname = os.path.basename (args.input_file[0])
        ext = bname.split(".")[-1]
        if ext == "fits":
            print ("Input file cannot be a fits file")
        else:
            testMaskDesign(args)
        sys.exit(0)
    else:
        print (f"File {args.input_file[0]} does not exist")
