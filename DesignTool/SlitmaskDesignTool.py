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
from maskLayouts import MaskLayouts

        
class SlitmaskDesignTool:

    def __init__(self, tlistRaw, useDSS, config):
        tlist = io.StringIO(tlistRaw.decode('UTF-8'))
        self.setTargetList(tlist, useDSS, config)
      
    def setTargetList (self, tlist, useDSS, config):
        self.targetList = TargetList(tlist, useDSS, config)          
    
    def drawDSSImage (self):
        """
        Returns the DSS image that covers the targets
        If no DSS requested, then just return an empty image.
        """       
        outData = io.BytesIO()
        # print(self.targetList.dssData.shape)
        plt.imsave(outData, self.targetList.dssData, origin='lower', format='png', cmap='gray')
        outData.seek(0)
        return outData.read()
        
    def getROIInfo (self):
        """
        Returns information on the region of interest, like center RA/DEC and platescale, etc
        """
        return self.targetList.getROIInfo()
    
    def getMaskLayout (self, instrument='deimos'):
        """
        Gets the mask layout, which is defined in maskLayout.py as a python data structure for convenience.
        """
        try:
            return MaskLayouts[instrument];
        except:
            return ((0,0,0),)
    
    def recalculateMask (self, targetIdx, raDeg, decDeg, paDeg):
        targets = self.targetList
        targets.centerRADeg = raDeg
        targets.centerDEC = decDeg
        targets.positionAngle = paDeg       
        targets.reCalcCoordinates (raDeg, decDeg, paDeg)
        newTargets= targets.select (targetIdx)
        
        return newTargets
        
        