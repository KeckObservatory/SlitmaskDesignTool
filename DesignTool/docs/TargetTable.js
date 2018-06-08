function TargetTable (container, targets) {

	function E(n) {return document.getElementById(n);}
	
	var self = this;
	
	self.container = container;
	self.targets = targets;
	
	self.showTable = function () {
		var i;
		var names = targets.name;
		var raHours = targets.raSexa;
		var decDegs = targets.decSexa;
		var pcodes = targets.pcode;
		var selecteds = targets.select;
		var slitPAs = targets.slitPA;
		var mags = targets.mag;
		var bands = targets.band;
		var len1s = targets.length1;
		var len2s = targets.length2;
		var slitWidths = targets.slitWidth;
		buf = [];
		buf.push ("<table id='targetTable'>");
		buf.push("<thead><tr>" +
				"<td width='100px'>Name</td>" +
				"<td width='70px'>RA</td>" +
				"<td width='70px'>DEC</td>" +
				"<td width='50px'>PCode</td>" +
				"<td width='50px'>Selected</td>" +
				"<td width='50px'>Slit PA</td>" +
				"<td width='50px'>Mag</td>" +
				"<td width='50px'>Band</td>" +
				"<td width='50px'>Len1</td>" +
				"<td width='50px'>Len2</td>" +
				"<td width='50px'>SlitWidth</td>" +
				"</tr></thead><tbody id='targetTableBody'>"
				);
		for (i in names) {
			var tId = "target" + i;
			var klass = i % 2 == 0 ? 'evenRow' : 'oddRow';			
			var row = "<tr id='" + tId + "' class='" + klass + "'><td width='100px'>" + names[i] +
			"<td width='70px'>" + raHours[i] +
			"<td width='70px'>" + decDegs[i] +
			"<td width='50px'>" + pcodes[i] +
			"<td width='50px'>" + selecteds[i] +
			"<td width='50px'>" + slitPAs[i] +
			"<td width='50px'>" + mags[i].toFixed(2) +
			"<td width='50px'>" + bands[i] +
			"<td width='50px'>" + len1s[i] +
			"<td width='50px'>" + len2s[i] +
			"<td width='50px'>" + slitWidths[i] +
			"</tr>";				
			buf.push (row);
		}
		buf.push ("</tbody></table>");
		return buf.join("");
	};
	
	self.setOnClickCB = function (fn) {
		var i;
		for (i in self.targets.xpos) {
			E('target' + i).onclick = fn;
		}
	};
	
	self.scrollTo = function (idx) {
		if (idx < 0) return;
		var tBody = E('targetTableBody');
		if (tBody && self.targets.xpos) { 
			var scrollY = idx * tBody.scrollHeight / self.targets.xpos.length;
			tBody.scrollTop = scrollY;
		}
	};
	
	self.highLight = function (idx) {
		if (idx < 0) return;
		E('target' + idx).className = 'hiRow';
	};
	
	self.markSelected = function (idx) {
		if (idx < 0) return;
		E('target' + idx).className = 'selectedRow';
	};
	
	self.markNormal = function (idx) {
		if (idx < 0) return;
		E('target' + idx).className = idx % 2 == 0 ? 'evenRow' : 'oddRow';
	};
	
	container.innerHTML = self.showTable();
	
	return self;
}