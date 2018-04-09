'''
Created on Mar 23, 2018

@author: skwok
'''

import io
import numpy as np

import matplotlib
matplotlib.use ('Agg')

import matplotlib.pyplot as plt
import smdtLibs.Dss2Client as Dss2Client
import smdtLibs.Dss2Header as DSS2Header

from Targets import TargetList

        
class SlitmaskDesignTool:

    def __init__(self, tlistRaw):
        tlist = io.StringIO(tlistRaw.decode('UTF-8'))
        self.setTargetList(tlist)
      
    def setTargetList (self, tlist):
        self.targetList = TargetList(tlist)          
    
    def drawDSSImage (self):
        """
        Returns the DSS image that covers the targets
        """        
        outData = io.BytesIO()
        plt.imsave(outData, self.targetList.dssData, origin='upper', format='png', cmap='gray')
        outData.seek(0)
        return outData.read()
    
    def getDSSInfo (self):
        def addHeader (keyname):
            out[keyname] = hdr.getHeader(keyname, 0)
            
        tl = self.targetList
        hdr = tl.fheader
        nlist = 'platescl', 'xpsize', 'ypsize', 'raDeg', 'decDeg'            
        out = { n: hdr.__dict__[n] for n in nlist }
        
        addHeader('NAXIS1')
        addHeader('NAXIS2')
        out['centerRADeg'] = "%.7f" % tl.centerRADeg
        out['centerDEC'] = "%.7f" % tl.centerDEC
        return out
        
