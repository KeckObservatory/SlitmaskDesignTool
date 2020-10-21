"""

Mask layouts for DEIMOS and other instruments.

Original coordinates are taken from foc_plane.dat in dsimulator.
Coordinates are flipped in y and shifted by 318, y = 318 - yOld.

Format: (x, y, flag), 
flag: 0: start vertex, 1: next vertex, 2: close polygon

Date: 2018-07-19
Author: Shui Hung Kwok
Initial version
"""
import math

MaskLayouts = {
    "deimos": (
        (502.02000000003864, 125.31800000000004, 0),
        (259.7114999999974, 125.12299999999996, 1),
        (261.7020000000366, -166.0229999999993, 1),
        (424.812000000054, -166.43100000000038, 1),
        (502.3485000000278, -90.1720000000008, 1),
        (502.02000000003864, 125.31800000000004, 2),
        (249.69300000001908, 125.68100000000122, 0),
        (6.221999999996797, 126.51799999999992, 1),
        (6.286500000038586, -109.21600000000086, 1),
        (19.249500000000808, -109.39399999999964, 1),
        (32.39250000002016, -110.3169999999997, 1),
        (46.27500000006535, -112.34900000000022, 1),
        (59.1030000000103, -114.87700000000078, 1),
        (71.6310000000476, -117.80200000000036, 1),
        (80.16000000000076, -120.19499999999965, 1),
        (88.10700000004204, -122.59700000000021, 1),
        (101.35050000006345, -127.10899999999938, 1),
        (110.67900000004443, -130.96500000000066, 1),
        (120.00900000002162, -134.9529999999996, 1),
        (128.13900000001013, -138.94199999999978, 1),
        (137.1945000000153, -143.5270000000006, 1),
        (146.79750000001945, -149.17900000000088, 1),
        (154.88250000001926, -154.55499999999932, 1),
        (162.3899999999935, -159.54899999999927, 1),
        (170.25450000003843, -165.66499999999937, 1),
        (233.36700000000405, -165.0269999999992, 1),
        (233.31900000002292, -167.79700000000054, 1),
        (250.3995000000259, -167.79499999999973, 1),
        (249.69300000001908, 125.68100000000122, 2),
        (-5.6834999999750835, 126.78900000000048, 0),
        (-249.62849999992613, 126.7590000000011, 1),
        (-248.98049999997625, -166.5660000000001, 1),
        (-168.53699999997502, -166.2520000000004, 1),
        (-158.94149999995193, -161.30700000000041, 1),
        (-147.90599999998335, -153.80800000000045, 1),
        (-141.50849999996922, -149.66000000000042, 1),
        (-133.35149999994655, -144.7140000000008, 1),
        (-122.31749999997419, -139.1299999999994, 1),
        (-111.1214999999504, -133.70600000000064, 1),
        (-99.12749999994617, -128.75999999999942, 1),
        (-86.33399999996527, -124.13300000000066, 1),
        (-77.37749999996595, -120.94200000000015, 1),
        (-66.82199999996215, -118.07100000000013, 1),
        (-58.505999999982805, -116.15599999999998, 1),
        (-50.66999999996824, -114.56100000000032, 1),
        (-41.873999999972966, -113.1250000000005, 1),
        (-29.560499999956846, -111.21000000000035, 1),
        (-17.885999999964497, -110.09299999999982, 1),
        (-5.411999999944328, -109.2959999999998, 1),
        (-5.6834999999750835, 126.78900000000048, 2),
        (-258.65550000000326, 125.26000000000046, 0),
        (-496.7774999999733, 126.4400000000002, 1),
        (-497.00849999995285, 119.08700000000039, 1),
        (-491.8754999999692, 118.67000000000125, 1),
        (-493.26299999999605, 83.65499999999848, 1),
        (-500.4674999999679, 83.93499999999872, 1),
        (-501.16799999993873, 31.31999999999895, 1),
        (-493.41449999997167, 31.187999999999683, 1),
        (-493.08899999997493, -1.567000000001073, 1),
        (-501.71100000000024, -1.89600000000123, 1),
        (-499.0604999999391, -20.424000000001108, 1),
        (-491.76449999999363, -14.47000000000127, 1),
        (-472.5344999999436, -33.99399999999968, 1),
        (-479.0654999999788, -41.05100000000075, 1),
        (-352.2104999999499, -166.11800000000034, 1),
        (-258.920999999998, -165.86200000000025, 1),
        (-258.65550000000326, 125.26000000000046, 2),
    ),
    "deimos1": (
        (502.916948123, 142.11429370000002, 0),
        (260.11093895, 143.43265359999998, 1),
        (260.29338155, -148.97285540299998, 1),
        (423.719489045, -150.3997073855, 1),
        (501.88801475599996, -74.300624555, 1),
        (502.916948123, 142.11429370000002, 2),
        (250.07538725, 144.05524075, 0),
        (6.110182399999985, 146.397334, 1),
        (4.727145200000052, -90.347323385, 1),
        (17.714662250000003, -90.605511185, 1),
        (30.877974050000034, -91.61305150999999, 1),
        (44.77538149999998, -93.73894269499999, 1),
        (57.61313825000002, -96.35654370499999, 1),
        (70.14785495000001, -99.37105453999999, 1),
        (78.67893064999998, -101.82674426, 1),
        (86.62678490000002, -104.287916975, 1),
        (99.86854370000003, -108.90075343999999, 1),
        (109.19157860000001, -112.83071824999999, 1),
        (118.51528895000001, -116.89328692999999, 1),
        (126.6366509, -120.949493345, 1),
        (135.6815663, -125.60997866, 1),
        (145.26844145, -131.345443835, 1),
        (153.3360518, -136.79438312, 1),
        (160.82732555, -141.85614142999998, 1),
        (168.6693356, -148.0469313605, 1),
        (231.90919505, -147.796796702, 1),
        (231.84387785, -150.578367821, 1),
        (248.95776635, -150.682295402, 1),
        (250.07538725, 144.05524075, 2),
        (-5.8181105500000285, 146.7424297, 0),
        (-250.26501789999992, 148.19655504999997, 1),
        (-251.39272315, -146.390607446, 1),
        (-170.78933124999998, -146.56220030449998, 1),
        (-161.14488879999993, -141.654216245, 1),
        (-150.04204314999998, -134.19005647999998, 1),
        (-143.60669920000004, -130.06312807999998, 1),
        (-135.40350115000007, -125.1454871, 1),
        (-124.31372604999996, -119.60463091999999, 1),
        (-113.06255395, -114.22548931999998, 1),
        (-101.0147182, -109.33129593499999, 1),
        (-88.16769474999995, -104.7623969, 1),
        (-79.17401875000002, -101.61231139999998, 1),
        (-68.58010689999998, -98.79338007499999, 1),
        (-60.23595310000002, -96.92091654499998, 1),
        (-52.374710499999935, -95.36691702499999, 1),
        (-43.552527699999985, -93.97848214999999, 1),
        (-31.202955399999894, -92.130520865, 1),
        (-19.498520799999994, -91.08012382999999, 1),
        (-6.994981449999955, -90.356035505, 1),
        (-5.8181105500000285, 146.7424297, 2),
        (-259.31974510000003, 146.74567660000002, 0),
        (-497.92632069999985, 149.3602843, 1),
        (-498.20175024999986, 141.97708254999998, 1),
        (-493.06060405, 141.52767129999995, 1),
        (-494.66036589999993, 106.3705936, 1),
        (-501.87801129999997, 106.69476220000001, 1),
        (-502.89438579999995, 53.85799405, 1),
        (-495.12582205000007, 53.679201250000006, 1),
        (-494.9955194499999, 20.781598599999995, 1),
        (-503.63695419999993, 20.50259035000002, 1),
        (-501.0918112000001, 1.8792251499999963, 1),
        (-493.7454984999999, 7.815293050000008, 1),
        (-474.59342184999997, -11.907278149999996, 1),
        (-481.17985330000005, -18.955610750000005, 1),
        (-354.8230663, -145.31894688949998, 1),
        (-261.3485124999999, -145.6235637005, 1),
        (-259.31974510000003, 146.74567660000002, 2),
    ),
    "deimosX": (
        (-498.0, 131.0, 0),
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
        (259.7, 131.0, 2),
    ),
    "deimosOrig": (
        (-498.0, 187.0, 0),  # mask x,y;  NB in arcsec on sky; sense depends on this
        (-498.0, 332.0, 1),
        (-460.0, 385.0, 1),
        (-420.0, 428.0, 1),
        (-360.0, 479.0, 1),
        (-259.7, 479.0, 1),
        (-259.7, 187.0, 1),
        (-498.0, 187.0, 2),
        (-249.3, 187.0, 0),
        (-249.3, 479.0, 1),
        (-5.2, 479.0, 1),
        (-5.2, 187.0, 1),
        (-249.3, 187.0, 2),
        (5.2, 187.0, 0),
        (5.2, 479.0, 1),
        (249.3, 479.0, 1),
        (249.3, 187.0, 1),
        (5.2, 187.0, 2),
        (259.7, 187.0, 0),
        (259.7, 479.0, 1),
        (360.0, 479.0, 1),
        (420.0, 428.0, 1),
        (460.0, 385.0, 1),
        (498.0, 332.0, 1),
        (498.0, 187.0, 1),
        (259.7, 187.0, 2),
    ),
    "lris": ((-100, -100, 0), (100, -100, 1), (100, 100, 1), (-100, 100, 2)),
}

GuiderFOVs = {
    "deimos": (
        (-206.73084339999997, 238.9636564, 0),
        (-205.70227525, 239.52587964999998, 1),
        (4.619843450000076, 241.66648734999995, 1),
        (6.690488750000043, 30.8876104, 1),
        (-203.66232144999998, 28.510867750000017, 1),
        (-206.73084339999997, 238.9636564, 2),
    ),
    "deimosOrig": (
        (-1.0, 94.0, 0),
        (-1.0, 174.0, 1),
        (208.0, 174.0, 1),
        (208.0, 94.0, 1),
        (-1.0, 94.0, 2),
        (-1.0, 174.0, 0),
        (-1.0, 298.4, 1),
        (208.0, 302.7, 1),
        (208.0, 174.0, 1),
        (-1.0, 174.0, 2),
    ),
    "lris": ((-206.73084339999997, 238.9636564, 0)),
}

BadColumns = {
    "deimos": (
        (-19.92899999997598, 116.58400000000091, 0),
        (-11.294999999975978, 116.58400000000091, 1),
        (-11.294999999975978, 124.6780000000009, 1),
        (-19.92899999997598, 124.6780000000009, 1),
        (-19.92899999997598, 116.58400000000091, 2),
        (-184.9604999999947, 117.43900000000087, 0),
        (-178.8044999999947, 117.43900000000087, 1),
        (-178.8044999999947, 123.57100000000088, 1),
        (-184.9604999999947, 123.57100000000088, 1),
        (-184.9604999999947, 117.43900000000087, 2),
        (377.2815000000378, 125.35899999999991, 0),
        (379.09500000006346, -166.46400000000023, 1),
        (377.2815000000378, 125.35899999999991, 2),
        (204.8865000000319, 125.88400000000135, 0),
        (205.5000000000689, -165.37400000000025, 1),
        (204.8865000000319, 125.88400000000135, 2),
        (-107.0819999999685, 126.6550000000004, 0),
        (-106.70249999995463, -132.40100000000047, 1),
        (-107.0819999999685, 126.6550000000004, 2),
        (-376.4294999999379, 125.41500000000028, 0),
        (-377.12999999995986, -142.18200000000022, 1),
        (-376.4294999999379, 125.41500000000028, 2),
        (-346.8074999999317, 125.08900000000054, 0),
        (-347.1494999999379, -166.72599999999954, 1),
        (-346.8074999999317, 125.08900000000054, 2),
        (-213.55199999994738, 126.50300000000101, 0),
        (-213.03449999997497, -166.59300000000064, 1),
        (-213.55199999994738, 126.50300000000101, 2),
        (-264.08999999994194, 124.71100000000047, 0),
        (-264.59399999994844, -109.33500000000045, 1),
        (-264.08999999994194, 124.71100000000047, 2),
    )
}


def shrinkMask(mask, margin=0.5):
    """
    mask is a list of points describing the mask
    t is the size of the margin (the mount to reduce the mask)

    For example: 
        reducedMask = shrinkMask (mask, margin=0.5)
    """

    def normalize(dx, dy):
        h = math.hypot(dx, dy)
        if h > 0:
            return dx / h, dy / h
        else:
            return 0, 0

    def intersect(a1, b1, c1, a2, b2, c2):
        det = a1 * b2 - a2 * b1
        x = (c1 * b2 - c2 * b1) / det
        y = (a1 * c2 - a2 * c1) / det
        return x, y

    def calc(x0, y0, x1, y1, x2, y2, t):
        ux1, uy1 = normalize(x1 - x0, y1 - y0)
        ux2, uy2 = normalize(x2 - x1, y2 - y1)
        c1 = (x1 - uy1 * t) * uy1 - (y1 + ux1 * t) * ux1
        c2 = (x1 - uy2 * t) * uy2 - (y1 + ux2 * t) * ux2

        return intersect(uy1, -ux1, c1, uy2, -ux2, c2)

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
            # print (f"({x0}, {y0})  ({x1}, {y1})  ({x2}, {y2}), flg={flag})")
            x, y = calc(x0, y0, x1, y1, x2, y2, margin)
            out.append((x, y, flag1))
            if flag1 == 0:
                ox0, oy0 = x, y
            flag1 = 1
        if state == 3:
            # print (f"({x0}, {y0})  ({x1}, {y1})  ({x2}, {y2}), flg={flag})")
            # print (f"({x1}, {y1})  ({x2}, {y2})  ({xStart1}, {yStart1}), flg={flag})")

            x, y = calc(x0, y0, x1, y1, x2, y2, margin)
            out.append((x, y, 1))

            x, y = calc(x1, y1, x2, y2, xStart1, yStart1, margin)
            out.append((x, y, 1))
            out.append((ox0, oy0, 2))
            flag1 = 0
            # print()
            state = 0
    return out
