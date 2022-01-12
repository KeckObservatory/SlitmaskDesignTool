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

import numpy as np

class TargetSelector:
    """
    A tool to select slits such that they don't overlap. 
    """

    def __init__(self, targetList, minX, maxX, minSlitLength, minSep):
        """
        targetList is a pandas data frame
        minSep is minimal separation between slits in arcsec.
        """
        self.targets = targetList.copy()

        self.targets["selected"] = 0
        self._sortTargets()
        self.minX = minX
        self.maxX = maxX
        self.minSlitLength = minSlitLength
        self.minSep = minSep
        self.xgaps = []

    def _sortTargets(self):
        """
        Sorts targets by x-coordinates
        """
        tgs = self.targets
        tgs["oldIndex"] = range(0, tgs.shape[0])
        tgs.sort_values(by=["pcode", "xarcs"], ascending=(False, True), inplace=True)
        #self.targets = tgs.reset_index(drop=True)
        self.targets = tgs

    def restoreIndex(self):
        self.targets.sort_values(by="oldIndex", ignore_index=True, inplace=True)
        #self.targets = self.targets.reset_index(drop=True)

    def _canFit(self, xgaps, xpos, slitLength, minSep):
        """
        Tries to fit the new segment in a gap
        Returns (canFit, index in xgaps)
        """
        # print ('xgaps', xgaps)
        for idx, (gapStart, gapEnd) in enumerate(xgaps):
            # print ("xpos", xpos, "gap", gapStart, gapEnd)
            if xpos < gapStart + minSep:
                """
                xpos is left of gap, 
                It is also left of all remaining gaps, so return false
                """
                return False, idx
            if xpos >= gapEnd - minSep:
                """
                xpos is on the right side, continue
                """
                continue
            """ xpos is in the gap, checks for margin
                returns True if inside            
                If xpos is in this gap, it cannot be in another gap, so OK to return 
            """
            gapLength = gapEnd - gapStart - minSep
            if gapLength < slitLength:
                # Gap too short
                return False, idx
            return True, idx
        return False, -1

    def _splitGap(self, xgaps, gIdx, xpos, slitLength, minSep):
        """
        Splits the gap at xgaps[gIdx] into two
        """
        gapStart, gapEnd = xgaps[gIdx]
        # gap will be split into two gaps

        halfSep = minSep / 2
        halfLength = slitLength / 2.0

        left = xpos - halfLength
        right = xpos + halfLength

        if left < gapStart:
            """ xpos is closer to the left side
                so adjust left 
            """
            left = gapStart
            right = left + slitLength
            xgaps[gIdx] = (right + minSep, gapEnd)
            #print (f"left {left:.2f}, {right:.2f}")
        elif right > gapEnd:
            """ xpos is closer to the right side, 
                so adjust right
            """
            right = gapEnd
            left = right - slitLength
            xgaps[gIdx] = (gapStart, left- minSep)
            #print (f"righ {left:.2f}, {right:.2f}")
        else:
            """ slit can fit in the gap, split gap into two
            """
            # gap1 = gapStart, left
            # gap2 = right, gapEnd
            leftEnd = left - minSep
            rightStart = right + minSep
            if leftEnd < gapStart:
                leftEnd = gapStart
            xgaps[gIdx] = (gapStart, leftEnd)
            if rightStart > gapEnd:
                rightStart = gapEnd
            xgaps.insert(gIdx + 1, (rightStart, gapEnd))            
            #print (f"both {gapStart:.2f}, {leftEnd:.2f}, {rightStart:.2f}, {gapEnd:.2f}")
        return xgaps, left, right

    def insertPairs(self, targets, minx, maxx):
        """
        First step in the target selection sequence.

        targets: alignment boxes or targets
        Returns a list of disjunct segments corresponding to the alignment boxes
        """
        sortedBoxes = targets.sort_values(by="xarcs")
        lastx = -1e10
        xsegms = []
        for aIdx, seg in sortedBoxes.iterrows():
            xpos = seg.xarcs
            x0, x1 = xpos - seg.length1, xpos + seg.length2
            if x1 < minx:
                continue
            if x0 > maxx:
                break
            if x0 > lastx:
                # no overlap
                xsegms.append((x0, x1))
            else:
                # merge
                lastSeg = xsegms[-1]
                xsegms[-1] = (lastSeg[0], x1)
            lastx = x1
            self.targets.at[aIdx, "selected"] = 1
        return xsegms

    def segments2Gaps(self, xsegms, minx, maxx, minSep):
        """
        Turns segments into gaps.
        Add separation to gaps
        Returns a list of gaps.
        
        A gap is a pair (left, right) of space that is not occupied.        
        """
        xgaps = []
        currX = minx
        for seg in xsegms:
            if currX > maxx:
                # beyond maxx, done
                break
            x0, x1 = seg
            if currX > x1:
                # seg is left of currX
                continue
            if x0 <= currX <= x1:
                # overlapped segments
                currX = x1
                continue
            if currX < x0:
                # Segments starts at x0
                # There is a gap from currX, to x0.
                # The next gap will start at x1
                left = currX + minSep
                right = x0 - minSep
                if left < right:
                    xgaps.append((left, right))                
                currX = x1
        if currX < maxx:
            xgaps.append((currX, maxx))
        return xgaps

    def _selectTargets(self, xgaps, tgs, minSlitLength, minSep):
        """
        Selects targets that can fit in a gap.
        
        tgs: list of targets, pcode > 0
        """            
        for tIdx, tg in tgs.iterrows():
            xpos = tg.xarcs
            fits, gIdx = self._canFit(xgaps, xpos, minSlitLength, minSep)
            if fits:
                xgaps, left, right = self._splitGap(xgaps, gIdx, xpos, minSlitLength, minSep)
                self.targets.at[tIdx, "length1"] = xpos - left
                self.targets.at[tIdx, "length2"] = right - xpos
                self.targets.at[tIdx, "selected"] = 1
            
        return xgaps

    def _extendSlits(self, xgaps, tgs, minSep):
        """
        Extends the slits beyond the maximum length
        """

        def updateLengths(start, end, idx, isGap):
            """
            Updates the segment at index idx with the new lengths
            Ignores segment is no a gap
            """
            if isGap == 0:
                mid = tgs.at[idx, "xarcs"]
                self.targets.at[idx, "length1"] = mid - start
                self.targets.at[idx, "length2"] = end - mid
                #print (f"update {idx=}, {mid=:.1f}, {start:.1f}, {end:.1f}")
            return start, end, idx, isGap

        def split3(pairs, idx1, halfSep):
            """
            Both left and right sides are segments.
            Splits the current gap, left side goes to the left segment
            and right side goes to the right segment.
            """
            idx0, idx2 = idx1 - 1, idx1 + 1
            leftSegm = pairs[idx0]
            gap = pairs[idx1]
            rightSegm = pairs[idx2]
            midX = (gap[0] + gap[1]) / 2

            pairs[idx0] = updateLengths(leftSegm[0], midX - halfSep, leftSegm[2], leftSegm[3])
            pairs[idx1] = midX, midX, gap[2], gap[3]
            pairs[idx2] = updateLengths(midX + halfSep, rightSegm[1], rightSegm[2], rightSegm[3])

        def split2Left(pairs, idx1):
            """
            Left side is a segment.
            Left segment takes all the gap.
            """
            idx0, idx2 = idx1 - 1, idx1 + 1
            leftSegm = pairs[idx0]
            gap = pairs[idx1]
            ref = gap[1]
            pairs[idx0] = updateLengths(leftSegm[0], ref, leftSegm[2], leftSegm[3])
            pairs[idx1] = ref, ref, gap[2], gap[3]

        def split2Right(pairs, idx1):
            """
            Right side is a segment
            Right segment takes all the gap.
            """
            idx0, idx2 = idx1 - 1, idx1 + 1
            rightSegm = pairs[idx2]
            gap = pairs[idx1]
            ref = gap[0]
            pairs[idx1] = ref, ref, gap[2], gap[3]            
            pairs[idx2] = updateLengths(ref, *rightSegm[1:])

        def genPairs(gaps, tgs):
            """
            Generates a list of tuples (x0, x1, idx, isGap),
            where x0, x1 are the start and end of a segment or gap, isGap = 1 if this is gap.
            idx is the index in the list
            """
            allPairs = []
            for i, g in enumerate(gaps):
                allPairs.append((g[0], g[1], None, 1))

            for tIdx, tg in tgs.iterrows():
                x = tg.xarcs
                x0, x1 = x - tg.length1, x + tg.length2
                isSegm = 0
                if tg.pcode == -2:
                    isSegm = -2
                allPairs.append((x0, x1, tIdx, isSegm))
                #print(f"gen gap {x0:.2f}, {x1:.2f}, {tIdx=}, {tg.oldIndex=} {tg.pcode}, {tg.orgIndex=}, {tg.selected=}")

            return sorted(allPairs, key=lambda x: x[0])

        def splitGaps(allPairs):
            """
            For all the gaps, split the gap to either left, right or both segments
            """
            halfSep = minSep / 2
            leftPair, currPair = allPairs[:2]
            if leftPair[3] == 1 and currPair[3] == 0:
                split2Right(allPairs, 0)
            leftPair = currPair = rightPair = None
            for idx, pair in enumerate(allPairs):                
                leftPair = currPair
                currPair = rightPair
                rightPair = pair

                if idx < 2: continue

                start, end, idx0, isGap = currPair
                if isGap <= 0:
                    continue

                if (end - start) < minSep:
                    continue

                # print ("pair ", idx, pair)

                # Is left pair a segmenet?
                leftIsSegm = leftPair[3] == 0
                # Is right pair a segment?
                rightIsSegm = rightPair[3] == 0

                if leftIsSegm:
                    if rightIsSegm:
                        # split gap
                        #print (idx, "split3", start, end)
                        split3(allPairs, idx-1, halfSep)
                    else:
                        # left takes all
                        #print (idx, "split left", start, end)
                        split2Left(allPairs, idx-1)
                else:
                    if rightIsSegm:
                        # right takes all
                        #print (idx, "split right", start, end)
                        split2Right(allPairs, idx-1)
            # end of splitGaps

        allPairs = genPairs(xgaps, tgs)
        #self.allPairs1 = allPairs.copy()
        splitGaps(allPairs)
        #self.allPairs2 = allPairs.copy()
        # print (self.targets[self.targets.pcode >0][['objectId','length1', 'length2']])
        return [x for x in allPairs if x[3] == 1]

    def performSelection(self, extendSlits=False):
        """
        This is the main method.
        
        Performs the selection of the targetS.
        Returns a list of indices of the selected targets.
        """

        # Inserts the alignment boxes
        inAlignBoxes = self.targets[self.targets.inMask == 1]
        inAlignBoxes = inAlignBoxes[inAlignBoxes.pcode < 0]
        xsegms = self.insertPairs(inAlignBoxes, self.minX, self.maxX)
        self.xsegms = xsegms.copy()
        # Turns the segments into gaps
        xgaps = self.segments2Gaps(xsegms, self.minX, self.maxX, self.minSep)
        self.xgaps0 = xgaps.copy()
        # Inserts the targets
        inTargets = self.targets[self.targets.inMask == 1]
        inTargets = inTargets[inTargets.pcode > 0]

        self.xgaps = self._selectTargets(xgaps, inTargets, self.minSlitLength, self.minSep)
        self.xgaps1 = self.xgaps.copy()
        self.allPairs1 = []
        if extendSlits:
            inTargets = self.targets[self.targets.selected == 1]
            xsegms = self.insertPairs (inTargets, self.minX, self.maxX)
            xgaps = self.segments2Gaps (xsegms, self.minX, self.maxX, self.minSep)
            self.xgaps = self._extendSlits(self.xgaps, inTargets, self.minSep)

        self.restoreIndex()
        return self.targets

