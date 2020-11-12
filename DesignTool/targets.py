"""
Created on Mar 20, 2018

@author: skwok
"""

import math
import os

os.environ["NUMEXPR_MAX_THREADS"] = "4"
os.environ["NUMEXPR_NUM_THREADS"] = "4"
import io
import sys
import numpy as np
import pandas as pd
import traceback
import json
import datetime

from smdtLibs import utils, dss2Header
from smdtLibs.inOutChecker import InOutChecker
from smdtLogger import SMDTLogger
from targetSelector import TargetSelector

if sys.version_info.minor < 7:

    class MyJsonEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.int64):
                return int(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return super(MyEncoder, self).default(obj)


else:
    MyJsonEncoder = json.JSONEncoder


class TargetList:
    """
    This class represents the Slitmask Design Tool target list.
    The input and output lists have the same format.
    Note that some colunms are optional.

    If line contains 'PA=nnnn' then the format is
        name RA DEC Eqn PA=nnnnn
        
    Columns of the input file:
        name: 16 chars, no white space
        ra: right ascension in hour
        dec: declination in deg
        equinox: 2000
        magn: magnitude
        passband: V, I, ...
        priority: high +value = high priority, -2:align, -1:guide star, 0: ignore
        
        Optional:
        sampleNr: 1,2,3
        selected: 0
        slitWPA: PA of the slit
        length1: 4
        length2: 4
        slitWidth: 1
    
    Input can be a string, a pandas data frame, or a file.
    After reading the input, the targets are stored in a pandas data frame.
    Then targets are projected on the the focal plane, via loadDSSInfo.
    If DSS is not desired (default) then the DSS image is a blank image and
    a header is generated using WCS using cenRA/cenDEC.

    """

    def __init__(self, input, raDeg=0, decDeg=0, paDeg=0, config=None):
        """
        Reads the target list from file of from string.
        """
        self.positionAngle = paDeg
        self.centerRADeg = raDeg
        self.centerDEC = decDeg
        self.config = config
        self.fileName = None
        if type(input) == type(io.StringIO()):
            self.targets = self.readRaw(input)
        elif type(input) == type(pd.DataFrame()):
            self.targets = input
        else:
            self.fileName = input
            self.targets = self.readFromFile(input)
        self.project2FocalPlane()
        self.__updateDate()

    def __updateDate(self):
        """
        Remembers the creation date.
        """
        self.createDate = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def project2FocalPlane(self):
        targets = self.targets
        if len(targets) <= 0:
            raDeg, decDeg = 0, 0
        else:
            raDeg, decDeg = self.centerRADeg, self.centerDEC

            w = h = 60 # 1 min
            self.fheader = dss2Header.DssWCSHeader(raDeg, decDeg, w, h)
            self.reCalcCoordinates(raDeg, decDeg, self.positionAngle)

    def _checkPA(self, inParts):
        """
        Checks if input line contains the center RA/DEC and PA
        Use in readRaw
        """
        paStr = inParts[3].upper()
        if "PA=" in paStr:
            parts0 = paStr.split("=")
            self.positionAngle = float(parts0[1])
            self.centerRADeg = utils.sexg2Float(inParts[0]) * 15
            self.centerDEC = utils.sexg2Float(inParts[1])
            # print ("Here", self.centerRADeg, self.centerDEC);
            return True
        else:
            return False

    def readFromFile(self, fname):
        """
        Reads target list from file
        Returns a Pandas dataframe
        """
        with open(fname, "r") as fh:
            return self.readRaw(fh)

    def readRaw(self, fh):
        """
        Reads target list from file handle
        Returns a Pandas dataframe
        """

        def toFloat(x):
            try:
                return float(x)
            except:
                return 0

        out = []
        cols = (
            "objectId",
            "raHour",
            "decDeg",
            "eqx",
            "mag",
            "pBand",
            "pcode",
            "sampleNr",
            "selected",
            "slitWPA",
            "length1",
            "length2",
            "slitWidth",
            "orgIndex",
            "inMask",
        )
        cnt = 0
        for nr, line in enumerate(fh):
            if not line:
                continue
            line = line.strip()
            p1, p2, p3 = line.partition("#")
            parts = p1.split()
            if len(parts) == 0:
                # line empty
                continue
            objectId = parts[0]
            parts = parts[1:]
            if len(parts) < 4:
                continue
            # print (nr, "len", parts)

            template = ["", "", "2000", "99", "I", "99", "0", "1", "0", "4.0", "4.0", "1.5", "0"]
            minLength = min(len(parts), len(template))
            template[:minLength] = parts[:minLength]
            if self._checkPA(parts):
                continue

            sampleNr, selected, slitWPA, length1, length2, slitWidth = 1, 1, 0, 4, 4, 1.5
            mag, pBand, pcode = 99, "I", 99

            try:
                raHour = utils.sexg2Float(template[0])
                if raHour < 0 or raHour > 24:
                    raise Exception("Bad RA value " + raHour)
                decDeg = utils.sexg2Float(template[1])
                if decDeg < -90 or decDeg > 90:
                    raise Exception("Bad DEC value " + decDeg)

                eqx = float(template[2])
                if eqx > 3000:
                    eqx = float(template[2][:4])
                    tmp = template[2][4:]
                    template[3 : minLength + 1] = parts[2:minLength]
                    template[3] = tmp

                mag = toFloat(template[3])
                pBand = template[4].upper()
                pcode = int(template[5])
                sampleNr = int(template[6])
                selected = int(template[7])
                slitWPA = toFloat(template[8])
                length1 = toFloat(template[9])
                length2 = toFloat(template[10])
                slitWidth = toFloat(template[11])
                inMask = 0
            except Exception as e:
                SMDTLogger.info("line {}, error {}, {}".format(nr, e, template))
                # traceback.print_exc()
                # break
                pass
            target = (
                objectId,
                raHour,
                decDeg,
                eqx,
                mag,
                pBand,
                pcode,
                sampleNr,
                selected,
                slitWPA,
                length1,
                length2,
                slitWidth,
                cnt,
                inMask,
            )
            out.append(target)
            cnt += 1
        df = pd.DataFrame(out, columns=cols)
        # df["inMask"] = np.zeros_like(df.name)

        if self.centerRADeg == 0 and self.centerRADeg == 0:
            self.centerRADeg = df.raHour.median() * 15
            self.centerDEC = df.decDeg.median()

        return df

    def getROIInfo(self):
        """
        Returns a dict with keywords that look like fits headers
        Used to show the footprint of the DSS image
        """
        hdr = self.fheader

        nlist = "platescl", "xpsize", "ypsize"  # , 'raDeg', 'decDeg'
        out = {n: hdr.__dict__[n] for n in nlist}

        out["centerRADeg"] = "%.7f" % self.centerRADeg
        out["centerDEC"] = "%.7f" % self.centerDEC
        out["NAXIS1"] = hdr.naxis1
        out["NAXIS2"] = hdr.naxis2

        out["northAngle"] = north
        out["eastAngle"] = east
        out["xpsize"] = hdr.xpsize  # pixel size in micron
        out["ypsize"] = hdr.ypsize  # pixel size in micron
        out["platescl"] = hdr.platescl  # arcsec / mm
        out["positionAngle"] = self.positionAngle
        return out

    def toJson(self):
        """
        Returns the targets in JSON format
        """
        tgs = self.targets
        data = [list(tgs[i]) for i in tgs]
        data1 = {}
        for i, colName in enumerate(tgs.columns):
            data1[colName] = data[i]

        return json.dumps(data1, cls=MyJsonEncoder)

    def toJsonWithInfo(self):
        """
        Returns the targets and ROI info in JSON format
        """
        tgs = self.targets
        data = [list(tgs[i]) for i in tgs]
        data1 = {}
        for i, colName in enumerate(tgs.columns):
            data1[colName] = data[i]

        data2 = {"info": self.getROIInfo(), "targets": data1}
        return json.dumps(data2, cls=MyJsonEncoder)

    def setColum(self, colName, value):
        """
        Updates the dataframe by column name
        """
        self.targets[colName] = value

    def select(self, idxList, minX, maxX, minSlitLength, minSep, boxSize):
        """
        Selects the targets to put on slits

        """
        targets = self.targets
        #
        targets["inMask"] = np.zeros(targets.shape[0])
        mIdx = targets.columns.get_loc("inMask")

        selector = TargetSelector(targets.iloc[idxList], minX, maxX, minSlitLength, minSep, boxSize)
        selIdx = selector.performSelection()
        orgIdx = selector.targets.iloc[selIdx].orgIndex
        targets.iloc[orgIdx, [mIdx]] = 1

        for i, stg in selector.targets.iterrows():
            targets.at[stg.orgIndex, "length1"] = stg.length1
            targets.at[stg.orgIndex, "length2"] = stg.length2

    def updateTarget(self, jvalues):
        """
        Used by GUI to change values in a target.
        """
        values = json.loads(jvalues)
        idx = values["idx"]
        tgs = self.targets

        pcode = int(values["prior"])
        selected = int(values["selected"])
        slitWPA = float(values["slitWPA"])
        slitWidth = float(values["slitWidth"])
        len1 = float(values["len1"])
        len2 = float(values["len2"])

        tgs.at[idx, "pcode"] = pcode
        tgs.at[idx, "selected"] = selected
        tgs.at[idx, "slitWPA"] = slitWPA
        tgs.at[idx, "slitWidth"] = slitWidth
        tgs.at[idx, "length1"] = len1
        tgs.at[idx, "length2"] = len2
        SMDTLogger.info(
            f"Updated target {idx}, pcode={pcode}, selected={selected}, slitWPA={slitWPA:.2f}, slitWidth={slitWidth:.2f}, len1={len1}, len2={len2}"
        )
        return 0

    def markInside(self, layout):
        """
        Sets the inMask flag to 1 (inside) or 0 (outside)
        """
        inOutChecker = InOutChecker(layout)
        tgs = self.targets
        inMask = []
        for i, stg in tgs.iterrows():
            isIn = 1 if inOutChecker.checkPoint(stg.xarcs, stg.yarcs) else 0
            inMask.append(isIn)
        self.targets["inMask"] = inMask

    def reCalcCoordinates(self, raDeg, decDeg, posAngleDeg):
        """
        Recalculates xarcs and yarcs for new center RA/DEC and positionAngle
        Results saved in xarcs, yarcs
        """
        telRaRad, telDecRad = self._fld2telax(raDeg, decDeg, posAngleDeg)
        self.telRaRad, self.telDecRad = telRaRad, telDecRad

        xarcs, yarcs = self._calcTelTargetCoords(telRaRad, telDecRad, self.targets.raHour, self.targets.decDeg, posAngleDeg)
        self.targets["xarcs"] = xarcs
        self.targets["yarcs"] = yarcs

        self.__updateDate()
        """
        try:
            self._calcSlitBoxCoords (posAngleDeg)
        except:
            traceback.print_exc()
        """

    def _project2FocalPlane(self, cenRADeg, cenDecDeg, raHours, decDegs, paDeg):
        """
        Alternative to reCalCoordinates

        Use the cosine method to project the RA/DEC to focal plane
        Then rotate by PA - 90 and shifted by fldcenx, fldceny
        Returns xs, ys in focal plane in arcsec
        """
        cf = self.config
        fldCenX = cf.getValue("fldCenX", 0)
        fldCenY = cf.getValue("fldCenY", 0)

        ras = (raHours * 15 - cenRADeg) * 3600
        decs = (decDegs - cenDecDeg) * 3600
        ras = ras * np.cos(np.radians(cenDecDeg))
        xs, ys = utils.rotate(ras, decs, paDeg - 90)
        return xs + fldCenX, ys + fldCenY

    """
    Migrated routines from dsimulator by Luca Rizzi
    ==================================    
    """

    def _fld2telax(self, raDeg, decDeg, posAngle):
        """
        Returns telRaRad and telDecRad.
        
        This is taken from dsim.x, procedure fld2telax
        FLD2TELAX:  from field center and rotator PA, calc coords of telescope axis    
        fldcenx = 0
        fldceny = 0        
        """
        cf = self.config
        fldCenX = cf.getValue("fldCenX", 0)
        fldCenY = cf.getValue("fldCenY", 0)

        r = math.radians(math.hypot(fldCenX, fldCenY) / 3600.0)
        pa_fld = math.atan2(fldCenY, fldCenX)
        cosr = math.cos(r)
        sinr = math.sin(r)

        #
        decRad = math.radians(decDeg)
        cosd = math.cos(decRad)  # this is the declination of the center of the field
        sind = math.sin(decRad)  # same
        # pa_fld

        pa_diff = math.radians(posAngle) - pa_fld

        cost = math.cos(pa_diff)  # pa_fld is calculated above as arctan(fldceny/fldcenx)
        sint = math.sin(pa_diff)

        sina = sinr * sint / cosd
        cosa = math.sqrt(1.0 - sina * sina)

        return (
            math.radians(raDeg) - math.asin(sina),
            math.asin((sind * cosd * cosa - cosr * sinr * cost) / (cosr * cosd * cosa - sinr * sind * cost)),
        )

    def _calcTelTargetCoords(self, ra0Rad, dec0Rad, raHours, decDegs, posAngle):
        """
        Converts targets coordinates (raHours, decDegs) to xarcs and yarcs
        Xarcs and Yarcs are in focal plane coordinates in arcsec.
        
        Ported from dsimulator
        ra0Rad and dec0Rad must be calculated via fld2telax().
        
        """

        pa0 = math.radians(posAngle)

        decRad = np.radians(decDegs)
        sinDec = np.sin(decRad)
        sinDec0 = math.sin(dec0Rad)
        cosDec = np.cos(decRad)
        cosDec0 = math.cos(dec0Rad)

        deltaRA = np.radians(raHours * 15) - ra0Rad
        cosDeltaRA = np.cos(deltaRA)
        sinDeltaRA = np.sin(deltaRA)

        cosr = sinDec * sinDec0 + cosDec * cosDec0 * cosDeltaRA
        # cosr = np.clip(cosr, 0, 1.0)
        sinr = np.sqrt(np.abs(1.0 - cosr * cosr))
        # r = np.arccos(cosr)
        t1 = np.where (sinr == 0.0, 0, cosDec * sinDeltaRA)
        t2 = np.where (sinr == 0.0, 1, sinr)
        sinp = np.divide (t1, t2)
        
        cosp = np.sqrt(np.abs(1.0 - sinp * sinp)) * np.where(decRad < dec0Rad, -1, 1)
        p = np.arctan2(sinp, cosp)

        rArcsec = sinr / cosr * math.degrees(1) * 3600
        deltaPA = pa0 - p
        return rArcsec * np.cos(deltaPA), rArcsec * np.sin(deltaPA)
