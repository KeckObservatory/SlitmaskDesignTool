#
# Test running inOutChecker
#
# Created: 2020-06-26, skwok
#
import pytest
import sys


sys.path.extend(("..", "../smdtLibs"))
from inOutChecker import InOutChecker
from maskLayouts import MaskLayouts


def test_inOutChecker1():
    chk = InOutChecker(MaskLayouts["deimos"])
    pnt = 520, 100
    assert not chk.checkPoint(*pnt), f"Unexpected result for {pnt}"
