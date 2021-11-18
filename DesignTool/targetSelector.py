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
        self.targets = tgs.reset_index(drop=True)

    def restoreIndex(self):
        self.targets.sort_values(by="oldIndex", ignore_index=True, inplace=True)
        self.targets = self.targets.reset_index(drop=True)

    def _canFit(self, xgaps, xpos, slitLength, minSep):
        """
        Tries to fit the new segment in a gap
        Returns (canFit, index in xgaps)
        """
        halfSep = minSep
        # print ('xgaps', xgaps)
        for idx, (gapStart, gapEnd) in enumerate(xgaps):
            # print ("xpos", xpos, "gap", gapStart, gapEnd)
            if xpos < gapStart + halfSep:
                """
                xpos is left of gap, 
                It is also left of all remaining gaps, so return false
                """
                return False, idx
            if xpos >= gapEnd - halfSep:
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

        left = xpos - halfLength - halfSep
        right = xpos + halfLength + halfSep

        if left < gapStart:
            """ xpos is closer to the left side
                so adjust left 
            """
            left = gapStart
            right = left + slitLength + minSep
            xgaps[gIdx] = (right, gapEnd)
        elif right > gapEnd:
            """ xpos is closer to the right side, 
                so adjust right
            """
            right = gapEnd
            left = right - slitLength - minSep
            xgaps[gIdx] = (gapStart, left)
        else:
            """ slit can fit in the gap, split gap into two
            """
            # gap1 = gapStart, left
            # gap2 = right, gapEnd
            xgaps[gIdx] = (gapStart, left)
            xgaps.insert(gIdx + 1, (right, gapEnd))

        return xgaps, left + halfSep, right - halfSep

    def insertAlignBoxes(self, aboxes, minx, maxx):
        """
        First step in the target selection sequence.

        aboxes: alignment boxes, pcode < -1
        Returns a list of disjunct segments corresponding to the alignment boxes
        """
        sortedBoxes = aboxes.sort_values(by="xarcs")
        lastx = -1e10
        halfSep = self.minSep / 2.0
        xsegms = []
        for aIdx, seg in sortedBoxes.iterrows():
            xpos = seg.xarcs
            x0, x1 = xpos - seg.length1 - halfSep, xpos + seg.length2 + halfSep
            if x1 < minx:
                continue
            if x0 > maxx:
                break
            if x0 > lastx:
                # no overlap
                lastx = x1
                xsegms.append((x0, x1))
            else:
                # merge
                lastSeg = xsegms[-1]
                xsegms[-1] = (lastSeg[0], x1)
            self.targets.at[aIdx, "selected"] = 1
        return xsegms

    def segments2Gaps(self, xsegms, minx, maxx):
        """
        Turns segments into gaps.
        Gaps already include min separation.
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
            if x1 < currX:
                # cannot happend
                # Segments are sorted, x0, x1 should be greater the currX always.
                continue
            if x0 <= currX <= x1:
                # overlapped segments
                currX = x1
                continue
            if currX < x0:
                # Segments starts at x0
                # There is a gap from currX, to x0.
                # The next gap will start at x1
                xgaps.append((currX, x0))
                currX = x1

        if currX < maxx:
            xgaps.append((currX, maxx))
        return xgaps

    def _printGaps(self, gaps):
        for l, r in gaps:
            print(f"({l:.1f} {r:.1f}, d={r-l:.2f})")
        print()

    def _selectTargets(self, xgaps, tgs, minSlitLength, minSep):
        """
        Selects targets that can fit in a gap.
        
        tgs: list of targets, pcode > 0
        """
        halfSep = minSep / 2
        for tIdx, tg in tgs.iterrows():
            xpos = tg.xarcs
            fits, gIdx = self._canFit(xgaps, xpos, minSlitLength, minSep)
            if fits:
                xgaps, left, right = self._splitGap(xgaps, gIdx, xpos, minSlitLength, minSep)
                # print ("gaps")
                # self.printGaps(xgaps)
                # print (f'tidx={tIdx}, gIdx={gIdx}, left={left:.1f}, right={right:.1f}')
                self.targets.at[tIdx, "length1"] = xpos - left
                self.targets.at[tIdx, "length2"] = right - xpos
                self.targets.at[tIdx, "selected"] = 1
        return xgaps

    def _extendSlits(self, xgaps, tgs, minSep):
        """
        Extends the slits beyond the maximum length
        """

        def equals(x, y, eps=1e-4):
            d = abs(x - y)
            return d < eps

        def checkIsSegm(pairs, idx, side, ref):
            """
            Returns True if the current segm is a segment, False if it is a gap
            If idx out of range, returns False
            if the end point is not equal to ref, returns False
            End point can be left side or right side.
            """
            # print ("check isSegm idx", idx)
            if idx < 0 or idx >= len(pairs):
                return False

            start, end, i, isGap = pairs[idx]
            if isGap == 1:
                return False

            if side == "left":
                # segm is left, gap right
                # print ("left", end, ref)
                return equals(end, ref)

            if side == "right":
                # segm is right, gap left
                # print ("right", start, ref)
                return equals(start, ref)

            return False

        def updateLengths(length1, length2, idx, isGap):
            """
            Updates the segment at index idx with the new lengths
            Ignores segment is no a gap
            """
            if isGap == 0:
                mid = tgs.at[idx, "xarcs"]
                # print(f"set length {idx}, {mid:.2f}, {length1:.2f}, {length2:.2f}, {tgs.at[idx, 'objectId']}")
                self.targets.at[idx, "length1"] = mid - length1
                self.targets.at[idx, "length2"] = length2 - mid
            return length1, length2, idx, isGap

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

        def split2Left(pairs, idx1, halfSep):
            """
            Left side is a segment.
            Left segment takes all the gap.
            """
            idx0, idx2 = idx1 - 1, idx1 + 1
            leftSegm = pairs[idx0]
            gap = pairs[idx1]
            ref = gap[1]
            pairs[idx0] = updateLengths(leftSegm[0], ref - halfSep, leftSegm[2], leftSegm[3])
            pairs[idx1] = updateLengths(ref, ref, gap[2], gap[3])

        def split2Right(pairs, idx1, halfSep):
            """
            Right side is a segment
            Right segment takes all the gap.
            """
            idx0, idx2 = idx1 - 1, idx1 + 1
            rightSegm = pairs[idx2]
            gap = pairs[idx1]
            ref = gap[0]
            pairs[idx2] = updateLengths(ref - halfSep, *rightSegm[1:])
            pairs[idx1] = updateLengths(ref, ref, gap[2], gap[3])

        def genPairs(gaps, tgs):
            """
            Generates a list of tuples (x0, x1, idx, isGap),
            where x0, x1 are the start and end of a segment or gap, isGap = 1 if this is gap.
            idx is the index in the list
            """
            allPairs = []
            for i, g in enumerate(gaps):
                allPairs.append((g[0], g[1], None, 1))

            halfSep = minSep / 2
            for tIdx, tg in tgs.iterrows():
                x = tg.xarcs
                x0, x1 = x - tg.length1 - halfSep, x + tg.length2 + halfSep
                allPairs.append((x0, x1, tIdx, 0))
                # print(f"{x0:.2f}, {x1:.2f}, {tIdx}, {tg.oldIndex} {tg.pcode}")

            return sorted(allPairs, key=lambda x: x[0])

        def splitGaps(allPairs):
            """
            For all the gaps, split the gap to either left, right or both segments
            """
            halfSep = minSep / 2
            for idx, pair in enumerate(allPairs):
                start, end, idx0, isGap = pair
                if isGap != 1:
                    continue

                if (end - start) < minSep:
                    continue

                # print ("pair ", idx, pair)

                # Is left pair a segmenet?
                leftIsSegm = checkIsSegm(allPairs, idx - 1, "left", start)
                # Is right pair a segment?
                rightIsSegm = checkIsSegm(allPairs, idx + 1, "right", end)

                if leftIsSegm:
                    if rightIsSegm:
                        # split gap
                        # print ("split3")
                        split3(allPairs, idx, halfSep)
                    else:
                        # left takes all
                        # print ("split left")
                        split2Left(allPairs, idx, halfSep)
                else:
                    if rightIsSegm:
                        # right takes all
                        # print ("split right")
                        split2Right(allPairs, idx, halfSep)
            # end of splitGaps

        allPairs = genPairs(xgaps, tgs)
        splitGaps(allPairs)
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
        xsegms = self.insertAlignBoxes(inAlignBoxes, self.minX, self.maxX)

        # Turns the segments into gaps
        xgaps = self.segments2Gaps(xsegms, self.minX, self.maxX)

        # Inserts the targets
        inTargets = self.targets[self.targets.inMask == 1]
        inTargets = inTargets[inTargets.pcode > 0]
        self.xgaps = self._selectTargets(xgaps, inTargets, self.minSlitLength, self.minSep)

        if extendSlits:
            inTargets = self.targets[self.targets.inMask == 1]
            inTargets = inTargets[inTargets.pcode > 0]
            inTargets = inTargets[inTargets.selected == 1]
            self.xgaps = self._extendSlits(self.xgaps, inTargets, self.minSep)

        self.restoreIndex()
        return self.targets

