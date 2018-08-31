"""
TargetSelector.py

This moddule provides tools to select targets and create slits such the meet given criteria
such as not overlapping, minimum separation, etc.

Date: 2018-08-01


Notes:

targets is a list of all targets that are inside the mask.

After selecting the targets, the flag 'selected' should be set to 1 for those targets that are selected.
If slit lengths, or angles or widths are changed, these are also updated in the data structure
and returned in getSelected.

"""

class TargetSelector:
    def __init__(self, targetList,  minX, maxX, minSlitLength, minSep, boxSize):
        """
        targetList is a pandas data frame
        minSep is minimal separation between slits in arcsec.
        """
        self.targets = targetList.copy()
        self._sortTargets()
        self.minX = minX
        self.maxX = maxX
        self.minSlitLength = minSlitLength
        self.boxSize = boxSize
        self.minSep = minSep
        
    def _sortTargets (self):
        tgs = self.targets
        tgs['xsort'] = tgs.xarcs - tgs.length1
        tgs.sort_values(by=['selected', 'pcode','xsort'], ascending=(False, False, True), inplace=True)
        self.targets = tgs.reset_index(drop=True)
    
    def _canFit (self, xgaps, xpos, slitLength, minSep, margin):
        """
        Tries to fit the new segment in a gap
        """        
        minMargin = minSep + margin
        #print ('xgaps', xgaps)
        for idx, (gapStart, gapEnd) in enumerate(xgaps):
            #print ("xpos", xpos, "gap", gapStart, gapEnd)
            if xpos < gapStart:
                return False, idx
            if xpos > gapEnd:
                continue
            
            if (gapStart + minMargin) < xpos < (gapEnd - minMargin):
                gapLength = gapEnd - gapStart - minSep
                if gapLength < slitLength:
                    """ Gap too short """
                    return False, idx
                return True, idx
        return False, -1
    
    def _splitGap (self, xgaps, gIdx, xpos, slitLength, minSep, margin):
        """
        Splits the gap at xgaps[gIdx] into two
        """
        gapStart, gapEnd = xgaps[gIdx]
        # gap will be split into two gaps
        
        minMargin = minSep + margin
        halfLength = slitLength / 2.0
        if xpos - halfLength < gapStart + minSep:
            left = gapStart + minSep
            right = left + slitLength
        elif gapEnd - minSep < xpos + halfLength:
            right = gapEnd - minSep
            left = right - slitLength
        else:
            left = xpos - halfLength
            right = xpos + halfLength
        
        # gap1 = gapStart, left
        # gap2 = right, gapEnd
        xgaps[gIdx] = (gapStart, left)
        xgaps.insert(gIdx+1, (right, gapEnd))
        return xgaps, left, right                     

    def mergeSegments (self, xsegms, left, right):
        if len(xsegms) == 0:
            return [(left, right)]
        else:
            xsegms.append((left, right))
        s0 = [ (a[0], a) for a in xsegms ]
        s0.sort()
        xsegms = [ t for s, t in s0 ]
        left, right = xsegms[0]
        newSegms = []
        for start, end in xsegms[1:]:
            #print ('newseg', newSegms)
            if right < start or end < left:
                # disjunct
                newSegms.append((left, right))
                left, right = start, end
                continue
            # merge
            x0 = min(start, left)
            x1 = max(end, right)
            left, right = x0, x1        
        newSegms.append((left, right))
        return newSegms
    
    def segments2Gaps (self, xsegms, xgaps, margin):
        for start, end in xsegms:
            newGaps = []
            #print ('segm', start, end, xgaps)
            for left, right in xgaps:
                if right < start or end < left:
                    # disjunct
                    newGaps.append ((left, right))
                else:
                    # merge gap and segm
                    if start < left:
                        if end > right:
                            continue
                        left = end
                        newGaps.append((left, right))
                    else:
                        newGaps.append((left, start))
                        if end < right:
                            newGaps.append((end, right))
            xgaps = newGaps
        return xgaps
    
    def insertAlignBoxes (self, tgs):
        xsegms = []
        selected = []
        half = (self.boxSize + self.minSep) / 2 
        boxHalf = self.boxSize / 2
        for tIdx, tg in tgs.iterrows():
            left = tg.xarcs - half
            right = tg.xarcs + half
            xsegms = self.mergeSegments (xsegms, left, right)
            self.targets.at[tIdx, 'length1'] = boxHalf
            self.targets.at[tIdx, 'length2'] = boxHalf
            selected.append(tIdx)
        return selected, xsegms
                
    def performSelection (self):
        """
        This is the main method.
        
        Performs the selection of the targetS.
        Returns a list of indices of the selected targets.
        """
        def _select (tgs, minSlitLength, margin): 
            selIdx = []        
            for tIdx, tg in tgs.iterrows():
                xpos = tg.xarcs
                fits, gIdx = self._canFit(xgaps, xpos, minSlitLength, self.minSep, margin)    
                if fits:
                    gaps, left, right = self._splitGap (xgaps, gIdx, xpos, minSlitLength, self.minSep, margin)
                    self.targets.at[tIdx, 'length1'] = xpos - left
                    self.targets.at[tIdx, 'length2'] = right - xpos
                    selIdx.append(tIdx)
            return selIdx
        
        xgaps = [(self.minX, self.maxX)] # a sorted list of gaps (xa,xb)

        # Insert the alignment boxes
        #selectedSlits = _select(self.targets [self.targets.pcode < -1], self.boxSize, self.boxSize/2)
        selected, xsegms = self.insertAlignBoxes (self.targets[self.targets.pcode < -1])
        xgaps = self.segments2Gaps (xsegms, xgaps, self.minSep)
        #print ("end align", xgaps)
        # Insert the targets       
        selected.extend(_select(self.targets [self.targets.pcode > 0], self.minSlitLength, self.minSep))
        
        return selected
    