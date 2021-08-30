#Using data from FITS files instead of .out files
# Name: (fits file, RA Hrs, DEC deg, position angle deg, LST deg, enabled flag
Test_Inputs = {
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
"NoOverlapPa90L4500": ("../DeimosExamples/experimentMasksShared/NoOverlapPa90L4500.fits","17:18:54.36","57:58:55.20",90.0,22.5,True)}