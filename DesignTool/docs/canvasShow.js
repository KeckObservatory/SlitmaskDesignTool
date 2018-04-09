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
			mat[1][0] = c * cosa - d * sina;
			mat[1][1] = c * sina + d * cosa;

			mat[0][2] = e * cosa - f * sina + xc;
			mat[1][2] = e * sina + f * cosa + yc;
			return;
		}
	};

	self.getScale = function() {
		with (self) {
			var ca = (mat[0][0] + mat[1][1]) / 2;
			var sa = (mat[0][1] + mat[1][0]) / 2;
			var l = Math.hypot(ca, sa);
			return l;
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

	self.reset(0);
} // TxMatrix

//
// This is main function for the canvas show object.
//
function CanvasShow(containerName) {
	var self = this;

	// For displaying mouse-over values and cuts
	self.rawData = null;

	// Variables for mouse handling.
	self.anchorx = 0;
	self.anchory = 0;
	self.dragging = 0;
	self.fromX = 0;
	self.fromY = 0;
	self.mustFit = 1;

	self.showMaxPriority = 9999;

	self.scale = 1;
	self.tMatrix = new TxMatrix();
	self.xPscale = self.yPscale = 1;
	self.maskOfsetX = 130;
	self.maskOffsetY = 320;
	self.slitColor = '#FF0000';
	self.maskColor = '#8888FF';

	self.contElem = E(containerName);

	// End variables

	function E(n) {
		return document.getElementById(n);
	}

	function toggleSmoothing(ctx, onoff) {
		ctx.imageSmoothingEnabled = onoff;
		ctx.mozImageSmoothingEnabled = onoff;
		ctx.webkitImageSmoothingEnabled = onoff;
		ctx.msImageSmoothingEnabled = onoff;
	}
	;

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
		toggleSmoothing(self.tmpCtx, false);

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

		self.drawImage = function(img) {
			/*-
				Convenient function, applies the filter and draws the image on the output canvas.
				
				The image is first drawn on the temp canvas.
				Then it takes the pixels from the temp canvas and filters them and
				draws the result on the output canvas.
			 */

			// Applies transformation
			// self.tmpCanvas.width = self.tmpCanvas.width;
			// self.tmpCtx.drawImage(img, 0, 0, img.width, img.height);
			self.tmpCtx.drawImage(img, 0, 0);

			var imgData = self.tmpCtx.getImageData(0, 0, self.tmpCanvas.width,
					self.tmpCanvas.height);

			// Applies contrast
			self.applyScaleOffset(imgData.data, self.scale, self.offset);
			// Copies to output canvas
			self.outCtx.putImageData(imgData, 0, 0);
			self.scaledImageData = self.outCtx.getImageData(0, 0,
					self.tmpCanvas.width, self.tmpCanvas.height);
		};
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
			cv.width = cont.clientWidth;
			cv.height = cont.clientHeight;
			if (cv.width == 0 || cv.height == 0) {
				cv.width = cv.height = 400;
			}
			cont.replaceChild(cv, cont.childNodes[0]);
			ctx = cv.getContext("2d");
			ctx.scale(1, 1);
			toggleSmoothing(ctx, false);
			self.destCtx = ctx;
			self.filter = new Filter(ctx, cv.width, cv.height);
			self._Ctx = self.filter.tmpCtx;
			// Creates a hidden image element to store the source image.
			self.img = new Image();
			self.img.onload = function() {
				if (self.mustFit) {
					self.fitImage();
					self.mustFit = 0;
				}
				self.redrawTxImage(self.tMatrix);
			};
		} else {
			alert("Your browser does not support canvas\nPlease use another browser.");
		}
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
	};

	self.redrawTxImage = function(t) {
		// Applies transform and redraws image.
		var cv = self._Canvas;

		with (self._Ctx) {
			setTransform(1, 0, 0, 1, 0, 0);
			clearRect(0, 0, cv.width, cv.height);
			var tp = t.getTx(self.flipY);
			transform(tp[0], tp[1], tp[2], tp[3], tp[4], tp[5]);
		}

		self.filter.drawImage(self.img, 0, 0);

		// Draw this after drawing the DSS/background image
		// because contrast filter is applied to the DSS/background image.

		with (self.destCtx) {
			setTransform(1, 0, 0, 1, 0, 0);
			var tp = t.getTx(self.flipY);
			transform(tp[0], tp[1], tp[2], tp[3], tp[4], tp[5]);
			self.drawTargets(self.destCtx);
			transform(1, 0, 0, 1, 130, 320);
			self.drawMask(self.destCtx);
			setTransform(1, 0, 0, 1, 0, 0);
		}
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
	}

	self.mouseUp = function(evt) {
		evt = evt || window.event;
		evt.stopPropagation();
		evt.preventDefault();
		self.dragging = 0;
		return false;
	};

	self.mouseDown = function(evt) {
		evt = evt || window.event;
		evt.stopPropagation();
		evt.preventDefault();
		self.anchorx = evt.pageX;
		self.anchory = evt.pageY;
		self.dragging = 1;
		var cv = self._Canvas;
		var ePos = getAbsPosition(self.contElem);
		var xc = cv.width / 2 + ePos.x;
		var yc = cv.height / 2 + ePos.y;
		self.baseAngle = Math.atan2(self.anchory - yc, self.anchorx - xc);
		return false;
	};

	self.reportPxValue = function(mx, my) {
		if (!self.rawData)
			return;
		var tmat = self.tMatrix;
		var tx = tmat.getTx();
		var det = tx[0] * tx[3] - tx[1] * tx[2];
		var mx1 = mx - tx[4];
		var my1 = my - tx[5];
		var x = (mx1 * tx[3] - my1 * tx[2]) / det;
		var y = (-mx1 * tx[1] + my1 * tx[0]) / det;
		if (self.showPxValue) {
			self.showPxValue(x, y);
		}
		if (!self.rawData)
			return;
	};

	self.mouseMove = function(evt) {
		function zoom() {
			// Zooming
			var scale = Math.pow(1.01, -dy);
			tx.scaleCenter(scale, xc, yc);
		}
		function pan() {
			// Panning
			tx.translate(dx, dy);
		}
		function rotate() {
			// Rotates the image around center of canvas
			tx.rotate(newAngle - self.baseAngle, xc, yc);

		}
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

		var dx = mx - self.anchorx;
		var dy = my - self.anchory;
		var ePos = getAbsPosition(self.contElem);

		if (!self.dragging) {
			self.reportPxValue(mx - ePos.x, my - ePos.y);
			return;
		}

		var tx = self.tMatrix;
		var cv = self._Canvas;
		var xc = cv.width / 2;
		var yc = cv.height / 2;

		var newAngle = Math.atan2(my - yc - ePos.y, mx - xc - ePos.x);

		// shiftKey, ctrlKey, altKey
		if (evt.shiftKey) {
			zoom()
		} else if (evt.ctrlKey) {
			rotate();
		} else if (evt.altKey) {
			contrasting();
		} else {
			pan();
		}

		self.redrawTxImage(tx);
		self.anchorx = mx;
		self.anchory = my;
		self.baseAngle = newAngle;
		return false;
	};

	//
	// Draws targets according to options
	//
	self.drawTargets = function(ctx) {
		var targets = self.targets;
		if (!targets)
			return;

		var xpos = targets.xpos;
		var ypos = targets.ypos;
		var selected = targets.select;
		var pcode = targets.pcode;
		var len = xpos.length;
		var height2 = self._Canvas.height;
		var i;
		var PI2 = Math.PI * 2;
		var radius = 2;
		var radiusX2 = radius * 2;
		with (ctx) {
			strokeStyle = self.slitColor;
			var s = self.tMatrix.getScale();
			if (s < 1)
				lineWidth = Math.floor(1 / s + 1);
			else
				lineWidth = 1;
			E('statusDiv').innerHTML = s;
			beginPath();
			for (i = 0; i < len; ++i) {
				var x = xpos[i];
				var y = ypos[i];
				var pri = pcode[i];

				if (pri == -2) {
					moveTo(x - radius, y - radius);
					rect(x - radius, y - radius, radiusX2, radiusX2);
				} else { // if (pri > self.showMinPriority) {
					var sel = selected[i];
					// moveTo(x + radius, y);
					// arc (x, y, radius, 0, PI2);
					moveTo(x - radius, y);
					lineTo(x + radiusX2, y);
				}
			}
			stroke();
		}
	};

	self.drawMask = function(ctx) {
		var layout = [ [ 5.10, 453.74, 0 ], [ 6.16, 233.80, 1 ],
				[ 82.12, 161.63, 1 ], [ 244.82, 163.17, 1 ],
				[ 244.82, 455.51, 1 ], [ 0.00, 0.00, 2 ],
				[ 256.20, 455.87, 0 ], [ 256.20, 163.17, 1 ],
				[ 333.46, 165.54, 1 ], [ 363.08, 185.81, 1 ],
				[ 410.60, 207.38, 1 ], [ 452.20, 218.28, 1 ],
				[ 498.53, 221.83, 1 ], [ 498.53, 457.88, 1 ],
				[ 0.00, 0.00, 2 ], [ 510.26, 460.96, 0 ],
				[ 510.26, 225.27, 1 ], [ 552.92, 220.65, 1 ],
				[ 597.48, 207.73, 1 ], [ 631.49, 193.04, 1 ], ,
				[ 671.07, 168.86, 1 ], [ 752.59, 168.86, 1 ],
				[ 752.59, 460.37, 1 ], [ 0.00, 0.00, 2 ],
				[ 765.15, 464.52, 0 ], [ 765.15, 171.94, 1 ],
				[ 856.75, 171.94, 1 ], [ 1005.24, 318.17, 1 ],
				[ 1005.24, 464.76, 1 ], [ 0.00, 0.00, 2 ] ];
		var i;
		var xscale = self.xPscale;
		var yscale = self.yPscale;

		with (ctx) {
			strokeStyle = self.maskColor;
			var s = self.tMatrix.getScale();
			if (s < 1)
				lineWidth = Math.floor(1 / s + 1);
			else
				lineWidth = 1;
			beginPath();
			var x0 = 0, y0 = 0;
			for (i in layout) {
				var row = layout[i];
				var x = row[0] * xscale;
				var y = row[1] * yscale;
				var code = row[2];
				if (code == 0) {
					x0 = x;
					y0 = y;
					moveTo(x, y);
					continue;
				}
				if (code == 1) {
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

	self.mouseExit = function(evt) {
		self.dragging = 0;
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
		self.fitImage();
		self.filter.setParams(1, 0);
		self.redrawTxImage(self.tMatrix);
	};

	self.refreshImage = function() {
		// Same as redraw image, but no parameters
		self.redrawTxImage(self.tMatrix);
	};

	self.doubleClick = function(evt) {
		self.resetDisplay();
	};

	self.initialize();

	self.contElem.onmouseup = self.mouseUp;
	self.contElem.onmousedown = self.mouseDown;
	self.contElem.onmousemove = self.mouseMove;
	self.contElem.onmouseout = self.mouseExit;
	self.contElem.ondblclick = self.doubleClick;

	return this;
}
