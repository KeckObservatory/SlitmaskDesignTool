#
# Test running configuration
#
# Created: 2020-06-26, skwok
#
import pytest
import sys

sys.path.append("../smdtLibs")
from configFile import ConfigFile


def test_config1():
    """
    Tests reading smdt.cfg
    """
    ccf = ConfigFile("../smdt.cfg")
    assert ccf.defaultfile == "DesignTool.html", "Unexpected value of defaultfile"


def test_config2():
    """
    Tests reading params.cfg
    """
    ccf = ConfigFile("../params.cfg")
    assert ccf.projectname[0] == "New Mask", "Unexpected value of projectname"


def test_config3():
    """
    Checks getting value
    """
    ccf = ConfigFile("../smdt.cfg")
    url = ccf.getValue("dssServerURL", "Failed")
    expectedUrl = "10.96.0.223:50041"
    assert url == expectedUrl, f"Unexpected URL {url}, expected {expectedUrl}"

    assert ccf.dssServerURL == expectedUrl, f"Failed to get attribute dssServerURL"

