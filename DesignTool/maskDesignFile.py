"""
Module to save the MDF, mask design FITS file.

Initial version: 2018-10-03, skwok

"""

import os
import sys
import math
import datetime
import numpy as np

import io
import pandas as pd
import astropy.io.fits as pf
import astropy.table as atb

from astropy.utils.exceptions import AstropyWarning
import warnings

from smdtLibs.inOutChecker import InOutChecker
from smdtLibs.configFile import ConfigFile
from smdtLibs.utils import sexg2Float, toSexagecimal, rotate

from targets import TargetList
from maskLayouts import MaskLayouts

SMDT_Name = "SMDT Version 0.9"

#
# Fields: "MEMBER_NAME", "KwdOrCol", "Element", "RDBtable", "RDBField"
#
RDBMapTable = """
BluSlits,C,bSlitId,BluSlits,bSlitId
BluSlits,C,BluId,BluSlits,BluId
BluSlits,C,dSlitId,BluSlits,dSlitId
BluSlits,C,slitX1,BluSlits,slitX1
BluSlits,C,slitY1,BluSlits,slitY1
BluSlits,C,slitX2,BluSlits,slitX2
BluSlits,C,slitY2,BluSlits,slitY2
BluSlits,C,slitX3,BluSlits,slitX3
BluSlits,C,slitY3,BluSlits,slitY3
BluSlits,C,slitX4,BluSlits,slitX4
BluSlits,C,slitY4,BluSlits,slitY4
MaskBlu,C,BluId,MaskBlu,BluId
MaskBlu,C,DesId,MaskBlu,DesId
MaskBlu,C,BluName,MaskBlu,BluName
MaskBlu,C,guiname,MaskBlu,guiname
MaskBlu,C,BluObsvr,MaskBlu,BluPId:Observers:email
MaskBlu,C,BluCreat,MaskBlu,BluCreat
MaskBlu,C,BluDate,MaskBlu,BluDate
MaskBlu,C,LST_Use,MaskBlu,LST_Use
MaskBlu,C,Date_Use,MaskBlu,Date_Use
MaskBlu,C,TELESCOP,MaskBlu,TeleId:Telescopes:TELESCOP
MaskBlu,C,AtmTempC,MaskBlu,AtmTempC
MaskBlu,C,AtmPres,MaskBlu,AtmPres
MaskBlu,C,AtmHumid,MaskBlu,AtmHumid
MaskBlu,C,AtmTTLap,MaskBlu,AtmTTLap
MaskBlu,C,RefWave,MaskBlu,RefWave
DesiSlits,C,dSlitId,DesiSlits,dSlitId
DesiSlits,C,DesId,DesiSlits,DesId
DesiSlits,C,SlitName,DesiSlits,SlitName
DesiSlits,C,slitRA,DesiSlits,slitRA
DesiSlits,C,slitDec,DesiSlits,slitDec
DesiSlits,C,slitTyp,DesiSlits,slitTyp
DesiSlits,C,slitLen,DesiSlits,slitLen
DesiSlits,C,slitLPA,DesiSlits,slitLPA
DesiSlits,C,slitWid,DesiSlits,slitWid
DesiSlits,C,slitWPA,DesiSlits,slitWPA
MaskDesign,C,DesId,MaskDesign,DesId
MaskDesign,C,DesName,MaskDesign,DesName
MaskDesign,C,DesAuth,MaskDesign,DesPId:Observers:email
MaskDesign,C,DesCreat,MaskDesign,DesCreat
MaskDesign,C,DesDate,MaskDesign,DesDate
MaskDesign,C,DesNslit,MaskDesign,DesNslit
MaskDesign,C,DesNobj,MaskDesign,DesNobj
MaskDesign,C,ProjName,MaskDesign,ProjName
MaskDesign,C,INSTRUME,MaskDesign,INSTRUME
MaskDesign,C,MaskType,MaskDesign,MaskType
MaskDesign,C,RA_PNT,MaskDesign,RA_PNT
MaskDesign,C,DEC_PNT,MaskDesign,DEC_PNT
MaskDesign,C,RADEPNT,MaskDesign,RADEPNT
MaskDesign,C,EQUINPNT,MaskDesign,EQUINPNT
MaskDesign,C,PA_PNT,MaskDesign,PA_PNT
MaskDesign,C,DATE_PNT,MaskDesign,DATE_PNT
MaskDesign,C,LST_PNT,MaskDesign,LST_PNT
ObjectCat,C,ObjectId,Objects,ObjectId
ObjectCat,C,OBJECT,Objects,OBJECT
ObjectCat,C,RA_OBJ,Objects,RA_OBJ
ObjectCat,C,DEC_OBJ,Objects,DEC_OBJ
ObjectCat,C,RADESYS,Objects,RADECSYS
ObjectCat,C,EQUINOX,Objects,EQUINOX
ObjectCat,C,MJD-OBS,Objects,MJD_OBS
ObjectCat,C,mag,Objects,mag
ObjectCat,C,pBand,Objects,pBand
ObjectCat,C,RadVel,Objects,RadVel
ObjectCat,C,MajAxis,Objects,MajAxis
ObjectCat,C,ObjectId,ExtendObj,ObjectId
ObjectCat,C,MajAxPA,ExtendObj,MajAxPA
ObjectCat,C,MinAxis,ExtendObj,MinAxis
ObjectCat,C,ObjectId,NearObj,ObjectId
ObjectCat,C,PM_RA,NearObj,PM_RA
ObjectCat,C,PM_Dec,NearObj,PM_Dec
ObjectCat,C,Parallax,NearObj,Parallax
ObjectCat,C,ObjClass,Objects,ObjClass
SlitObjMap,C,DesId,SlitObjMap,DesId
SlitObjMap,C,ObjectId,SlitObjMap,ObjectId
SlitObjMap,C,dSlitId,SlitObjMap,dSlitId
SlitObjMap,C,TopDist,SlitObjMap,TopDist
SlitObjMap,C,BotDist,SlitObjMap,BotDist
"""


class MaskDesignOutputFitsFile:
    def __init__(self, targetList):
        """
        This class represents the Mask Design Fits File.
        It is used to save the FITS file as output of the design process

        targetList: input target list.
    
        The FITS file contains 8 tables, see _getHDUList().

        - Table objectcat: star catalog
        - Table catfiles:  input catalog file name(s), not used?
        - Table maskdesign: mask's metadata, contains reference RA/DEC
        - Table desislits: Slits RA/DEC, lengths, PAs
        - Table slitobjmap: object position inside the slits
        - Table maskblu: more meta data, includes, temp, humidity, pressure, wavelength
        - Table bluslits: slist coordiantes, 4 corners
        - Table rdbmap: field name mapping to database

        """
        self.targetList = targetList

    def genObjCatTable(self):
        """
        Generates the object catalog table
        """
        targets = self.targetList.targets
        objClassTable = ("Alignment_Star", "Guide_Star", "Ignored", "Program_Target")
        cols = []
        nTargets = targets.shape[0]
        zeros = [0] * nTargets
        objClass = [objClassTable[min(3, p + 2)] for p in targets.pcode]
        cols.append(pf.Column(name="ObjectId", format="I6", null="-9999", unit="None", array=range(nTargets)))
        cols.append(pf.Column(name="OBJECT", format="A68", null="INDEF", unit="None", array=targets.objectId))
        cols.append(pf.Column(name="RA_OBJ", format="F12.8", null="-9999.000000", unit="deg", array=targets.raHour * 15.0))
        cols.append(pf.Column(name="DEC_OBJ", format="F12.8", null="-9999.000000", unit="deg", array=targets.decDeg))
        cols.append(pf.Column(name="RADESYS", format="A8", null="INDEF", unit="None"))
        cols.append(pf.Column(name="EQUINOX", format="F8.3", null="-9999.00", unit="a", array=[2000] * nTargets))
        cols.append(pf.Column(name="MJD-OBS", format="F11.3", null="-9999.000", unit="d", array=zeros))
        cols.append(pf.Column(name="mag", format="F7.3", null="-9999.0", unit="None", array=targets.mag))
        cols.append(pf.Column(name="pBand", format="A6", null="INDEF", unit="None", array=targets.pBand))
        cols.append(pf.Column(name="RadVel", format="F10.3", null="-9999.000", unit="None", array=zeros))
        cols.append(pf.Column(name="MajAxis", format="F9.2", null="-9999.00", unit="arcsec", array=zeros))
        cols.append(pf.Column(name="MajAxPA", format="F8.2", null="-9999.00", unit="deg", array=zeros))
        cols.append(pf.Column(name="MinAxis", format="F9.2", null="-9999.00", unit="arcsec", array=zeros))
        cols.append(pf.Column(name="PM_RA", format="F9.4", null="-9999.000", unit="arcsec/a", array=zeros))
        cols.append(pf.Column(name="PM_Dec", format="F9.4", null="-9999.000", unit="arcsec/a", array=zeros))
        cols.append(pf.Column(name="Parallax", format="F7.4", null="-9999.0", unit="arcsec", array=zeros))
        cols.append(pf.Column(name="ObjClass", format="A20", null="INDEF", unit="None", array=objClass))
        cols.append(pf.Column(name="CatFilePK", format="I6", null="-9999", unit="None", array=[1] * nTargets))
        return pf.TableHDU.from_columns(cols, name="ObjectCat")

    def genCatFiles(self):
        """
        Generates the catalog file table. Maybe not used downstream.
        """
        targets = self.targetList.targets
        cols = []
        cols.append(pf.Column(name="CatFilePK", format="I6", null="-9999", unit="None", array=[1]))
        cols.append(pf.Column(name="CatFileName", format="A255", null="INDEF", unit="None", array=["INDEF"],))
        return pf.TableHDU.from_columns(cols, name="CatFiles")

    def genMaskDesign(self):
        """
        Generates the mask design parameter table.
        """
        tlist = self.targetList
        targets = tlist.targets
        params = tlist.config.params
        cols = []
        createDate = tlist.createDate
        objInMask = targets[targets.inMask > 0]
        nSlits = objInMask[objInMask.pcode > 0].shape[0]
        nObjs = nSlits + objInMask[objInMask == -2].shape[0]
        pId = -1

        cols.append(pf.Column(name="DesId", format="I11", null="-9999", unit="None", array=[1]))
        cols.append(pf.Column(name="DesName", format="A68", null="INDEF", unit="None", array=[params.MaskName[0]],))
        cols.append(pf.Column(name="DesAuth", format="A68", null="INDEF", unit="None", array=[params.Author[0]],))
        cols.append(pf.Column(name="DesCreat", format="A68", null="INDEF", unit="None", array=[SMDT_Name],))
        cols.append(pf.Column(name="DesDate", format="A19", null="INDEF", unit="None", array=[createDate],))
        cols.append(pf.Column(name="DesNslit", format="I11", null="-9999", unit="None", array=[nSlits]))
        cols.append(pf.Column(name="DesNobj", format="I11", null="-9999", unit="None", array=[nObjs]))
        cols.append(pf.Column(name="ProjName", format="A68", null="INDEF", unit="None", array=[params.ProjectName[0]],))
        cols.append(pf.Column(name="INSTRUME", format="A68", null="INDEF", unit="None", array=[params.Instrument[0]],))
        cols.append(pf.Column(name="MaskType", format="A68", null="INDEF", unit="None", array=["Mask"]))
        cols.append(pf.Column(name="RA_PNT", format="F12.8", null="-9999.000000", unit="deg", array=[tlist.centerRADeg],))
        cols.append(pf.Column(name="DEC_PNT", format="F12.8", null="-9999.000000", unit="deg", array=[tlist.centerDEC],))
        cols.append(pf.Column(name="RADEPNT", format="A8", null="INDEF", unit="None", array=[""]))
        cols.append(pf.Column(name="EQUINPNT", format="F13.6", null="-9999.000000", unit="a", array=[2000.0],))
        cols.append(pf.Column(name="PA_PNT", format="F12.7", null="-9999.000000", unit="deg", array=[params.MaskPA[0]],))
        cols.append(pf.Column(name="DATE_PNT", format="A19", null="INDEF", unit="None", array=[params.ObsDate[0]],))
        cols.append(pf.Column(name="LST_PNT", format="F8.3", null="-9999.00", unit="deg", array=[0]))  # May be HourAngle in deg
        return pf.TableHDU.from_columns(cols, name="MaskDesign")

    def genDesiSlits(self):
        """
        Generates the slit table
        Includes slits RA/DEC and PA

        Slit type:
        A: alignment
        G: guider
        I: ignore
        P: target
        """
        targets = self.targetList.targets
        cols = []

        objInMask = targets[targets.inMask > 0]
        nSlits = objInMask.shape[0]
        if nSlits > 0:
            slitTypeTable = ("A", "G", "I", "P")

            slitNames = [("%03d" % x) for x in range(nSlits)]
            slitTypes = [slitTypeTable[min(3, p + 2)] for p in objInMask.pcode]
            slitLengths = [(l1 + l2) for l1, l2 in zip(objInMask.length1, objInMask.length2)]

            cols.append(pf.Column(name="dSlitId", format="I11", null="-9999", unit="None", array=range(nSlits)))
            cols.append(pf.Column(name="DesId", format="I11", null="-9999", unit="None", array=[1] * nSlits))
            cols.append(pf.Column(name="SlitName", format="A20", null="None", unit="None", array=slitNames))
            cols.append(pf.Column(name="slitRA", format="F12.8", null="-9999.000000", unit="deg", array=objInMask.raHour * 15))
            cols.append(pf.Column(name="slitDec", format="F12.8", null="-9999.000000", unit="deg", array=objInMask.decDeg))
            cols.append(pf.Column(name="slitTyp", format="A1", null="I", unit="None", array=slitTypes))
            cols.append(pf.Column(name="slitLen", format="F11.3", null="-9999.000", unit="arcsec", array=slitLengths))
            cols.append(pf.Column(name="slitLPA", format="F8.3", null="-9999.00", unit="deg", array=objInMask.slitLPA))
            cols.append(pf.Column(name="slitWid", format="F11.3", null="-9999.000", unit="arcsec", array=objInMask.slitWidth))
            cols.append(pf.Column(name="slitWPA", format="F8.3", null="-9999.00", unit="deg", array=[140] * nSlits))
        return pf.TableHDU.from_columns(cols, name="DesiSlits")

    def genSlitObMap(self):
        """
        Generates the slits object table with distances to star and end of slit
        """
        targets = self.targetList.targets
        cols = []
        objInMask = targets[targets.inMask > 0]
        nSlits = objInMask.shape[0]
        if nSlits > 0:
            cols.append(pf.Column(name="DesId", format="I11", null="-9999", unit="None", array=[1] * nSlits,))
            cols.append(pf.Column(name="ObjectId", format="I11", null="-9999", unit="None", array=range(nSlits)))
            cols.append(pf.Column(name="dSlitId", format="I11", null="-9999", unit="None", array=range(nSlits)))
            cols.append(pf.Column(name="TopDist", format="F11.3", null="-9999.000", unit="arcsec", array=objInMask.length1))
            cols.append(pf.Column(name="BotDist", format="F11.3", null="-9999.000", unit="arcsec", array=objInMask.length2))

        return pf.TableHDU.from_columns(cols, name="SlitObjMap")

    def genMaskBlu(self):
        """
        Generates table with mask information
        """
        tlist = self.targetList
        targets = tlist.targets
        params = tlist.config.params
        cols = []
        ts = datetime.datetime.strptime(params.ObsDate[0], "%Y-%m-%d %H:%M:%S")
        obsDate = ts.strftime("%Y-%m-%d")
        obsTime = sexg2Float(ts.strftime("%H:%M:%S")) * 15  # to degree
        refWave = float(params.CenterWaveLength[0]) / 10  # to nanometer

        cols.append(pf.Column(name="BluId", format="I11", null="-9999", unit="None", array=[1]))
        cols.append(pf.Column(name="DesId", format="I11", null="-9999", unit="None", array=[1]))
        cols.append(pf.Column(name="BluName", format="A68", null="INDEF", unit="None", array=[params.MaskName[0]]))
        cols.append(pf.Column(name="guiname", format="A8", null="INDEF", unit="None", array=[params.MaskName[0]]))
        cols.append(pf.Column(name="BluObsvr", format="A68", null="INDEF", unit="None", array=[params.Observer[0]]))
        cols.append(pf.Column(name="BluCreat", format="A68", null="INDEF", unit="None", array=[SMDT_Name]))
        cols.append(pf.Column(name="BluDate", format="A19", null="INDEF", unit="None", array=[tlist.createDate]))
        cols.append(pf.Column(name="LST_Use", format="F8.3", null="-9999.00", unit="deg", array=[obsTime]))  # Needs HA here
        cols.append(pf.Column(name="Date_Use", format="A19", null="INDEF", unit="None", array=[obsDate]))
        cols.append(pf.Column(name="TELESCOP", format="A68", null="INDEF", unit="None", array=[params.Telescope[0]]))
        cols.append(pf.Column(name="RefrAlg", format="A68", null="INDEF", unit="None", array=["Built-in"]))

        cols.append(pf.Column(name="AtmTempC", format="F5.1", null="-9999", unit="degC", array=[params.Temperature[0]]))

        cols.append(pf.Column(name="AtmPres", format="F6.1", null="-999.0", unit="hPa", array=[params.Pressure[0]]))
        cols.append(pf.Column(name="AtmHumid", format="F5.3", null="-9999", unit="None", array=[0.4]))
        cols.append(pf.Column(name="AtmTTLap", format="F7.5", null="-9999.0", unit="K/m", array=[0.0065]))
        cols.append(pf.Column(name="RefWave", format="F7.2", null="-999.0", unit="nm", array=[refWave / 10.0]))  # A to nm.
        cols.append(pf.Column(name="DistMeth", format="A68", null="INDEF", unit="None", array=["INDEF"]))
        return pf.TableHDU.from_columns(cols, name="MaskBlu")

    def genBluSlits(self):
        """
        Generates the list of slits coordinates
        """
        targets = self.targetList.targets
        params = self.targetList.config.params

        cols = []
        objInMask = targets[targets.inMask > 0]
        nSlits = objInMask.shape[0]
        if nSlits > 0:
            cols.append(pf.Column(name="bSlitId", format="I11", null="-9999", unit="None", array=range(nSlits)))
            cols.append(pf.Column(name="BluId", format="I11", null="-9999", unit="None", array=[1] * nSlits))
            cols.append(pf.Column(name="dSlitId", format="I11", null="-9999", unit="None", array=range(nSlits)))
            cols.append(pf.Column(name="slitX1", format="F9.3", null="0.000", unit="mm", array=objInMask.slitX1))
            cols.append(pf.Column(name="slitY1", format="F9.3", null="0.000", unit="mm", array=objInMask.slitY1))
            cols.append(pf.Column(name="slitX2", format="F9.3", null="0.000", unit="mm", array=objInMask.slitX2))
            cols.append(pf.Column(name="slitY2", format="F9.3", null="0.000", unit="mm", array=objInMask.slitY2))
            cols.append(pf.Column(name="slitX3", format="F9.3", null="0.000", unit="mm", array=objInMask.slitX3))
            cols.append(pf.Column(name="slitY3", format="F9.3", null="0.000", unit="mm", array=objInMask.slitY3))
            cols.append(pf.Column(name="slitX4", format="F9.3", null="0.000", unit="mm", array=objInMask.slitX4))
            cols.append(pf.Column(name="slitY4", format="F9.3", null="0.000", unit="mm", array=objInMask.slitY4))

        return pf.TableHDU.from_columns(cols, name="BluSlits")

    def genRDBmap(self):
        """
        Generates the database field mapping
        """
        df = pd.read_csv(io.StringIO(RDBMapTable))
        df.columns = "MEMBER_NAME", "KwdOrCol", "Element", "RDBtable", "RDBField"

        targets = self.targetList.targets

        cols = []
        cols.append(pf.Column(name="MEMBER_NAME", format="A32", null="None", unit="None", array=df.MEMBER_NAME,))
        cols.append(pf.Column(name="KwdOrCol", format="A1", unit="None", array=df.KwdOrCol))
        cols.append(pf.Column(name="Element", format="A16", null="None", unit="None", array=df.Element))
        cols.append(pf.Column(name="RDBtable", format="A32", null="None", unit="None", array=df.RDBtable,))
        cols.append(pf.Column(name="RDBfield", format="A32", null="None", unit="None", array=df.RDBField,))
        return pf.TableHDU.from_columns(cols, name="RDBmap")

    def _getHDUList(self):
        """
        Assembles all the HDUs
        """
        hdus = []
        hdus.append(pf.PrimaryHDU())
        hdus.append(self.genObjCatTable())
        hdus.append(self.genCatFiles())
        hdus.append(self.genMaskDesign())
        hdus.append(self.genDesiSlits())
        hdus.append(self.genSlitObMap())
        hdus.append(self.genMaskBlu())
        hdus.append(self.genBluSlits())
        hdus.append(self.genRDBmap())
        return pf.HDUList(hdus)

    def getFitsAsBytes(self):
        """
        Converts HDUs to bytes
        """
        hlist = self._getHDUList()
        outfh = io.BytesIO()
        hlist.writeto(outfh)
        outfh.seek(0)
        return outfh.read()

    def writeTo(self, fileName):
        """
        Writes to file
        """
        hlist = self._getHDUList()
        hlist.writeto(fileName)


def _outputAsList(fh, targets):
    for i, row in targets.iterrows():
        print(
            "{:18s}{} {} {:.0f}{:>6.2f} {} {:5d} {} {} {}".format(
                row.objectId,
                toSexagecimal(row.raHour),
                toSexagecimal(row.decDeg),
                row.eqx,
                row.mag,
                row.pBand,
                row.pcode,
                row.sampleNr,
                row.selected,
                row.slitLPA,
            ),
            file=fh,
        )


def getListAsBytes(targets):
    """
    Outputs target list.
    Returns bytes
    """
    outfh = io.BytesIO()
    _outputAsList(outfh, targets)
    outfh.seek(0)
    return outfh.read()


def outputAsList(fileName, targets):
    """
    Outputs target list in list form to a file
    """
    with open(fileName, "w") as fh:
        _outputAsList(fh, targets)


class MaskDesignInputFitsFile:
    """
    This class handles the Fits File generated by MaskDesignOutputFitsFile
    """

    def __init__(self, fileName):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", AstropyWarning)
            self.tables = []
            ff = pf.open(fileName)
            for hdr in ff:
                self.tables.append(hdr.name)
                self.__dict__[hdr.name.lower()] = pd.DataFrame(hdr.data)
            self.allSlits = self.mergeSlitTables()

    def _genPcode(self, slits):
        table = {"A": -2, "G": -1, "I": 0, "P": 1}
        return [table.get(t, 0) for t in slits.slitTyp]
        
    def mergeSlitTables(self):
        """
        Returns a dataframe that contains all the slit information.

        slitobjmap : object position inside slits
        bluslits: X/Y of 4 corners of the slits
        desislits: RA/DEC coordinate and PAs of the slists
        
        All joined together in a single table: allSlits

        """
        self.objectcat.ObjClass = [s.strip() for s in self.objectcat.ObjClass]
        self.objectcat.OBJECT = [s.strip() for s in self.objectcat.OBJECT]

        out = self.objectcat.merge(self.slitobjmap, on="ObjectId", how="outer")
        out = out.merge(self.bluslits, on="dSlitId", how="outer")
        out = out.merge(self.desislits, on="dSlitId", how="outer")
        out["pcode"] = self._genPcode(out)
        return out

    def getObjOnSlit(self, slits=None):
        """
        Returns the position of the object within the slit, 
        using the geometry of the list and the lenghts ratio
        """
        slits = self.allSlits if slits is None else slits
        x0 = (slits.slitX1 + slits.slitX4) / 2
        y0 = (slits.slitY1 + slits.slitY4) / 2
        x1 = (slits.slitX3 + slits.slitX2) / 2
        y1 = (slits.slitY3 + slits.slitY2) / 2

        t = slits.BotDist / (slits.TopDist + slits.BotDist)
        x = (x1 - x0) * t + x0
        y = (y1 - y0) * t + y0
        return x, y

    def getLengths(self):
        slits = self.allSlits
        x0 = slits.slitX1
        x1 = slits.slitX2
        y0 = slits.slitY1
        y1 = slits.slitY2
        dists = np.max(np.abs(x1 - x0), np.abs(y1 - y0))
        return dists

    def getPNTCenter(self):
        """
        Returns the pointing RA/DEC as (ra, dec), PA
        """
        return (
            self.maskdesign.RA_PNT[0],
            self.maskdesign.DEC_PNT[0],
            self.maskdesign.PA_PNT[0],
        )

    def getRotationCenter(self, config):
        vx, vy = config.getValue("fldCenX"), config.getValue("fldCenY")
        radius = math.hypot(vx, vy) / 3600  # arcsec to degree

        pntX, pntY, paDeg = self.getPNTCenter()
        paRad = -math.radians(paDeg)

        dx = math.cos(paRad) * radius
        dy = math.sin(paRad) * radius
        return pntX - dx, pntY - dy

    def getAlignBoxes(self, slits=None):
        slits = self.allSlists if slits == None else slits
        return slits[["A" == s for s in slits.slitTyp]]

    def pntCen2MaskCenter (self, config):
        """
        Calculates the mask center using the PNT center.
        Returns mask center Ra/dec, and paDeg
        """               
        pntX, pntY = config.properties["fldcenx"], config.properties["fldceny"]
        pntRa, pntDec, paDeg = self.getPNTCenter()

        x1, y1 = rotate(-pntX, -pntY, -paDeg - 90)
        cosd = np.cos(np.radians(pntDec))

        y1 = y1 / cosd
        return pntRa + x1 / 3600, pntDec + y1 / 3600, paDeg

    def getAsTargets(self, config):
        """
        Returns the target list stored int the FITS file as a TargetList object.
        Pcode: -2 alignment, -1 guide box, 0 ignore, 1 target
        """


        objects = self.objectcat
        objIndices = dict([(i1, i0) for i0, i1 in enumerate(objects.ObjectId)])

        orgIndices = [objIndices[d] for d in self.slitobjmap.ObjectId]
        nSlits = len(self.allSlits)
        self.allSlits["raHour"] = [objects.RA_OBJ.iloc[d] / 15.0 for d in orgIndices]
        self.allSlits["decDeg"] = [objects.DEC_OBJ.iloc[d] for d in orgIndices]
        self.allSlits["raRad"] =  [math.radians(objects.RA_OBJ.iloc[d]) for d in orgIndices]
        self.allSlits["decRad"] =  [math.radians(objects.DEC_OBJ.iloc[d]) for d in orgIndices]

        self.allSlits["objectId"] = [objects.OBJECT.iloc[d].strip() for d in orgIndices]
        self.allSlits["eqx"] = [objects.EQUINOX.iloc[d] for d in orgIndices]
        self.allSlits["mag"] = [objects.mag.iloc[d] for d in orgIndices]
        self.allSlits["pBand"] = [objects.pBand.loc[d].strip() for d in orgIndices]
        self.allSlits["length1"] = self.allSlits["TopDist"]
        self.allSlits["length2"] = self.allSlits["BotDist"]

        self.allSlits["orgIndex"] = range(nSlits)
        self.allSlits["inMask"] = [0] * nSlits
        self.allSlits["selected"] = [0] * nSlits
        self.allSlits["sampleNr"] = [1] * nSlits
        self.allSlits["slitWidth"] = self.allSlits.slitWid

        # raDeg, decDeg = self.getCenter()
        paDeg = self.maskdesign.PA_PNT[0]

        return TargetList(pd.DataFrame(self.allSlits).copy(), config)

