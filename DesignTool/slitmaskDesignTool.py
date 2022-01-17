"""
Created on Mar 23, 2018

@author: skwok
"""

import io
import os
import numpy as np

import matplotlib

from smdtLibs import utils

from targets import TargetList
from maskLayouts import MaskLayouts, GuiderFOVs, BadColumns
from maskDesignFile import MaskDesignOutputFitsFile
from smdtLogger import SMDTLogger

import traceback


class SlitmaskDesignTool:
    """
    This class encapsulates the functionality of the Slitmask design tool.
    """

    def __init__(self, tlistRaw, instrument, config):
        """
        tlistRaw is the target list in raw format (bytes)
        config: configuration object        
        """
        if tlistRaw is None:
            self.setTargetList(None, config=config)
        elif type(tlistRaw) == TargetList:
            self.targetList = tlistRaw
        else:
            tlist = io.StringIO(tlistRaw.decode("UTF-8"))
            self.setTargetList(tlist, config=config)
        self.instrument = instrument
        self.config = config        
        self.maskLayout = MaskLayouts[instrument]

    def setTargetList(self, tlist, config):
        """
        Reset the target list
        """
        self.targetList = TargetList(tlist, config=config)

    def getROIInfo(self):
        """
        Returns information on the region of interest, like center RA/DEC and platescale, etc
        """
        return self.targetList.getROIInfo()

    def getMaskLayout(self):
        """
        Gets the mask layout, which is defined in maskLayout.py as a python data structure for convenience.
        MaskLayoput, GuiderFOV and Badcolumns are defined in maskLayouts.py
        
        Returns a JSON with mask, guiderFOC and badColumns
        """
        try:
            instrument = self.instrument
            mask = MaskLayouts[instrument]  # a list of (x,y,flag), polygon vertices
            guiderFOV = GuiderFOVs[instrument]  # list of (x, y, w, h, ang), boxes
            badColumns = BadColumns[instrument]  # list of lines, as polygons
            return {"mask": mask, "guiderFOV": guiderFOV, "badColumns": badColumns}
        except Exception as e:
            traceback.print_exc()
            return ((0, 0, 0),)

    def recalculateMask(self, raDeg, decDeg, paDeg, minSlitLength, minSep, ext):
        """
        targetIdx: a list of indices of targets that are inside the mask
        ext: extend flag to fill gaps
        """
        targets = self.targetList
        if targets.getNrTargets() <= 0:
            return
        targets.centerRADeg = raDeg
        targets.centerDEC = decDeg
        targets.positionAngle = paDeg
        mask = self.maskLayout
        minX, maxX = np.min(mask, axis=0)[0], np.max(mask, axis=0)[0]

        # Updates targets coordinates for the new center raDeg and decDeg
        targets.reCalcCoordinates(raDeg, decDeg, paDeg)
        targets.markInside ()
        targets.calcSlitPosition(minX, maxX, minSlitLength, minSep, ext)
        # Results are stored in targets

    def setColumnValue(self, colName, value, avalue):
        """
        Updates the entire column in tagets
        """
        targets = self.targetList.targets

        targets.loc[targets.pcode > 0, colName] = value
        targets.loc[targets.pcode < 0, colName] = avalue

    def saveDesignAsFits(self, fname):
        """
        Saves mask design FITS file
        """
        mdf = MaskDesignOutputFitsFile(self.targetList)
        backupName = utils.getBackupName(fname)
        if backupName:
            os.rename(fname, backupName)
        mdf.writeTo(fname)
        SMDTLogger.info("Saved mask degins as FITS " + fname)
        return fname, backupName

    def saveDesignAsList(self, fname):
        tgs = self.targetList
        backupName = utils.getBackupName(fname)
        if backupName:
            os.rename(fname, backupName)
        tgs.writeTo(fname)
        SMDTLogger.info("Saved mask design as list " + fname)
        return fname, backupName

