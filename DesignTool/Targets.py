'''
Created on Mar 20, 2018

@author: skwok
'''

import math
from smdtLibs import utils
from smdtLibs import Dss2Client, Dss2Header
import io
import sys
import numpy as np
import pandas as pd
import traceback
import json

from smdtLogger import SMDTLogger


class TargetList:
    '''
    Columns of the input file:
        name: 16 chars, no white space
        ra: right ascension in hour
        dec: declination in deg
        equinox: 2000
        magn: magnitude
        passband: V, I, ...
        priority: high +value = high priority, -2:align, -1:guide star, 0: ignore
        
        Optional:
        sample: 1,2,3
        select: 0
        slitPA: PA of the slit
        length1: 4
        length2: 4
        slitWidth: 1
        '''

    def __init__(self, fname, useDSS, config):
        self.fileName = fname
        self.positionAngle = 0
        self.centerRADeg = 0
        self.centerDEC = 0
        self.dssSizeDeg = 0.35  # deg
        self.config = config
        if type(fname) == type(io.StringIO()):
            self.targets = self.readRaw (fname)
        else:
            self.targets = self.readFromFile(fname) 
        self.loadDSSInfo(useDSS)
        
    def loadDSSInfo (self, useDSS=True):
        self._getDSSInfo(useDSS)
        self._proj2DSS()
        
    def _getDSSInfo (self, useDSS=True):
        """
        Gets DSS image and info
        """
        cf = self.config
        url = cf.get('dssServerURL', None) if cf != None else None
        dss2 = Dss2Client.Dss2Client (url) 
        targets = self.targets
        if len(targets) <= 0:
            raDeg, decDeg = 0, 0
        else:
            raDeg, decDeg = self.centerRADeg, self.centerDEC
            
        SMDTLogger.info ("raHour %s, decDeg %s", utils.toSexagecimal(raDeg / 15),
            utils.toSexagecimal(decDeg))
        
        self.dssFits = dss2.getFITS(raDeg, decDeg, self.dssSizeDeg) if useDSS else None
        
        if self.dssFits == None:
            h = int(self.dssSizeDeg * 3600)
            w = h
            self.dssData = np.zeros(shape=(h, w))
            self.fheader = Dss2Header.DssWCSHeader(raDeg, decDeg, w, h)
        else:
            self.dssData = self.dssFits[0].data
            self.fheader = Dss2Header.DssHeader(self.dssFits[0].header, raDeg, decDeg)        
        
    def _checkPA (self, inParts):
        """
        Checks if input line contains the center RA/DEC and PA
        Use in readRaw
        """
        paStr = inParts[3].upper()
        if 'PA=' in paStr:
            parts0 = paStr.split('=')
            self.positionAngle = float(parts0[1])
            self.centerRADeg = utils.sexg2Float(inParts[0]) * 15
            self.centerDEC = utils.sexg2Float(inParts[1])
            return True
        else:
            return False
        
    def readFromFile (self, fname):
        with open(fname, "r") as fh:
            return self.readRaw(fh)            
        
    def readRaw(self, fh): 

        def toFloat(x):
            try:
                return float(x)
            except:
                return math.nan
                  
        out = []
        cols = 'name', 'raHour', 'decDeg', 'eqx', 'mag', 'band', 'pcode', \
            'sample', 'select', 'slitPA', 'length1', 'length2', 'slitWidth'
        
        for nr, line in enumerate(fh):
            if not line:
                continue
            line = line.strip()
            p1, p2, p3 = line.partition('#')
            parts = p1.split()
            if len(parts) == 0:
                continue
            name = parts[0]
            parts = parts[1:]
            if len(parts) < 4:
                continue
            # print (nr, "len", parts)
            
            template = ['', '', 2000.0, 99, 'I', 99, 0, 1, 0, 4.0, 4.0, 1.5]                
            minLength = min(len(parts), len(template))
            template[:minLength] = parts[:minLength]
            if self._checkPA (parts):
                continue
            
            sample, select, slitPA, length1, length2, slitWidth = 1, 1, 0, 4, 4, 1.5
            mag, band, pcode = 99, 'I', 99
            
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
                    template.insert(3, tmp)                   
                
                mag = float(template[3])
                band = template[4].upper()
                pcode = int(template[5])
                sample = int(template[6])
                select = int(template[7])
                slitPA = toFloat(template[8])
                length1 = float(template[9])
                length2 = float(template[10])
                slitWidth = float(template[11])
            except Exception as e:
                SMDTLogger.info  ("{},{},{}".format(nr, e, template))
                # traceback.print_exc()
                # break
                pass
            target = (name, raHour, decDeg,
                    eqx, mag, band, pcode,
                    sample, select, slitPA, length1, length2, slitWidth)
            out.append(target)        
        df = pd.DataFrame(out, columns=cols)
        if self.centerRADeg == self.centerDEC and self.centerRADeg == 0:
            self.centerRADeg = df.raHour.median() * 15
            self.centerDEC = df.decDeg.median() 

        return df
    
    def _proj2DSS (self):
        """
        Projects targes from RA/DEC to X/Y in image pixel coordinates.
        """
        targets = self.targets
        if len(targets) <= 0:
            targets['xpos'] = []
            targets['ypos'] = []
            return
        fheader = self.fheader
        if fheader == None:
            return
        
        xs, ys = fheader.rd2xy(targets.raHour, targets.decDeg)
        targets['xpos'] = xs
        targets['ypos'] = ys
        
    def getDSSInfo (self):
        hdr = self.fheader
        
        nlist = 'platescl', 'xpsize', 'ypsize'  # , 'raDeg', 'decDeg'            
        out = { n: hdr.__dict__[n] for n in nlist }
        
        out['centerRADeg'] = '%.7f' % self.centerRADeg
        out['centerDEC'] = '%.7f' % self.centerDEC
        out['NAXIS1'] = hdr.naxis1
        out['NAXIS2'] = hdr.naxis2
        
        north, east = hdr.skyPA()
        out['northAngle'] = north
        out['eastAngle'] = east
        out['xpsize'] = hdr.xpsize  # pixel size in micron
        out['ypsize'] = hdr.ypsize  # pixel size in micron
        out['platescl'] = hdr.platescl  # arcsec / mm
        
        return out

    def toJson (self):
        data = [ list(self.targets[i]) for i in self.targets ]
        data1 = {'PA' : self.positionAngle } 
        for i, colName in enumerate(self.targets.columns):
            data1[colName] = data[i]        
            
        return json.dumps(data1)                    

    """
    Migrated routines from dsimulator
    ==================================    
    """
    
    def fld2telax (self, fldcenx, fldceny):
        """
        this is taken from dsim.x, procedure fld2telax
        FLD2TELAX:  from field center and rotator PA, calc coords of telescope axis    
        fldcenx = 0
        fldceny = 0
        """
        r = math.radians(math.hypot(fldcenx, fldceny) / 3600.0)
        pa_fld = math.atan2(fldceny, fldcenx)
        cosr = math.cos(r)
        sinr = math.sin(r)
        
        #
        decRad = math.radians(self.centerDEC)
        cosd = math.cos(decRad)  # this is the declination of the center of the field
        sind = math.sin(decRad)  # same
        # pa_fld
        
        pa_diff = math.radians(self.positionAngle) - pa_fld
        
        cost = math.cos(pa_diff)  # pa_fld is calculated above as arctan(fldceny/fldcenx)
        sint = math.sin(pa_diff)
        
        sina = sinr * sint / cosd
        cosa = math.sqrt(1.0 - sina * sina)        
        
        self.telRARad = math.radians(self.centerRADeg) - math.asin(sina)
        self.telDecRad = math.asin((sind * cosd * cosa - cosr * sinr * cost) / (cosr * cosd * cosa - sinr * sind * cost))
            
    
    def calcTelTargetCoords (self, flip, proj_len):   
        """
        Ported from dsimulator
        telRARad and telDecRad must be calculated via fld2telax().
        """     
        ra0 = self.telRARad
        dec0 = self.telDecRad
        pa0 = math.radians(self.positionAngle)
        tt = self.targets
        
        decRad = np.radians(tt.decDeg)
        sinDec = np.sin(decRad)
        sinDec0 = math.sin(dec0)
        cosDec = np.cos(decRad)
        cosDec0 = math.cos(dec0)
        
        deltaRA = np.radians(tt.raHour*15) - ra0
        cosDeltaRA = np.cos(deltaRA)
        sinDeltaRA = np.sin(deltaRA)
        
        cosr = sinDec * sinDec0 + cosDec * cosDec0 * cosDeltaRA
        #cosr = np.clip(cosr, 0, 1.0)
        sinr = np.sqrt(np.abs(1.0 - cosr * cosr))
        r = np.arccos(cosr)
        
        sinp = cosDec * sinDeltaRA / sinr
        cosp = np.sqrt(np.abs(1.0 - sinp*sinp)) * np.where (decRad < dec0, -1, 1)
        p = np.arctan2(sinp, cosp)
        
        rArcsec = sinr / cosr * math.degrees(1) * 3600
        deltaPA = pa0 - p
        tt['xarcs'] = rArcsec * np.cos(deltaPA)
        tt['yarcs'] = rArcsec * np.sin(deltaPA)        
        
    def calcSlitBoxCoords (self):
        """
        xarcs and yarcs must be calculated via calcTelTargetCoords
        """        
        pa0 = math.radians(self.positionAngle)
        tt = self.targest
        
        slitPA = tt.slitPA.copy()
        slitPA[np.isnan(slitPA)] = pa0
        rangle = slitPA - pa0
        tt['relPA'] = rangle
        
        cosRangle = np.cos(rangle)
        factor = (1.0/np.abs(cosRangle)) if proj_len else np.ones_like(cosRangle)
            
        xgeom = np.abs(np.cos(rangle)) * factor
        ygeom = np.sin(rangle) * factor
       
        tt['x1'] = tt.xarcs - tt.length1 * xgeom
        tt['y1'] = tt.yarcs - tt.length1 * ygeom
        tt['x2'] = tt.xarcs + tt.length2 * xgeom
        tt['y2'] = tt.yarcs + tt.length2 * ygeom
                        
        buf=[]
        for i, row in tt.iterrows():
            if row.x1 > row.x2:
                buf.append((row.x2, row.x1, row.y2, row.y1))
            else:
                buf.append((row.x1, row.x2, row.y1, row.y2))
        bufT = np.array(buf).T
        tt.x1 = bufT[0]
        tt.y1 = bufT[2]
        tt.x2 = bufT[1]
        tt.y2 = bufT[3]
    
if __name__ == '__main__':
    import sys    
    from smdtLibs.configFile import ConfigFile
    
    defConfigName = 'smdt.cfg'
    cf = ConfigFile(defConfigName)
    tglist = TargetList(sys.argv[1], useDSS=False, config=cf)
    print ("PA=", tglist.positionAngle, "RA=", tglist.centerRADeg, "DEC=", tglist.centerDEC)
    print ("nr targets", len(tglist.targets))
    for t in tglist.targets:
        print (t)

    print (tglist.targets.slitPA)
    
    #print ("tglist.json", tglist.toJson())
