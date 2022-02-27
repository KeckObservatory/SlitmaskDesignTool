#
# Helper functions for distortion model
#
import numpy as np
from smdtLibs import utils
from astropy.modeling import models, fitting

from maskDesignFile import (
    MaskDesignInputFitsFile
)
from  diffSlitMask import genCode, getTargetPos


def projectTargetXYs(allSlits, scale=1.0):
    """
    Takes the DSIM slits coordinates in mm,
    and builds the outline of the slits for plotting.
    
    Returns targetOnSlitX, targetOnSlitY from Slits (Dsim), slitXYs
    targetOnSlitX: list of X
    targetOnSlitY: list of Y
    slitsXYs: closed outline of the slit, ie the corners 0,1,2,3,0
    """

    slitXYs = []

    x1 = allSlits.slitX1 * scale
    y1 = allSlits.slitY1 * scale
    x2 = allSlits.slitX2 * scale
    y2 = allSlits.slitY2 * scale
    x3 = allSlits.slitX3 * scale
    y3 = allSlits.slitY3 * scale
    x4 = allSlits.slitX4 * scale
    y4 = allSlits.slitY4 * scale

    for xx1, yy1, xx2, yy2, xx3, yy3, xx4, yy4 in zip(x1, y1, x2, y2, x3, y3, x4, y4):
        slitXYs.append((xx1, yy1, 0))
        slitXYs.append((xx2, yy2, 1))
        slitXYs.append((xx3, yy3, 1))
        slitXYs.append((xx4, yy4, 1))
        slitXYs.append((xx1, yy1, 2))

    xLeft, yLeft = (x1 + x4) / 2, (y1 + y4) / 2
    xRight, yRight = (x2 + x3) / 2, (y2 + y3) / 2

    t = allSlits.BotDist / (allSlits.TopDist + allSlits.BotDist)
    #t = (allSlits.slitLen - allSlits.TopDist) / allSlits.slitLen

    targetOnSlitX = (xRight - xLeft) * t + xLeft
    targetOnSlitY = (yRight - yLeft) * t + yLeft

    return targetOnSlitX, targetOnSlitY, slitXYs


@np.vectorize
def noopx(x, y):
    return x


@np.vectorize
def noopy(x, y):
    return y


def deplicated_projectTargets2Slits(targets, config, offx=0, offy=0, pfx=noopx, pfy=noopy):
    """
    Calculates the slits position for targets
    Returns slisXYs for plotting.
    """

    # Get slit length and width from configuration
    slitLen = config.params.minslitlength[0]
    slitWidth = config.params.slitwidth[0]
    slitWidth = 0.7
    slitHalf = slitLen / 2
    slitHWidth = slitWidth / 2

    slitXYs = []  # Stores slits coordinates in arcsec

    # print(f"Calculate slit positions, slit width = {slitWidth}")

    xarcs = targets.xarcs + offx
    yarcs = targets.yarcs + offy

    xarcs, yxarcs = pfx(xarcs, yarcs), pfy(xarcs, yarcs)

    top = targets.TopDist
    bot = targets.BotDist

    x0 = xarcs - top
    y0 = yarcs - slitHWidth

    x1 = xarcs + bot
    y1 = yarcs - slitHWidth

    x2 = xarcs + top
    y2 = yarcs + slitHWidth

    x3 = xarcs - top
    y3 = yarcs + slitHWidth

    for xx0, yy0, xx1, yy1, xx2, yy2, xx3, yy3 in zip(x0, y0, x1, y1, x2, y2, x3, y3):
        slitXYs.append((xx0, yy0, 0))
        slitXYs.append((xx1, yy1, 1))
        slitXYs.append((xx2, yy2, 1))
        slitXYs.append((xx3, yy3, 1))
        slitXYs.append((xx0, yy0, 2))

    return xarcs, yarcs, slitXYs


def deplicated_getMDF(designInfo):
    """
    Creates a Mask design fits file object
    Returns MDF object and center
    """
    (input_fname, input_RA, input_DEC, fieldPA, xxslitPA, enabled,) = designInfo  # Test_Inputs[objName]
    mdf = MaskDesignInputFitsFile(input_fname)

    cenRADeg = utils.sexg2Float(input_RA) * 15
    cenDECDeg = utils.sexg2Float(input_DEC)

    return mdf, cenRADeg, cenDECDeg


def fitModel(calcX, calcY, dsimX, dsimY, deg=4):
    """
    Fit the 4th deg 2D polynomial function to map from original to calculated.
    Returns the fitted X/Y.
    """
    pdeg = deg
    model0 = models.Polynomial2D(degree=pdeg)
    xfitter = fitting.LinearLSQFitter()
    yfitter = fitting.LinearLSQFitter()

    xfitted = xfitter(model0, calcX, calcY, dsimX)
    yfitted = yfitter(model0, calcX, calcY, dsimY)
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

def getXYmm(designInfo, config):
    (input_fname, input_RA, input_DEC, fieldPA, slittPA, enabled) = designInfo
    raDeg, decDeg = utils.sexg2Float(input_RA) * 15, utils.sexg2Float(input_DEC)

    mdf = MaskDesignInputFitsFile(input_fname)

    tg = mdf.getAsTargets(config)
    tg.reCalcCoordinates(raDeg, decDeg, fieldPA)
    tg.markInside()
    allTargets = tg.targets
    selectedTargets = allTargets[allTargets.inMask > 0]
    selectedTargets = selectedTargets[selectedTargets.pcode > 0]

    # jCols = "OBJECT", "RA_OBJ", "DEC_OBJ", "EQUINOX", "pcode"
    # joined = selectedTargets.merge(mdf.allSlits, on=jCols, how="left")

    # joined = joined[joined.pcode > 0]
    # joined = joined[joined.inMask_x > 0]

    dsimTargets = selectedTargets
    inDsims = dsimTargets

    dsimXs, dsimYs = getTargetPos(
        inDsims,
        "",
        inDsims.slitX1,
        inDsims.slitY1,
        inDsims.slitX2,
        inDsims.slitY2,
        inDsims.slitX3,
        inDsims.slitY3,
        inDsims.slitX4,
        inDsims.slitY4,
    )
    selectedTargets["dsimXs"] = dsimXs
    selectedTargets["dsimYs"] = dsimYs
    return mdf, selectedTargets

def calcDistortionCoef(designInfo, config, deg):
    """
    Fits model to map from xarcs/yarcs to targetX/targetY
    Return MaskDesign object, model
    """
    mdf, slits = getXYmm(designInfo, config)
    xmm, ymm = slits.xmm, slits.ymm
    dsimXs, dsimYs = slits.dsimXs, slits.dsimYs
    
    xfitted, yfitted = fitModel(xmm, ymm, dsimXs, dsimYs, deg)

    xresid = np.linalg.norm(dsimXs - xfitted(xmm, ymm))
    yresid = np.linalg.norm(dsimYs - yfitted(xmm, ymm))

    return mdf, xfitted, yfitted, xresid, yresid



def plotPairs(pairs, ecolor, y0, label):
    """
    To display gaps 
    """
    vertices = []
    codes = []
    as2mm = utils.AS2MM
    if len(pairs) == 0:
        return
    for i, ab in enumerate(pairs):
        y = y0 + (i % 2) * 20
        vertices.append((ab[0]*as2mm, y))
        vertices.append((ab[1]*as2mm, y))
        codes.append(path.Path.MOVETO)
        codes.append(path.Path.LINETO)

    slits = path.Path(vertices, codes)
    patch = patches.PathPatch(slits, facecolor=ecolor, edgecolor=ecolor, label=label)
    ax = plt.gca()
    ax.add_patch(patch)
    for i, ab in enumerate(pairs):
        y = y0 + (i % 2) * 20
        ax.annotate(
            f"{ab[3]}", xy=(ab[0]*as2mm, y0 + 0.2), xytext=((ab[0] + ab[1])*as2mm / 2, y + 0.2)
        )

