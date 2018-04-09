'''
Created on Mar 20, 2018

@author: skwok
'''

import math
from smdtLibs import utils
from smdtLibs import Dss2Client, Dss2Header
import io
import sys
import pandas as pd
import traceback
import json


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

    def __init__(self, fname):
        self.fileName = fname
        self.positionAngle = 0
        self.centerRADeg = 0
        self.centerDEC = 0
        self.dssSizeDeg = 0.35  # deg
        if type(fname) == type(io.StringIO()):
            self.targets = self.readRaw (fname)
        else:
            self.targets = self.readFromFile(fname)
        self._getDSSInfo()
        self._proj2DSS()   
        
    def _getDSSInfo (self):
        """
        Gets DSS image and info
        """
        dss2 = Dss2Client.Dss2Client ("10.96.0.223:50041")
        targets = self.targets
        if len(targets) <= 0:
            raDeg, decDeg = 0, 0
        else:
            raDeg, decDeg = self.centerRADeg, self.centerDEC
            
        print ("raHour, decDeg", utils.toSexagecimal(raDeg / 15),
            utils.toSexagecimal(decDeg))
        self.dssFits = dss2.getFITS(raDeg, decDeg, self.dssSizeDeg)
        self.dssData = self.dssFits[0].data
        self.fheader = Dss2Header.DssHeader(self.dssFits[0].header)        
        
    def checkPA (self, inParts):
        """
        Checks if input line contains the center RA/DEC and PA
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
            'sample', 'select', 'slitPA', 'length1', 'length2', 'slitWidth'
        
        for nr, line in enumerate(fh):
            if not line or len(line) == 0:
                continue
            if line[0] == '#':
                continue
            line = line.strip()
            parts = line.split()
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
            if self.checkPA (parts):
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
                print (nr, e, template, file=sys.stderr)
                # traceback.print_exc()
                # break
                pass
            target = (name, raHour, decDeg, \
                            eqx, mag, band, pcode, \
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
        xycoords = []
        targets = self.targets
        if len(targets) <= 0:
            targets['xpos'] = []
            targets['ypos'] = []
            return
        fheader = self.fheader
        for raHour, decdeg in zip(targets.raHour, targets.decDeg):
            xycoords.append(fheader.rd2xy(raHour * 15, decdeg))
        
        # Transponse and make columns
        xys = list(map (list, zip(*xycoords)))
        targets['xpos'] = xys[0]
        targets['ypos'] = xys[1]

    def toJson (self):
        data = [ list(self.targets[i]) for i in self.targets ]
        data1 = {'PA' : self.positionAngle } 
        for i, colName in enumerate(self.targets.columns):
            data1[colName] = data[i]        
            
        return json.dumps(data1)                    

    
if __name__ == '__main__':
    import sys
    tglist = TargetList(sys.argv[1])
    print ("PA=", tglist.positionAngle, "RA=", tglist.centerRADeg, "DEC=", tglist.centerDEC)
    for t in tglist.targets:
        print (t)

    # print ("tglist.json", tglist.toJson())
