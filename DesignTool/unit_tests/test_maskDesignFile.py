#
# Test running MaskDesignFile
#
# Created: 2020-06-26, skwok
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
from maskDesignFile import MaskDesignOutputFitsFile, MaskLayouts
import utils

logging.disable()


@pytest.fixture
def init_targets():
    config = ConfigFile("../smdt.cfg")
    config.properties["params"] = ConfigFile("../params.cfg")
    tlist = TargetList("../../DeimosExamples/MihoIshigaki/CetusIII.lst", config=config)
    return tlist, config


def test_targets(init_targets):
    tlist, config = init_targets
    tlist.positionAngle == 52
    raStr = utils.toSexagecimal(tlist.centerRADeg / 15).strip()
    decStr = utils.toSexagecimal(tlist.centerDEC).strip()
    assert raStr == "02:05:10.30" and decStr == "-04:15:11.50", "Unexpected ra and dec values"
    assert 318 == tlist.targets.shape[0], "Unexpected number of targets"


def test_MaskDesignFile(init_targets):
    tlist, config = init_targets
    ft = MaskDesignOutputFitsFile(tlist)
    fileout = "testout.fits"
    if os.path.exists(fileout):
        os.unlink(fileout)
    ft.writeTo(fileout)
    assert os.path.exists("testout.fits"), "Failed to create mask design file"


def test_MaskDesignFile2(init_targets):
    tlist, config = init_targets
    inOutChecker = InOutChecker(MaskLayouts[config.params.Instrument[0].lower()])
    for i, stg in tlist.targets.iterrows():
        if inOutChecker.checkPoint(stg.xarcs, stg.yarcs):
            tlist.targets.at[stg.orgIndex, "inMask"] = 1

    ft = MaskDesignOutputFitsFile(tlist)

    fileout = "testout.fits"
    if os.path.exists(fileout):
        os.unlink(fileout)
    ft.writeTo(fileout)

    assert os.path.exists("testout.fits"), "Failed to create mask design file"

