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

	self.translate = function(tx, ty) {
		with (self) {
			mat[0][2] += tx;
			mat[1][2] += ty;
		}
	};

	self.rotate = function(angRad, xc, yc) {
		with (self) {
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

	self.getScale = function() {
		with (self) {
			var ca2 = (mat[0][0] * mat[1][1]);
			var sa2 = (mat[0][1] * mat[1][0]);
			return Math.sqrt(Math.abs(ca2-sa2));
		}
	};
	
	self.getRotAngle = function () {
		// Returns angle in radians
		with (self) {
			var ca = (mat[0][0] + mat[1][1])/2;
			var sa = (mat[0][1] - mat[1][0])/2;
			return Math.atan2(sa, ca);
		}
	};

	self.scale = function(s) {
		with (self) {
			mat[0][0] *= s;
			mat[0][1] *= s;
			mat[1][0] *= s;
			mat[1][1] *= s;
		}
	};

	self.scaleCenter = function(s, xc, yc) {
		// Scale such that the pixel in the center of the canvas stays there.
		with (self) {
			scale(s);
			mat[0][2] = mat[0][2] * s + xc * (1 - s);
			mat[1][2] = mat[1][2] * s + yc * (1 - s);
		}
	};

	// Returns arguments for Ctx.transform()
	// First 4 values represents 2x2 rotation/scale matrix
	// Last 2 values are translation.
	self.getTx = function(flipY) {
		with (self) {
			var r0 = mat[0];
			var r1 = mat[1];
			if (flipY)
				return [ r0[0], r0[1], -r1[0], -r1[1], r0[2], r1[2] ];
			else
				return [ r0[0], r0[1], r1[0], r1[1], r0[2], r1[2] ];
		}
	};

	self.reset = function(height) {
		self.mat = [ [ 1, 0, 0 ], [ 0, 1, height ], [ 0, 0, 1 ] ];
	};

	// World to screen coordinates
	self.w2s = function (x, y, flipY) {
		var tx = self.getTx(flipY);
		var x1 = x * tx[0] - y * tx[1] + tx[4];
		var y1 = -x * tx[2] + y * tx[3] + tx[5];
		
		return [x1, y1];
	};
	
	// Screen to world coordinates
	self.s2w = function (x, y, flipY) {
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

//
// This is main function for the canvas show object.
//
function CanvasShow(containerName) {
	var self = this;
	
	var AlignBox = -2;
	var GuideBox = -99;
	
	// For displaying mouse-over values and cuts
	self.rawData = null;

	// Variables for mouse handling.
	self.anchorx = 0;
	self.anchory = 0;
	self.dragging = 0;

	self.skyX = 0;
	self.skyY = 0;
	self.mustFit = 1;
	self.northAngle = 90;
	self.eastAngle = 0;
	self.centerRaDeg = 0;
	self.centerDecDeg = 0;

	self.showMinPriority = -999;

	self.scale = 1;
	self.tMatrix = new TxMatrix();
	self.maskTx = new TxMatrix();
	self.maskOffsetX = 0;
	self.maskOffsetY = 0;
	self.slitColor = '#FF0000';
	self.maskColor = '#8888FF';
	self.rotAngle = 0;

	// for selecting targets
	self.findIt = 0;
	self.searchX = 0;
	self.searchY = 0;
	self.thold = 0;
	self.selectedTargetIdx = -1;	
	
	self.maskLayout = [[-498.0, 131.0, 0],
		[-498.0, -14.0, 1],
		[-460.0, -67.0, 1],
		[-420.0, -110.0, 1],
		[-360.0, -161.0, 1],
		[-259.7, -161.0, 1],
		[-259.7, 131.0, 1],
		[-498.0, 131.0, 2],
		[-249.3, 131.0, 0],
		[-249.3, -161.0, 1],
		[-164.0, -161.0, 1],
		[-132.0, -141.0, 1],
		[-98.0, -125.0, 1],
		[-51.0, -112.0, 1],
		[-5.2, -109.0, 1],
		[-5.2, 131.0, 1],
		[-249.3, 131.0, 2],
		[5.2, 131.0, 0],
		[5.2, -109.0, 1],
		[52.0, -111.0, 1],
		[100.0, -126.0, 1],
		[134.0, -142.0, 1],
		[164.0, -161.0, 1],
		[249.3, -161.0, 1],
		[249.3, 131.0, 1],
		[5.2, 131.0, 2],
		[259.7, 131.0, 0],
		[259.7, -161.0, 1],
		[360.0, -161.0, 1],
		[420.0, -110.0, 1],
		[460.0, -67.0, 1],
		[498.0, -14.0, 1],
		[498.0, 131.0, 1],
		[259.7, 131.0, 2],	
		// Cross to mark center.
		[-11.850, 0.000, 0],
		[11.850, 0.000, 3],
		[0.000, -11.850, 0],
		[0.000, 11.850, 3],
		];
		

	self.contElem = E(containerName);

	// End variables

	function E(n) {
		return document.getElementById(n);
	}
	
	function abs(x) {
		if (x < 0) return -x;
		return x;
	}
	
	function showMsg (dname, msg) {
		E(dname).innerHTML = msg;
	}

	function toggleSmoothing(ctx, onoff) {
		ctx.imageSmoothingEnabled = onoff;
		//ctx.mozImageSmoothingEnabled = onoff;
		ctx.webkitImageSmoothingEnabled = onoff;
		ctx.msImageSmoothingEnabled = onoff;
	}	

	function toSexa (inDeg) {
		var val = inDeg;
		var sign = ' ';
		if (val < 0) { sign = '-';
			val = -val;
		}
		var dd = Math.floor(val);
		val = (val - dd) * 60;
		var mm = Math.floor(val);
		var ss = (val - mm) * 60;
		if (dd < 10) dd = '0' + dd;
		if (mm < 10) mm = '0' + mm;
		var cc = ':';
		if (ss < 10) cc = ':0';
		return sign + dd + ':' + mm + cc + ss.toFixed(2);
	}
	
	function degrees(rad) {
		return rad * 180.0 / Math.PI;
	}
	
	function radians(deg) {
		return deg * Math.PI / 180.0;
	}
	
	function rotate (angRad, x, y) {
		var sa = Math.sin(angRad);
		var ca = Math.cos(angRad);
		return rotate1 (sa, ca, x, y);
	}
	
	function rotate1 (sa, ca, x, y) {
		var x1 = x * ca - y * sa;
		var y1 = x * sa + y * ca;
		return [Math.floor(x1), Math.floor(y1)];
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

		self.applyScaleOffset = function(data, scale, offset) {
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

		self.setParams = function(scale, offset) {
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

	self.initialize = function() {
		/*
		 * Creates a canvas and puts it in the container. Sets default size to
		 * 400x400 is not defined. Instantiates a filter object to process the
		 * image.
		 */
		var cv = document.createElement("canvas");
		if (cv.getContext) {
			var cont = self.contElem;
			self._Canvas = cv;
            cv.tabIndex = 99999;
            cont.tabIndex = 99999;
			cv.width = cont.clientWidth;
			cv.height = cont.clientHeight;
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
			self.img = new Image();
			self.img.onload = function() {
				if (self.mustFit) {
					self.fitMask();
					self.mustFit = 0;
				}
				self.redrawTxImage();
			};
			self.zoomCanvas = new ZoomCanvas(E('zoomCanvasDiv'));
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
	
	self.fitMask = function () {		
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
		self.tMatrix.scale(scale);
		self.tMatrix.translate(x, y);
	};
	
	self.fitImage = function() {
		// Calculates the scale factor to fit the image in canvas
		var cv = self._Canvas;
		var img = self.img;
		var sw = cv.width / img.width;
		var sh = cv.height / img.height;
		var scale = Math.min(sw, sh);

		// scaled image dimensions
		var iw = scale * img.width;
		var ih = scale * img.height;

		var x = (cv.width - iw) / 2;
		var y = (cv.height - ih) / 2;
		var yOrigin = 0;
		if (self.flipY)
			yOrigin = cv.height - 2 * y;
		self.tMatrix.reset(yOrigin);
		self.tMatrix.scale(scale);
		self.tMatrix.translate(x, y);
		
		// self.maskTx.reset(yOrigin);
		// self.maskTx.scale(1);
		// self.maskTx.translate(x+self.maskOffsetX, x+self.maskOffsetY);
	};

	self.showPositionInfo = function () {
        var maskAngleRad = self.maskTx.getRotAngle();
        
		var north = 90 - self.northAngle;		
		var angle = north + degrees(self.tMatrix.getRotAngle());

		var sx = self.xPscale;
		var sy = self.yPscale;
		
		var rxy = rotate(radians(north), -self.skyY*sy, -self.skyX*sx);
		
		var decDeg = self.centerDecDeg - rxy[0] / 3600;		
		
		var cosDec = Math.cos (radians(decDeg));
		cosDec = Math.max (cosDec, 1E-4);
		
		var raHrs = (self.centerRaDeg  - rxy[1] / 3600 / cosDec) / 15;				
			
        E('centerRAfd').value = toSexa(raHrs);
        E('centerDECfd').value = toSexa(decDeg);
        E('rotAngle').value = angle.toFixed(3);
        showMsg ('statusDiv', degrees(maskAngleRad)  + " " + north + " scale " + self.tMatrix.getScale());
	};
	
	self.drawCompass = function (ctx) {		
		
		function arrow (ctx, x0, y0, x1, y1, size) {
			var dx = x1 - x0;
			var dy = y1 - y0;
			
			var len = Math.sqrt(dx*dx + dy*dy);
			var dx0 = dx / len;
			var dy0 = dy / len;
			var pdx = -dy0;
			var pdy = dx0;
			
			var px0 = x1 - dx0 * size;
			var py0 = y1 - dy0 * size;
			var size2 = size/2;
			
			ctx.moveTo (x0, y0);
			ctx.lineTo (x1, y1);
			ctx.lineTo (px0 + pdx*size2, py0 + pdy*size2);
			ctx.lineTo (px0 - pdx*size2, py0 - pdy*size2);
			ctx.lineTo (x1, y1);
		}
		
		var color = '#ffff00';
		var rotAngleDeg = degrees(self.tMatrix.getRotAngle()) + 90 - self.northAngle;		
		var aRad = radians(rotAngleDeg);
		var ca = Math.cos(aRad);
		var sa = Math.sin(aRad);
		
		var x0 = 70;
		var y0 = 70;
		var len = 50;
		
		var north = rotate1 (sa, ca, 0, -len);
		var northText = rotate1 (sa, ca, 0, -len-10);
		var east = rotate1 (sa, ca, -len, 0);
		var eastText = rotate1 (sa, ca, -len-10, 0); 
		
		with (ctx) {
			setTransform (1, 0, 0, 1, 0, 0);			
			strokeStyle = color;	
			lineWidth = 1;
		
			beginPath();	
			arrow (ctx, x0, y0, x0+north[0], y0+north[1], 8);			
			arrow (ctx, x0, y0, x0+east[0], y0+east[1], 8);
			
			stroke();
			
			strokeText ('N', x0+northText[0], y0+northText[1]);
			strokeText ('E', x0+eastText[0], y0+eastText[1]);
		}
	};	

	self.reallyDrawTxImage = function () {		
	
		// Applies transform and redraws image.
		var cv = self._Canvas;
		var tx = self.tMatrix;
		var tp = tx.getTx(self.flipY);
		var scaleF = tx.getScale();
		
		var iwidth = self.img.width/2;
		var iheight = self.img.height/2;		
		
		with (self._Ctx) {
			setTransform(1, 0, 0, 1, 0, 0);
			clearRect(0, 0, cv.width, cv.height);			
			transform(tp[0], tp[1], tp[2], tp[3], tp[4], tp[5]);
		}
	
		self.filter.drawToOutputPart1 (self.img, self.skyX - iwidth, self.skyY - iheight);
	
		// Draw this after drawing the DSS/background image
		// because contrast filter is applied to the DSS/background image.
		var ctx2 = self.filter.tmpCtx2;
		with (ctx2) {
			// setTransform(1, 0, 0, 1, 0, 0);
			setTransform(tp[0], tp[1], tp[2], tp[3], tp[4], tp[5]);

			// transform(1, 0, 0, 1, self.maskOffsetX, self.maskOffsetY);
			var checker = self.drawMask(ctx2);
			
			self.drawTargets(ctx2, checker);			
		}
		
		self.filter.drawToOutputPart2 ();
		
		self.showPositionInfo();
		self.drawCompass(self.destCtx);
		 
	};

	self.redrawTxImage = function() {
		window.requestAnimationFrame (self.reallyDrawTxImage);
	};
	
	self.drawPolylines = function (ctx, lines, color, linewidth) {
		with (ctx) {
			strokeStyle = color;
			beginPath();
			var x0 = 0, y0 = 0;
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
	self.drawTargets = function(ctx, checker) {	
		function addTo (list, idx, x, y) {
			list.push (idx);
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
						self.selectedTargetIdx = i;
					}
				}
			}
		}
		
		function classify () {
			// Depending on if target is inside/outside, or selected, push it to
			// a different list to be displayed later.
			for (i = 0; i < len; ++i) {
				var x = xpos[i] + skyx;
				var y = ypos[i] + skyy;
				var pri = pcode[i];	
				if (pri == AlignBox) {
					if (showAlignBox)
						addTo (alignBoxIdx, i, x, y);
					continue;
				}
				if (showSelected && selected[i]) {
					if (checker.checkPoint (x, y)) 
						addTo (selectedInIdx, i, x, y);
					else
						addTo (selectedOutIdx, i, x, y);
					continue;
				}
				if (showByPriority && pri >= showPriority) {
					if (selected[i]) {
						if (checker.checkPoint (x, y)) 
							addTo (selectedInIdx, i, x, y);
						else
							addTo (selectedOutIdx, i, x, y);
						continue;
					}
					if (checker.checkPoint (x, y)) {
						addTo (showInIdx, i, x, y);
					}
					else {
						addTo (showOutIdx, i, x, y);
					}
					continue;
				}
			}
		}
		
		function calcSlitDisplayAngle () {
			var rotAngleDeg = degrees(self.tMatrix.getRotAngle()) + 90 - self.northAngle;		
			var aRad = -radians(rotAngleDeg);
			var ca = Math.cos(aRad);
			var sa = Math.sin(aRad);
			
			vec1 = rotate1(sa, ca, radiusX2, 0);
			vec2 = rotate1(sa, ca, 0, radiusX2);
		}
		
		function drawAlignBox (x, y) {
			// alignemtn box
			with (ctx) {
				moveTo(x - vec1[0] - vec2[0], y - vec1[1] - vec2[1]);
				lineTo(x + vec1[0] - vec2[0], y + vec1[1] - vec2[1]);
				lineTo(x + vec1[0] + vec2[0], y + vec1[1] + vec2[1]);
				lineTo(x - vec1[0] + vec2[0], y - vec1[1] + vec2[1]);
				lineTo(x - vec1[0] - vec2[0], y - vec1[1] - vec2[1]);
			}
			
			// ctx.moveTo(x - radius, y - radius);
			// ctx.rect(x - radius, y - radius, radiusX2, radiusX2);
		}

		function drawTarget (x, y) {
			with (ctx) {
				moveTo(x - vec1[0], y - vec1[1]);
				lineTo(x + vec1[0], y + vec1[1]);				
				// moveTo(x - vec2[0], y - vec2[1]);
				// lineTo(x + vec2[0], y + vec2[1]);
			}
		}
		
		function drawSelTarget (x, y) {
			with (ctx) {
				moveTo(x - vec1[0], y - vec1[1]);
				lineTo(x + vec1[0], y + vec1[1]);				
				moveTo(x - vec2[0], y - vec2[1]);
				lineTo(x + vec2[0], y + vec2[1]);
			}			
		}
		
		function drawClickedOn (x, y) {
			with (ctx) {
				arc (x, y, radiusX2, 0, 2*Math.PI);
			}
		}
		
		function drawList (tlist, color, fnc) {
			var idx;
			ctx.strokeStyle = color;
			ctx.beginPath();
			for (idx in tlist) {
				var i = tlist[idx];				
				var x = Math.floor(xpos[i] + skyx);
				var y = Math.floor(ypos[i] + skyy);
				fnc(x, y);
			}
			ctx.stroke();
		}
		
		var targets = self.targets;
		if (!targets)
			return;

		if (!targets.xpos)
			return;

		var xpos = targets.xpos;
		var ypos = targets.ypos;
		var selected = targets.select;
		var pcode = targets.pcode;
		var len = xpos.length;
				
		var selectedInIdx = [];
		var selectedOutIdx = []
		var showInIdx = [];
		var showOutIdx = [];
		var alignBoxIdx = [];
		
		var height2 = self._Canvas.height;
		var i;
		var radius = 2;
		var radiusX2 = radius * 2;
		var minDist = 1E10;
		
		var s = self.tMatrix.getScale();		
		var vec1 = [radius, 0];
		var vec2 = [0, radius];
		
		var skyx = self.skyX;
		var skyy = self.skyY;
        var showAll = E('showAll').checked;
        var showAlignBox = E('showAlignBox').checked;
        var showSelected = E('showSelected').checked;
        var showByPriority = E('showByPriority').checked;
        var showPriority = self.showMinPriority;
        
        if (showAll) {
        	showPriority = -1;
        	showByPriority = 1;
        	showSelected = 1;
        }
        
		if (s < 1) {
			radius = Math.min (15, radius/s);
			radiusX2 = radius * 2;
			ctx.lineWidth = Math.floor(1 / s + 1);
		} else {
			ctx.lineWidth = 1;
		}	
		
		calcSlitDisplayAngle ();
		classify();
		drawList (alignBoxIdx, '#ff0000', drawAlignBox);
		
		drawList (selectedInIdx, '#99ff99', drawSelTarget);
		drawList (showInIdx, '#99ff99', drawTarget);

		drawList (selectedOutIdx, '#ff0000', drawSelTarget);
		drawList (showOutIdx, '#ff0000', drawTarget);
		
		if (self.selectedTargetIdx >= 0) {
			radiusX2 = radiusX2 + 4;
			drawList([self.selectedTargetIdx], '#ffffff', drawClickedOn);
		}
	};	

	self.selectTarget = function (mx, my) {		
		var skyx = self.skyX;
		var skyy = self.skyY;
		var tmat = self.tMatrix;
		var xy = tmat.s2w (mx, my, 0);
		
		self.searchX = xy[0];
		self.searchY = xy[1];
		self.thold = Math.min(tmat.getScale() * 7, 5);
		
		var sIdx = self.selectedTargetIdx;
		if (sIdx >=0) {
			self.targetTable.markNormal (sIdx); 
		}
		self.selectedTargetIdx = -1;
		self.findIt = 1;	
		self.reallyDrawTxImage();
		self.findIt = 0;
		
		var i, row;
		var found = self.selectedTargetIdx;
		if (found >= 0) {
			self.targetTable.scrollTo (found);
			self.targetTable.highLight (found);
		}
	};
	
	self.clickedRow = function (evt) {
		var oldIdx = self.selectedTargetIdx;
		var tId = this.id;
		var idx = Number(tId.replace('target', ''));

		self.targetTable.markNormal (oldIdx);
		self.targetTable.highLight (idx);
		self.selectedTargetIdx = idx;
		self.reallyDrawTxImage();
	};
	
	self.drawMask = function(ctx) {
		function rotateP (mtx, layout) {
			var i;
			var tx = mtx.mat;
			var a = tx[0][0];
			var b = tx[0][1];
			var c = tx[1][0];
			var d = tx[1][1];
			var e = tx[0][2];
			var f = tx[1][2];			
			var out = Array();
			for (i in layout) {
				var row = layout[i];
				var x = (row[0]-rotX) * sx;
				var y = (row[1]-rotY) * sy;
				out.push([a * x + c * y+rotX, b * x + d * y+rotY, row[2]]);
			}
			return out;
		}
		
		var sx = 1.0/ self.xPscale;
		var sy = 1.0/ self.yPscale;
		var rotX = self.maskOffsetX;
		var rotY = self.maskOffsetY;		
		var mtx = self.maskTx;		

		var s = self.tMatrix.getScale();
		var lineWidth = 1;
		if (s < 1)
			lineWidth = 1.0 / s;
		
		var layout1 = rotateP(mtx, self.maskLayout);		
		var checker = InOutChecker (layout1);
		self.drawPolylines (ctx, layout1, self.maskColor, lineWidth);
		return checker;
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
			x : absLeft,
			y : absTop
		};
	};

	self.mouseUp = function(evt) {
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
			self.selectTarget (mx - ePos.x, my - ePos.y);
			self.zoomCanvas.update (self.destCtx, mx - ePos.x, my - ePos.y); 
		}
		return false;
	};

	self.mouseDown = function(evt) {
		evt = evt || window.event;
		evt.stopPropagation();
		evt.preventDefault();
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

	self.reportPxValue = function(mx, my) {
		var tmat = self.tMatrix;
		var xy = tmat.s2w (mx, my, 0);
		var sx = self.xPscale;
		var sy = self.yPscale;
		
		var rxy = rotate(radians(90-self.northAngle), (xy[1]-self.skyY)*sy, (xy[0]-self.skyX)*sx);
		
		var dec = self.centerDecDeg - (rxy[0]) / 3600;
		
		var cosDec = Math.cos (radians(dec));
		cosDec = Math.max (cosDec, 1E-4);
		
		var raHrs = (self.centerRaDeg - (rxy[1]) / 3600 / cosDec) / 15;
		while (raHrs > 24) raHrs -= 24;
		while (raHrs < 0) raHrs += 24;

		showMsg('mouseStatus', "RA hrs= " + toSexa(raHrs) + " DEC deg= "  + toSexa(dec) +
				" x=" + xy[0].toFixed(2) + " y=" + xy[1].toFixed(2));		
		
		self.zoomCanvas.update (self.destCtx, mx, my); 
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

	self.rotateAround = function (angRad) {
		//
		// Rotates sky around center of mask,
		// such that the remains at the same display position.
		//
		var tx = self.tMatrix;
		var xy = tx.w2s (self.maskOffsetX, self.maskOffsetY, false);		
		
		tx.rotate(angRad, xy[0], xy[1]);
	};
	
	self.rotateAll = function (ang) {
		// Rotates the image around center of canvas
		var tx = self.tMatrix;
		var cv = self._Canvas;
		var xc = cv.width / 2;
		var yc = cv.height / 2;
		tx.rotate(ang, xc, yc);
	};	
	
	self.panSky = function (dx, dy) {
		var tx = self.tMatrix;
		var cv = self._Canvas;
		var xc = cv.width / 2;
		var yc = cv.height / 2;
		var scale = tx.getScale();

		var mat = tx.mat;
		var a = mat[0][0];
		var b = mat[0][1];
		var c = mat[1][0];
		var d = mat[1][1];
		
		var ndx = a * dx + b * dy;
		var ndy = c * dx + d * dy;
		
		self.skyX += ndx / scale /scale;
		self.skyY += ndy /scale /scale;
	};

	self.rotateMask = function (ang) {
		// Rotates mask around center of canvas
		var tx = self.maskTx;

		var cv = self._Canvas;
		var xc = cv.width / 2;
		var yc = cv.height / 2;
		tx.rotate(ang, xc, yc);
	};
	
	self.mouseMove = function(evt) {
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
        if (!E('enableNav').checked)
            return;

		var tx = self.tMatrix;
		var cv = self._Canvas;
		var xc = cv.width / 2;
		var yc = cv.height / 2;
		var scale = tx.getScale();
		
		var newAngle = Math.atan2(my - yc - ePos.y, mx - xc - ePos.x);
		
		// shiftKey, ctrlKey, altKey
		if (evt.shiftKey) {
			self.rotateMask (-newAngle+self.baseAngle);
			// self.rotateAll(newAngle-self.baseAngle);
			self.rotateAround (newAngle-self.baseAngle);
		} else if (evt.ctrlKey) {
			self.rotateAll(newAngle-self.baseAngle);
		} else if (evt.altKey) {
			contrasting();
		} else {
			self.panSky(dx, dy);
		}

		self.redrawTxImage();
		self.lastmx = mx;
		self.lastmy = my;
		self.baseAngle = newAngle;
		return false;
	};

	self.mouseExit = function(evt) {
		self.dragging = 0;
	};

	self.moveLeft = function() {
		self.skyX -= 10;
	};

	self.moveRight = function() {
		self.skyX += 10;
	};

	self.moveUp = function() {
		self.skyY -= 10;
	};

	self.moveDown = function() {
		self.skyY += 10;
	};

	self.keypressed = function(evt) {
        if (!E('enableNav').checked)
            return;
        evt.preventDefault();
		var k = evt.key;
		switch (k) {
		case 'h':
			self.panAll(5, 0);
			break;
		case 'l':
			self.panAll(-5, 0);
			break;
		case 'j':
			self.panAll(0, 5);
			break;
		case 'k':
			self.panAll(0, -5);
			break;
		case '+':
		case '>':
		case '.':
			self.zoomAll (3);
			break;
		case '-':
		case '<':
		case ',':
			self.zoomAll (-3);
			break;
		default:	
			break;
		}
		self.redrawTxImage();
	};

	self.setMinPriority = function(mprio) {
		self.showMinPriority = Number(mprio);
	};

	self.show = function(imgUrl, flipY) {
		self.img.src = imgUrl;
		self.flipY = flipY;
	};

	self.fit = function() {
		self.mustFit = 1;
	};
	
	self.resetDisplay = function() {
		// Refit image and redraw
		if (!self.img)
			return;
		var maskAngleRad = self.maskTx.getRotAngle();
		// showMsg ('testDiv', "mask=" + self.maskTx.toString() + "sky=" +
		// self.tMatrix.toString());
		self.fitMask();
		self.rotateAround (-maskAngleRad);
		self.filter.setParams(1, 0);
		self.redrawTxImage();
	};
	
	self.resetOffsets = function() {
		/*
		 * SkyX, SkyY = position of the sky, The matrix tmatrix is for display
		 * only. The rotation in maskTx is the real rotation.
		 */
		self.skyX = 0;
		self.skyY = 0;		

		// var before = "mask=" + self.maskTx.toString() + "sky=" +
		// self.tMatrix.toString();

		var maskAngleRad = self.maskTx.getRotAngle();
		
		self.maskTx.reset(0);
		self.maskTx.scale(1);

		self.rotateAround (maskAngleRad);
		
		// var after = "mask=" + self.maskTx.toString() + "sky=" +
		// self.tMatrix.toString();
		// showMsg ('testDiv', "before " + before + "<br>after=" + after);
		
		self.redrawTxImage();
	};
	
	self.setTargets = function(targets) {
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
		self.targetTable = TargetTable (E('targetTableDiv'), targets);
		self.targetTable.setOnClickCB (self.clickedRow);
	};
	
	self.initialize();

	self.contElem.onmouseup = self.mouseUp;
	self.contElem.onmousedown = self.mouseDown;
	self.contElem.onmousemove = self.mouseMove;
	self.contElem.onmouseout = self.mouseExit;
	self.contElem.ondblclick = self.doubleClick;
	window.onkeypress = self.keypressed;

	return this;
}
