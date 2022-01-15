#!/usr/bin/env python
# Test running MaskDesignFile
#
# Created: 2020-01-12, skwok
#
import sys
import os
import numpy as np
import logging
import argparse
import matplotlib.pyplot as plt

rpath = os.path.dirname(os.path.realpath(__file__))
sys.path.extend((rpath + "/smdtLibs",))

from configFile import ConfigFile
from targets import TargetList
from maskDesignFile import MaskDesignInputFitsFile
import maskLayouts
from smdtLibs import drawUtils, utils

logging.disable()


class DiffSlitMask:
    def __init__(self, fits1, fits2):
        self.fitsname1 = fits1
        self.fitsname2 = fits2
        self.mdf1 = MaskDesignInputFitsFile(fits1)
        self.mdf2 = MaskDesignInputFitsFile(fits2)
        self.allSlits = None

    def diffValues(self, v1, v2):
        return v1 - v2

    def calcDiffs(self):
        slits1 = self.mdf1.allSlits
        slits2 = self.mdf2.allSlits
        jCols = "OBJECT", "RA_OBJ", "DEC_OBJ", "EQUINOX"
        joined = slits1.merge (slits2, on=jCols, how="outer")
        self.joinedSlits = joined
        out = {}
        for a in "x", "y":
            for y in range(1, 5):
                name = f"{a}{y}"
                colName = f"slitX{y}"
                out[f"d{name}"] = self.diffValues(joined[colName+"_x"], joined[colName+"_y"])
        return out

    def printDiffs(self, diffs):
        format = ",".join(["{:4.2f}"] * 8)
        for row in zip(*diffs.values()):
            print(format.format(*row))

    
    def plotSlits (self):
        def genCode (x1, y1, x2, y2, x3, y3, x4, y4):
            slitXYs = []
            for xx1, yy1, xx2, yy2, xx3, yy3, xx4, yy4 in zip (x1, y1, x2, y2, x3, y3, x4, y4):
                slitXYs.append ((xx1, yy1, 0))
                slitXYs.append ((xx2, yy2, 1))
                slitXYs.append ((xx3, yy3, 1))
                slitXYs.append ((xx4, yy4, 1))
                slitXYs.append ((xx1, yy1, 2))                
            return slitXYs
        
        def getTargetPos (x1, y1, x2, y2, x3, y3, x4, y4):
            xLeft, yLeft = (x1 + x4) / 2, (y1 + y4) / 2
            xRight, yRight = (x2 + x3) / 2, (y2 + y3) / 2
            
            t = (allSlits.slitLen_y - allSlits.TopDist_y) / allSlits.slitLen_y

            targetOnSlitX = (xRight - xLeft) * t + xLeft
            targetOnSlitY = (yRight - yLeft) * t + yLeft
            return targetOnSlitX, targetOnSlitY
        
        layout = maskLayouts.MaskLayouts["deimos"]
        layoutMM = maskLayouts.scaleLayout(layout, utils.AS2MM, 0, -128)

        allSlits = self.joinedSlits

        codes1 = genCode (allSlits.slitX1_x,allSlits.slitY1_x,allSlits.slitX2_x,allSlits.slitY2_x,
            allSlits.slitX3_x,allSlits.slitY3_x,allSlits.slitX4_x,allSlits.slitY4_x)

        codes2 = genCode (allSlits.slitX1_y,allSlits.slitY1_y,allSlits.slitX2_y,allSlits.slitY2_y,
            allSlits.slitX3_y,allSlits.slitY3_y,allSlits.slitX4_y,allSlits.slitY4_y)

        drawUtils.drawPatch(plt.gca(), codes1, fc="None", ec="r", label=self.fitsname1)        
        drawUtils.drawPatch(plt.gca(), codes2, fc="None", ec="b", label=self.fitsname2)
        drawUtils.drawPatch(plt.gca(), layoutMM, fc="None", ec="y")


        xs, ys = getTargetPos(allSlits.slitX1_y,allSlits.slitY1_y,allSlits.slitX2_y,allSlits.slitY2_y,
            allSlits.slitX3_y,allSlits.slitY3_y,allSlits.slitX4_y,allSlits.slitY4_y)

        plt.plot (xs, ys, '.')
        plt.gca().invert_xaxis()
        plt.grid()
        plt.legend()


    def plotDiffs(self, diffs):
        slits1 = self.mdf1.allSlits
        x1, x2, x3, x4 = slits1.slitX1, slits1.slitX2, slits1.slitX3, slits1.slitX4
        y1, y2, y3, y4 = slits1.slitY1, slits1.slitY2, slits1.slitY3, slits1.slitY4

        fig, sps = plt.subplots(3, figsize=(10, 8))
        plt.subplot(311)
        self.plotSlits()

        plt.subplot(312)        
        plt.title ("Compare " + self.fitsname1 + " and " + self.fitsname2)
        plt.plot(x1, diffs["dx1"], ".", label="dX1")
        plt.plot(x2, diffs["dx2"], ".", label="dX2")
        plt.plot(x3, diffs["dx3"], ".", label="dX3")
        plt.plot(x4, diffs["dx4"], ".", label="dX4")
        plt.xlabel("Slit X position [mm]")
        plt.ylabel("X position Error [mm]")
        plt.legend()
        plt.grid()
        plt.tight_layout()

        plt.subplot(313)
        plt.plot(y1, diffs["dy1"], ".", label="dy1")
        plt.plot(y2, diffs["dy2"], ".", label="dy2")
        plt.plot(y3, diffs["dy3"], ".", label="dy3")
        plt.plot(y4, diffs["dy4"], ".", label="dy4")

        plt.xlabel("Slit Y position [mm]")
        plt.ylabel("Y Error [mm]")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.show()

    def projectTargetXYs(self, allSlits):
        """
        Takes the DSIM slits coordinates in mm,
        and builds the outline of the slits for plotting.
        
        Returns targetOnSlitX, targetOnSlitY from Slits (Dsim), slitXYs

        targetOnSlitX: list of X
        targetOnSlitY: list of Y
        slitsXYs: closed outline of the slit, ie the corners 0,1,2,3,0
        """

        slitXYs = []

        x1 = allSlits.slitX1
        y1 = allSlits.slitY1
        x2 = allSlits.slitX2
        y2 = allSlits.slitY2
        x3 = allSlits.slitX3
        y3 = allSlits.slitY3
        x4 = allSlits.slitX4
        y4 = allSlits.slitY4

        for xx1, yy1, xx2, yy2, xx3, yy3, xx4, yy4 in zip(x1, y1, x2, y2, x3, y3, x4, y4):
            slitXYs.append((xx1, yy1, 0))
            slitXYs.append((xx2, yy2, 1))
            slitXYs.append((xx3, yy3, 1))
            slitXYs.append((xx4, yy4, 1))
            slitXYs.append((xx1, yy1, 2))

        xLeft, yLeft = (x1 + x4) / 2, (y1 + y4) / 2
        xRight, yRight = (x2 + x3) / 2, (y2 + y3) / 2

        t = (allSlits.slitLen - allSlits.TopDist) / allSlits.slitLen

        targetOnSlitX = (xRight - xLeft) * t + xLeft
        targetOnSlitY = (yRight - yLeft) * t + yLeft

        return targetOnSlitX, targetOnSlitY, slitXYs


if __name__ == "__main__":
    epilog = """
    Compares the output from DSIM and Slitmask Design Tool.
    Plot and display the differences.
    """
    parser = argparse.ArgumentParser(
        description="Compares DSIM outputs", epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(dest="input1", help="Input1", nargs=1)
    parser.add_argument(dest="input2", help="Input2", nargs=1)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    diffTest = DiffSlitMask(args.input1[0], args.input2[0])
    diffs = diffTest.calcDiffs()
    # diffTest.printDiffs(diffs)
    diffTest.plotDiffs(diffs)