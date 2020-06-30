import traceback
import sys
import math

import numpy as np
import astropy.wcs as wcs


class DssWCSHeader:
    def __init__(self, raDeg, decDeg, width, height):
        """
        This is synthesized header when DSS is not used, which is the default case.
        """
        plateScale = 1.0 / 3600  # 1 arcsec per pixel
        self.raDeg = raDeg
        self.decDeg = decDeg

        w = wcs.WCS(naxis=2)
        w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
        w.wcs.cdelt = [plateScale, plateScale]
        w.wcs.crpix = [width // 2, height // 2]  # [67.61, -105.74] # ref in pixel
        w.wcs.crval = [raDeg, decDeg]  # ref in world coordinates
        self.wcs = w
        self.defineKwds(width, height)

    def xy2rd(self, xin, yin):
        print("xy2rd, not implemented")
        pass

    def rd2xy(self, ra, dec):
        """
        Converts RA/DEC to X/Y in pxiels.
        ra: list of RA in hour
        dec: list of DEC in degree

        The center of the field is self.raDeg and self.decDeg, and X=0, Y=0

        Returns xs, ys
        """
        xcen, ycen = self.wcs.wcs_world2pix([self.raDeg], [self.decDeg], 0)

        x0, y0 = xcen[0], ycen[0]
        xs, ys = self.wcs.wcs_world2pix(ra * 15, dec, 1)

        return [(x0 - x) for x in xs], [(y0 - y) for y in ys]

    def skyPA(self):
        """
        Finds the North by checking two points plus/minus a small angle from decDeg.
        And East is 90 deg from North.

        Returns North, East in degrees
        """
        raDeg, decDeg = self.raDeg, self.decDeg
        smallAng = 100.0 / 3600.0

        decDeg1 = decDeg + smallAng
        raDeg1 = raDeg + smallAng

        wcs = self.wcs

        x0, y0 = wcs.wcs_world2pix([raDeg], [decDeg], 0)
        x1, y1 = wcs.wcs_world2pix([raDeg], [decDeg1], 0)
        x2, y2 = wcs.wcs_world2pix([raDeg1], [decDeg], 0)

        north = math.degrees(math.atan2(y1 - y0, x1 - x0))
        east = math.degrees(math.atan2(y2 - y0, x2 - x0))

        return north, east

    def defineKwds(self, width, height):
        """
        Makes this class compatible with DSSHeader 
        """

        self.naxis1 = width
        self.naxis2 = height

        self.xpsize = 1  # pixel size in micron
        self.ypsize = 1  # pixel size in micron
        self.platescl = 1000  # arcsec/um


class DssHeader:
    def __init__(self, headers, raDeg, decDeg):
        """
        DSSHeader, a helper class to deal with header information
        raDeg: RA of the reference coordinates
        decDeg: DEC of the reference coordinates
        """
        self.headers = headers
        self.centerRaDeg = raDeg
        self.centerDecDeg = decDeg
        if headers:
            # Extract WCS info from headers
            self._getWCS()

    def _getHeader(self, keyname, defValue):
        """
        Returns the keyword valur or default value
        """
        value = self.headers.get(keyname)
        return value if value else defValue

    def _getFloat(self, keyname, defValue):
        """
        Returns the keywords as float
        """
        value = self._getHeader(keyname, defValue)
        return float(value)

    def getFootprint(self, steps=5):
        """
        Returns foot print as array of corners' coordinates
        """
        width, height = int(self.xSize), int(self.ySize)

        out = []
        for x in range(0, width, width // steps):
            out.append(self.xy2rd(x, 0))
        for y in range(0, height, height // steps):
            out.append(self.xy2rd(width, y))
        for x in range(width, 0, -width // steps):
            out.append(self.xy2rd(x, height))
        for y in range(height, 0, -height // steps):
            out.append(self.xy2rd(0, y))

        return out

    def _getWCS(self):
        """ Extracts info from headers.
        """
        if len(self.headers) == 0:
            return
        getFloat = self._getFloat
        getHeader = self._getHeader

        self.naxis1 = getHeader("NAXIS1", 0)
        self.naxis2 = getHeader("NAXIS2", 0)
        amdx = []
        amdy = []
        # AMDX, AMDY = 'AMDREX', 'AMDREY'
        # if getFloat('AMDREX1', 0) == 0:
        # AMDX, AMDY = 'AMDX', 'AMDY'
        AMDX, AMDY = "AMDX", "AMDY"
        for i in range(1, 14):
            amdx.append(getFloat(AMDX + str(i), 0))
            amdy.append(getFloat(AMDY + str(i), 0))
        self.amdx = amdx
        self.amdy = amdy

        self.raDeg = 15 * utils.sexg2Float("%s %s %s" % (getHeader("PLTRAH", 0), getHeader("PLTRAM", 0), getHeader("PLTRAS", 0)))

        decSign = 1
        if "-" in getHeader("PLTDECSN", ""):
            decSign = -1

        self.decDeg = decSign * utils.sexg2Float(
            "%s %s %s" % (getHeader("PLTDECD", 0), getHeader("PLTDECM", 0), getHeader("PLTDECS", 0))
        )

        self.xpoff = getFloat("CNPIX1", 0)
        self.ypoff = getFloat("CNPIX2", 0)

        self.xSize = getFloat("XPIXELS", 0)
        self.ySize = getFloat("YPIXELS", 0)
        self.xpsize = getFloat("XPIXELSZ", 0)
        self.ypsize = getFloat("YPIXELSZ", 0)

        self.ppo3 = getFloat("PPO3", 0)
        self.ppo6 = getFloat("PPO6", 0)

        self.platescl = getFloat("PLTSCALE", 0)
        # self._printVars()

    def _printVars(self):
        print("xoff", self.xpoff, "yoff", self.ypoff)
        print("xpsize", self.xpsize, "ypsize", self.ypsize)
        print("xSize", self.xSize, "ySize", self.ySize)
        print("ppo3", self.ppo3, "ppo6", self.ppo6)
        print("raDeg", self.raDeg, "decDeg", self.decDeg)
        print("platescale", self.platescl)

    def _xy2rd(self, xin, yin):
        """ xin, yin in image pixel coordinates
            Returns ra/dec in degree corresponding to xin/yin
        """
        x = xin  # float(xin) - 0.5
        y = yin  # float(yin) - 0.5
        obx = (self.ppo3 - (self.xpoff + x) * self.xpsize) / 1000.0
        oby = ((self.ypoff + y) * self.ypsize - self.ppo6) / 1000.0

        obx2 = obx * obx
        obx3 = obx2 * obx
        oby2 = oby * oby
        oby3 = oby2 * oby

        xi = (
            self.amdx[0] * obx
            + self.amdx[1] * oby
            + self.amdx[2]
            + self.amdx[3] * obx2
            + self.amdx[4] * obx * oby
            + self.amdx[5] * oby2
            + self.amdx[6] * (obx2 + oby2)
            + self.amdx[7] * obx3
            + self.amdx[8] * obx2 * oby
            + self.amdx[9] * obx * oby2
            + self.amdx[10] * oby3
            + self.amdx[11] * obx * (obx2 + oby2)
            + self.amdx[12] * obx * (obx2 + oby2) ** 2
        )

        eta = (
            self.amdy[0] * oby
            + self.amdy[1] * obx
            + self.amdy[2]
            + self.amdy[3] * oby2
            + self.amdy[4] * oby * obx
            + self.amdy[5] * obx2
            + self.amdy[6] * (obx2 + oby2)
            + self.amdy[7] * oby3
            + self.amdy[8] * oby2 * obx
            + self.amdy[9] * oby * obx2
            + self.amdy[10] * obx3
            + self.amdy[11] * oby * (obx2 + oby2)
            + self.amdy[12] * oby * (obx2 + oby2) ** 2
        )

        toRad = math.pi / 180
        raRad = self.raDeg * toRad
        decRad = self.decDeg * toRad

        xi = xi * toRad / 3600
        eta = eta * toRad / 3600

        numerator = xi / math.cos(decRad)
        denominator = 1.0 - eta * math.tan(decRad)
        ra0 = math.atan2(numerator, denominator)
        ra = ra0 + raRad

        twopi = 2.0 * math.pi
        if ra < 0:
            ra = ra + twopi
        elif ra > twopi:
            ra = ra - twopi

        numerator = math.cos(ra - raRad)
        denominator = (1.0 - eta * math.tan(decRad)) / (eta + math.tan(decRad))
        dec = math.atan(numerator / denominator)

        ra = ra / toRad
        dec = dec / toRad
        return ra, dec

    def _rd2xy(self, ra, dec):
        """ given ra/dec in degree
            Returns x/y in image pixel coordinate
        """
        toRad = math.pi / 180
        arcsecPerRadian = 3600 / toRad
        ra = ra * toRad
        dec = dec * toRad

        iters = 0
        maxiters = 50
        tolerance = 0.0000005
        pltra = self.raDeg * toRad
        pltdec = self.decDeg * toRad

        cosd = math.cos(dec)
        sind = math.sin(dec)

        ra_dif = ra - pltra
        div = sind * math.sin(pltdec) + cosd * math.cos(pltdec) * math.cos(ra_dif)
        xi = cosd * math.sin(ra_dif) * arcsecPerRadian / div

        eta = (sind * math.cos(pltdec) - cosd * math.sin(pltdec) * math.cos(ra_dif)) * arcsecPerRadian / div
        obx = xi / self.platescl
        oby = eta / self.platescl

        deltx = 10.0
        delty = 10.0
        while min([abs(deltx), abs(delty)]) > tolerance and iters < maxiters:
            obx2 = obx * obx
            obx3 = obx2 * obx
            oby2 = oby * oby
            oby3 = oby2 * oby
            f = (
                self.amdx[0] * obx
                + self.amdx[1] * oby
                + self.amdx[2]
                + self.amdx[3] * obx2
                + self.amdx[4] * obx * oby
                + self.amdx[5] * oby2
                + self.amdx[6] * (obx2 + oby2)
                + self.amdx[7] * obx3
                + self.amdx[8] * obx2 * oby
                + self.amdx[9] * obx * oby2
                + self.amdx[10] * oby3
                + self.amdx[11] * obx * (obx2 + oby2)
                + self.amdx[12] * obx * (obx2 + oby2) ** 2
            )

            fx = (
                self.amdx[0]
                + self.amdx[3] * 2.0 * obx
                + self.amdx[4] * oby
                + self.amdx[6] * 2.0 * obx
                + self.amdx[7] * 3.0 * obx2
                + self.amdx[8] * 2.0 * obx * oby
                + self.amdx[9] * oby2
                + self.amdx[11] * (3.0 * obx2 + oby2)
                + self.amdx[12] * (5.0 * obx2 * obx2 + 6.0 * obx2 * oby2 + oby2 * oby2)
            )

            fy = (
                self.amdx[1]
                + self.amdx[4] * obx
                + self.amdx[5] * 2.0 * oby
                + self.amdx[6] * 2.0 * oby
                + self.amdx[8] * obx2
                + self.amdx[9] * obx * 2.0 * oby
                + self.amdx[10] * 3.0 * oby2
                + self.amdx[11] * 2.0 * obx * oby
                + self.amdx[12] * (4.0 * obx3 * oby + 4.0 * obx * oby3)
            )

            g = (
                self.amdy[0] * oby
                + self.amdy[1] * obx
                + self.amdy[2]
                + self.amdy[3] * oby2
                + self.amdy[4] * oby * obx
                + self.amdy[5] * obx2
                + self.amdy[6] * (obx2 + oby2)
                + self.amdy[7] * oby3
                + self.amdy[8] * oby2 * obx
                + self.amdy[9] * oby * obx2
                + self.amdy[10] * obx3
                + self.amdy[11] * oby * (obx2 + oby2)
                + self.amdy[12] * oby * (obx2 + oby2) ** 2
            )

            gx = (
                self.amdy[1]
                + self.amdy[4] * oby
                + self.amdy[5] * 2.0 * obx
                + self.amdy[6] * 2.0 * obx
                + self.amdy[8] * oby2
                + self.amdy[9] * oby * 2.0 * obx
                + self.amdy[10] * 3.0 * obx2
                + self.amdy[11] * 2.0 * obx * oby
                + self.amdy[12] * (4.0 * obx3 * oby + 4.0 * obx * oby3)
            )

            gy = (
                self.amdy[0]
                + self.amdy[3] * 2.0 * oby
                + self.amdy[4] * obx
                + self.amdy[6] * 2.0 * oby
                + self.amdy[7] * 3.0 * oby2
                + self.amdy[8] * 2.0 * oby * obx
                + self.amdy[9] * obx2
                + self.amdy[11] * (3.0 * oby2 + obx2)
                + self.amdy[12] * (5.0 * oby2 * oby2 + 6.0 * obx2 * oby2 + obx2 * obx2)
            )

            f = f - xi
            g = g - eta
            deltx = (-f * gy + g * fy) / (fx * gy - fy * gx)
            delty = (-g * fx + f * gx) / (fx * gy - fy * gx)

            obx = obx + deltx
            oby = oby + delty
            iters = iters + 1

        x = (self.ppo3 - obx * 1000.0) / self.xpsize - self.xpoff
        y = (self.ppo6 + oby * 1000.0) / self.ypsize - self.ypoff
        return x, y

    def xy2rd(self, xs, ys):
        """
        Converts X/Y pixels to RA/DEC
        """
        raDeg, decDeg = [], []
        fxy2rd = self._xy2rd
        for x, y in zip(xs, ys):
            rao, deco = fxy2rd(x, y)
            raDeg.append(rao)
            decDeg.append(deco)
        return raDeg, decDeg

    def rd2xy(self, raHourList, decDegList):
        """
        Convert RA/DEC to X/Y in pixels relative to reference coordinates
        """
        xout, yout = [], []
        frd2xy = self._rd2xy
        x0, y0 = frd2xy(self.centerRaDeg, self.centerDecDeg)
        x0, y0 = x0 - 1, y0 - 1
        for ra, dec in zip(raHourList, decDegList):
            x, y = frd2xy(ra * 15, dec)
            xout.append(x - x0)
            yout.append(y0 - y)
        return xout, yout

    def skyPA(self):
        """
        Return Position angles north and east in degree
        """

        """ Gets center pixel x/y """
        xc = self._getFloat("NAXIS1", 0) / 2.0
        yc = self._getFloat("NAXIS2", 0) / 2.0
        """ Converts to ra/dec in degree """
        r1, d1 = self._xy2rd(xc, yc)

        """ Moves 20 arcsec north """
        """ converts back to x/y in image pixels """
        d2 = d1 + 100.0 / 3600.0
        # print "ra ", deg2Sexd (r1/15.0), " dec " , deg2Sexd (d1)
        r2 = r1

        d3 = d1
        r3 = r1 + 100.0 / 3600.0

        x2, y2 = self._rd2xy(r2, d2)
        x3, y3 = self._rd2xy(r3, d3)

        """ Returns position angle in degree """
        north = math.degrees(math.atan2((y2 - yc), (x2 - xc)))
        east = math.degrees(math.atan2((y3 - yc), (x3 - xc)))

        # print xc, yc, x2, y2
        return north, east

    def skyPAAsDegree(self):
        """
        Return Position angles north and east in degree
        """

        """ Gets center pixel x/y """
        xc = self._getFloat("NAXIS1", 0) / 2.0
        yc = self._getFloat("NAXIS2", 0) / 2.0

        """ Converts to ra/dec in degree """
        r1, d1 = self._xy2rd(xc, yc - 100)
        r2, d2 = self._xy2rd(xc, yc + 100)

        r3, d3 = self._xy2rd(xc - 100, yc)
        r4, d4 = self._xy2rd(xc + 100, yc)

        """ Returns position angle in degree """
        north = math.degrees(math.atan2((d2 - d1), (r2 - r1)))
        east = math.degrees(math.atan2((d4 - d3), (r4 - r3)))

        # print xc, yc, x2, y2
        return north, east
