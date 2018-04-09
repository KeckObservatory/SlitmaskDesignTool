function SlitmaskDesignTool() {
	var self = this;

	self.xPscale = 1;
	self.yPscale = 1;

	function E(n) {
		return document.getElementById(n);
	}

	function guid() {
		function s4() {
			return Math.floor((1 + Math.random()) * 0x10000).toString(16)
					.substring(1);
		}
		return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4()
				+ s4() + s4();
	}

	self.setStatus = function(msg) {
		self.statusDiv.innerHTML = msg;
	}

	function callback(data) {
		alert('got ' + data);
		return;
	}

	self.loadParams = function() {
		var filename = E('targetList');
		if (!filename.value) {
			self.setStatus('Please select parameter file to load');
			return;
		}
		self.setStatus("Loading ...");
		var form2 = E('form2');
		form2.submit();
	};

	self.loadBackgroundImage = function() {
		// This is the DSS image
		self.canvasShow.show('getDSSImage?r=' + Date.now(), 0);
	};

	self.loadTargets = function() {
		function displayCB(data) {
			// Chained callback
			// dssPlatescale in arcsec/micron
			// xpsize in micron/pixel
			// xPscale in arcsec/pixel
			self.dssInfo = data;
			var platescl = data['platescl']
			self.xPscale = platescl * data['xpsize'] / 1000;
			self.yPscale = platescl * data['ypsize'] / 1000;
			self.setStatus("OK");
			self.canvasShow.xPscale = self.xPscale;
			self.canvasShow.yPscale = self.yPscale;
			self.resetDisplay();
			E('centerRAfd').value = data['centerRADeg'];
			E('centerDECfd').value = data['centerDEC'];
		}

		function callback(data) {
			// Targets are here. 
			// Next, get more ROI info.
			self.targets = data;
			self.setStatus("Drawing targets ...");
			self.canvasShow.targets = self.targets;
			ajaxCall("getROIInfo", {
				'sid' : 0
			}, displayCB);
		}
		ajaxCall("getTargets", {}, callback);
	};

	self.redraw = function() {
		self.loadBackgroundImage();
		self.loadTargets();
	};

	self.resetDisplay = function() {
		// Refit and redraw
		self.canvasShow.resetDisplay();
	};

	self.setMinPcode = function() {
		var value = E('minPriority').value;
		self.canvasShow.setMinPriority(value);
		self.canvasShow.refreshImage();
	};

	self.statuDiv = E('statusDiv');
	self.canvasShow = CanvasShow('canvasDiv');
	self.loadBackgroundImage();

	E('targetListFrame').onload = self.redraw;

	E('loadParams').onclick = self.loadParams;
	E('resetDisplay').onclick = self.resetDisplay;
	E('minPriority').onchange = self.setMinPcode;

	E('quit').onclick = function() {
		ajaxCall('./quit', {}, callback);
	};

}
