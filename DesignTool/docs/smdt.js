/*
Main entry point for the Slitmask Design Tool.
Invoked by body.onload.
This module interfaces with the server,
while the canvasShow object renders the targets and the mask.
*/
function SlitmaskDesignTool() {
	var self = this;

	self.xAsPerPixel = 1;
	self.yAsPerPixel = 1;

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

	self.setStatus = function (msg) {
		self.statusDiv.innerHTML = msg;
	}

	self.sendTargets2Server = function () {
		// The browser loads the targets and sends them to the server.
		// The server responds with "OK". 
		// The targets are sent to the frame 'targetListFrame'.
		// That then triggers the onload event and loadAll() is invoked.

		var filename = E('targetList');
		if (!filename.value) {
			self.setStatus('Please select target list file to load');
			return;
		}
		self.setStatus("Loading ...");

		var form2 = E('form2');
		form2.submit();
	};

	self.loadBackgroundImage = function () {
		// This is the DSS image if requested
		// or a blank image, if no DSS.
		// The URL 'getDssImage' returns an image that is pushed to a <img>."
		//self.canvasShow.show('getDSSImage?r=' + Date.now(), 0);
		//self.canvasShow.redrawTxImage();
	};

	self.loadMaskLayout = function () {
		function callback(data) {
			self.canvasShow.setMaskLayout(data.mask, data.guiderFOV, data.badColumns);
			return;
		}

		ajaxCall("getMaskLayout", { 'instrument': 'deimos' }, callback);
	};

	self.buildParamTable = function (params) {
		// params
		var buf = Array();
		var row, i;
		var value, unit, label, descText;
		var txt;
		buf.push('<table id="paramTable">');
		for (i in params) {
			row = params[i];
			value = row[0];
			unit = row[1];
			label = row[2];
			descText = row[3];
			txt = '<tr><td>' +
				label + ':<td><input id="' + i + 'fd" value="' + value + '">' +
				'<td>' + descText;
			buf.push(txt);
		}
		buf.push('</table>');
		E('paramTableDiv').innerHTML = buf.join('');
	};

	self.updateLoadedTargets = function (data) {
		if (!data) return;

		self.targets = data.targets;
		self.dssInfo = data.info;

		self.setStatus("Drawing targets ...");
		E('minPriority').value = 0;
		
		// dssPlatescale in arcsec/micron
		// xpsize in micron/pixel
		var info = data.info;
		var platescl = info['platescl'] // arcsec/micron
		self.xAsPerPixel = platescl * info['xpsize'] / 1000; // arcsec/pixel
		self.yAsPerPixel = platescl * info['ypsize'] / 1000; // arcsec/pixel
		self.setStatus("OK");
		var cs = self.canvasShow;

		cs.xAsPerPixel = self.xAsPerPixel;
		cs.yAsPerPixel = self.yAsPerPixel;
		cs.northAngle = info['northAngle'] * 1;
		cs.eastAngle = info['eastAngle'] * 1;
		cs.centerRaDeg = info['centerRADeg'] * 1;
		cs.centerDecDeg = info['centerDEC'] * 1;
		cs.positionAngle = 0;
		cs.origPA = info['positionAngle'] * 1;
		cs.currRaDeg = cs.centerRaDeg;
		cs.currDecDeg = cs.centerDecDeg;

		cs.setShowPriorities(E('minPriority').value, E('maxPriority').value);
		cs.setTargets(self.targets);

		// E('inputRAfd').value = toSexagecimal(cs.centerRaDeg / 15);
		// E('inputDECfd').value = toSexagecimal(cs.centerDecDeg);

		cs.resetDisplay();
		cs.resetOffsets();
		self.redraw();
	};

	self.loadTargets = function () {
		ajaxCall("getTargetsAndInfo", {}, self.updateLoadedTargets);
	};

	self.loadConfigParams = function () {
		function callback(data) {
			self.buildParamTable(data.params);
		}
		ajaxCall('getConfigParams', {}, callback);
	};

	self.loadAll = function () {
		self.loadBackgroundImage();
		self.loadTargets();
		return false;
	};

	self.redraw = function () {
		self.canvasShow.redrawTxImage();
	};

	self.resetDisplay1 = function () {
		// Refit and redraw
		self.canvasShow.resetDisplay();
		self.redraw();
	};

	self.resetOffsets1 = function () {
		self.canvasShow.resetOffsets();
		self.redraw();
	};

	self.setMinPcode = function () {
		self.canvasShow.setShowPriorities(E('minPriority').value, E('maxPriority').value);
		self.canvasShow.redrawTxImage();
	};

	self.showHideParams = function (evt) {
		var curr = this.value;
		var elm = E('paramTableDiv');
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

	self.setMaskPA = function (evt) {
		var pa = Number(E('maskpafd').value);
		self.canvasShow.setMaskPA(pa);
	};

	self.setSlitsPA = function (evt) {
		var pa = Number(E('slitpafd').value);
		var tgs = self.canvasShow.targets;
		var ntgs = tgs.length1.length;
		var i;
		for (i = 0; i < ntgs; ++i) {
			tgs.slitPA[i] = pa;
		}
		self.canvasShow.reDrawTable();
		self.redraw();

		var colName = 'slitPA';
		var value = pa;
		var params = { 'colName': colName, 'value': value };
		ajaxPost('setColumnValue', params, function () { });
	};

	self.setSlitsLength = function (evt) {
		var halfLen = 0.5 * Number(E('minslitlengthfd').value);
		var tgs = self.canvasShow.targets;
		var ntgs = tgs.length1.length;
		var i;
		for (i = 0; i < ntgs; ++i) {
			tgs.length1[i] = halfLen;
			tgs.length2[i] = halfLen;
		}
		self.canvasShow.reDrawTable();
		self.redraw();

		var colName = 'length1';
		var value = halfLen;
		var params = { 'colName': colName, 'value': value };
		ajaxPost('setColumnValue', params, function () { });

		colName = 'length2';
		value = halfLen;
		params = { 'colName': colName, 'value': value };
		ajaxPost('setColumnValue', params, function () { });
	};

	self.setSlitsWidth = function (evt) {
		var width = Number(E('slitwidthfd').value);
		var tgs = self.canvasShow.targets;
		var ntgs = tgs.length1.length;
		var i;
		for (i = 0; i < ntgs; ++i) {
			tgs.slitWidth[i] = width;
		}
		self.canvasShow.reDrawTable();
		self.redraw();

		var colName = 'slitWidth';
		var value = pa;
		var params = { 'colName': colName, 'value': value };
		ajaxPost('setColumnValue', params, function () { });
	};

	self.recalculateMaskHelper = function (callback) {
		// Send targets that are inside mask to server.
		// Retrieve selected mask information and display.
		var cs = self.canvasShow;
		if (!cs) {
			alert("No targets available");
			return;
		}
		cs.centerRaDeg = cs.currRaDeg;
		cs.centerDecDeg = cs.currDecDeg;

		var minSepAs = E('minslitseparationfd').value;
		var minSlitLengthAs = E('minslitlengthfd').value;
		var boxSizeAs = E('alignboxsizefd').value;

		var params = {
			'insideTargets': cs.insideTargetsIdx,
			'currRaDeg': cs.currRaDeg, 'currDecDeg': cs.currDecDeg,
			'currAngleDeg': cs.positionAngle + cs.origPA,
			'minSepAs': minSepAs,
			'minSlitLengthAs': minSlitLengthAs,
			'boxSize': boxSizeAs
		};
		var ajax = new AjaxClass();
		ajax.postRequest('recalculateMask', params, callback);
	};

	self.recalculateMask = function (evt) {
		function callback(data) {			
			self.canvasShow.slitsReady = false;
			if (!data) return;
			if (!data.targets) return;

			self.canvasShow.slitsReady = true;
			self.updateLoadedTargets (data);
		}
		self.recalculateMaskHelper(callback);
	};

	self.updateTarget = function (evt) {
		var idx = self.canvasShow.selectedTargetIdx;
		var prior = Number(E('targetPrior').value);
		var selected = Number(E('targetSelect').value);
		var slitLPA = Number(E('targetSlitPA').value);
		var slitWidth = Number(E('targetSlitWidth').value);
		var length1 = Number(E('targetLength1').value);
		var length2 = Number(E('targetLength2').value);

		var params = {
			'idx': idx, 'prior': prior, 'selected': selected, 'slitLPA': slitLPA, 'slitWidth': slitWidth,
			'len1': length1, 'len2': length2
		};
		var ajax = new AjaxClass();
		ajax.sendRequest('updateTarget', { 'values': JSON.stringify(params) }, function (data) {return;});
		self.canvasShow.updateTarget();
	};

	self.saveMDF = function (evt) {
		function callSave() {
			if (done < 10) {
				if (flag != 0) {
					done = 10;
					var mdFile = E('outputfitsfd').value;
					window.open('saveMaskDesignFile?mdFile=' + mdFile);
				}
				else {
					done += 1;
					setTimeout(callSave, 1000);
				}
			}
		}

		function callback(data) {
			self.targets = data;
			self.canvasShow.setShowPriorities(E('minPriority').value, E('maxPriority').value);
			self.canvasShow.setTargets(data);
			self.redraw();
			flag = 1;
		}
		self.recalculateMaskHelper(callback);
		var flag = 0, done = 0;
		setTimeout(callSave, 1000);
	};

	self.checkQuit = function () {
		ajaxCall("quit", {}, function () { });
		return "Quit";
	};

	window.onbeforeunload = self.checkQuit

	self.statusDiv = E('statusDiv');
	self.canvasShow = new CanvasShow('canvasDiv', 'zoomCanvasDiv');
	self.canvasShow.setShowPriorities(E('minPriority').value, E('maxPriority').value);
	self.loadConfigParams();
	self.loadMaskLayout();
	self.loadBackgroundImage();

	E('showHideParams').onclick = self.showHideParams;
	E('targetListFrame').onload = self.loadAll;
	E('loadTargets').onclick = self.sendTargets2Server;
	E('resetDisplay').onclick = self.resetDisplay1;
	E('resetOffsets').onclick = self.resetOffsets1;
	E('minPriority').onchange = self.setMinPcode;
	E('maxPriority').onchange = self.setMinPcode;

	E('showAll').onchange = self.setMinPcode;
	E('showSelected').onchange = self.setMinPcode;
	E('showAlignBox').onchange = self.redraw;
	E('showGuideBox').onchange = self.redraw;
	E('showByPriority').onchange = self.redraw;

	E('setSlitsPA').onclick = self.setSlitsPA;
	E('setMaskPA').onclick = self.setMaskPA;
	E('setSlitsLength').onclick = self.setSlitsLength;
	E('setSlitsWidth').onclick = self.setSlitsWidth;

	E('recalculateMask').onclick = self.recalculateMask;

	E('updateTarget').onclick = self.updateTarget;
	E('saveMDF').onclick = self.saveMDF;


	return this;
}
