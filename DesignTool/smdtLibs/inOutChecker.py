"""
In/Out checker, python version

Example:

chk = InOutChecker (mask)
pnt = x, y
if chk.checkPoint (x, y):
    print ("inside")

Date: 2018-08-03
Author: Shui Hung Kwok

"""
import math


class InOutChecker:
    def __init__(self, mask):
        """
        mask defines a set of polygons specified as a list of points. 
        A point is a tuple (x, y, flag), 
        where flag is 0 (move), 1 (goto), 2 (back to first point).
        """
        self.mask = mask
        self.ymin, self.ymax, self.edges = self._buildEdges(mask)

    def _buildEdges(self, mask):
        """
        Builds a list of segments from ymin to ymax.
        For each y, a list of segments define what is inside.
        If a point is within a segment, then it is inside.        
        """
        x0, y0 = 0, 0
        x1, y1, x2, y2 = 0, 0, 0, 0
        ys = [int(t[1]) for t in mask]
        ymin, ymax = min(ys), max(ys)
        edges = {}
        for x, y, flag in mask:
            if flag == 0:
                x0, y0 = x, y
                x1, y1 = x, y
                x2, y2 = x, y
                continue
            elif flag == 1:
                x1, y1 = x2, y2
                x2, y2 = x, y
            elif flag == 2:
                x1, y1 = x2, y2
                x2, y2 = x0, y0

            if y1 > y2:
                xx1, yy1, xx2, yy2 = x2, y2, x1, y1
            else:
                xx1, yy1, xx2, yy2 = x1, y1, x2, y2

            y1i, y2i = int(yy1), int(yy2)
            if y1i == y2i:
                continue
            # print (y1i, y2i)
            m = (xx2 - xx1) / (yy2 - yy1)
            b = -m * yy1 + xx1
            for yidx in range(y1i, y2i):
                xpos = m * yidx + b
                try:
                    edges[yidx].append(xpos)
                except:
                    edges[yidx] = [xpos]

        for y in range(ymin, ymax):
            try:
                edges[y].sort()
            except Exception as e:
                print("Exception in sort ", y, e)
                pass
        return ymin, ymax, edges

    def checkPoint(self, x, y):
        """
        Checks if the given point (x,y) is inside the mask
        First, finds the segments at the y position, where int(y) is used.
        Then, the point is inside the mask if x in inside one of the segments. 
        """
        try:
            yi = math.floor(y)
            if yi <= self.ymin or self.ymax <= yi:
                return False
            row = self.edges[yi]

            for idx in range(0, len(row), 2):
                x0, x1 = row[idx : idx + 2]
                if x0 < x < x1:
                    return True
        except Exception as e:
            print("Check point exception", e)
            pass
        return False
