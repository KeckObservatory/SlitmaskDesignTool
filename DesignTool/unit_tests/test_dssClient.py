#
# Test running Dss2Client
#
# Created: 2020-06-26, skwok
#
import pytest
import sys

sys.path.append("../smdtLibs")
from dss2Client import Dss2Client


def test_dss2client():
    url = "10.96.0.223:50041"
    raDeg = 10
    decDeg = 11
    sizeDeg = 0.3
    dss2 = Dss2Client(url)
    if dss2.ping():
        fits = dss2.getFITS(raDeg, decDeg, sizeDeg)
        assert fits is not None, f"Failed to get DSS image from {url}"
    else:
        # Server not reachable, it's OK is outside Keck.
        pass

