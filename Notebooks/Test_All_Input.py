#Using data from FITS files instead of .out files
# Short name: {filename, cenRAdeg, cenDECdeg, PA, LST, selectFLAG}
Test_Inputs = {
"dec0Pa0a": ("../DeimosExamples/Examples2/dec0Pa0.fits","16:29:31.20","00:54:39.60",0.0,0.015,True),
"dec0Pa30a": ("../DeimosExamples/Examples2/dec0Pa30.fits","16:29:31.20","00:54:39.60",30.0,0.015,True),
"dec0Pa75a": ("../DeimosExamples/Examples2/dec0Pa75.fits","16:29:31.20","00:54:39.60",75.0,0.015,True),
"dec0Pa45a": ("../DeimosExamples/Examples2/dec0Pa45.fits","16:29:31.20","00:54:39.60",45.0,0.015,True),
"dec0Pa90a": ("../DeimosExamples/Examples2/dec0Pa90.fits","16:29:31.20","00:54:39.60",90.0,0.015,True),
"dec0Pa60a": ("../DeimosExamples/Examples2/dec0Pa60.fits","16:29:31.20","00:54:39.60",60.0,0.015,True),
"dec0Pa15a": ("../DeimosExamples/Examples2/dec0Pa15.fits","16:29:31.20","00:54:39.60",15.0,0.015,True),
"dec0Pa105a": ("../DeimosExamples/Examples2/dec0Pa105.fits","16:29:31.20","00:54:39.60",105.0,0.015,True),
"dec0Pa150a": ("../DeimosExamples/Examples2/dec0Pa150.fits","16:29:31.20","00:54:39.60",150.0,0.015,True),
"dec0Pa120a": ("../DeimosExamples/Examples2/dec0Pa120.fits","16:29:31.20","00:54:39.60",120.0,0.015,True),
"dec0Pa135a": ("../DeimosExamples/Examples2/dec0Pa135.fits","16:29:31.20","00:54:39.60",135.0,0.015,True),
"dec0Pa180a": ("../DeimosExamples/Examples2/dec0Pa180.fits","16:29:31.20","00:54:39.60",180.0,0.015,True),
"dec0Pa165a": ("../DeimosExamples/Examples2/dec0Pa165.fits","16:29:31.20","00:54:39.60",165.0,0.015,True),
"dec0Pa0": ("../DeimosExamples/Examples1/dec0Pa0.fits","16:29:38.40","00:54:39.60",0.0,0.015,True),
"dec0Pa105": ("../DeimosExamples/Examples1/dec0Pa105.fits","16:29:30.67","00:55:10.70",105.0,0.015,True),
"dec0Pa120": ("../DeimosExamples/Examples1/dec0Pa120.fits","16:29:30.40","00:51:11.70",120.0,0.015,True),
"dec0Pa135": ("../DeimosExamples/Examples1/dec0Pa135.fits","16:29:27.08","00:54:39.60",135.0,0.015,True),
"dec0Pa15": ("../DeimosExamples/Examples1/dec0Pa15.fits","16:29:38.40","00:54:39.60",15.0,0.015,True),
"dec0Pa150": ("../DeimosExamples/Examples1/dec0Pa150.fits","16:29:31.47","00:53:39.60",150.0,0.015,True),
"dec0Pa165": ("../DeimosExamples/Examples1/dec0Pa165.fits","16:29:34.54","00:54:24.10",165.0,0.015,True),
"dec0Pa180": ("../DeimosExamples/Examples1/dec0Pa180.fits","16:29:38.40","00:54:39.60",180.0,0.015,True),
"dec0Pa30": ("../DeimosExamples/Examples1/dec0Pa30.fits","16:29:32.94","00:54:17.60",30.0,0.015,True),
"dec0Pa45": ("../DeimosExamples/Examples1/dec0Pa45.fits","16:29:29.91","00:53:57.20",45.0,0.015,True),
"dec0Pa60": ("../DeimosExamples/Examples1/dec0Pa60.fits","16:29:29.47","00:54:31.60",60.0,0.015,True),
"dec0Pa75": ("../DeimosExamples/Examples1/dec0Pa75.fits","16:29:29.64","00:55:06.50",75.0,0.015,True),
"dec0Pa90": ("../DeimosExamples/Examples1/dec0Pa90.fits","16:29:30.40","00:54:39.60",90.0,0.015,True),
"M53_GAIA_Gmag_le_16_hp4_out": ("../DeimosExamples/M53/M53_GAIA_Gmag_le_16_hp4_out.fits","13:12:56.30","18:09:57.10",0.0,60.0,True),
"M53_GAIA_Gmag_le_16_hp0_out": ("../DeimosExamples/M53/M53_GAIA_Gmag_le_16_hp0_out.fits","13:12:56.30","18:09:57.10",0.0,0.0,True),
"LeoIa": ("../DeimosExamples/EvanKirby/LeoIa.fits","10:08:28.65","12:18:56.00",106.0,-52.5,True),
"n2419c": ("../DeimosExamples/EvanKirby/n2419c.fits","07:38:09.20","38:51:12.00",50.0,-30.0,False),
"denseOverlappingMask": ("../DeimosExamples/experimentMasksShared/denseOverlappingMask.fits","17:19:15.60","57:55:55.20",0.0,0.0,True),
"denseNoOverlappingMask": ("../DeimosExamples/experimentMasksShared/denseNoOverlappingMask.fits","17:19:15.60","57:55:55.20",0.0,0.0,True),
"denseOverlappingPa90Mask": ("../DeimosExamples/experimentMasksShared/denseOverlappingPa90Mask.fits","17:18:45.42","57:58:55.20",90.0,22.5,True),
"denseNoOverlappingPa90Mask": ("../DeimosExamples/experimentMasksShared/denseNoOverlappingPa90Mask.fits","17:18:46.80","57:58:55.20",90.0,22.5,True),
"denseNoOverlapPa270": ("../DeimosExamples/experimentMasksShared/denseNoOverlapPa270.fits","17:18:54.34","57:56:55.20",270.0,22.5,True),
"denseNoOverlapPa180": ("../DeimosExamples/experimentMasksShared/denseNoOverlapPa180.fits","17:19:09.40","57:55:55.10",180.0,22.5,True),
"NoOverlapPa180L4500": ("../DeimosExamples/experimentMasksShared/NoOverlapPa180L4500.fits","17:18:46.80","57:58:55.20",180.0,22.5,True),
"NoOverlapPa270L4500": ("../DeimosExamples/experimentMasksShared/NoOverlapPa270L4500.fits","17:18:46.79","58:01:55.20",270.0,22.5,True),
"NoOverlapPa90L4500": ("../DeimosExamples/experimentMasksShared/NoOverlapPa90L4500.fits","17:18:54.36","57:58:55.20",90.0,22.5,True)
}
