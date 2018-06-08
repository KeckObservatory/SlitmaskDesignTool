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
			self.setStatus('Please select target list file to load');
			return;
		}
		self.setStatus("Loading ...");

        var useDSS = E('useDSS').checked; 
        E('formUseDSS').value = useDSS ? 1:0;
		var form2 = E('form2');
		form2.submit();
	};

	self.loadBackgroundImage = function() {
		// This is the DSS image
		self.canvasShow.show('getDSSImage?r=' + Date.now(), 0);
	};

	self.loadTargets = function() {
		function dig2 (x) {
			if (x < 10) return '0' + x;
			return x;
		}
		function displayCB(data) {
			// Chained callback
			// dssPlatescale in arcsec/micron
			// xpsize in micron/pixel
			// xPscale in arcsec/pixel
			if (!data) return;
			self.dssInfo = data;
			var platescl = data['platescl']
			self.xPscale = platescl * data['xpsize'] / 1000;
			self.yPscale = platescl * data['ypsize'] / 1000;			
			self.setStatus("OK");
			var cs = self.canvasShow;
			
			cs.xPscale = self.xPscale;
			cs.yPscale = self.yPscale;
			cs.northAngle = data['northAngle']*1;
			cs.eastAngle = data['eastAngle']*1;
			cs.centerRaDeg = data['centerRADeg']*1;
			cs.centerDecDeg = data['centerDEC']*1;
			
			E('centerRAfd').value = cs.centerRaDeg / 15;
			E('centerDECfd').value = cs.centerDecDeg;
			
			self.resetDisplay();
			self.resetOffsets();
			
			var now = new Date();
			E('obsdatefd').value = now.getUTCFullYear() + '-' + dig2(now.getUTCMonth()+1) + '-' + dig2(now.getUTCDate());
		}

		function callback(data) {
			// Targets are here. 
			// Next, get more ROI info.

			var useDSS = E('useDSS').checked ? 1:0;
			self.targets = data;			
			self.setStatus("Drawing targets ...");
			E('minPriority').value = 0;
			self.canvasShow.setMinPriority(0);
			self.canvasShow.setTargets(self.targets);
			ajaxCall("getROIInfo", {
				'sid' : 0,
			}, displayCB);
		}
		ajaxCall("getTargets", {}, callback);
	};

	
	self.loadAll = function() {
		self.loadBackgroundImage();
		self.loadTargets();
	};

	self.redraw = function() {
		self.canvasShow.redrawTxImage();
	};

	self.resetDisplay = function() {
		// Refit and redraw
		self.setMinPcode ();
		self.canvasShow.resetDisplay();
	};

	self.resetOffsets = function() {
		self.setMinPcode ();
		self.canvasShow.resetOffsets();
	};
	
	self.setMinPcode = function() {
		var value = E('minPriority').value;
		self.canvasShow.setMinPriority(value);
		self.canvasShow.redrawTxImage();
	};

	self.showHideParams = function (evt) {
		var curr = this.value;
		var elm = E('paramTable');
		if (curr == 'Show Parameters') {
			this.value = 'Hide Parameters';
			with (elm.style) {
				visibility = 'visible';
				display = 'block';
			}
		} else {
			this.value = 'Show Parameters';
			with (elm.style) {
				visibility = 'hidden';
				display = 'none';
			}
		}
	};
	
	self.statusDiv = E('statusDiv');
	self.canvasShow = CanvasShow('canvasDiv');
	self.canvasShow.setMinPriority(E('minPriority').value);
	self.loadBackgroundImage();

	E('showHideParams').onclick = self.showHideParams;
	E('targetListFrame').onload = self.loadAll;
	E('loadTargets').onclick = self.loadParams;
	E('resetDisplay').onclick = self.resetDisplay;
	E('resetOffsets').onclick = self.resetOffsets;
	E('minPriority').onchange = self.setMinPcode;
    E('showAll').onchange = self.setMinPcode;
    E('showSelected').onchange = self.setMinPcode;
    E('showAlignBox').onchange = self.redraw;
    E('showByPriority').onchange = self.redraw;

	return this;
}
