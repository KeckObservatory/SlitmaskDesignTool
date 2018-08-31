"""

Mask layouts for DEIMOS and other instruments.

Original coordinates are taken from foc_plane.dat in dsimulator.
Coordinates are flipped in y and shifted by 318, y = 318 - yOld.

Date: 2018-07-19
Author: Shui Hung Kwok
Initial version
"""
import math

MaskLayouts ={
    'deimos' :
        ((-498.0, 131.0, 0),
        (-498.0, -14.0, 1),
        (-460.0, -67.0, 1),
        (-420.0, -110.0, 1),
        (-360.0, -161.0, 1),
        (-259.7, -161.0, 1),
        (-259.7, 131.0, 1),
        (-498.0, 131.0, 2),
        (-249.3, 131.0, 0),
        (-249.3, -161.0, 1),
        (-164.0, -161.0, 1),
        (-132.0, -141.0, 1),
        (-98.0, -125.0, 1),
        (-51.0, -112.0, 1),
        (-5.2, -109.0, 1),
        (-5.2, 131.0, 1),
        (-249.3, 131.0, 2),
        (5.2, 131.0, 0),
        (5.2, -109.0, 1),
        (52.0, -111.0, 1),
        (100.0, -126.0, 1),
        (134.0, -142.0, 1),
        (164.0, -161.0, 1),
        (249.3, -161.0, 1),
        (249.3, 131.0, 1),
        (5.2, 131.0, 2),
        (259.7, 131.0, 0),
        (259.7, -161.0, 1),
        (360.0, -161.0, 1),
        (420.0, -110.0, 1),
        (460.0, -67.0, 1),
        (498.0, -14.0, 1),
        (498.0, 131.0, 1),
        (259.7, 131.0, 2)
        ),
    'lris':
        ((-100, -100, 0),
         (100, -100, 1),
         (100, 100, 1), 
         (-100, 100, 2))
    }

def shrinkMask (mask, margin=0.5):
    """
    mask is a list of points describing the mask
    t is the size of the margin (the mount to reduce the mask)
    
    For example: 
        reducedMask = shrinkMask (mask, margin=0.5)
    """
    def normalize (dx, dy):
        h = math.hypot(dx, dy)
        if h > 0:
            return dx/h, dy/h
        else:
            return 0, 0
    def intersect (a1, b1, c1, a2, b2, c2):
        det = a1 * b2 - a2 * b1
        x = (c1 * b2 - c2 * b1) / det
        y = (a1 * c2 - a2 * c1) / det
        return x, y
    def calc (x0, y0, x1, y1, x2, y2, t):
        ux1, uy1 = normalize (x1 - x0, y1 - y0)
        ux2, uy2 = normalize (x2 - x1, y2 - y1)
        c1 = (x1-uy1*t) * uy1 - (y1+ux1*t) * ux1
        c2 = (x1-uy2*t) * uy2 - (y1+ux2*t) * ux2
        
        return intersect (uy1, -ux1, c1, uy2, -ux2, c2)
        
    """
    Shrink mask from all sides
    """
    state = 0
    flag1 = 0
    xStart, yStart, flag = mask[0]
    out = []
    for x, y, flag in mask:
        if flag == 0:
            xStart, yStart = x, y
            x0, y0 = x, y
            x1, y1 = x, y
            x2, y2 = x, y
        elif flag == 1:
            if state == 0:
                xStart1, yStart1 = x, y
            if state < 2:                
                state += 1
            x0, y0 = x1, y1
            x1, y1 = x2, y2
            x2, y2 = x, y
        elif flag == 2:
            state = 3
            x0, y0 = x1, y1
            x1, y1 = x2, y2
            x2, y2 = xStart, yStart
        if state == 2:
            #print (f"({x0}, {y0})  ({x1}, {y1})  ({x2}, {y2}), flg={flag})")
            x, y = calc (x0, y0, x1, y1, x2, y2, margin)
            out.append ((x, y, flag1))
            if flag1 == 0:
                ox0, oy0 = x, y
            flag1 = 1
        if state == 3:
            #print (f"({x0}, {y0})  ({x1}, {y1})  ({x2}, {y2}), flg={flag})") 
            #print (f"({x1}, {y1})  ({x2}, {y2})  ({xStart1}, {yStart1}), flg={flag})") 
            
            x, y = calc (x0, y0, x1, y1, x2, y2, margin)
            out.append((x, y, 1))
            
            x, y = calc (x1, y1, x2, y2, xStart1, yStart1, margin)
            out.append((x, y, 1))
            out.append((ox0, oy0, 2))
            flag1 = 0
            #print()
            state = 0
    return out
    
