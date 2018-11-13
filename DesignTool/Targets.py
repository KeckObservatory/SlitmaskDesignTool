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
import datetime

from smdtLogger import SMDTLogger
from TargetSelector import TargetSelector

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
        selected: 0
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
        self.useDSS = useDSS
        if type(fname) == type(io.StringIO()):
            self.targets = self.readRaw (fname)
        else:
            self.targets = self.readFromFile(fname) 
        self.loadDSSInfo(useDSS)
        self.__updateDate()
        
    def __updateDate (self):        
        self.createDate = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
    def loadDSSInfo (self, useDSS=True):
        self._getDSS(useDSS)
        
        if len(self.targets) <= 0:
            return
        if useDSS:
            self._proj2DSS()
        else:                      
            self.reCalcCoordinates(self.centerRADeg, self.centerDEC, self.positionAngle)
        
    def _getDSS (self, useDSS=True):
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

        self.dssFits = None
        
        if useDSS:
            SMDTLogger.info ("Load DSS RA %s hr, DEC %s deg", utils.toSexagecimal(raDeg / 15),
                         utils.toSexagecimal(decDeg))
            self.dssFits = dss2.getFITS(raDeg, decDeg, self.dssSizeDeg)
            if self.dssFits == None:
                SMDTLogger.info ("Failed to load DSS")
            else:
                self.dssData = self.dssFits[0].data
                self.fheader = Dss2Header.DssHeader(self.dssFits[0].header, raDeg, decDeg)    
        
        if self.dssFits == None:
            # Not useDss or failed to load DSS
            h = int(self.dssSizeDeg * 3600)
            w = h
            self.dssData = np.zeros(shape=(h, w))
            self.fheader = Dss2Header.DssWCSHeader(raDeg, decDeg, w, h)
            SMDTLogger.info("No DSS, use WCS") 
                    
        
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
                return 0
                  
        out = []
        cols = 'name', 'raHour', 'decDeg', 'eqx', 'mag', 'band', 'pcode', \
            'sample', 'selected', 'slitPA', 'length1', 'length2', 'slitWidth', \
            'orgIndex'
        cnt = 0
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
            
            template = ['', '', 2000.0, 99, 'I', 99, 0, 1, 0, 4.0, 4.0, 1.5, 0]                
            minLength = min(len(parts), len(template))
            template[:minLength] = parts[:minLength]
            if self._checkPA (parts):
                continue
            
            sample, selected, slitPA, length1, length2, slitWidth = 1, 1, 0, 4, 4, 1.5
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
                selected = int(template[7])
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
                    sample, selected, slitPA, length1, length2, slitWidth, cnt)
            out.append(target) 
            cnt += 1       
        df = pd.DataFrame(out, columns=cols)
        df['inMask'] = np.zeros_like(df.selected)
        
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
            targets['xarcs'] = []
            targets['xarcs'] = []
            return
        fheader = self.fheader
        if fheader == None:
            return
        
        xs, ys = fheader.rd2xy(targets.raHour, targets.decDeg)
        targets['xarcs'] = xs
        targets['yarcs'] = ys
        
    def getROIInfo (self):
        """
        Returns a dict with keywords that look like fits headers
        """
        hdr = self.fheader
        
        nlist = 'platescl', 'xpsize', 'ypsize'  # , 'raDeg', 'decDeg'            
        out = { n: hdr.__dict__[n] for n in nlist }
        
        out['centerRADeg'] = '%.7f' % self.centerRADeg
        out['centerDEC'] = '%.7f' % self.centerDEC
        out['NAXIS1'] = hdr.naxis1
        out['NAXIS2'] = hdr.naxis2
        
        if self.useDSS:
            north, east = hdr.skyPA()
            north = north - 180
            east = east - 180
        else:
            north = 0
            east = 90
        out['useDSS'] = 1 if self.useDSS else 0
        out['northAngle'] = north
        out['eastAngle'] = east
        out['xpsize'] = hdr.xpsize  # pixel size in micron
        out['ypsize'] = hdr.ypsize  # pixel size in micron
        out['platescl'] = hdr.platescl  # arcsec / mm
        out['positionAngle'] = self.positionAngle
        return out

    def toJson (self):
        tgs = self.targets                    
        data = [ list(tgs[i]) for i in tgs ]
        data1 = {} 
        for i, colName in enumerate(tgs.columns):
            data1[colName] = data[i]        
            
        return json.dumps(data1, cls=MyJsonEncoder)
    
    def toJsonWithInfo (self):
        tgs = self.targets                    
        data = [ list(tgs[i]) for i in tgs ]
        data1 = {} 
        for i, colName in enumerate(tgs.columns):
            data1[colName] = data[i]
        
        data2 = {'info': self.getROIInfo(), 'targets' : data1}
        return json.dumps(data2, cls=MyJsonEncoder)
    
    def setColum (self, colName, value):
        self.targets[colName] = value
    
    def select (self, idxList, minX, maxX, minSlitLength, minSep, boxSize):
        targets = self.targets
        targets['inMask'] = np.zeros(targets.shape[0])
        mIdx = targets.columns.get_loc('inMask')
        
        selector = TargetSelector (targets.iloc[idxList], minX, maxX, minSlitLength, minSep, boxSize)
        selIdx = selector.performSelection()
        orgIdx = selector.targets.iloc[selIdx].orgIndex
        targets.iloc[orgIdx, [mIdx]] = 1       
        
        for i, stg in selector.targets.iterrows():
            targets.at[stg.orgIndex, 'length1'] = stg.length1
            targets.at[stg.orgIndex, 'length2'] = stg.length2        

    def updateTarget (self, jvalues):
        values = json.loads(jvalues)
        idx = values['idx']        
        tgs = self.targets
        
        pcode = int(values['prior'])
        selected = int(values['selected'])
        slitPA = float(values['slitPA'])
        slitWidth =  float(values['slitWidth'])       
        len1 = float(values['len1'])
        len2 = float(values['len2']) 
        
        tgs.at[idx, 'pcode'] = pcode
        tgs.at[idx, 'selected'] = selected
        tgs.at[idx, 'slitPA'] = slitPA
        tgs.at[idx, 'slitWidth'] = slitWidth
        tgs.at[idx, 'length1'] = len1
        tgs.at[idx, 'length2'] = len2
        SMDTLogger.info (f'Updated target {idx}, pcode={pcode}, selected={selected}, slitPA={slitPA:.2f}, slitWidth={slitWidth:.2f}, len1={len1}, len2={len2}')
        return 0

    def reCalcCoordinates (self, raDeg, decDeg, posAngleDeg): 
        """
        Recalculates xarcs and yarcs for new center RA/DEC and positionAngle
        Results saved in xarcs, yarcs
        """        
        telRaRad, telDecRad = self._fld2telax( raDeg, decDeg, posAngleDeg)
        self._calcTelTargetCoords(telRaRad, telDecRad,  raDeg, decDeg, posAngleDeg)
        self.__updateDate()
        """
        try:
            self._calcSlitBoxCoords (posAngleDeg)
        except:
            traceback.print_exc()
        """
            
    """
    Migrated routines from dsimulator by Luca Rizzi
    ==================================    
    """
    
    def _fld2telax (self, raDeg, decDeg, posAngle):
        """
        Returns telRaRad and telDecRad.
        
        This is taken from dsim.x, procedure fld2telax
        FLD2TELAX:  from field center and rotator PA, calc coords of telescope axis    
        fldcenx = 0
        fldceny = 0        
        """
        cf = self.config
        fldCenX =  cf.get('fldCenX', 0)
        fldCenY = cf.get('fldCenY', 0)
        
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
        
        return (math.radians(raDeg) - math.asin(sina),
            math.asin((sind * cosd * cosa - cosr * sinr * cost) / (cosr * cosd * cosa - sinr * sind * cost)))
            
    
    def _calcTelTargetCoords (self, ra0, dec0, raDeg, decDeg, posAngle):   
        """
        Calculates xarcs and yarcs, position of the targets in focal plane coordinates in arcsec.
        
        Ported from dsimulator
        telRARad and telDecRad must be calculated via fld2telax().
        """
        cf = self.config
        offx = cf.get('maskOffsetX', 0)
        offy = cf.get('maskOffsetY', 0)  
        
        pa0 = math.radians(posAngle)
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
       
        tt['xarcs'] = rArcsec * np.cos(deltaPA) + offx
        tt['yarcs'] = rArcsec * np.sin(deltaPA) - offy       
    
        
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
    
    print ("tglist.json", tglist.toJson())
