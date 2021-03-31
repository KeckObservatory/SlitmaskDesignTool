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

    def __init__(self, latitudeDeg, centerWL, pressure, temperature):
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
        self.pressure = pressure * self.toMMHg
        self.temperature = temperature


    def _calcAR(self, a, b, zangleRad):
        """
        tanz = tan (zenithAngle_vac)
        zenith_obs = zenith_vac (A * tanz + B tanz^3) / (1 + (A + 3 * B * tanz^2) * secz^2   
        Returns the observed DAR at zenith angle in arcsec
        """
        tanz = np.tan(zangleRad)
        secz = 1.0 / np.cos(zangleRad)
        tanz2 = tanz * tanz
        btanz = tanz * b
        num = a * tanz + btanz * tanz2
        denom = 1 + (a + 3 * btanz * tanz) * secz * secz
        return np.degrees(num / denom) * 3600

    def _calcRefPars(self, press, temp, wlenNM):        
        """
        Calculates REFA and REFB based on pressure (hPa) and temperature (degC),
        and wlen (um)
        Returns REFA and REFB
        """
        wlen = wlenNM / 1000
        K = 0.00010514  # proportionality constant in radians
        n0_1 = K * press / (273.15 + temp) * (1 + 0.00567 / wlen / wlen)
        ratio = self.H0 / self.r0
        refa = n0_1 * (1 - ratio)
        refb = -n0_1 * (ratio - n0_1 / 2)
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
        dars = self._calcDARHelper(self.pressure, self.temperature, targetWavelength, self.centerWavelength, zenithDistRad)
        return dars, parangRad, elRad
        

    def calcAR (self, haDeg, tlist):
        """
        Calculates the atmospheric refraction for the targets.
        Returns atmospheric refraction, parallactic angle, zenith distance
        """        
        targets = tlist.targets
        targets = targets[targets.pcode > 0]
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
        
        refa, refb = self._calcRefPars(self.pressure, self.temperature, self.centerWavelength)    
        refAR = self._calcAR(refa, refb, zenithDistRad)
        return refAR, parangRad, elRad


    def parallacticAngle (self, sinha, cosha, sinLatitude, cosLatitude, sinDeclination, cosDeclination):
        t2 = sinLatitude / cosLatitude * cosDeclination - sinDeclination * cosha
        pa = np.pi - np.arctan2(sinha, t2)
        return pa
     
