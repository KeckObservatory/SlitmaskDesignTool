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
	self.dirtyFlag = 0;
	self.sessId = false;

	function sexa2deg(sexa) {
		let parts = sexa.split(":");
		let dd = Number(parts[0]);
		let mm = Number(parts[1]) / 60;
		let ss = Number(parts[2]) / 3600;
		return dd + mm + ss;
	}

	function E(n) {
		``
		return document.getElementById(n);
	}

	function guid() {
		function s4() {
			return Math.floor((1 + Math.random()) * 0x10000).toString(16)
				.substring(1);
		}
		return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() +
			s4() + s4();
	}

	function array2Query(arr) {
		let buf = new Array();
		for (idx in arr) {
			buf.push(idx + "=" + arr[idx]);
		}
		return buf.join("&");
	}

	self.remoteCall = function (command, params, callback) {
		let options = { method: 'POST', body: array2Query(params) }
		//fetch(command, options).then(resp => resp.json()).then(data => callback(data));
		fetch(command, options).then(resp => resp.json()).then(callback);
	};

	self.remoteCallDirty = function (command, params, callback) {
		self.dirtyFlag = 1;
		params["sessId"] = self.sessId;
		self.remoteCall(command, params, callback);
	};

	self.setStatus = function (msg) {
		self.statusDiv.innerHTML = msg;
	};

	self.sendTargets2Server = function () {
		// The browser loads the targets and sends them to the server.
		// The server responds with "OK". 
		// The targets are sent to the frame 'targetListFrame'.
		// That then triggers the onload event and loadAll() is invoked.

		let filename = E('targetList');
		if (!filename.value) {
			self.setStatus('Please select target list file to load');
			return;
		}
		self.setStatus("Loading ...");

		let form2 = E('form2');
		E("sessId").value = self.sessId;
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

		self.remoteCallDirty("getMaskLayout", {
			'instrument': 'deimos'
		}, callback);
	};

	self.buildParamTable = function (params) {
		// params
		let buf = Array();
		let row, i;
		let value, unit, label, descText;
		let txt;
		buf.push('<table id="paramTable">');
		for (i in params) {
			row = params[i];
			value = row[0];
			unit = row[1];
			label = row[2];
			descText = row[3];
			txt = `<tr><td> ${label} :<td><input id="${i}fd" name="${i}fd" value="${value}"><td>${descText}`;
			/* 
			txt = '<tr><td>' +
				label + ':<td><input id="' + i + 'fd" value="' + value + '">' +
				'<td>' + descText;
			*/
			buf.push(txt);
		}
		buf.push('</table>');
		E('paramTableDiv').innerHTML = buf.join('');
	};

	self.updateLoadedTargets = function (data) {
		// Called when targets are loaded from server
		if (!data) return;

		self.targets = data.targets;
		self.dssInfo = data.info;

		self.setStatus("Drawing targets ...");
		E('minPriority').value = 0;

		// dssPlatescale in arcsec/micron
		// xpsize in micron/pixel
		let info = data.info;
		let platescl = info['platescl'] // arcsec/micron
		self.xAsPerPixel = platescl * info['xpsize'] / 1000; // arcsec/pixel
		self.yAsPerPixel = platescl * info['ypsize'] / 1000; // arcsec/pixel
		self.setStatus("OK");
		let cs = self.canvasShow;

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
		cs.setGaps(data.xgaps);
		// E('inputRAfd').value = toSexagecimal(cs.centerRaDeg / 15);
		// E('inputDECfd').value = toSexagecimal(cs.centerDecDeg);

		cs.resetDisplay();
		cs.resetOffsets();
		self.redraw();
		self.canvasShow.selectTargetByIndex(self.canvasShow.selectedTargetIdx);
	};

	self.reloadTargets = function (newIdx) {
		function callback(data) {
			self.updateLoadedTargets(data);
			self.canvasShow.selectTargetByIndex(newIdx);
		}

		self.remoteCallDirty("getTargetsAndInfo", {}, callback);
	};

	self.getSessId = function (callThis) {
		function callback(data) {
			self.sessId = data.sessId;
			callThis();
		}
		self.remoteCall('getNewSession', { "sessId": 0 }, callback);
	};

	self.loadConfigParams = function () {
		function callback(data) {
			self.buildParamTable(data.params);
		}
		self.remoteCallDirty('getConfigParams', {}, callback);
	};

	self.loadAll = function () {
		self.loadBackgroundImage();
		self.canvasShow.clearTargetSelection();
		self.canvasShow.slitsReady = false;
		self.reloadTargets(0);
	};

	self.redraw = function () {
		self.canvasShow.redrawTxImage();
		if (self.dirtyFlag) {
			E('recalculateMask').style.backgroundColor = "#ffaaaa";
		} else {
			E('recalculateMask').style.backgroundColor = "#bbbbbb";
		}
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
		self.redraw()
	};

	self.showHideParams = function (evt) {
		let curr = this.value;
		let elm = E('paramTableDiv');
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
		self.setCenterRADEC(evt);
	};

	self.setSlitsPA = function (evt) {
		let pa = Number(E('slitpafd').value);
		let tgs = self.canvasShow.targets;
		let ntgs = tgs.length1.length;
		let i;
		for (i = 0; i < ntgs; ++i) {
			if (tgs.pcode[i] <= 0) continue;
			tgs.slitLPA[i] = pa;
		}
		self.canvasShow.reDrawTable();
		self.redraw();

		let colName = 'slitLPA';
		let value = pa;
		let params = {
			'colName': colName,
			'value': value,
			'avalue': value
		};
		self.remoteCallDirty('setColumnValue', params, function () { });
		return false;
	};

	self.setSlitsLength = function (evt) {
		let asize = Number(E('alignboxsizefd').value);
		let ahalf = 0.5 * asize;
		let halfLen = 0.5 * Number(E('minslitlengthfd').value);
		let tgs = self.canvasShow.targets;
		let ntgs = tgs.length1.length;
		let i;
		for (i = 0; i < ntgs; ++i) {
			if (tgs.pcode[i] <= 0) {
				tgs.length1[i] = ahalf;
				tgs.length2[i] = ahalf;
			} else {
				tgs.length1[i] = halfLen;
				tgs.length2[i] = halfLen;
			}
		}
		self.canvasShow.reDrawTable();
		self.redraw();

		let colName = 'length1';
		let value = halfLen;
		let params = {
			'colName': colName,
			'value': value,
			'avalue': ahalf
		};
		self.remoteCallDirty('setColumnValue', params, function () { });

		colName = 'length2';
		value = halfLen;
		params = {
			'colName': colName,
			'value': value,
			'avalue': ahalf
		};
		self.remoteCallDirty('setColumnValue', params, function () { });
		return false;
	};

	self.setSlitsWidth = function (evt) {
		let width = Number(E('slitwidthfd').value);
		let tgs = self.canvasShow.targets;
		let ntgs = tgs.length1.length;
		let i;
		for (i = 0; i < ntgs; ++i) {
			if (tgs.pcode[i] <= 0) continue;
			tgs.slitWidth[i] = width;
		}
		self.canvasShow.reDrawTable();
		self.redraw();

		let colName = 'slitWidth';
		let value = width;
		let params = {
			'colName': colName,
			'value': value,
			'avalue': value
		};
		self.remoteCallDirty('setColumnValue', params, function () { });
		return false;
	};

	self.setCenterRADEC = function (evt) {
		function callback(data) {
			self.reloadTargets(self.selectedTargetIdx);
		}
		let raSexa = E('inputrafd').value;
		let decSexa = E('inputdecfd').value;

		let raDeg = sexa2deg(raSexa) * 15;
		let decDeg = sexa2deg(decSexa);
		let paDeg = Number(E('maskpafd').value);

		if (isNaN(raDeg) || isNaN(decDeg)) {
			alert("Invalid inpuit");
			return;
		}

		self.remoteCallDirty("setCenterRADEC", {
			"raDeg": raDeg,
			"decDeg": decDeg,
			'paDeg': paDeg
		}, callback);
		return false;
	};

	self.clearSelection = function (evt) {
		let tgs = self.canvasShow.targets;
		let ntgs = tgs.length1.length;
		let i;
		for (i = 0; i < ntgs; ++i) {
			if (tgs.pcode[i] <= 0) continue;
			tgs.selected[i] = 0;
		}
		self.canvasShow.reDrawTable();
		self.canvasShow.slitsReady = false;
		self.redraw();

		let colName = 'selected';
		let params = {
			'colName': colName,
			'value': 0,
			'avalue': 0
		};
		self.remoteCallDirty('setColumnValue', params, function () { });
	};

	self.recalculateMaskHelper = function (callback) {
		// Send targets that are inside mask to server.
		// Retrieve selected mask information and display.
		let cs = self.canvasShow;
		if (!cs) {
			alert("No targets available");
			return;
		}
		cs.centerRaDeg = cs.currRaDeg;
		cs.centerDecDeg = cs.currDecDeg;

		let minSepAs = E('minslitseparationfd').value;
		let minSlitLengthAs = E('minslitlengthfd').value;
		let boxSizeAs = E('alignboxsizefd').value;
		let extendSlits = E('extendSlits').checked ? 1 : 0;

		let params = {
			'currRaDeg': cs.currRaDeg,
			'currDecDeg': cs.currDecDeg,
			'currAngleDeg': cs.positionAngle + cs.origPA,
			'minSepAs': minSepAs,
			'minSlitLengthAs': minSlitLengthAs,
			'boxSize': boxSizeAs,
			'extendSlits': extendSlits
		};

		self.setStatus("Recalculating ...");
		self.remoteCallDirty('recalculateMask', params, callback);
	};

	self.recalculateMask = function (evt) {
		function callback(data) {
			self.canvasShow.slitsReady = false;
			let msg = "No data returned, recalculate failed";
			if (data && data.targets) {
				self.dirtyFlag = 0;
				self.canvasShow.slitsReady = true;
				self.updateLoadedTargets(data);
				msg = "OK";
			}
			self.setStatus(msg);
		}
		self.recalculateMaskHelper(callback);
	};

	self.updateTarget = function (evt) {
		// Updates an existing or adds a new target.
		function callback(data) {
			let i = idx;
			if (data && data.length > 0)
				i = data[0]
			self.reloadTargets(idx, i);
			self.canvasShow.selectedTargetIdx = i;
		}
		// Sends new target info to server
		let idx = self.canvasShow.selectedTargetIdx;
		let prior = Number(E('targetPrior').value);
		let selected = Number(E('targetSelect').value);
		let slitLPA = Number(E('targetSlitPA').value);
		let slitWidth = Number(E('targetSlitWidth').value);
		let length1 = Number(E('targetLength1').value);
		let length2 = Number(E('targetLength2').value);
		let tname = E("targetName").value;
		let targetRA = E("targetRA").value;
		let targetDEC = E("targetDEC").value;
		let targetMagn = E("targetMagn").value;
		let targetBand = E('targetBand').value;

		let params = {
			'idx': idx,
			'raSexa': targetRA,
			'decSexa': targetDEC,
			'eqx': 2000,
			'mag': targetMagn,
			'pBand': targetBand,
			'prior': prior,
			'selected': selected,
			'slitLPA': slitLPA,
			'slitWidth': slitWidth,
			'len1': length1,
			'len2': length2,
			'targetName': tname
		};

		self.remoteCallDirty('updateTarget', {
			'values': JSON.stringify(params)
		}, callback);
	};

	self.deleteTarget = function (evt) {
		function callback() {
			self.reloadTargets(idx, 0);
		}

		let idx = self.canvasShow.selectedTargetIdx;
		if (idx < 0) return;
		let params = {
			'idx': idx
		};

		self.remoteCallDirty("deleteTarget", params, callback);
	};

	self.showDiv = function (divname, cont) {
		//
		// Shows dialog box
		//
		let elem = E(divname);

		elem.style.display = "block";
		elem.style.position = "absolute";
		elem.style.visibility = "visible";

		let button = "<br><input type='button' value='Close' id='closeBt'>";
		elem.innerHTML = cont + button;
		let w = document.body.clientWidth;
		let h = document.body.clientWidth;
		let w1 = elem.offsetWidth;
		let h1 = elem.offsetHeight;
		let x1 = document.body.scrollLeft + (w - w1) / 2;
		let y1 = document.body.scrollTop + (h - h1) / 2;
		elem.style.left = "500px";
		elem.style.top = "500px";

		let closeBt = E('closeBt');
		if (closeBt)
			closeBt.onclick = function (evt) {
				self.hideDiv(divname);
			};
	};

	self.hideDiv = function (divname) {
		let elem = E(divname);
		let s = elem.style;
		s.display = "none";
		s.visibility = "hidden";
	};

	self.saveMDF = function (evt) {
		function callbackSave(data) {
			let fname = data['fitsname'];
			let lname = data['listname']
			let path = data['path'];
			let errstr = data['errstr'];
			let fbackup = data['fbackup'];
			let lbackup = data['lbackup'];
			self.setStatus("OK");

			if (errstr != "OK") {
				alert(`Failed to save mask design ${mdFile}`);
				self.setStatus("Failed to save mask design");
				return;
			}
			let fbstr = "";
			if (fbackup != null) {
				fbstr = `<br>Backup file:  <b>${fbackup}</b>`;
			}
			let lbstr = "";
			if (lbackup != null) {
				lbstr = `<br>Backup file: <b>${lbackup}</b>`;
			}
			let fstr = `Fits file<br><b>${fname}</b> successfully saved to <b>${path}</b> ${fbstr}`;
			let lstr = `Target list<br><b>${lname}</b> successfully saved to <b>${path}</b> ${lbstr}`;

			self.showDiv("savePopup", `${fstr}<br><br>${lstr}`);
			self.dirtyFlag = 0;

		}

		function callback(data) {
			self.canvasShow.slitsReady = false;
			let msg = "No returned, recalculate failed";
			if (data && data.targets) {
				self.dirtyFlag = 0;
				self.canvasShow.slitsReady = true;
				self.updateLoadedTargets(data);
				msg = "OK";
			}
			self.setStatus(msg);

			let mdFile = E('outputfitsfd').value;
			let params = {
				'mdFile': mdFile
			};
			self.remoteCall("downloadMDF", params, downloadCB); self.remoteCallDirty("saveMaskDesignFile", params, callbackSave);
		}

		self.recalculateMaskHelper(callback);
	};

	function splitArgs() {
		var parts = window.location.search.replace('?', '').split("&");
		var out = Array();
		for (arg in parts) {
			var twoparts = parts[arg].split('=');
			out[twoparts[0]] = twoparts[1];
		}
		return out;
	} // splitArgs	

	self.checkQuit = function () {
		let args = splitArgs();
		if (!args["quit"]) return;

		self.remoteCallDirty("quit", {}, function () { });
		return "Quit";
	};

	window.onbeforeunload = self.checkQuit

	self.statusDiv = E('statusDiv');
	self.centerStatusDiv = E('centerStatusDiv');
	self.canvasShow = new CanvasShow('canvasDiv', 'zoomCanvasDiv');
	self.canvasShow.setShowPriorities(E('minPriority').value, E('maxPriority').value);
	self.getSessId(function () {
		self.loadConfigParams();
		self.loadMaskLayout();
		self.loadBackgroundImage();
	});

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
	E('setCenterRADEC').onclick = self.setCenterRADEC;

	E('recalculateMask').onclick = self.recalculateMask;
	E('clearSelection').onclick = self.clearSelection;

	E('updateTarget').onclick = self.updateTarget;
	E('deleteTarget').onclick = self.deleteTarget;
	E('saveMDF').onclick = self.saveMDF;

	hideDiv("savePopup");

	return this;
}

