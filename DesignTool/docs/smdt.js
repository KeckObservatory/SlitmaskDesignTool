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

	self.loadParams = function() {
		var filename = E('targetList');
		if (!filename.value) {
			self.setStatus('Please select target list file to load');
			return;
		}
		self.setStatus("Loading ...");

		var useDSS = E('useDSS');
		if (useDSS) {			 
			E('formUseDSS').value = useDSS.checked ? 1 : 0;
		}
        //E('formUseDSS').value = 0;
		var form2 = E('form2');
		form2.submit();
	};

	self.loadBackgroundImage = function() {
		// This is the DSS image
		self.canvasShow.show('getDSSImage?r=' + Date.now(), 0);
	};

	self.loadMaskLayout = function () {
		function callback (data) {
			self.canvasShow.setMaskLayout (data);
			return;
		}

		ajaxCall("getMaskLayout", {'instrument': 'deimos'}, callback);
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
			var platescl = data['platescl'] // arcsec/micron
			self.xPscale = platescl * data['xpsize'] / 1000; // arcsec/pixel
			self.yPscale = platescl * data['ypsize'] / 1000; // arcsec/pixel
			self.setStatus("OK");
			var cs = self.canvasShow;
			
			cs.xPscale = self.xPscale;
			cs.yPscale = self.yPscale;
			cs.northAngle = data['northAngle']*1;
			cs.eastAngle = data['eastAngle']*1;
			cs.centerRaDeg = data['centerRADeg']*1;
			cs.centerDecDeg = data['centerDEC']*1;
			cs.positionAngle = cs.origPA = data['positionAngle']*1;
			cs.useDSS = data['useDSS']*1
			cs.currRaDeg = cs.centerRaDeg;
			cs.currDecDeg = cs.centerDecDeg;
			
			E('inputRAfd').value = cs.centerRaDeg / 15;
			E('inputDECfd').value = cs.centerDecDeg;
			
			cs.resetDisplay();
			cs.resetOffsets();
			self.redraw ();
			
			var now = new Date();
			E('obsdatefd').value = now.getUTCFullYear() + '-' + dig2(now.getUTCMonth()+1) + '-' + dig2(now.getUTCDate());
		}

		function callback(data) {
			// Targets are here. 
			// Next, get more ROI info.

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
		E('showPreview').checked = true;
		self.loadMaskLayout();
		self.loadBackgroundImage();
		self.loadTargets();
		return false;
	};

	self.redraw = function() {
		self.canvasShow.redrawTxImage();
	};

	self.resetDisplay1 = function() {
		// Refit and redraw
		//self.setMinPcode ();
		self.canvasShow.resetDisplay();
		self.redraw();
	};

	self.resetOffsets1 = function() {
		//self.setMinPcode ();
		self.canvasShow.resetOffsets();
		self.redraw();
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
	
	self.recalculateMask = function (evt) {
		function callback (data) {
			self.targets = data;
			self.canvasShow.setMinPriority(0);
			self.canvasShow.setTargets(data);
			self.resetOffsets1();
		}
		// Send targets that are inside mask to server.
		// Retrieve selected mask information and display.
		var cs = self.canvasShow;
		if (!cs) {
			alert ("No targets available");
			return;
		}
		cs.centerRaDeg = cs.currRaDeg;
		cs.centerDecDeg = cs.currDecDeg;
		cs.positionAngle = cs.currAngleDeg;

		E('showSlitPos').checked = true;
		var params = {'insideTargets' : cs.insideTargetsIdx,
				'currRaDeg' : cs.currRaDeg, 'currDecDeg' : cs.currDecDeg,
				'currAngleDeg': cs.currAngleDeg};
		ajaxPost ('recalculateMask', params, callback);
	};
	
	self.updateTarget = function (evt) {
		var idx = self.canvasShow.selectedTargetIdx;
		var prior = Number(E('targetPrior').value);
		var selected = Number(E('targetSelect').value);
		var slitPA = Number(E('targetSlitPA').value);
		var slitWidth = Number(E('targetSlitWidth').value);
		var length1 = Number(E('targetLength1').value);
		var length2 = Number(E('targetLength2').value);
		
		var params = {'idx': idx, 'prior' : prior, 'selected' : selected, 'slitPA': slitPA, 'slitWidth' : slitWidth,
				'len1': length1, 'len2': length2};
		ajaxPost ('updateTarget', {'values':JSON.stringify(params)}, function(){});
		self.canvasShow.updateTarget ();
	};
	
	self.statusDiv = E('statusDiv');
	self.canvasShow = new CanvasShow('canvasDiv', 'zoomCanvasDiv');
	self.canvasShow.setMinPriority(E('minPriority').value);
	self.loadBackgroundImage();
	
	E('enableSelection').checked = true;
	E('showHideParams').onclick = self.showHideParams;
	E('targetListFrame').onload = self.loadAll;
	E('loadTargets').onclick = self.loadParams;
	E('resetDisplay').onclick = self.resetDisplay1;
	E('resetOffsets').onclick = self.resetOffsets1;
	E('minPriority').onchange = self.setMinPcode;
	
    E('showAll').onchange = self.setMinPcode;
    E('showSelected').onchange = self.setMinPcode;
    E('showAlignBox').onchange = self.redraw;
    E('showByPriority').onchange = self.redraw;
    E('showSlitPos').onchange = self.redraw;
    E('showPreview').onchange = self.redraw;
    
    
    E('recalculateMask').onclick = self.recalculateMask;
	
	E('updateTarget').onclick = self.updateTarget;

	return this;
}
