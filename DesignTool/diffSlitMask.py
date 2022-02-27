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
import pandas as pd
import matplotlib.pyplot as plt

from astropy.modeling import models, fitting

rpath = os.path.dirname(os.path.realpath(__file__))
sys.path.extend((rpath + "/smdtLibs",))

from configFile import ConfigFile
from targets import TargetList, ZPT_YM
from maskDesignFile import MaskDesignInputFitsFile
import maskLayouts
from smdtLibs import drawUtils, utils

logging.disable()


class DiffSlitMask:
    def __init__(self, fits1, fits2):
        self.fitsname1 = fits1
        mdf1 = MaskDesignInputFitsFile(fits1)
        self.mdf1 = mdf1
        self.allSlits1 = mdf1.allSlits
        #self.allSlits1 = self.allSlits1[self.allSlits1.dSlitId > 0]

        self.fitsname2 = "internal"
        if type(fits2) == type(pd.DataFrame()):
            self.allSlits2 = fits2
        elif type(fits2) == str:
            self.fitsname2 = fits2
            mdf2 = MaskDesignInputFitsFile(fits2)
            self.mdf2 = mdf2
            self.allSlits2 = mdf2.allSlits
        else: 
            return
        self._merge ()
    
    def diffValues(self, v1, v2):
        return v1 - v2

    def _merge(self):
        slits1 = self.allSlits1
        slits2 = self.allSlits2
        jCols = "OBJECT", "RA_OBJ", "DEC_OBJ", "EQUINOX",
        joined = slits1.merge (slits2, on=jCols, how="outer")
        joined['pcode'] = joined.pcode_y
        self.joinedSlits = joined
        self._calcTargetPositions()

    def calcDiffs (self):
        slits = self.joinedSlits
        slits = slits[slits.pcode > 0]     
        out = {}
        for a in "x", "y":
            for y in range(1, 5):
                name = f"{a}{y}"
                colName = f"slitX{y}"
                out[f"d{name}"] = self.diffValues(slits[colName+"_x"], slits[colName+"_y"])
        out["pcode"] = slits.pcode
        
        return out

    def _calcTargetPositions (self):
        allSlits = self.joinedSlits
        #allSlits = allSlits[allSlits.pcode > 0]                

        xs1, ys1 = getTargetPos(allSlits, "_x", allSlits.slitX1_x,allSlits.slitY1_x,allSlits.slitX2_x,allSlits.slitY2_x,
            allSlits.slitX3_x,allSlits.slitY3_x,allSlits.slitX4_x,allSlits.slitY4_x)

        xs2, ys2 = getTargetPos(allSlits, "_y", allSlits.slitX1_y,allSlits.slitY1_y,allSlits.slitX2_y,allSlits.slitY2_y,
            allSlits.slitX3_y,allSlits.slitY3_y,allSlits.slitX4_y,allSlits.slitY4_y)

        allSlits["xs1"] = xs1
        allSlits["ys1"] = ys1
        allSlits["xs2"] = xs2
        allSlits["ys2"] = ys2    

    def printDiffs(self, diffs):
        format = ",".join(["{:4.2f}"] * 8)
        for row in zip(*diffs.values()):
            print(format.format(*row))
    
    def plotSlits (self, annotate=False):
        
        layout = maskLayouts.MaskLayouts["deimos"]
        layoutMM = maskLayouts.scaleLayout(layout, utils.AS2MM, 0, -ZPT_YM)

        allSlits = self.joinedSlits
        aboxes = allSlits[allSlits.pcode < 0]
        allSlits = allSlits[allSlits.pcode > 0]

        codes1 = genCode (allSlits.slitX1_x,allSlits.slitY1_x,allSlits.slitX2_x,allSlits.slitY2_x,
            allSlits.slitX3_x,allSlits.slitY3_x,allSlits.slitX4_x,allSlits.slitY4_x)

        codes2 = genCode (allSlits.slitX1_y,allSlits.slitY1_y,allSlits.slitX2_y,allSlits.slitY2_y,
            allSlits.slitX3_y,allSlits.slitY3_y,allSlits.slitX4_y,allSlits.slitY4_y)

        boxCodes1 = genCode (aboxes.slitX1_x,aboxes.slitY1_x,aboxes.slitX2_x,aboxes.slitY2_x,
            aboxes.slitX3_x,aboxes.slitY3_x,aboxes.slitX4_x,aboxes.slitY4_x)

        boxCodes2 = genCode (aboxes.slitX1_y,aboxes.slitY1_y,aboxes.slitX2_y,aboxes.slitY2_y,
            aboxes.slitX3_y,aboxes.slitY3_y,aboxes.slitX4_y,aboxes.slitY4_y)
      
        ax = plt.gca()
        drawUtils.drawPatch(ax, boxCodes1, fc="None", ec='g', label="A.box1")
        drawUtils.drawPatch(ax, boxCodes2, fc="None", ec='k', label="A.box2")
            
        drawUtils.drawPatch(ax, codes1, fc="None", ec="r", label=os.path.basename(self.fitsname1)[-10:])        
        drawUtils.drawPatch(ax, codes2, fc="None", ec="b", label=os.path.basename(self.fitsname2)[-10:])
        drawUtils.drawPatch(ax, layoutMM, fc="None", ec="y")

        plt.plot (allSlits.xs1, allSlits.ys1, 'r.') 
        if annotate:
            drawUtils.annotate(ax, allSlits.OBJECT, allSlits.xs1, allSlits.ys1, color='r')
            drawUtils.annotate(ax, allSlits.OBJECT, allSlits.xs2, allSlits.ys2, color='b')
        
        plt.plot (allSlits.xs2, allSlits.ys2, 'b.')

        plt.gca().invert_xaxis()
        plt.grid()
        plt.legend()

    def calcSlitXY (self, slits):
        """
        Calculates the slit corners using slit ceneters in RA/DEC and lengths
        """
        slitRADeg = slits.slitRA 
        slitDec = slits.slitDec
        
        slitAngle = np.radians(slits.slitLPA-90)
        half = slits.slitLen / 2 / 3600
        cosdec = np.cos (np.radians(slitDec))

        sines = np.sin(slitAngle)
        cosines = np.cos(slitAngle)
        vx = cosines * half * cosdec
        vy = sines * half

        upX = sines * slits.slitWid/2 / 3600
        upY = cosines * slits.slitWid/2 / 3600

        leftX = slitRADeg - vx
        leftY = slitDec - vy
        rightX = slitRADeg + vx
        rightY = slitDec + vy

        x2 = leftX + upX
        y2 = leftY + upY
        
        x3 = leftX - upX
        y3 = leftY - upY

        x1 = rightX + upX
        y1 = rightY + upY
        
        x4 = rightX - upX
        y4 = rightY - upY
        return genCode(x1, y1, x2, y2, x3, y3, x4, y4)


    def plotSlitCenters (self, annotate=False):        
        """
        Plot slits using slits Center and slitlength, in arcsec
        """

        layout = maskLayouts.MaskLayouts["deimos"]

        allSlits = self.joinedSlits
        aboxes = allSlits[allSlits.pcode < 0]
        allSlits = allSlits[allSlits.pcode > 0]

        codes1 = self.calcSlitXY(self.allSlits2[self.allSlits2.pcode > 0])
      
        ax = plt.gca()

        drawUtils.drawPatch(ax, codes1, fc="None", ec="r", label=os.path.basename(self.fitsname1)[-10:])        
        #drawUtils.drawPatch(ax, layout, fc="None", ec="y")

        #plt.gca().invert_xaxis()
        plt.grid()
        plt.legend()

    def plotTargetDiffs (self): 
        allSlits = self.joinedSlits  
        allSlits = allSlits[allSlits.pcode > 0]
        dxs = allSlits.xs2-allSlits.xs1
        dys = allSlits.ys2-allSlits.ys1

        plt.subplot(312)        
        plt.title ("Diff target Xs and Ys " + self.fitsname1 + " and " + self.fitsname2)
        plt.plot(allSlits.xs2, dxs, "v", label="dXs")  
        plt.plot(allSlits.xs2, dys, "v", label="dYs")  

        plt.legend()
        plt.xlabel ("X position [mm]") 
        plt.ylabel("X or Y error [mm]")     
        plt.grid()
        plt.tight_layout()

        plt.subplot(313)
        plt.plot(allSlits.ys2, dxs, ".", label="dXs")
        plt.plot(allSlits.ys2, dys, ".", label="dYs")
        
        plt.legend()
        plt.xlabel("Y position [mm]")
        plt.ylabel("X or Y error [mm]")
        plt.grid()
        plt.tight_layout()


    def plotCorners (self, diffs):
        slits1 = self.allSlits2
        slits1 = slits1[slits1.pcode > 0]
        x1, x2, x3, x4 = slits1.slitX1, slits1.slitX2, slits1.slitX3, slits1.slitX4
        y1, y2, y3, y4 = slits1.slitY1, slits1.slitY2, slits1.slitY3, slits1.slitY4
        plt.subplot(312)        
        plt.plot(x1, diffs["dx1"], "v", label="dX1")
        plt.plot(x2, diffs["dx2"], "^", label="dX2")
        plt.plot(x3, diffs["dx3"], ".", label="dX3")
        plt.plot(x4, diffs["dx4"], ".", label="dX4")
        plt.xlabel("Slit X position [mm]")
        plt.ylabel("X position Error [mm]")
        plt.legend()
        plt.grid()
        plt.tight_layout()

        plt.subplot(313)
        plt.plot(y1, diffs["dy1"], "v", label="dy1")
        plt.plot(y2, diffs["dy2"], "^", label="dy2")
        plt.plot(y3, diffs["dy3"], ".", label="dy3")
        plt.plot(y4, diffs["dy4"], ".", label="dy4")

        plt.xlabel("Slit Y position [mm]")
        plt.ylabel("Y Error [mm]")
        
        plt.grid()
        plt.tight_layout()


    def plotDiffs(self, showDiffs=True):

        fig, sps = plt.subplots(3, figsize=(10, 8))
        plt.subplot(311)
        
        plt.title ("Compare " + self.fitsname1 + " and " + self.fitsname2)
        self.plotSlits()
        
        if showDiffs:
            self.plotTargetDiffs()
        else:
            self.plotCorners(self.calcDiffs())
        try:
            plt.show()
        except:
            print ("Keyboard interrupt.")
            pass

    def fitModel (self):
        xs2, ys2 = self.target2XYs
        xs1, ys1 = self.target1XYs

        pdeg = 1
        model0 = models.Polynomial2D(degree=pdeg)
        xfitter = fitting.LinearLSQFitter()
        yfitter = fitting.LinearLSQFitter()

        xfitted = xfitter(model0, xs2, ys2, xs1)
        yfitted = yfitter(model0, xs2, ys2, ys1)
        return xfitted, yfitted


def getTargetPos (allSlits, suffix, x1, y1, x2, y2, x3, y3, x4, y4):
    xLeft, yLeft = (x1 + x4) / 2, (y1 + y4) / 2
    xRight, yRight = (x2 + x3) / 2, (y2 + y3) / 2
    
    #t = (allSlits[f"slitLen{suffix}"] - allSlits[f"TopDist{suffix}"]) / allSlits[f"slitLen{suffix}"]
    botDist = allSlits[f"BotDist{suffix}"]
    t = botDist / (allSlits[f"TopDist{suffix}"] + botDist)
    targetOnSlitX = (xRight - xLeft) * t + xLeft
    targetOnSlitY = (yRight - yLeft) * t + yLeft
    return targetOnSlitX, targetOnSlitY


def genCode (x1, y1, x2, y2, x3, y3, x4, y4):
    slitXYs = []
    if len(x1) == 0: return slitXYs
    for xx1, yy1, xx2, yy2, xx3, yy3, xx4, yy4 in zip (x1, y1, x2, y2, x3, y3, x4, y4):
        slitXYs.append ((xx1, yy1, 0))
        slitXYs.append ((xx2, yy2, 1))
        slitXYs.append ((xx3, yy3, 1))
        slitXYs.append ((xx4, yy4, 1))
        slitXYs.append ((xx1, yy1, 2))                
    return slitXYs
    

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
    parser.add_argument ("-m", "--fitModel", help="Fit a model", action="store_true")

    try:
        args = parser.parse_args()
    except:
        sys.exit(0)

    diffTest = DiffSlitMask(args.input1[0], args.input2[0])
    diffs = diffTest.calcDiffs()
    
    if args.fitModel:
        xf, yf = diffTest.fitModel()
        print("X fit", list(zip(xf.param_names, xf.parameters)))
        print("Y fit", list(zip(yf.param_names, yf.parameters)))

    diffTest.plotDiffs(diffs)
