"""
Created on Jul 10, 2012
Differential atmospheric refraction calculator

Use matplotlib

@author: skwok
"""
import numpy as np
import sys


class DARCalculator:
    """
    Differential Atmospheric Refraction calculations
    """

    def __init__(self, latitudeDeg, centerWL, pressure=615, temperature=0):
        """
        Constructor
        latitude of telescope in deg
        centerWaveLength centerWL in nm
        pressure in hPa
        temperature in degC
        """
        self.H0 = 10  # 10km equalivalent height of homogeneous atmosphere
        self.r0 = 6738  # 6738km radius of earth
        self.toMMHg = 0.7500616827042 # from hPa to mmHg, hPa=mBar
        self.latitudeDeg = latitudeDeg
        self.centerWavelength = centerWL
        self.pressureMMHg = pressure * self.toMMHg
        self.pressMBar = pressure
        self.temperature = temperature


    def _calcAR(self, a, b, zangleRad):
        """
        tanz = tan (zenithAngle_vac)
        zenith_obs = zenith_vac (A * tanz + B tanz^3) / (1 + (A + 3 * B * tanz^2) * secz^2   
        Returns the observed AR at zenith angle in degrees
        """
        tanz = np.tan(zangleRad)
        secz = 1.0 / np.cos(zangleRad)
        tanz2 = tanz * tanz
        btanz = tanz * b
        num = a * tanz + btanz * tanz2
        denom = 1 + (a + 3 * btanz * tanz) * secz * secz
        return np.degrees(num / denom) 

    def _calcRefPars(self, press, temp, wlenNM):        
        """
        Calculates REFA and REFB based on pressure (hPa) and temperature (degC),
        and wlen (um)
        Returns REFA and REFB
        """
        wlen = wlenNM / 1000
        K = 0.00010514  # proportionality constant in radians
        n0_1 = K * press / (273.15 + temp) * (1 + 0.00567 / wlen / wlen)
        ratio = (self.H0) / (self.r0)
        refa = n0_1 * (1 - ratio)
        refb = -n0_1 * (ratio - n0_1 / 2)
        return refa, refb

    def _calcRefParsX(self, pressMBar, tempC, wlenNM):
        """
        From slablib refcoq.
        """
        rh = 0.2
        ps = np.power ( 10.0, ( 0.7859 + 0.03477 * tempC ) / ( 1.0 + 0.00412 * tempC) ) * ( 1.0 + pressMBar * ( 4.5e-6 + 6e-10 * tempC * tempC )  )
        pw = rh * ps / ( 1.0 - ( 1.0 - rh ) * ps / pressMBar )

        tempK = tempC + 273.15
        wlen = wlenNM / 1000.0
        wlen2 = wlen * wlen
        gamma = ( ( 77.53484e-6 + ( 4.39108e-7 + 3.666e-9/wlen2 ) / wlen2 ) * pressMBar - 11.2684e-6*pw ) / tempK
        beta = 4.4474e-6 * tempK
        refa = gamma * (1.0 - beta)
        refb = -gamma * (beta - gamma / 2.0)
        return refa, refb


    def _calcDARHelper(self, press, temp, targWlen, refWlen, zangles):
        """
        press in hPA
        temp in degC
        targWlen, refWlen in nm

        Returns DAR in elevation direction in degrees
        """
        refa, refb = self._calcRefPars(press, temp, refWlen)
        targRefa, targRefb = self._calcRefPars(press, temp, targWlen)

        refAR = self._calcAR(refa, refb, zangles)
        targAR = self._calcAR(targRefa, targRefb, zangles)
        
        return (refAR - targAR)

    def _sincos (self, rad):
        return np.sin(rad), np.cos(rad)

    def calcDAR (self, haDeg, targetWavelength, tlist):
        """
        Returns DARS, parallactic angle Rad, elevation Rad
        """

        targets = tlist.targets
        raRads = np.radians(15 * targets.raHour)
        decRads = np.radians(targets.decDeg)
        latitudeRad = np.radians(self.latitudeDeg) 
        
        cenRARad = np.radians(tlist.centerRADeg)
        cenDECRad = np.radians(tlist.centerDEC)
        diffRA = cenRARad - np.radians(haDeg)
        
        hourRads = raRads - diffRA
        sincos = self._sincos

        # Calculate zenith distance for given hour angle
        sinlat, coslat = sincos(latitudeRad)
        sindec, cosdec = sincos(decRads)
        sinra, cosra = sincos (raRads)    
        sinha, cosha = sincos(hourRads)

        sinEL = sinlat * sindec + coslat * cosdec * cosha
        sinEL = np.clip (sinEL, 0, 90)
        elRad = np.arcsin(sinEL)

        zenithDistRad = np.pi/2.0 - elRad

        # Calculate parallacticAngle       
        parangRad = self.parallacticAngle(sinha, cosha, sinlat, coslat, sindec, cosdec)
        dars = self._calcDARHelper(self.pressureMMHg, self.temperature, targetWavelength, self.centerWavelength, zenithDistRad)
        return dars, parangRad, elRad
        

    def calcARHelper (self, haDeg, cenRa, cenDec, raDegs, decDegs):
        raRads = np.radians (raDegs)
        decRads = np.radians(decDegs)

        latitudeRad = np.radians(self.latitudeDeg) 
        
        cenRARad = np.radians(cenRa)
        cenDECRad = np.radians(cenDec)
        diffRA = cenRARad - np.radians(haDeg)
        
        hourRads = raRads - diffRA
        sincos = self._sincos

        # Calculate zenith distance for given hour angle
        sinlat, coslat = sincos(latitudeRad)
        sindec, cosdec = sincos(decRads)
        sinra, cosra = sincos (raRads)    
        sinha, cosha = sincos(hourRads)

        sinEL = sinlat * sindec + coslat * cosdec * cosha
        sinEL = np.clip (sinEL, 0, 90)
        elRad = np.arcsin(sinEL)
        zenithDistRad = np.pi/2.0 - elRad
        # Calculate parallacticAngle       
        parangRad = self.parallacticAngle(sinha, cosha, sinlat, coslat, sindec, cosdec)
        
        refa, refb = self._calcRefPars(self.pressureMMHg, self.temperature, self.centerWavelength)    
        refAR = self._calcAR(refa, refb, zenithDistRad)
        return refAR, parangRad, elRad

    def calcAR (self, haDeg, tlist):
        """
        Calculates the atmospheric refraction for the targets.
        Returns atmospheric refraction, parallactic angle, elevation Rad
        """        
        targets = tlist.targets
        #targets = targets[targets.pcode > 0]

        return self.calcARHelper (haDeg, tlist.centerRADeg, tlist.centerDEC, targets.raHour * 15, targets.decDeg)


    def parallacticAngle (self, sinha, cosha, sinLatitude, cosLatitude, sinDeclination, cosDeclination):
        t2 = sinLatitude / cosLatitude * cosDeclination - sinDeclination * cosha
        pa = np.pi - np.arctan2(sinha, t2)
        return pa
        

    def hd2ae(self, latDeg, haDegs, decDegs):
        """
        ha = lst - ra
        """
        latRad = np.radians(latDeg)
        decRad = np.radians(decDegs)

        sinLatitude = np.sin(latRad)
        cosLatitude = np.cos(latRad)
        sinDeclination = np.sin(decRad)
        cosDeclination = np.cos(decRad)

        haRad = np.radians(haDegs)
        cosHangle = np.cos(haRad)
        sinHangle = np.sin(haRad)

        sinEl = sinLatitude * sinDeclination + cosLatitude * cosDeclination * cosHangle
        sinEl = np.clip(sinEl, 0.0, 1.0)
        el = np.degrees(np.arcsin(sinEl))

        c1 = np.where(cosDeclination == 0.0, 1.0, cosDeclination)
        cosAz = -(cosHangle * sinLatitude - sinDeclination / c1 * cosLatitude)
        cosAz = np.where(cosDeclination == 0.0, 0, cosAz)
        az = np.degrees(np.arctan2(-sinHangle, cosAz))

        return az, el


    def ae2rd(self, latDeg, azDegs, elDegs, lstDeg):
        """
        ra = lst - ha
        """
        azRad = np.radians(azDegs)
        elRad = np.radians(elDegs)
        latRad = np.radians(latDeg)

        sinAz = np.sin(azRad)
        cosAz = np.cos(azRad)
        sinElev = np.sin(elRad)
        cosElev = np.cos(elRad)
        sinLat = np.sin(latRad)
        cosLat = np.cos(latRad)

        sinDec = sinLat * sinElev + cosLat * cosElev * cosAz
        denom = sinElev - sinLat * sinDec

        num = -cosElev * cosLat * sinAz
        if denom == 0:
            ha = 0
        else:
            ha = np.arctan2(num, denom)

        haDeg = np.degrees(ha)
        raDeg = lstDeg - haDeg
        decDeg = np.degrees(np.arcsin(sinDec))
        decDeg = np.where(decDeg > 270, decDeg - 360.0, decDeg)

        return raDeg, decDeg
        
    def getRefr(self, raDegs, decDegs, raDeg0, haDeg):
        """
        Returns refractetd raDegs, decDegs, and refracted amount in degress
        """
        refa, refb = self._calcRefPars(
            self.pressureMMHg, self.temperature, self.centerWavelength
        )
        tellat = self.latitudeDeg

        lstDeg = raDeg0 + haDeg
        haDegs = np.subtract(lstDeg, raDegs)
        az, el = self.hd2ae(tellat, haDegs, decDegs)
        lstDegs = np.add(raDegs, haDeg)

        zdistRad = np.radians(90 - el)
        refr = self._calcAR(refa, refb, zdistRad)
        el = el + refr

        raDeg, decDeg = self.ae2rd(tellat, az, el, lstDegs)
        return raDeg, decDeg, refr
