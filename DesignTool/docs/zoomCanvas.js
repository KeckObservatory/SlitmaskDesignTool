function ZoomCanvas(container) {
	var self = this;
	
	function toggleSmoothing(ctx, onoff) {
		ctx.imageSmoothingEnabled = onoff;
		//ctx.mozImageSmoothingEnabled = onoff;
		ctx.webkitImageSmoothingEnabled = onoff;
		ctx.msImageSmoothingEnabled = onoff;
	}	

	
	self.initialize = function () {
		var cv = document.createElement("canvas");
		if (cv.getContext) {
			self._Canvas = cv;
			cv.tabIndex = 99998;
			container.tabIndex = 99998;
			cv.width = container.clientWidth;
			cv.height = container.clientHeight;
			if (cv.width == 0 || cv.height == 0) {
				cv.width = cv.height = 250;
			}
			container.replaceChild(cv, container.childNodes[0]);
			var ctx = cv.getContext ('2d');

			toggleSmoothing(ctx, false);
		
			self._zoomCtx = ctx;
			
			self.tmpCanvas = document.createElement("canvas");
			self.tmpCanvas.width = cv.width;
			self.tmpCanvas.height = cv.height;
			self.tmpCtx = self.tmpCanvas.getContext("2d");
			toggleSmoothing(self.tmpCtx, false);
		}
		else {
			alert("Your brower does not support canvas\nPlease use another browser.");
		}
	};
	
	self.update = function (sourceCtx, x, y) {	
		var cv = self._Canvas;
		var factor = 4;
		var w = Math.floor(cv.width/factor);
		var h = Math.floor(cv.height/factor);
		var x0 = x - w/2;
		var y0 = y - h/2;
		
		var imgData = sourceCtx.getImageData (x0, y0, w, h);

		self.tmpCtx.putImageData(imgData, 0, 0);

		self._zoomCtx.clearRect(0, 0, cv.width, cv.height);	
		self._zoomCtx.setTransform (factor, 0, 0, factor, 0, 0);
		self._zoomCtx.drawImage(self.tmpCanvas, 0, 0);
		
	};
	
	self.initialize ();
	
	return this;
}