"""
Created on Mar 20, 2018

@author: skwok
"""

from targetSelector import TargetSelector
from smdtLogger import SMDTLogger
from smdtLibs.inOutChecker import InOutChecker
from maskLayouts import MaskLayouts
from smdtLibs import utils, dss2Header, DARCalculator
from astropy.modeling import models
import datetime
import json
import traceback
import pandas as pd
import numpy as np
import sys
import io
import math
import os

os.environ["NUMEXPR_MAX_THREADS"] = "4"
os.environ["NUMEXPR_NUM_THREADS"] = "4"

MyJsonEncoder = json.JSONEncoder


M_RCURV = 2120.9
R_IMSURF = 2133.6
M_ANGLE = 6.0
M_ANGLERAD = math.radians(M_ANGLE)
ZPT_YM = 128.803  # Dist to tel.axis, in SMCS-XXX (mm) 5.071in
MASK_HT0 = 3.378
PPLDIST = 20018.4

DIST_C0 = 0
DIST_C2 = -1.111311e-8


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
        pcode: high +value = high priority, -2:align, -1:guide star, 0: ignore

        Optional:
        sampleNr: 1,2,3
        selected: 0 or 1
        slitLPA: PA of the slit
        length1: 4 arcsec
        length2: 4 arcsec
        slitWidth: 1 arcsec

    Input can be a string, a pandas data frame, or a file.
    After reading the input, the targets are stored in a pandas data frame.
    Then targets are projected on the the focal plane, via loadDSSInfo.
    If DSS is not desired (default) then the DSS image is a blank image and
    a header is generated using WCS using cenRA/cenDEC.

    """

    def __init__(self, input, config):
        """
        Reads the target list from file of from string.
        """
        self.config = config
        self.positionAngle = None
        self.centerRADeg = None
        self.centerDEC = None
        self.fileName = None
        self.maskName = "Unknown"
        if type(input) == type(io.StringIO()):
            self.targets = self.readRaw(input)
        elif type(input) == type(pd.DataFrame()):
            self.targets = input
        elif input is None:
            self.targets = pd.DataFrame()
        else:
            self.fileName = input
            self.targets = self.readFromFile(input)

        instrument = "deimos"
        if config is not None:
            instrument = config.properties["instrument"]

        self.xgaps = []
        self.layout = MaskLayouts[instrument]
        self.project2FocalPlane()
        self.__updateDate()

    def getNrTargets(self):
        return self.targets.shape[0]

    def __updateDate(self):
        """
        Remembers the creation date.
        """
        self.createDate = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def project2FocalPlane(self):
        targets = self.targets
        if self.positionAngle is None:
            self.positionAngle = 0
        if len(targets) <= 0:
            self.centerRADeg = self.centerDEC = 0, 0
        else:
            if self.centerRADeg is None and self.centerDEC is None:
                self.centerRADeg = np.mean(targets.raHour) * 15
                self.centerDEC = np.mean(targets.decDeg)

            self.reCalcCoordinates(self.centerRADeg, self.centerDEC, self.positionAngle)

    def _checkPA(self, inLine):
        """
        Checks if input line contains the center RA/DEC and PA
        Used in readRaw
        """
        if not "PA=" in inLine.upper():
            return False
        parts = inLine.split()

        # name, ra, dec, eqx, pa = parts

        for i, s in enumerate(parts):
            if "PA=" in s.upper():
                self.centerRADeg = utils.sexg2Float(parts[i - 3]) * 15
                self.centerDEC = utils.sexg2Float(parts[i - 2])
                parts1 = (" ".join(parts[i:])).split("=")
                self.positionAngle = float(parts1[1].strip())
                self.maskName = parts[i - 4]
                return True
        return False

    def readFromFile(self, fname):
        """
        Reads target list from file
        Returns a Pandas dataframe
        """
        with open(fname, "r") as fh:
            try:
                return self.readRaw(fh)
            except:
                SMDTLogger.info(f"Failed to open {fname}")
                return None

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
            "slitLPA",
            "length1",
            "length2",
            "slitWidth",
            "orgIndex",
            "inMask",
            "raRad",
            "decRad",
        )
        cnt = 0
        params = self.config.getValue("params")
        slitLength = params.getValue("minslitlength", 10)[0]
        halfLen = slitLength / 2
        slitWidth = params.getValue("slitwidth", 1)[0]
        slitpa = params.getValue("slitpa", 0)[0]

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
            if len(parts) < 3:
                continue
            # print (nr, "len", parts)

            template = ["", "", "2000", "99", "I", "0", "-1", "0", slitpa, halfLen, halfLen, slitWidth, "0", "0"]
            minLength = min(len(parts), len(template))
            template[:minLength] = parts[:minLength]
            if self._checkPA(p1):
                continue

            sampleNr, selected, slitLPA, length1, length2, slitWidth = 1, 1, 0, 4, 4, 1.5
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
                slitLPA = toFloat(template[8])
                length1 = toFloat(template[9])
                length2 = toFloat(template[10])
                slitWidth = toFloat(template[11])
                inMask = int(template[12])
            except Exception as e:
                SMDTLogger.info("line {}, error {}, {}".format(nr, e, line))
                # traceback.print_exc()
                # break
                pass
            raRad = math.radians(raHour * 15)
            decRad = math.radians(decDeg)
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
                slitLPA,
                length1,
                length2,
                slitWidth,
                cnt,
                inMask,
                raRad,
                decRad,
            )
            out.append(target)
            cnt += 1
        df = pd.DataFrame(out, columns=cols)
        # df["inMask"] = np.zeros_like(df.name)

        if self.centerRADeg is None or self.centerRADeg is None:
            msg = "Center RA and DEC undefined. Using averge of input RA and DEC."
            SMDTLogger.info(msg)
            # print(msg)
            self.centerRADeg = df.raHour.mean() * 15
            self.centerDEC = df.decDeg.mean()
            self.positionAngle = 0

        return df

    def getROIInfo(self):
        """
        Returns a dict with keywords that look like fits headers
        Used to show the footprint of the DSS image
        """
        hdr = dss2Header.DssWCSHeader(self.centerRADeg, self.centerDEC, 60, 60)
        north, east = hdr.skyPA()

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

        data2 = {"info": self.getROIInfo(), "targets": data1, "xgaps": self.xgaps}

        return json.dumps(data2, cls=MyJsonEncoder)

    def setColum(self, colName, value):
        """
        Updates the dataframe by column name
        """
        self.targets[colName] = value

    def calcSlitPosition(self, minX, maxX, minSlitLength, minSep, ext):
        """
        Selects the targets to put on slits
        ext: extends to fill gaps
        """
        self.markInside()
        selector = TargetSelector(self.targets, minX, maxX, minSlitLength, minSep)
        self.targets = selector.performSelection(extendSlits=ext)
        self.xgaps = selector.xgaps
        self.selector = selector
        self.calcSlitXYs()

    def findTarget(self, targetName):
        """
        Finds entry with the given targName.
        Returns idx, or -1 if not found
        """
        for i, stg in self.targets.iterrows():
            if stg.objectId == targetName:
                return stg.orgIndex
        return -1

    def updateTarget(self, jvalues):
        """
        Used by GUI to change values in a target.
        """
        values = json.loads(jvalues)
        tgs = self.targets

        pcode = int(values["prior"])
        selected = int(values["selected"])
        slitLPA = float(values["slitLPA"])
        slitWidth = float(values["slitWidth"])
        len1 = float(values["len1"])
        len2 = float(values["len2"])
        targetName = values["targetName"]

        raSexa = values["raSexa"]
        decSexa = values["decSexa"]
        raHour = utils.sexg2Float(raSexa)
        decDeg = utils.sexg2Float(decSexa)

        raRad = math.radians(raHour * 15)
        decRad = math.radians(decDeg)

        idx = self.findTarget(targetName)

        if idx >= 0:
            # Existing entry
            tgs.at[idx, "pcode"] = pcode
            tgs.at[idx, "selected"] = selected
            tgs.at[idx, "slitLPA"] = slitLPA
            tgs.at[idx, "slitWidth"] = slitWidth
            tgs.at[idx, "length1"] = len1
            tgs.at[idx, "length2"] = len2

            tgs.at[idx, "raHour"] = raHour
            tgs.at[idx, "decDeg"] = decDeg
            tgs.at[idx, "raRad"] = raRad
            tgs.at[idx, "decRad"] = decRad

            SMDTLogger.info(
                f"Updated target {idx}, ra {raSexa}, dec {decSexa}, pcode={pcode}, selected={selected}, slitLPA={slitLPA:.2f}, slitWidth={slitWidth:.2f}, len1={len1}, len2={len2}"
            )
        else:
            # Add a new entry
            idx = self.targets.obejctName.shape[0]
            newItem = {
                "objectId": targetName,
                "raHour": raHour,
                "decDeg": decDeg,
                "eqx": 2000,
                "mag": int(values["mag"]),
                "pBand": values["pBand"],
                "pcode": int(values["prior"]),
                "sampleNr": 1,
                "selected": selected,
                "slitLPA": slitLPA,
                "inMask": 0,
                "length1": len1,
                "length2": len2,
                "slitWidth": slitWidth,
                "orgIndex": idx,
                "raRad": raRad,
                "decRad": decRad,
            }

            self.targets = tgs.append(newItem, ignore_index=True)

            SMDTLogger.info(
                f"New target {targetName}, ra {raSexa}, dec {decSexa}, pcode={pcode}, selected={selected}, slitLPA={slitLPA:.2f}, slitWidth={slitWidth:.2f}, len1={len1}, len2={len2}, idx={idx}"
            )

        self.reCalcCoordinates(self.centerRADeg, self.centerDEC, self.positionAngle)
        return idx

    def deleteTarget(self, idx):
        """
        Remove a row idx from the data frame
        """
        if idx < 0:
            return
        tgs = self.targets
        self.targets = tgs.drop(tgs.index[idx])
        SMDTLogger.info("Delete target idx")

    def markInside(self):
        """
        Sets the inMask flag to 1 (inside) or 0 (outside)
        """
        inOutChecker = InOutChecker(self.layout)
        tgs = self.targets
        inMask = []
        for i, stg in tgs.iterrows():
            isIn = 1 if inOutChecker.checkPoint(stg.xarcs, stg.yarcs) else 0
            inMask.append(isIn)
        self.targets["inMask"] = inMask

    def calcRefrCoords(self, centerRADeg, centerDECDeg, haDeg):
        """
        Applies refraction on the cneter of mask coordinates
        """
        atRefr = DARCalculator.DARCalculator(
            self.config.properties["tellatitude"], self.config.properties["referencewavelen"] * 1000, 615, 0,
        )
        raDeg, decDeg, refr = atRefr.getRefr([centerRADeg], [centerDECDeg], centerRADeg, haDeg)

        return raDeg, decDeg

    def toPNTCenter(self, paDeg, haDeg):
        """
        Rotates vector to center of telescope and adds refraction correction to center of mask
        Result is pointing center to be stored in FITS file.
        Returns pntRaDeg and pntDecDeg
        """
        ra1, dec1 = self.calcRefrCoords(self.centerRADeg, self.centerDEC, haDeg)
        pntX, pntY = self.config.properties["fldcenx"], self.config.properties["fldceny"]

        ra2, dec2 = utils.rotate(pntX, pntY, -paDeg - 90.0)
        cosd = np.cos(np.radians(dec1[0]))
        if abs(cosd) > 1e-5:
            ra2 = ra2 / cosd
        pntRaDeg = ra1[0] + ra2 / 3600
        pntDecDeg = dec1[0] + dec2 / 3600

        return pntRaDeg, pntDecDeg

    def calcSlitXYs(self):
        """
        Calculates the corners of the slits
        """
        targets = self.targets
        selector = targets.inMask > 0
        aboxSelect = targets.pcode == -2
        targets.loc[aboxSelect, "slitLPA"] = self.positionAngle
        selected = targets[selector]
        nSlits = selected.shape[0]
        if nSlits > 0:
            slitWidths = selected.slitWidth
            half = slitWidths / 2

            relAngles = np.radians(self.positionAngle - selected.slitLPA)
            sines = np.sin(relAngles)
            cosines = np.cos(relAngles)

            slitX = selected.xarcs
            slitY = selected.yarcs
            l1 = selected.length1
            l2 = selected.length2

            slitX10 = slitX - cosines * l1
            slitY10 = slitY - sines * l1
            slitX2, slitY2, pa0 = self.proj_to_mask(slitX10, slitY10 + half, 0)
            slitX3, slitY3, pa0 = self.proj_to_mask(slitX10, slitY10 - half, 0)

            slitX30 = slitX + cosines * l2
            slitY30 = slitY + sines * l2
            slitX4, slitY4, pa0 = self.proj_to_mask(slitX30, slitY30 - half, 0)
            slitX1, slitY1, pa0 = self.proj_to_mask(slitX30, slitY30 + half, 0)

            targets.loc[selector, "slitX1"] = slitX1
            targets.loc[selector, "slitY1"] = slitY1
            targets.loc[selector, "slitX2"] = slitX2
            targets.loc[selector, "slitY2"] = slitY2
            targets.loc[selector, "slitX3"] = slitX3
            targets.loc[selector, "slitY3"] = slitY3
            targets.loc[selector, "slitX4"] = slitX4
            targets.loc[selector, "slitY4"] = slitY4
            targets.loc[selector, "slitLen"] = l1 + l2
            targets.loc[selector, "TopDist"] = l1
            targets.loc[selector, "BotDist"] = l2

    def reCalcCoordinates(self, raDeg, decDeg, posAngleDeg):
        """
        Recalculates xarcs and yarcs for new center RA/DEC and positionAngle
        Results saved in xarcs, yarcs

        Returns xarcs, yarcs in focal plane coordinates in arcs.
        """

        # raDeg, decDeg = self.calcRefrCoords(raDeg, decDeg)

        telRaRad, telDecRad = self._fld2telax(raDeg, decDeg, posAngleDeg)
        self.telRaRad, self.telDecRad = telRaRad, telDecRad

        xarcs, yarcs = self._calcTelTargetCoords(telRaRad, telDecRad, self.targets.raRad, self.targets.decRad, posAngleDeg)

        self.targets["xarcs"] = xarcs
        self.targets["yarcs"] = yarcs

        xmm, ymm, pas = self.proj_to_mask(xarcs, yarcs, 0)

        self.targets["xmm"] = xmm
        self.targets["ymm"] = ymm

        self.targets["orgIndex"] = range(0, self.targets.shape[0])

        self.__updateDate()
        return xarcs, yarcs

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
        # this is the declination of the center of the field
        cosd = math.cos(decRad)
        sind = math.sin(decRad)  # same
        # pa_fld

        pa_diff = math.radians(posAngle) - pa_fld

        # pa_fld is calculated above as arctan(fldceny/fldcenx)
        cost = math.cos(pa_diff)
        sint = math.sin(pa_diff)

        sina = sinr * sint / cosd
        cosa = math.sqrt(1.0 - sina * sina)

        return (
            math.radians(raDeg) - math.asin(sina),
            math.asin((sind * cosd * cosa - cosr * sinr * cost) / (cosr * cosd * cosa - sinr * sind * cost)),
        )

    def _calcTelTargetCoords(self, ra0Rad, dec0Rad, raRads, decRads, posAngle):
        """
        Converts targets coordinates (raRads, decRads) to xarcs and yarcs
        Xarcs and Yarcs are in focal plane coordinates in arcsec.

        Ported from dsimulator
        ra0Rad and dec0Rad must be calculated via fld2telax().
        """
        pa0 = math.radians(posAngle)

        sinDec = np.sin(decRads)
        sinDec0 = math.sin(dec0Rad)
        cosDec = np.cos(decRads)
        cosDec0 = math.cos(dec0Rad)

        deltaRA = raRads - ra0Rad
        cosDeltaRA = np.cos(deltaRA)
        sinDeltaRA = np.sin(deltaRA)

        cosr = sinDec * sinDec0 + cosDec * cosDec0 * cosDeltaRA
        # cosr = np.clip(cosr, 0, 1.0)
        sinr = np.sqrt(np.abs(1.0 - cosr * cosr))
        # r = np.arccos(cosr)
        t1 = np.where(sinr == 0.0, 0, cosDec * sinDeltaRA)
        t2 = np.where(sinr == 0.0, 1, sinr)
        sinp = np.divide(t1, t2)

        cosp = np.sqrt(np.abs(1.0 - sinp * sinp)) * np.where(decRads < dec0Rad, -1, 1)
        p = np.arctan2(sinp, cosp)

        rArcsec = sinr / cosr * math.degrees(1) * 3600
        deltaPA = pa0 - p
        return rArcsec * np.cos(deltaPA), rArcsec * np.sin(deltaPA)

    def _gnom_to_dproj(self, xg, yg):
        """
        GNOMONIC projection
        xg, yg in [mm]
        """
        rho2 = xg * xg + yg * yg
        f = 1.0 + DIST_C0 + DIST_C2 * rho2
        xd = xg * f
        yd = yg * f
        return xd, yd

    def _spherical_proj_to_mask(self, xp, yp, ap):
        """
        xp, yp: output of the GNOM projection
        """
        mu = np.arcsin(np.clip(xp / M_RCURV, -1.0, 1.0))
        cosm = np.cos(mu)
        cost = np.cos(M_ANGLERAD)
        tant = np.tan(M_ANGLERAD)
        xx = M_RCURV * mu
        yy = (yp - ZPT_YM) / cost + M_RCURV * tant * (1 - cosm)

        tanpa = np.tan(np.radians(ap)) * cosm / cost + tant * xp / M_RCURV
        ac = np.degrees(np.arctan(tanpa))

        # spherical image surface height
        rho = np.sqrt(xp * xp + yp * yp)
        rho = np.minimum(rho, R_IMSURF)
        hs = R_IMSURF * (1 - np.sqrt(1 - (rho / R_IMSURF) ** 2))
        # mask surface height
        hm = MASK_HT0 + yy * np.sin(M_ANGLERAD) + M_RCURV * (1 - cosm)
        # correction
        yc = yy + (hs - hm) * yp / PPLDIST / cost
        xc = xx + (hs - hm) * xp / PPLDIST / cosm
        return xc, yc, ac

    def proj_to_mask(self, xs, ys, ap):
        as2mm = utils.AS2MM
        xmm, ymm = self._gnom_to_dproj(xs * as2mm, ys * as2mm)
        return self._spherical_proj_to_mask(xmm, ymm, ap)

    def getDistortionFunctions(self):
        """
        Gets distortion coefficients from the configuration
        Returns the polynomial models for X and Y
        """

        def _getPoly(coeffs):
            pol = models.Polynomial2D(degree=4)
            pol.parameters = [float(x) for x in coeffs.split(",")]
            return pol

        ccf = self.config

        xPoly = _getPoly(ccf.distortionXCoeffs)
        yPoly = _getPoly(ccf.distortionYCoeffs)
        return xPoly, yPoly

    def writeTo(self, fileName):
        def outputPA(fh):
            print("# Mark name, center:", file=fh)
            print("#", file=fh)
            print(
                "{:20s} {} {} 2000.0 PA={:.3f}".format(
                    self.maskName,
                    utils.toSexagecimal(self.centerRADeg / 15, secFmt="{:06.3f}"),
                    utils.toSexagecimal(self.centerDEC, plus="+"),
                    self.positionAngle,
                ),
                file=fh,
            )
            print("#", file=fh)
            print("#", file=fh)
            print ("# Columns", file=fh)
            print("# Obj_Id, RA, DEC, EQX, Magn, pBand, pCode, sampleNr, selected, slitLPA, length1, length2, slitWidth", file=fh)
            print("#", file=fh)
            print("#", file=fh)
            # end of outputPA

        def outputTargets(fh):
            for i, row in tgs.iterrows():
                print(
                    fmt.format(
                        row.objectId,
                        utils.toSexagecimal(row.raHour, secFmt="{:06.3f}"),
                        utils.toSexagecimal(row.decDeg, plus="+"),
                        row.eqx,
                        row.mag,
                        row.pBand,
                        row.pcode,
                        row.sampleNr,
                        row.selected,
                        row.slitLPA,
                        row.length1,
                        row.length2,
                        row.slitWidth,
                    ),
                    file=fh,
                )
            # end outputTargets

        tgs = self.targets
        fmt = "{:20s} {} {} {} {:.3f} {} {:5.0f} {:.0f} {:.0f} {:.1f} {:.1f} {:.1f} {:.1f}"
        with open(fileName, "w") as fh:
            outputPA(fh)
            outputTargets(fh)

