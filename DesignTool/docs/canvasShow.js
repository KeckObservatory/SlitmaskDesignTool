/**
 * 
 * Displays an image, allowing pan, zoom, rotate, contrast/brightness change.
 * 
 * This is derived from imgShow.js. 2018-03-30, skwok.
 *  
 */

function TxMatrix() {
	var self = this;
	self.scaleFactor = 1;

	function norm(x) {
		while (x < 0)
			x += 360;
		while (x >= 360)
			x -= 360;
		return x;
	}

	function normRad(x) {
		while (x < 0)
			x += Math.PI * 2;
		while (x > Math.PI * 2)
			x -= Math.PI * 2;
		return x;
	}

	self.translate = function (tx, ty) {
		with(self) {
			mat[0][2] += tx;
			mat[1][2] += ty;
		}
	};

	self.rotate = function (angRad, xc, yc) {
		with(self) {
			angRad = normRad(angRad);
			var sina = Math.sin(angRad);
			var cosa = Math.cos(angRad);
			var a = mat[0][0];
			var b = mat[0][1];
			var c = mat[1][0];
			var d = mat[1][1];

			var e = mat[0][2] - xc;
			var f = mat[1][2] - yc;

			mat[0][0] = a * cosa - b * sina;
			mat[0][1] = a * sina + b * cosa;

			// mat[1][0] = c * cosa - d * sina;
			// mat[1][1] = c * sina + d * cosa;
			mat[1][0] = -mat[0][1];
			mat[1][1] = mat[0][0];

			mat[0][2] = e * cosa - f * sina + xc;
			mat[1][2] = e * sina + f * cosa + yc;
			return;
		}
	};

	self.getScale = function () {
		with(self) {
			var ca2 = (mat[0][0] * mat[1][1]);
			var sa2 = (mat[0][1] * mat[1][0]);
			return Math.sqrt(Math.abs(ca2 - sa2));
		}
	};

	self.getTranslation = function () {
		return [self.mat[0][2], self.mat[1][2]];
	};

	self.setRotAngle = function (angRad) {
		with(self) {
			var s = self.getScale();
			var sina = Math.sin(angRad);
			var cosa = Math.cos(angRad);
			mat[0][0] = mat[1][1] = s * cosa;
			mat[0][1] = s * sina;
			mat[1][0] = -s * sina;
		}
	};

	self.getRotAngle = function () {
		// Returns angle in radians
		with(self) {
			var ca = (mat[0][0] + mat[1][1]) / 2;
			var sa = (mat[0][1] - mat[1][0]) / 2;
			return Math.atan2(sa, ca);
		}
	};

	self.scale = function (s) {
		with(self) {
			mat[0][0] *= s;
			mat[0][1] *= s;
			mat[1][0] *= s;
			mat[1][1] *= s;
		}
	};

	self.scaleCenter = function (s, xc, yc) {
		// Scale such that the pixel in the center of the canvas stays there.
		with(self) {
			scale(s);
			mat[0][2] = mat[0][2] * s + xc * (1 - s);
			mat[1][2] = mat[1][2] * s + yc * (1 - s);
		}
	};

	// Returns arguments for Ctx.transform()
	// First 4 values represents 2x2 rotation/scale matrix
	// Last 2 values are translation.
	self.getTx = function (flipY) {
		with(self) {
			var r0 = mat[0];
			var r1 = mat[1];
			if (flipY)
				return [r0[0], r0[1], -r1[0], -r1[1], r0[2], r1[2]];
			else
				return [r0[0], r0[1], r1[0], r1[1], r0[2], r1[2]];
		}
	};

	self.reset = function (height) {
		self.mat = [
			[1, 0, 0],
			[0, 1, height],
			[0, 0, 1]
		];
	};

	self.rotatePnt = function (x, y, flipY = 0) {
		var tx = self.getTx(flipY);
		var x1 = x * tx[0] + y * tx[1];
		var y1 = x * tx[2] + y * tx[3];

		return [x1, y1];
	};

	// World to screen coordinates
	self.w2s = function (x, y, flipY = 0) {
		var tx = self.getTx(flipY);
		var x1 = x * tx[0] - y * tx[1] + tx[4];
		var y1 = -x * tx[2] + y * tx[3] + tx[5];

		return [x1, y1];
	};

	// Screen to world coordinates
	self.s2w = function (x, y, flipY = 0) {
		// inverse transform
		var tx = self.getTx(flipY);
		var det = tx[0] * tx[3] - tx[1] * tx[2];
		var x1 = x - tx[4];
		var y1 = y - tx[5];
		var x2 = (x1 * tx[3] - y1 * tx[2]) / det;
		var y2 = (-x1 * tx[1] + y1 * tx[0]) / det;

		return [x2, y2];
	};

	self.toString = function () {
		var angDeg = self.getRotAngle() / Math.PI * 180.0;
		var tx = self.getTx(0);
		var out = "<table><tr>" +
			"<td>" + tx[0].toFixed(2) + "<td>" + tx[1].toFixed(2) +
			"<td>Angle:" + angDeg.toFixed(2) +
			"<tr>" +
			"<td>" + tx[2].toFixed(2) + "<td>" + tx[3].toFixed(2) +
			"<tr>" +
			"<td>" + tx[4].toFixed(2) + "<td>" + tx[5].toFixed(2) +
			"</table>";
		return out;
	};

	self.reset(0);
} // TxMatrix


function toggleSmoothing(ctx, onoff) {
	ctx.imageSmoothingEnabled = onoff;
	ctx.mozImageSmoothingEnabled = onoff;
	ctx.webkitImageSmoothingEnabled = onoff;
	ctx.msImageSmoothingEnabled = onoff;
}

function Filter(ctx, width, height) {
	/*
	 * Creates a temporary canvas element with given width and height. ctx
	 * is the destination canvas context.
	 */
	var self = this;
	self.scale = 1.4;

	self.offset = -42;
	self.outCtx = ctx;

	self.tmpCanvas = document.createElement("canvas");
	self.tmpCanvas.width = width;
	self.tmpCanvas.height = height;
	self.tmpCtx = self.tmpCanvas.getContext("2d");

	self.tmpCanvas2 = document.createElement("canvas");
	self.tmpCanvas2.width = width;
	self.tmpCanvas2.height = height;
	self.tmpCtx2 = self.tmpCanvas2.getContext("2d");

	toggleSmoothing(self.tmpCtx, false);
	toggleSmoothing(self.tmpCtx2, false);

	self.applyScaleOffset = function (data, scale, offset) {
		/*
		 * This is for contrast and brightness control. Scales and offsets
		 * the pixel values.
		 */
		var len = data.length;
		var t = 0;
		var i = 0;

		while (i < len) {
			data[i] = data[i] * scale + offset;
			++i;

			data[i] = data[i] * scale + offset;
			++i;

			data[i] = data[i] * scale + offset;
			++i;

			++i; // skip alpha
		}
	};

	self.setParams = function (scale, offset) {
		/*
		 * Sets the contrast (scale) and brightness (offset) parameters.
		 */
		self.scale = scale;
		self.offset = offset;
	};

	// Split drawImage into two functions
	self.drawToOutputPart1 = function (img, offx, offy) {
		self.tmpCtx.drawImage(img, offx, offy);

		var imgData = self.tmpCtx.getImageData(0, 0, self.tmpCanvas.width,
			self.tmpCanvas.height);

		// Applies contrast
		self.applyScaleOffset(imgData.data, self.scale, self.offset);
		// Copies image to ctx2
		self.tmpCtx2.putImageData(imgData, 0, 0);
		// After this, new update should go to ctx2.
	};

	self.drawToOutputPart2 = function () {
		// When updates are completed, copy ctx2 to output
		var imgData = self.tmpCtx2.getImageData(0, 0, self.tmpCanvas.width,
			self.tmpCanvas.height);
		self.outCtx.putImageData(imgData, 0, 0);
	};
	return this;
} /* End of Filter */

// This is main function for the canvas show object.

function CanvasShow(containerName, zoomContainer) {
	var self = this;

	var AlignBox = -2;
	var GuideBox = -1;

	// For displaying mouse-over values and cuts
	// self.rawData = null;

	// Variables for mouse handling.
	self.anchorx = 0;
	self.anchory = 0;
	self.dragging = 0;

	self.mustFit = 1;

	self.centerRaDeg = 0;   // original center RA deg
	self.centerDecDeg = 0;  // original center DEC deg

	self.currRaDeg = 0;
	self.currDecDeg = 0;

	self.positionAngle = 0;
	self.origPA = 0;

	self.xAsPerPixel = 1;
	self.yAsPerPixel = 1;
	self.showMinPriority = -999;

	self.scale = 1;
	self.tMatrix = new TxMatrix(); // describes the view
	self.targetMatrix = new TxMatrix(); // describes the sky
	self.origSkyMatrix = new TxMatrix(); // describes the orignal sky PA

	self.maskOffsetX = 0;
	self.maskOffsetY = 270;
	self.slitColor = '#FF0000';
	self.maskColor = '#8888FF';
	self.guiderFOVColor = '#FFFF88';
	self.badColumnsColor = '#FFaaaa';

	self.slitsReady = false;

	// for selecting targets
	self.findIt = 0;
	self.searchX = 0;
	self.searchY = 0;
	self.thold = 0;
	self.selectedTargetIdx = -1;

	self.centerMarker = [
		[-11.850, 0.000, 0],
		[11.850, 0.000, 3],
		[0.000, -11.850, 0],
		[0.000, 11.850, 3],

		[-11.850, 270.000, 0],
		[11.850, 270.000, 3],
		[0.000, 270 - 11.850, 0],
		[0.000, 270 + 11.850, 3],
	];

	self.maskLayout = [];

	self.contElem = E(containerName);
	self.zoomElem = E(zoomContainer);

	self.mouseAction = 'panSky';
	self.showInfo = function () {};
	// End variables

	function E(n) {
		return document.getElementById(n);
	}

	function abs(x) {
		if (x < 0) return -x;
		return x;
	}

	function showMsg(dname, msg) {
		E(dname).innerHTML = msg;
	}


	function toSexa(inDeg) {
		var val = inDeg;
		var sign = ' ';
		if (val < 0) {
			sign = '-';
			val = -val;
		}
		var dd = Math.floor(val);
		val = (val - dd) * 60;
		var mm = Math.floor(val);
		var ss = (val - mm) * 60;
		if (dd < 10) dd = '0' + dd;
		if (mm < 10) mm = '0' + mm;
		var cc = ':';
		var ss100 = Math.round(ss * 100);
		ss = ss100 / 100;
		if (ss100 < 1000) cc = ':0';
		return sign + dd + ':' + mm + cc + ss.toFixed(2);
	}

	function toBoolean(s) {
		// String to boolean
		s = s.toUpperCase();
		return (s == 'YES') || (s == '1') || (s == 'TRUE') || (s == 'ON');
	}

	function norm360(x) {
		while (x > 360) x -= 360;
		while (x < 0) x += 360;
		return x;
	}

	function norm180(x) {
		if (x > 180) return x - 360;
		if (x < -180) return x + 360;
		return x;
	}

	function degrees(rad) {
		return norm180(rad * 180.0 / Math.PI);
	}

	function radians(deg) {
		return deg * Math.PI / 180.0;
	}

	function rotate(angRad, x, y) {
		var sa = Math.sin(angRad);
		var ca = Math.cos(angRad);
		return rotateSaCa(sa, ca, x, y);
	}

	function rotateSaCa(sa, ca, x, y) {
		var x1 = x * ca - y * sa;
		var y1 = x * sa + y * ca;
		return [x1, y1];
	}

	self.onloadImage = function () {
		if (self.mustFit) {
			// self.fitMask();
			self.resetDisplay();
			self.resetOffsets();
			self.mustFit = 0;
		}
		self.redrawTxImage();
	};

	self.initialize = function () {
		/*
		 * Creates a canvas and puts it in the container. Sets default size to
		 * 400x400 if not defined. Instantiates a filter object to process the
		 * image.
		 */
		var cv = document.createElement("canvas");
		if (cv.getContext) {
			var cont = self.contElem;
			self._Canvas = cv;
			cv.tabIndex = 99999;
			cont.tabIndex = 99999;
			var w = Math.max(1000, cont.clientWidth);
			cv.width = w;
			cv.height = Math.max(500, w / 3);
			if (cv.width == 0 || cv.height == 0) {
				cv.width = cv.height = 400;
			}
			cont.replaceChild(cv, cont.childNodes[0]);
			var ctx = cv.getContext("2d");
			ctx.scale(1, 1);
			toggleSmoothing(ctx, false);
			self.destCtx = ctx;
			self.filter = new Filter(ctx, cv.width, cv.height);
			self._Ctx = self.filter.tmpCtx;
			// Creates a hidden image element to store the source image.
			self.bgImg = new Image();
			self.bgImg.onload = self.onloadImage;
			self.findMaskMinMax();
		} else {
			alert("Your browser does not support canvas\nPlease use another browser.");
		}
	};

	self.findMaskMinMax = function () {
		var layout = self.maskLayout;
		var i;
		var minx, miny, maxx, maxy;
		minx = miny = 999999;
		maxx = maxy = -999999;

		for (i in layout) {
			var row = layout[i];
			var x = row[0];
			var y = row[1];
			minx = Math.min(minx, x);
			miny = Math.min(miny, y);
			maxx = Math.max(maxx, x);
			maxy = Math.max(maxy, y);
		}
		self.maskMinMax = [minx, miny, maxx, maxy];
	};

	self.fitMask = function (atx, aty) {
		// Fit display centered at world coord atx,aty
		var mmm = self.maskMinMax;
		var xrange = mmm[2] - mmm[0];
		var yrange = mmm[3] - mmm[1];

		var cv = self._Canvas;
		var sw = cv.width / xrange;
		var sh = cv.height / yrange;
		var scale = Math.min(sw, sh) * 0.9;

		var x = cv.width / 2;
		var y = cv.height / 2;

		self.tMatrix.reset(0);
		self.tMatrix.setRotAngle(0);
		self.tMatrix.scale(scale);
		var sxy = self.tMatrix.w2s(atx, aty);
		self.tMatrix.translate(x + sxy[0], y + sxy[1]);
	};

	self.showPositionInfo = function () {
		// Updates the current PA, center RA/DEC
		// and shows them in the parameter form.

		var tmatAngleRad = self.tMatrix.getRotAngle();

		var sxy = self.origSkyMatrix.s2w(self.maskOffsetX, self.maskOffsetY, 0);

		self.currDecDeg = self.centerDecDeg + (sxy[0] + self.maskOffsetX) / 3600;

		var cosDec = Math.cos(radians(self.currDecDeg));
		cosDec = Math.max(cosDec, 1E-4);

		self.currRaDeg = self.centerRaDeg + (self.maskOffsetY - sxy[1]) / 3600 / cosDec;		

		var raSexa = toSexa(self.currRaDeg/15);
		var decSexa = toSexa(self.currDecDeg);
		var paDeg = self.positionAngle + self.origPA;

		if (E('inputrafd')) {
			E('inputrafd').value = raSexa;
			E('inputdecfd').value = decSexa;
			E('maskpafd').value = paDeg.toFixed(3);

			showMsg("statusDiv",
				" RA= <b>" + raSexa +
				"</b> hrs; DEC= <b>" + decSexa +
				"</b> deg; Pos Ang= <b>" + paDeg.toFixed(2) + "</b> deg "
			);
		}
	};

	self.drawCompass = function (ctx) {

		function arrow(ctx, x0, y0, x1, y1, size) {
			var dx = x1 - x0;
			var dy = y1 - y0;

			var len = Math.sqrt(dx * dx + dy * dy);
			var dx0 = dx / len;
			var dy0 = dy / len;
			var pdx = -dy0;
			var pdy = dx0;

			var px0 = x1 - dx0 * size;
			var py0 = y1 - dy0 * size;
			var size2 = size / 2;

			ctx.moveTo(x0, y0);
			ctx.lineTo(x1, y1);
			ctx.lineTo(px0 + pdx * size2, py0 + pdy * size2);
			ctx.lineTo(px0 - pdx * size2, py0 - pdy * size2);
			ctx.lineTo(x1, y1);
		}

		var color = '#ffff00';
		var rotAngleDeg = self.compassNorthDeg; // calculated in calcualteAngles()

		var aRad = radians(rotAngleDeg);
		var ca = Math.cos(aRad);
		var sa = Math.sin(aRad);

		var x0 = 70;
		var y0 = 70;
		var len = 50;

		var north = rotateSaCa(sa, ca, 0, -len);
		var northText = rotateSaCa(sa, ca, 0, -len - 10);
		var east = rotateSaCa(sa, ca, -len, 0);
		var eastText = rotateSaCa(sa, ca, -len - 10, 0);

		with(ctx) {
			setTransform(1, 0, 0, 1, 0, 0);
			strokeStyle = color;
			lineWidth = 1;

			beginPath();
			arrow(ctx, x0, y0, x0 + north[0], y0 + north[1], 8);
			arrow(ctx, x0, y0, x0 + east[0], y0 + east[1], 8);

			stroke();

			strokeText('N', x0 + northText[0], y0 + northText[1]);
			strokeText('E', x0 + eastText[0], y0 + eastText[1]);
		}
	};

	self.calculateAngles = function () {
		// positionAngle is telescope PA
		// view angle in screen coordinates
		var tmAngle = self.tMatrix.getRotAngle();

		self.positionAngle = degrees(self.targetMatrix.getRotAngle());

		// compass North in screen angle
		self.compassNorthDeg = degrees(tmAngle) + 90 + self.positionAngle + self.origPA;
		// not used
		// slit angle in screen angle
		self.slitBaseAngleDeg = self.compassNorthDeg + 90;

		// mask angle in screen angle
		self.maskBaseAngleDeg = degrees(tmAngle);

		// Deprecated
		// mask angle relative to north
		self.slitRel2MaskDeg = norm180(self.positionAngle);
		self.slitRel2Mask = radians(norm180(self.positionAngle));
	};

	self.reallyDrawTxImage = function () {
		// Applies transform and redraws image.
		var cv = self._Canvas;
		var tx = self.tMatrix;
		var tp = tx.getTx(self.flipY);
		var scaleF = tx.getScale();

		var iwidth = self.bgImg.width / 2;
		var iheight = self.bgImg.height / 2;

		self.calculateAngles();

		with(self._Ctx) {
			setTransform(1, 0, 0, 1, 0, 0);
			clearRect(0, 0, cv.width, cv.height);
			transform(tp[0], tp[1], tp[2], tp[3], tp[4], tp[5]);
		}

		// Draws the background images, applies contrast and copies result to
		// tmpCtx2
		
		self.filter.drawToOutputPart1(self.bgImg, - iwidth, - iheight);

		// Draw this after drawing the DSS/background image
		// because contrast filter is applied to the DSS/background image.
		var ctx2 = self.filter.tmpCtx2;
		with(ctx2) {
			setTransform(1, 0, 0, 1, 0, 0);
			self.drawGuiderFOV(ctx2, self.guiderFOV);
			self.drawBadColumns(ctx2, self.badColumns);
			var rotatedMask = self.drawMask(ctx2, self.maskLayout);

			var checker = new InOutChecker(rotatedMask);
			self.drawTargets(ctx2, checker);
			self.drawCompass(ctx2);
		}
		// Copies result to destCtx
		self.filter.drawToOutputPart2();

		self.showPositionInfo();
	};

	self.redrawTxImage = function () {
		window.requestAnimationFrame(self.reallyDrawTxImage);
	};

	self.drawPolylines = function (ctx, lines, color, lw) {
		with(ctx) {
			strokeStyle = color;

			lineWidth = lw;
			beginPath();
			var x0 = 0,
				y0 = 0;
			for (i in lines) {
				var row = lines[i];
				var x = row[0];
				var y = row[1];
				var code = row[2];
				if (code == 0) {
					x0 = x;
					y0 = y;
					moveTo(x, y);
					continue;
				}
				if (code == 1 || code == 3) {
					lineTo(x, y);
					continue;
				}
				if (code == 2) {
					lineTo(x0, y0);
				}
			}
			stroke();
		}
	};

	//
	// Draws targets according to options
	//
	self.drawTargets = function (ctx, checker) {

		// This function is called once per target.
		// It adds the target to the given list.

		function checkClick(idx, x, y) {
			if (self.findIt) {
				// Check if target is near to where the mouse was clicked.
				var dx = Math.abs(self.searchX - x);
				var dy = Math.abs(self.searchY - y);
				if (dx < self.thold && dy < self.thold) {
					// If close enough, then if this target is the closest one.
					var dist = Math.hypot(dx, dy);
					if (dist < minDist) {
						minDist = dist;
						self.minDist = dist;
						self.selectedTargetIdx = idx;
					}
				}
			}
		}

		function classify() {
			// Depending on if target is inside/outside, or selected, push it to
			// a different list to be displayed later.
			for (i = 0; i < len; ++i) {

				var xy = self.targetMatrix.w2s(xpos[i], ypos[i]);
				var x = xy[0];
				var y = xy[1];
				var sxy = tmax.w2s(x, y);
				var sx = sxy[0];
				var sy = sxy[1];

				var pri = pcode[i];
				var inMask = checker.checkPoint(sx, sy);

				xOut.push(sx);
				yOut.push(sy);

				checkClick (i, x, y);

				if (pri == GuideBox) {
					if (inMask)
						guideBoxInIdx.push(i);
					else
						guideBoxOutIdx.push(i);
					continue;
				}

				if (pri == AlignBox) {
					if (inMask)
						alignBoxInIdx.push(i);
					else
						alignBoxOutIdx.push(i);						
					continue;
				}

				if (inMask) {
					// currently selected (via algorithm)
					// show when when showing splits
					slitsInMaskIdx.push(i);
				}

				if (showMinPriority <= pri && pri <= showMaxPriority) {
					if (inMask) 
						showInIdx.push(i);
					else 
						showOutIdx.push(i);
				}

				if (selected[i]) {
					if (inMask) 
						selectedInIdx.push(i);
					else
						selectedOutIdx.push(i);
				}
			}
		}

		function drawGuideBox (idx) {
			var x = xOut[idx];
			var y = yOut[idx];
			
			var l1 = length1s[idx] * alignBoxSize / 2;
			var l2 = length2s[idx] * alignBoxSize / 2;
			with(ctx) {
				moveTo(x - l1, y - l1);
				lineTo(x - l1, y + l2);
				lineTo(x + l2, y + l2);
				lineTo(x + l2, y - l1);
				lineTo(x - l1, y - l1);
			}
		}

		function drawAlignBox(idx) {
			// alignemtn box
			var x = xOut[idx];
			var y = yOut[idx];
			
			var l1 = length1s[idx] * alignBoxSize / 2;
			var l2 = length2s[idx] * alignBoxSize / 2;
			with(ctx) {
				moveTo(x - l1, y - l1);
				lineTo(x - l1, y + l2);
				lineTo(x + l2, y + l2);
				lineTo(x + l2, y - l1);
				lineTo(x - l1, y - l1);
			}
		}

		function limit (x, lo, hi) {
			if (x < lo) return lo;
			if (x > hi) return hi;
			return x;
		}

		function drawTarget(idx) {
			var x = xOut[idx];
			var y = yOut[idx];
			var bSize = targetSizeScale / magn[idx];			
			bSize = limit(bSize, 3, 20);
			with(ctx) {
				moveTo(x + bSize, y);
				arc(x, y, bSize, 0, 2 * Math.PI);
			}
		}

		function drawSelTarget(idx) {
			var x = xOut[idx];
			var y = yOut[idx];
			var bSize = targetSizeScale / magn[idx];			
			bSize = limit(bSize, 3, 20);
			with(ctx) {
				moveTo(x + bSize, y);
				arc(x, y, bSize, 0, 2 * Math.PI);
				moveTo(x - bSize * 3, y);
				lineTo(x + bSize * 3, y);
				moveTo(x, y - bSize * 2);
				lineTo(x, y + bSize * 2);
			}
		}

		function drawClickedOn(idx) {
			var x = xOut[idx];
			var y = yOut[idx];
			var bSize = targetSizeScale / magn[idx];			
			bSize = limit(bSize, 3, 20);
			with(ctx) {
				moveTo(x + bSize + 4, y);
				arc(x, y, bSize + 4, 0, 2 * Math.PI);
				moveTo(x - bSize, y - bSize);
				lineTo(x + bSize, y + bSize);
				moveTo(x - bSize, y + bSize);
				lineTo(x + bSize, y - bSize);
			}
		}

		function drawSlit(idx) {
			/*-
			 * Position of the star is at x/y, already transformed to screen coordinates 
			 * Lengths to left and right are l1/l2, in screen coordinates
			 * Slit width adjusted by scale.			 * 
			 */

			// Mask Angle relative to screen
			var maskBaseAngleRad = radians(self.maskBaseAngleDeg);
			var maskXY = rotateSaCa(
				Math.sin(maskBaseAngleRad),
				Math.cos(maskBaseAngleRad), 0, 1);

			// Angle relative to screen
			var slitAngle = radians(Number(slitPAs[idx]));
			var slitAngleOnScreen = radians(self.slitBaseAngleDeg) - slitAngle;

			var x = xOut[idx];
			var y = yOut[idx];
			var l1 = length1s[idx] / self.xAsPerPixel * tmScale;
			var l2 = length2s[idx] / self.xAsPerPixel * tmScale;

			var slitWidth = slitWidths[idx];
			var halfWidth = slitWidth / 2 / self.yAsPerPixel * tmScale;

			var cosa = Math.cos(slitAngleOnScreen);
			var sina = Math.sin(slitAngleOnScreen);

			// maskX,maskY = vector perpendicular to mask
			var maskX = maskXY[0] * halfWidth;
			var maskY = maskXY[1] * halfWidth;

			var cosaMask = Math.abs(Math.cos(self.slitRel2Mask - slitAngle));

			if (projSlitLen) {
				if (cosaMask < 0.3)
					cosaMask = 0.3;
				l1 /= cosaMask;
				l2 /= cosaMask;
			}

			// var res = rotateSaCa(sina, cosa, 1, 0);
			var x11 = x + cosa * l1;
			var y11 = y + sina * l1;
			var x12 = x - cosa * l2;
			var y12 = y - sina * l2;

			var t;
			if (x11 < x12) {
				t = x12;
				x12 = x11;
				x11 = t;
				t = y12;
				y12 = y11;
				y11 = t;
				// t = x22; x22 = x21; x21 = t;
				// t = y22; y22 = y21; y21 = t;
			}

			with(ctx) {
				/*
				 * just one line moveTo (x11, y11); lineTo (x12, y12);
				 */

				moveTo(x11 + maskX, y11 + maskY);
				lineTo(x11 - maskX, y11 - maskY);
				lineTo(x12 - maskX, y12 - maskY);
				lineTo(x12 + maskX, y12 + maskY);
				lineTo(x11 + maskX, y11 + maskY);

				// Draw a cross that is aligned with the mask
				moveTo(x - maskX, y - maskY);
				lineTo(x + maskX, y + maskY);
				moveTo(x + maskY, y - maskX);
				lineTo(x - maskY, y + maskX);
			}
		} // end drawSlit

		function drawListIdx(tlist, color, fnc) {
			var idx;
			ctx.strokeStyle = color;
			ctx.beginPath();
			for (idx in tlist) {
				fnc(tlist[idx]);
			}
			ctx.stroke();
		}

		var targets = self.targets;
		if (!targets)
			return;

		var tmax = self.tMatrix;
		var xpos = targets.xarcs;
		var ypos = targets.yarcs;
		var slitPAs = targets.slitLPA;
		var slitWidths = targets.slitWidth;
		var length1s = targets.length1;
		var length2s = targets.length2;

		var selected = targets.selected;
		var pcode = targets.pcode;
		var len = xpos.length;

		var selectedInIdx = [];
		var selectedOutIdx = []
		var showInIdx = [];
		var showOutIdx = [];
		var alignBoxInIdx = [];
		var alignBoxOutIdx = [];
		var guideBoxInIdx = [];
		var guideBoxOutIdx = [];
		var slitsInMaskIdx = [];
		var xOut = [];
		var yOut = [];
		var magn = targets.mag;

		var height2 = self._Canvas.height;
		var i;

		var tmScale = tmax.getScale();
		var targetSizeScale = tmScale;

		var alignBoxSize = tmScale / self.xAsPerPixel;
		var minDist = 1E10;

		var showAll = E('showAll').checked;
		var showAlignBox = E('showAlignBox').checked;
		var showGuideBox = E('showGuideBox').checked;
		var showSelected = E('showSelected').checked;
		var projSlitLen = toBoolean(E('projslitlengthfd').value);
		var showByPriority = E('showByPriority').checked;
		var showMinPriority = Number(E('minPriority').value);
		var showMaxPriority = Number(E('maxPriority').value);

		if (showAll) {
			showByPriority = true;
			showMinPriority = 0;
			showMaxPriority = 99999;
		}

		ctx.lineWidth = 1;
		ctx.lineCap = 'square';

		classify();

		self.insideTargetsIdx = new Array().concat(selectedInIdx, showInIdx, alignBoxInIdx);

		if (showAlignBox) {
			drawListIdx(alignBoxInIdx, '#99ff99', drawAlignBox);
			drawListIdx(alignBoxOutIdx, '#ff0000', drawAlignBox);
		}

		if (showGuideBox) {
			drawListIdx(guideBoxInIdx, '#ffff99', drawGuideBox);
			drawListIdx(guideBoxOutIdx, '#ff0000', drawGuideBox);
		}

		if (showSelected || showByPriority) {
			drawListIdx(selectedInIdx, '#99ff99', drawSelTarget);
			drawListIdx(selectedOutIdx, '#ff0000', drawSelTarget);
		}

		if (showByPriority) {
			drawListIdx(showInIdx, '#99ff99', drawTarget);
			drawListIdx(showOutIdx, '#ff0000', drawTarget);
		}

		if (self.selectedTargetIdx >= 0) {
			drawListIdx([self.selectedTargetIdx], '#ffffff', drawClickedOn);
		}

		if (self.slitsReady) {
			drawListIdx(slitsInMaskIdx, '#22ffaa', drawSlit);
		}
	};

	self.selectTarget = function (mx, my) {
		// Selecte target with mouse
		var tmat = self.tMatrix;
		var scale = tmat.getScale();
		var xy = tmat.s2w(mx, my, 0);

		self.searchX = xy[0];
		self.searchY = xy[1];
		self.thold = Math.min(7 / scale, 7);

		var sIdx = self.selectedTargetIdx;
		if (sIdx >= 0) {
			self.targetTable.markNormal(sIdx);
		}
		self.selectedTargetIdx = -1;
		self.findIt = 1;
		self.reallyDrawTxImage();
		self.findIt = 0;

		var i, row;
		var found = self.selectedTargetIdx;
		if (found >= 0) {
			self.showTargetForm(found);
			self.targetTable.scrollTo(found);
			self.targetTable.highLight(found);
		}
	};

	self.showTargetForm = function (idx) {
		var targetTable = self.targetTable;
		var targetIdx = idx;
		var targets = targetTable.targets;

		E('targetName').innerHTML = targets.objectId[targetIdx];
		E('targetRA').innerHTML = targets.raSexa[targetIdx];
		E('targetDEC').innerHTML = targets.decSexa[targetIdx];

		E('targetPrior').value = targets.pcode[targetIdx];
		E('targetSelect').value = targets.selected[targetIdx];
		E('targetSlitPA').value = targets.slitLPA[targetIdx];
		E('targetSlitWidth').value = targets.slitWidth[targetIdx];
		E('targetLength1').value = targets.length1[targetIdx].toFixed(2);
		E('targetLength2').value = targets.length2[targetIdx].toFixed(2);
	};

	self.updateTarget = function () {
		var idx = self.selectedTargetIdx;
		if (idx < 0) return;

		targets.pcode[idx] = Number(E('targetPrior').value);
		targets.selected[idx] = Number(E('targetSelect').value);
		targets.slitLPA[idx] = Number(E('targetSlitPA').value);
		targets.slitWidth[idx] = Number(E('targetSlitWidth').value);
		targets.length1[idx] = Number(E('targetLength1').value);
		targets.length2[idx] = Number(E('targetLength2').value);

		self.reDrawTable();
		self.targetTable.scrollTo(idx);
		self.targetTable.highLight(idx);
		self.reallyDrawTxImage();
	};

	self.clickedRow = function (evt) {
		var oldIdx = self.selectedTargetIdx;
		var tId = this.id;
		var idx = Number(tId.replace('target', ''));

		self.targetTable.markNormal(oldIdx);
		self.targetTable.highLight(idx);
		self.selectedTargetIdx = idx;
		self.showTargetForm(idx);
		self.redrawTxImage();
	};

	self.rotateMaskLayout = function (mask) {
		// Rotates mask layout for drawing.
		// Applies rotation directly to the vertices of the mask.
		// Returns the rotated coordinates of the mask for drawing.
		var sx = 1.0 / self.xAsPerPixel;
		var sy = 1.0 / self.yAsPerPixel;
		var rotX = self.maskOffsetX;
		var rotY = self.maskOffsetY;
		var tmax = self.tMatrix;
		var i;

		var out = Array();
		for (i in mask) {
			var row = mask[i];

			var sxy = tmax.w2s(row[0], row[1]);
			var x0 = sxy[0];
			var y0 = sxy[1];
			out.push([x0, y0, row[2]]);
		}
		return out;
	};

	self.drawGuiderFOV = function (ctx, guiderFOV) {
		if (!E('showGuiderFOV').checked) return;
		var layout = self.rotateMaskLayout(guiderFOV);
		self.drawPolylines(ctx, layout, self.guiderFOVColor, 3);
	};

	self.drawBadColumns = function (ctx, badColumns) {
		if (!E('showBadColumns').checked) return;
		var layout = self.rotateMaskLayout(badColumns);
		self.drawPolylines(ctx, layout, self.BadColumnsColor, 3);
	};

	self.drawMask = function (ctx, mask) {
		var layout = mask.concat(self.centerMarker);
		var layout1 = self.rotateMaskLayout(layout);
		self.drawPolylines(ctx, layout1, self.maskColor, 1);
		return layout1;
	};


	// Gets absolute position x/y in pixel coordinates of an element.
	// Returns array [x, y]
	function getAbsPosition(elem) {
		var prent = elem.offsetParent;
		var absLeft = elem.offsetLeft;
		var absTop = elem.offsetTop;
		while (prent) {
			absLeft += prent.offsetLeft;
			absTop += prent.offsetTop;
			prent = prent.offsetParent;
		}
		return {
			x: absLeft,
			y: absTop
		};
	};

	self.mouseUp = function (evt) {
		evt = evt || window.event;
		evt.stopPropagation();
		evt.preventDefault();
		var mx = evt.pageX;
		var my = evt.pageY;
		var dx = mx - self.anchorx;
		var dy = my - self.anchory;
		self.dragging = 0;
		if (E('enableSelection').checked && abs(dx) < 2 && abs(dy) < 2) {
			var ePos = getAbsPosition(self.contElem);
			self.selectTarget(mx - ePos.x, my - ePos.y);
		}
		self.redrawTxImage();
		return false;
	};

	self.mouseDown = function (evt) {
		evt = evt || window.event;
		evt.stopPropagation();
		evt.preventDefault();
		self.contElem.focus();
		self.lastmx = self.anchorx = evt.pageX;
		self.lastmy = self.anchory = evt.pageY;
		self.dragging = 1;
		var cv = self._Canvas;
		var ePos = getAbsPosition(self.contElem);
		var xc = cv.width / 2 + ePos.x;
		var yc = cv.height / 2 + ePos.y;
		self.baseAngle = Math.atan2(self.anchory - yc, self.anchorx - xc);
		return false;
	};

	self.mouseWheel = function (evt) {
		var activeElem = document.activeElement;
		if (self.contElem != activeElem) return true;
		evt = evt || window.event;
		evt.stopPropagation();
		evt.preventDefault();
		var delta = -6 * Math.sign(evt.wheelDelta || evt.deltaY);
		self.zoomAll(delta);

		self.redrawTxImage();
		return false;
	};

	self.reportPxValue = function (mx, my) {
		if (!self.targets)
			return;
		var sx = self.xAsPerPixel;
		var sy = self.yAsPerPixel;
		var tmat = self.tMatrix;

		// screen to focal plane
		var xy0 = tmat.s2w(mx * sx, my * sy, 0);

		// focal plane to sky
		var rxy = self.origSkyMatrix.s2w(xy0[0], xy0[1], 0);	

		var dec = self.centerDecDeg + (rxy[0] + self.maskOffsetX) / 3600;
		var cosDec = Math.cos(radians(dec));
		cosDec = Math.max(cosDec, 1E-4);
		rxy[1] = (rxy[1] - self.maskOffsetY) / cosDec;
		var raHrs = (self.centerRaDeg - rxy[1] / 3600) / 15;
		while (raHrs > 24) raHrs -= 24;
		while (raHrs < 0) raHrs += 24;

		showMsg('mouseStatus', "RA= <b>" + toSexa(raHrs) + "</b> hrs; DEC= <b>" + toSexa(dec) + 
		"</b> deg, px=");
	};

	self.zoomAll = function (mv) {
		var tx = self.tMatrix;
		var cv = self._Canvas;
		var xc = cv.width / 2;
		var yc = cv.height / 2;
		var scale = Math.pow(1.01, mv);
		tx.scaleCenter(scale, xc, yc);
	};

	self.panAll = function (dx, dy) {
		var tx = self.tMatrix;
		tx.translate(dx, dy);
	};

	self.rotateAll = function (angRad) {
		// Rotates the image around center of canvas
		var tx = self.tMatrix;
		var cv = self._Canvas;
		var xc = cv.width / 2;
		var yc = cv.height / 2;
		tx.rotate(angRad, xc, yc);
	};

	self.panSky = function (dx, dy) {
		var txM = self.tMatrix;
		var scale = txM.getScale();
		var ndxy = txM.rotatePnt(dx, dy, 0);
		var s2 = scale * scale;
		self.targetMatrix.translate(ndxy[0] / s2, ndxy[1] / s2);
		self.origSkyMatrix.translate(ndxy[0] / s2, ndxy[1] / s2);
	};

	self.rotateSky = function (ang) {
		// Rotates mask around center of canvas
		self.targetMatrix.rotate(ang, self.maskOffsetX, self.maskOffsetY);
		self.origSkyMatrix.rotate(ang, self.maskOffsetX, self.maskOffsetY);
	};

	self.mouseMove = function (evt) {
		function whichButton(evt) {
			var bbb = evt.buttons || evt.which || evt.button;
			if (bbb === 1) return 1;
			if (bbb === 2) return 2;
			if (bbb === 4) return 4;
			return 0;
		}

		// Not used
		function contrasting() {
			// Contrast/Brightness
			var f = (mx - ePos.x) / xc;
			var sc = 1;
			if (0 < f && f < 2) {
				sc = -1.0 / (f - 2);
				var ofs = 127 * (my - ePos.y - yc) / yc;
				self.filter.setParams(sc, ofs);
			}
		}

		function performMouseAction() {
			var diffAngle = newAngle - self.baseAngle;
			switch (self.mouseAction) {
				case 'panAll':
					self.panAll(dx, dy);
					break;
				case 'panSky':
					self.panSky(dx, dy);
					break;
				case 'rotateAll':
					self.rotateAll(diffAngle);
					break;
				case 'rotateSky':
					self.rotateSky(diffAngle);
					break;
				case 'zoom':
					break;
				case 'contrast':
					contrasting();
					break;
			}
		}

		evt = evt || window.event;

		evt.stopPropagation();
		evt.preventDefault();

		var mx = evt.pageX;
		var my = evt.pageY;

		var dx = mx - self.lastmx;
		var dy = my - self.lastmy;
		var ePos = getAbsPosition(self.contElem);

		if (!self.dragging) {
			self.reportPxValue(mx - ePos.x, my - ePos.y);
			return;
		}

		var tx = self.tMatrix;
		var cv = self._Canvas;
		var xc = cv.width / 2;
		var yc = cv.height / 2;
		var scale = tx.getScale();

		var newAngle = Math.atan2(my - yc - ePos.y, mx - xc - ePos.x);
		var button = whichButton(evt);

		performMouseAction();

		self.redrawTxImage();
		self.lastmx = mx;
		self.lastmy = my;
		self.baseAngle = newAngle;
		return false;
	};

	self.mouseExit = function (evt) {
		self.dragging = 0;
		self.contElem.blur();
	};

	self.moveLeft = function () {
		self.targetMatrix.translate(-10, 0);
		self.origSkyMatrix.translate(-10, 0);
	};

	self.moveRight = function () {
		self.targetMatrix.translate(+10, 0);
		self.origSkyMatrix.translate(+10, 0);
	};

	self.moveUp = function () {
		self.targetMatrix.translate(0, -10);
		self.origSkyMatrix.translate(0, -10);
	};

	self.moveDown = function () {
		self.targetMatrix.translate(0, 10);
		self.origSkyMatrix.translate(0, 10);
	};

	self.keypressed = function (evt) {
		var activeElem = document.activeElement;
		if (self.contElem != activeElem)
			return true;
		evt.preventDefault();
		var k = evt.key;
		switch (k) {
			case 'h':
				self.panSky(-5, 0);
				break;
			case 'l':
				self.panSky(5, 0);
				break;
			case 'j':
				self.panSky(0, 5);
				break;
			case 'k':
				self.panSky(0, -5);
				break;
			case '+':
			case '>':
			case '.':
				self.zoomAll(3);
				break;
			case '-':
			case '<':
			case ',':
				self.zoomAll(-3);
				break;
			default:
				break;
		}
		self.redrawTxImage();
		return false;
	};

	self.captureContext = function (evt) {
		var activeElem = document.activeElement;
		if (self.contElem != activeElem) return true;

		return false;
	};

	self.setShowPriorities = function (minP, maxP) {
		self.showMinPriority = Number(minP);
		self.showMaxPriority = Number(maxP);
	};

	self.showBgImage = function (imgUrl, flipY) {
		self.bgImg.src = imgUrl;
		self.flipY = flipY;
	};

	self.fit = function () {
		self.mustFit = 1;
	};

	self.resetDisplay = function () {
		// Refits image and redraw

		self.fitMask(self.maskOffsetX, self.maskOffsetY + 60);

		var tx = self.tMatrix;
		var xy = tx.w2s(0, 0, 0);
		tx.rotate(Math.PI, xy[0], xy[1]);

		// Only for changing contrast, not needed now
		//self.filter.setParams(1, 0);
	};

	self.resetOffsets = function () {
		// Resets the target matrix.
		self.targetMatrix.reset(0);
		self.targetMatrix.scale(1);
		self.origSkyMatrix.reset(0);
		self.origSkyMatrix.scale(1);
		self.origSkyMatrix.rotate(radians(self.origPA), self.maskOffsetX, self.maskOffsetY);
	};

	self.reDrawTable = function () {
		E('targetTableDiv').innerHTML = self.targetTable.showTable();
		self.targetTable.setOnClickCB(self.clickedRow);
		self.targetTable.setSortClickCB(self.reDrawTable);
	};

	self.setTargets = function (targets) {
		self.targets = targets;

		var raHours = targets.raHour;
		var decDegs = targets.decDeg;
		var raSexa = [];
		var decSexa = [];
		for (i in raHours) {
			var raH = raHours[i];
			var dec = decDegs[i];
			raSexa[i] = toSexa(raH);
			decSexa[i] = toSexa(dec);
		}
		targets.raSexa = raSexa;
		targets.decSexa = decSexa;

		self.origSkyMatrix.reset(0);
		self.origSkyMatrix.rotate(radians(self.origPA), self.maskOffsetX, self.maskOffsetY);

		self.insideTargetsIdx = [];
		self.targetTable = new TargetTable(targets);
		self.reDrawTable();
	};

	self.setMaskLayout = function (layout, guiderFOV, badCols) {
		self.maskLayout = layout;
		self.guiderFOV = guiderFOV;
		self.badColumns = badCols;
		self.findMaskMinMax();
		self.resetDisplay();
		self.resetOffsets();
		self.reallyDrawTxImage();
	};

	self.initialize();

	E('showGuiderFOV').onchange = self.reallyDrawTxImage;
	E('showBadColumns').onchange = self.reallyDrawTxImage;

	E('panAll').onchange = function () {
		self.mouseAction = 'panAll'
	};
	E('panSky').onchange = function () {
		self.mouseAction = 'panSky'
	};
	E('rotateAll').onchange = function () {
		self.mouseAction = 'rotateAll'
	};
	E('rotateSky').onchange = function () {
		self.mouseAction = 'rotateSky'
	};
	E('enableSelection').onchange = function () {
		self.mouseAction = 'selection'
	};
	E('panSky').checked = true;

	self.contElem.onmouseup = self.mouseUp;
	self.contElem.onmousedown = self.mouseDown;
	self.contElem.onmousemove = self.mouseMove;
	self.contElem.onmouseout = self.mouseExit;
	self.contElem.ondblclick = self.doubleClick;
	self.contElem.onwheel = self.mouseWheel;
	window.onkeypress = self.keypressed;
	document.oncontextmenu = self.captureContext;
	
	return this;
}