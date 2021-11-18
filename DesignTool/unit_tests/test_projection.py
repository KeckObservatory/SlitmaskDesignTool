#
# Test projection
#
# Created: 2021-08-06, skwok
#
import pytest
import sys
import os
import numpy as np
import logging

sys.path.extend(("..", "../smdtLibs"))
from configFile import ConfigFile
from targets import TargetList
from inOutChecker import InOutChecker
from maskDesignFile import MaskDesignInputFitsFile, MaskDesignOutputFitsFile, MaskLayouts
import utils

logging.disable()


@pytest.fixture
def init_targets():
    config = ConfigFile("../smdt.cfg")
    config.properties["params"] = ConfigFile("../params.cfg")
    prefix = "../../DeimosExamples/MihoIshigaki/"
    tlist = TargetList(prefix + "CetusIII.lst", config=config)
    mdf = MaskDesignInputFitsFile(prefix + "CetusIII.fits")
    return mdf, tlist, config


def test_proj1(init_targets):
    """
    Compares calculated coordinates (using TargetList) with the coordinates in the FITS file.
    """
    mdf, tlist, config = init_targets
    dsimXs, dsimYs = mdf.getObjOnSlit()

    # Calculate object coordinates
    selectedTargets = tlist.targets
    selectedTargets = selectedTargets[selectedTargets.selected > 0]
    selectedTargets = selectedTargets[selectedTargets.pcode > 0]
    calcXs, calcYs = selectedTargets.xmm, selectedTargets.ymm

    # Make sure they are the same objects
    inBoth = calcXs.index.join(dsimXs.index, how="inner")
    # Make them lists
    calcXs, calcYs, dsimXs, dsimYs = [x[inBoth] for x in (calcXs, calcYs, dsimXs, dsimYs)]

    # Apply disctortion
    pfx, pfy = tlist.getDistortionFunctions()
    calcXs, calcYs = pfx(calcXs, calcYs), pfy(calcXs, calcYs)

    xErr, yErr = np.mean(calcXs - dsimXs), np.mean(calcYs - dsimYs)
    assert xErr < 0.1 and yErr < 0.1, "Calculated coordinates do not match dsim's"

