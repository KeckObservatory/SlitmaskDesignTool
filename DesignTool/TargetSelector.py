"""
TargetSelector.py

This moddule provides tools to select targets and create slits such the meet given criteria
such as not overlapping, minimum separation, etc.

Date: 2018-08-01

"""

class TargetSelector:
    def __init__(self, targetList):
        self.targes = targetList
        
    def getSelected (self):
        """
        Returns a list of selected targets
        """
        return []
