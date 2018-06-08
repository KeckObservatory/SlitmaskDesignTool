
/*
 * Takes a set of points (corners of the CCDs) and returns
 * a set of the min and max x and y points.
 *
 * return minMax: set of min and max points for quick
 *      exclusion of points outside of the CCD perimeter
 */
function minMaxPts(ccdPts){
    var minX = pow(2,31)-1;
    var maxX = 0;
    var minY = pow(2,31)-1;
    var maxY = 0;
    for (var set in ccdPts){
        if (set[2]==0){
           if (set[0] < minX) minX = set[0];
           if (set[1] > maxY) maxY = set[1];
        }
        else if (set[2]==1){
            if (set[0] > maxX) maxX = set[0];
            if (set[1] < minY) minY = set[1];
        }
        else continue;
    }
    var minMax = {'minX':minX, 'maxX':maxX, 'minY':minY, 'maxY', maxY};
    return minMax;
};

/*
 * Takes the set of CCD points and splits them into individual CCDS
 *
 * return ccds: returns the CCD points split into four separate arrays
 */
function splitCCDs(ccdPts){
    var ccds = [[], [], [], []];

    var ccdCount = 0;
    for (var set in ccdPts){
        ccds[ccdCount].push(set);
        if (set[2]==2) ccdCount++;
    }
    return ccds;
};

/*
 * Takes two points and creates a function to evaluate
 * points on that line.
 *
 * pts: array of two points to create a line between
 *
 * return f: function that evaluates a given value
 */
function createLinEqn(pts){
    // Extract x and y values to reduce array accesses
    var x1 = pts[0][0];
    var y1 = pts[0][1];
    var x2 = pts[1][0];
    var y2 = pts[1][1];

    // Calculate the slope between the points
    var dx = x2-x1;
    var dy = y2-y1;
    var m = dy/dx;

    // Calculate the value of b
    var b = (x2*y1-x1*y2)/dx;

    // Create the linear function between the two points
    function f(x) { return m*x + b; };
    return f;
};

/*
 * Takes three points and returns a quadratic equation
 * that passes through all three points.
 *
 * pts: an array of points
 * return f: quadratic function that takes an x-value and returns
 *      the corresponding y-value
 */
function createQuadEqn(pts){
    // Extract points to reduce array accesses
    var x1 = pts[0][0];
    var x2 = pts[1][0];
    var x3 = pts[2][0];
    var y1 = pts[0][1];
    var y2 = pts[1][1];
    var y3 = pts[2][1];

    // point 2 - point 1
    var a1 = x2*x2 - x1*x1;
    var b1 = x2 - x1;
    var f1 = y2 - y1;

    // point 3 - point 1
    var a2 = x3*x3 - x1*x1;
    var b2 = x3 - x1;
    var f2 = y3 - y1;

    // scale equation 1 so that b cancels
    a1 = b2/b1*a1;
    f1 = b2/b1*f1;

    // reduce the rows so that b cancels
    var a3 = a2 - a1;
    var f3 = f2 - f1;

    // solve for a
    var a = f3 / a3;

    // solve for b
    var b = (f2 - a*a1) / b2;

    // solve for c
    var c = y1 - a*x1*x1 - b*x1;

    // create the function with the new a, b, and c
    function f(x){ return a*x*x + b*x + c; };
    return f;
};

function isInCCD(listPts, ccdPts){
    var insPts = [];
    var outPts = [];
    var minMax = minMaxPts(ccdPts);
    var ccds = splitCCDs(ccdPts);

    var minX = minMax['minX'];
    var maxX = minMax['maxX'];
    var minY = minMax['minY'];
    var maxY = minMax['maxY'];

    for (int i=0; i<listPts.length; i++){
        if (listPts[i][0] < minX ||
                listPts[i][0] > maxX ||
                listPts[i][1] < minY ||
                listPts[i][1] > maxY){
                    outPts.push(listPts[i]);
                }
        else if(listPts[i][0] ){
            outPts.push(listPts[i]);
        }
        else insPts.push(listPts[i]);
    }
    return insidePts;
};

/*********************
 * Original checks. Only checks 1 point at a time.
 *
 * Checks if an object is within the mask?
 * x: x-value of the object location on the mask
 * y: y-value of the object location on the mask
 * full_check: Denotes whether the gaps need to be checked
 *
 * Original note: this function could be replaced by limiting curves
 */
function chk_stat(x, y, full_check){
    var r = x*x + y*y;

    // Is the object within 1 10 arcmin radius?
    if (r>600) return false;

    // inner edge of the mask
    if (y<YMSKMIN) return false;

    // outer edge of the mask
    if (y>YMSKMAX) return false;

    // outer edge of the mask
    if (x>XUPP_LIM || x<XLOW_LIM) return false;

    // cut corner
    if (x > -0.98273 * y + 833.0) return false;

    // If not full check, okay to put slit
    if (full_check == 'NO') return true;

    // Does it sit within the vignette?
    if (x*x+pow((y*YCAMCEN),2) < pow(RADVIGN,2)) return false;

    // Is it in the gaps in the mosaic?
    if (abs(x-GAP1CEN) < GAP1HWD) return false;
    if (abs(x-GAP2CEN) < GAP2HWD) return false;
    if (abs(x-GAP3CEN) < GAP3HWD) return false;

    // Everything looks okay
    return true;
};
