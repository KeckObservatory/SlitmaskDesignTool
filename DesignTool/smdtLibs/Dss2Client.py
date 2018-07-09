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

    def _dummyFITS (self, raDeg, decDeg, searchDeg, dataSet='dss2red'):
           return None
       
    def _getFITS (self, raDeg, decDeg, searchDeg, dataSet='dss2red'):
        """
        dataSet: dss2red, dss2ir, dss2blue
        """        
        conn = HTTPConnection (self.hostport)
        query = []
        query.append('raDeg=%f' % raDeg)
        query.append('decDeg=%f' % decDeg)
        query.append('searchDeg=%f' % searchDeg)
        query.append('dataSet=%s' % dataSet)
        
        conn.request ('GET', '/getimage?' + '&'.join(query))
        resp = conn.getresponse()
        out = None
        if resp.status == 200:
            data = resp.read()
            out = pf.open(io.BytesIO(data))
            conn.close()
        else:
            conn.close()
            raise Exception ("unexpected response {}".format(resp.status))
        return out
    
    def getFITS (self, raDeg, decDeg, searchDeg, dataSet='dss2red'):
        try:
            if self.hostport == None:
                return None
            return self._getFITS (raDeg, decDeg, searchDeg, dataSet)
        except:
            return self._dummyFITS (raDeg, decDeg, searchDeg, dataSet)


if __name__ == "__main__":
    url = "10.96.0.223:50041"
    raDeg = 10
    decDeg = 11
    sizeDeg = 0.3
    dss2 = Dss2Client (url) 
    fits = dss2.getFITS(raDeg, decDeg, sizeDeg) 
    print (fits[0].header.cards)
    