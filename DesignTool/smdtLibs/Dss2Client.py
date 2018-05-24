'''
Created on Mar 29, 2018

For example:

dss2Client = DSS2Client('10.96.0.223:50041')
ff = dss2Client.getFITS(202.475, 47.2, 0.2)

ff is a FITS object, see astropy.io.fits

@author: skwok
'''

import io
import astropy.io.fits as pf
from http.client import HTTPConnection

class Dss2Client:
    
    def __init__ (self, hostport):
        """
        hostport: hostname:portNr
        """
        self.hostport = hostport
        
    def getFITS (self, raDeg, decDeg, radiusDeg, dataSet='dss2red'):
        """
        dataSet: dss2red, dss2ir, dss2blue
        """        
        conn = HTTPConnection (self.hostport)
        query = []
        query.append('raDeg=%f' % raDeg)
        query.append('decDeg=%f' % decDeg)
        query.append('sRadiusDeg=%f' % radiusDeg)
        query.append('dataSet=%s' % dataSet)
        
        conn.request ('GET', '/getimage?' + '&'.join(query))
        resp = conn.getresponse()
        out = None
        if resp.status == 200:
            data = resp.read()
            out = pf.open(io.BytesIO(data))
        else:
            print ("unexpected response", resp.status, '*')
        conn.close()
        return out     