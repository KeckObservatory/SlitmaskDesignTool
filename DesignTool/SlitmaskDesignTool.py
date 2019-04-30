'''
Created on Mar 23, 2018

@author: skwok
'''

import io
import numpy as np

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import smdtLibs.Dss2Client as Dss2Client
import smdtLibs.Dss2Header as DSS2Header

from Targets import TargetList
from maskLayouts import MaskLayouts, GuiderFOVs, BadColumns

import traceback


class SlitmaskDesignTool:

    def __init__(self, tlistRaw, useDSS, config):
        tlist = io.StringIO(tlistRaw.decode('UTF-8'))
        self.setTargetList(tlist, useDSS, config)
        self.config = config

    def setTargetList(self, tlist, useDSS, config):
        self.targetList = TargetList(tlist, useDSS, config)

    def drawDSSImage(self):
        """
        Returns the DSS image that covers the targets
        If no DSS requested, then just return an empty image.
        """
        outData = io.BytesIO()
        # print(self.targetList.dssData.shape)
        plt.imsave(outData, self.targetList.dssData,
                   origin='lower', format='png', cmap='gray')
        outData.seek(0)
        return outData.read()

    def getROIInfo(self):
        """
        Returns information on the region of interest, like center RA/DEC and platescale, etc
        """
        return self.targetList.getROIInfo()

    def getMaskLayout(self, instrument='deimos'):
        """
        Gets the mask layout, which is defined in maskLayout.py as a python data structure for convenience.
        """
        try:
            mask = MaskLayouts[instrument] # a list of (x,y,flag), polygon vertices
            guiderFOV = GuiderFOVs[instrument] # list of (x, y, w, h, ang), boxes
            badColumns = BadColumns[instrument] # list of lines, as polygons
            return {'mask': mask, 'guiderFOV': guiderFOV, 
                    'badColumns' : badColumns}
        except Exception as e:
            traceback.print_exc()
            return ((0, 0, 0),)

    def recalculateMask(self, targetIdx, raDeg, decDeg, paDeg, minSlitLength, minSep, boxSize):
        """
        targetIdx: a list of indices of targets that are inside the mask
        """
        targets = self.targetList
        targets.centerRADeg = raDeg
        targets.centerDEC = decDeg
        targets.positionAngle = paDeg
        mask = MaskLayouts[self.config.get('Instrument').lower()]
        minX, maxX = np.min(mask, axis=0)[0], np.max(mask, axis=0)[0]
        
        # Updates targets coordinates for the new center raDeg and decDeg
        targets.reCalcCoordinates(raDeg, decDeg, paDeg)
        targets.select(targetIdx, minX, maxX, minSlitLength, minSep, boxSize)
        # Results are stored in targets
