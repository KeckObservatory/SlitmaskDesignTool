"""
TargetSelector.py

This moddule provides tools to select targets and create slits such the meet given criteria
such as not overlapping, minimum separation, etc.

Date: 2018-08-01


Notes:

targets is a list of all targets that are inside the mask.

Main entry point is performSelection

After selecting the targets, the flag 'selected' should be set to 1 for those targets that are selected.
If slit lengths, or angles or widths are changed, these are also updated in the data structure
and returned in getSelected.

"""


class TargetSelector:
    def __init__(self, targetList, minX, maxX, minSlitLength, minSep, boxSize):
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

    def _sortTargets(self):
        tgs = self.targets
        tgs["xsort"] = tgs.xarcs - tgs.length1
        tgs.sort_values(by=["selected", "pcode", "xsort"], ascending=(False, False, True), inplace=True)
        self.targets = tgs.reset_index(drop=True)

    def _canFit(self, xgaps, xpos, slitLength, minSep, margin):
        """
        Tries to fit the new segment in a gap
        """
        minMargin = minSep + margin
        # print ('xgaps', xgaps)
        for idx, (gapStart, gapEnd) in enumerate(xgaps):
            # print ("xpos", xpos, "gap", gapStart, gapEnd)
            if xpos < gapStart:
                """
                xpos is left of gap, 
                It is also left of all remaining gaps, so return false
                """
                return False, idx
            if xpos > gapEnd:
                """
                xpos is on the right side, continue
                """
                continue
            """ xpos is in the gap, checks for margin
                returns True if inside
            """
            if (gapStart + minMargin) < xpos < (gapEnd - minMargin):
                """
                If xpos is in this gap, it cannot be in another gap, so OK to return 
                """
                gapLength = gapEnd - gapStart - minSep
                if gapLength < slitLength:
                    """ Gap too short """
                    return False, idx
                return True, idx
        return False, -1

    def _splitGap(self, xgaps, gIdx, xpos, slitLength, minSep, margin):
        """
        Splits the gap at xgaps[gIdx] into two
        """
        gapStart, gapEnd = xgaps[gIdx]
        # gap will be split into two gaps

        minMargin = minSep + margin
        halfLength = slitLength / 2.0

        if xpos - halfLength < gapStart + minSep:
            """ xpos is closer to the left side
                so adjust left 
            """
            left = gapStart + minSep
            right = left + slitLength
        elif gapEnd - minSep < xpos + halfLength:
            """ xpos is closer to the right side, 
                so adjust right
            """
            right = gapEnd - minSep
            left = right - slitLength
        else:
            """ slit can fit in the gap
            """
            left = xpos - halfLength
            right = xpos + halfLength

        # gap1 = gapStart, left
        # gap2 = right, gapEnd
        xgaps[gIdx] = (gapStart, left)
        xgaps.insert(gIdx + 1, (right, gapEnd))
        return xgaps, left, right

    def mergeSegments(self, xsegms, left, right):
        if len(xsegms) == 0:
            return [(left, right)]
        else:
            xsegms.append((left, right))
        s0 = [(a[0], a) for a in xsegms]
        s0.sort()
        xsegms = [t for s, t in s0]
        left, right = xsegms[0]
        newSegms = []
        for start, end in xsegms[1:]:
            # print ('newseg', newSegms)
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

    def segments2Gaps(self, xsegms, xgaps, margin):
        """
        Turns segments into gaps.
        Returns a list of gaps.
        
        A gap is a pair (left, right) of space that is not occupied.
        
        """
        for segmLeft, segmRight in xsegms:
            newGaps = []
            # print ('segm', segmLeft, segmRight, xgaps)
            """ Checks if a segment is in a gap, if so, split the gap in two. """
            for gapLeft, gapRight in xgaps:
                if gapRight < segmLeft or segmRight < gapLeft:
                    """Segm is not in gap, keep this gap """
                    newGaps.append((gapLeft, gapRight))
                else:
                    """ Segm and gap intersect, need to merge """
                    if segmLeft < gapLeft:
                        if segmRight > gapRight:
                            """ segm is bigger than the gap.
                                so, don't keep the gap
                            """
                            continue
                        """ segm is on the left side of gap, segmRight must be in the gap
                            so, gap is shortened on the left side
                        """
                        gapLeft = segmRight
                        newGaps.append((gapLeft, gapRight))
                    else:
                        if segmRight < gapRight:
                            """ segm is entirely inside the gap
                                so, split the gap in two
                            """
                            newGaps.append((gapLeft, segmLeft))
                            newGaps.append((segmRight, gapRight))
                            continue

                        """ segm is on the right side of the gap, segmLeft is in the gap
                            so, gap is shortened on the right side 
                        """
                        newGaps.append((gapLeft, segmLeft))

            xgaps = newGaps
        return xgaps

    def insertAlignBoxes(self, tgs):
        """
        Inserts by merging the segments into xsesegmRight
        Returns a list of selected targets and the segments they occupy: (selected, xsegms) 
        
        tgs: alignment boxes, pcode < -1
        A segment is a pair (left,right), where left and right are the limits of the alignment box.
        """
        xsegms = []
        selected = []
        half = (self.boxSize + self.minSep) / 2
        boxHalf = self.boxSize / 2
        for tIdx, tg in tgs.iterrows():
            left = tg.xarcs - half
            right = tg.xarcs + half
            xsegms = self.mergeSegments(xsegms, left, right)
            self.targets.at[tIdx, "length1"] = boxHalf
            self.targets.at[tIdx, "length2"] = boxHalf
            selected.append(tIdx)
        return selected, xsegms

    def _printGaps(self, gaps):
        for l, r in gaps:
            print(f"({l:.1f} {r:.1f})", end=",")
        print()

    def _selectTargets(self, xgaps, tgs, minSlitLength, margin):
        """
        Selects targets that can fit in a gap.
        Returns a list of indices of selected targets
        
        tgs: list of targets, pcode > 0
        """
        selIdx = []

        # print ("gaps")
        # self.printGaps(xgaps)
        for tIdx, tg in tgs.iterrows():
            xpos = tg.xarcs
            fits, gIdx = self._canFit(xgaps, xpos, minSlitLength, self.minSep, margin)
            if fits:
                xgaps, left, right = self._splitGap(xgaps, gIdx, xpos, minSlitLength, self.minSep, margin)
                # print ("gaps")
                # self.printGaps(xgaps)
                # print (f'tidx={tIdx}, gIdx={gIdx}, left={left:.1f}, right={right:.1f}')
                self.targets.at[tIdx, "length1"] = xpos - left
                self.targets.at[tIdx, "length2"] = right - xpos
                selIdx.append(tIdx)
        return selIdx

    def performSelection(self):
        """
        This is the main method.
        
        Performs the selection of the targetS.
        Returns a list of indices of the selected targets.
        """

        xgaps = [(self.minX, self.maxX)]  # a sorted list of gaps (xa,xb)

        """ Inserts the alignment boxes"""
        selected, xsegms = self.insertAlignBoxes(self.targets[self.targets.pcode < -1])

        """ Turns the segments into gaps """
        xgaps = self.segments2Gaps(xsegms, xgaps, self.minSep)

        """ Inserts the targets """
        selTargets = self._selectTargets(xgaps, self.targets[self.targets.pcode > 0], self.minSlitLength, self.minSep)

        """ Merges with selected aligment boxes"""
        selected.extend(selTargets)

        return selected
