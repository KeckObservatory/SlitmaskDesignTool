#
# Helper functions for distortion model
#

from targets import TargetList
from smdtLibs import utils

from astropy.modeling import models, fitting

from smdtLibs.inOutChecker import InOutChecker
from maskDesignFile import (
    MaskDesignInputFitsFile,
    MaskDesignOutputFitsFile,
    outputAsList,
)

def projectTargetXYs(allSlits, offx, offy):
    """
    Converts the DSIM slits coordinates in mm to arcsec,
    and builds the outline of the slits for plotting.
    
    Returns targetOnSlitX, targetOnSlitY from Slits (Dsim), slitXYs
    targetOnSlitX: list of X
    targetOnSlitY: list of Y
    slitsXYs: closed outline of the slit, ie the corners 0,1,2,3,0
    """

    slitXYs = [] 
    mm2as = utils.MM2AS

    x1 = allSlits.slitX1 * mm2as + offx
    y1 = allSlits.slitY1 * mm2as + offy
    x2 = allSlits.slitX2 * mm2as + offx
    y2 = allSlits.slitY2 * mm2as + offy
    x3 = allSlits.slitX3 * mm2as + offx
    y3 = allSlits.slitY3 * mm2as + offy
    x4 = allSlits.slitX4 * mm2as + offx
    y4 = allSlits.slitY4 * mm2as + offy
    
    for xx1, yy1, xx2, yy2, xx3, yy3, xx4, yy4 in zip (x1, y1, x2, y2, x3, y3, x4, y4):
        slitXYs.append ((xx1, yy1, 0))
        slitXYs.append ((xx2, yy2, 1))
        slitXYs.append ((xx3, yy3, 1))
        slitXYs.append ((xx4, yy4, 1))
        slitXYs.append ((xx1, yy1, 2))

    xLeft, yLeft = (x1 + x4) / 2, (y1 + y4) / 2
    xRight, yRight = (x2 + x3) / 2, (y2 + y3) / 2
    
    #t = allSlits.BotDist / (allSlits.TopDist + allSlits.BotDist)
    t = (allSlits.slitLen - allSlits.TopDist) / allSlits.slitLen

    targetOnSlitX = (xRight - xLeft) * t + xLeft
    targetOnSlitY = (yRight - yLeft) * t + yLeft

    return targetOnSlitX, targetOnSlitY, slitXYs


def getMDFSlits(designInfo):
    """
    Creates a Mask design fits file object
    Returns MDF object and the center
    """
    (
        input_fname,
        input_RA,
        input_DEC,
        fieldPA,
        xxslitPA,
        enabled,
    ) = designInfo  # Test_Inputs[objName]
    mdf = MaskDesignInputFitsFile(input_fname)

    cenRADeg = utils.sexg2Float(input_RA) * 15
    cenDECDeg = utils.sexg2Float(input_DEC)

    return mdf, cenRADeg, cenDECDeg


def fitModel(calcX, calcY, dsimX, dsimY):
    """
    Fit the 4th deg 2D polynomial function to map from original to calculated.
    Returns the fitted X/Y.
    """
    pdeg = 4
    model0 = models.Polynomial2D(degree=pdeg)
    fitter = fitting.LinearLSQFitter()

    xfitted = fitter(model0, calcX, calcY, dsimX)
    yfitted = fitter(model0, calcX, calcY, dsimY)
    return xfitted, yfitted


def applyDistortionCorrection(xs, ys, targetList):
    """
    Gets the distortion models (as functions) and applies to the xs and ys
    Returns corrected xs, and ys
    """
    xf, yf = targetList.getDistortionFunctions()
    pxs = xf(xs, ys)
    pys = yf(xs, ys)
    return pxs, pys


def project(designInfo, config, layout, offx, offy):
    """
    Given a designInfo, reads FITS file and the center.
    Then gets the targets coordinates and projects them onto the focal plane.

    xarcs,yarcs are the projected coordinates
    targetX, targetY are the DSIM coordinates

    Returns the MaskDesign object, the targets, xarcs, yarcs, targetX, targetY, slitsXY
    """
    mdf, cenRADeg, cenDECDeg = getMDFSlits(designInfo)

    # Gets targets as TargetList object
    tlist = mdf.getAsTargets(cenRADeg, cenDECDeg, config)
    tlist.markInside(layout)

    allTargets = tlist.targets
    allTargets = allTargets[allTargets.pcode > 0]

    # targetX, and targetY from DSIM
    targetX, targetY, slitXYs = projectTargetXYs(allTargets, offx, offy)

    return mdf, tlist, allTargets.xarcs, allTargets.yarcs, targetX, targetY, slitXYs


def calcDistortionCoef(designInfo, config, layout, offx, offy):
    """
    Fits model to map from xarcs/yarcs to targetX/targetY
    Return MaskDesign object, model
    """
    mdf, tlist, xarcs, yarcs, targetX, targetY, slitXYs = project(designInfo, config, layout, offx, offy)
    return mdf, fitModel(xarcs, yarcs, targetX, targetY)
