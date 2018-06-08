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
        
    def getDSSInfo (self):
        # print ("DSS ", self.targetList.getDSSInfo())
        return self.targetList.getDSSInfo()
    