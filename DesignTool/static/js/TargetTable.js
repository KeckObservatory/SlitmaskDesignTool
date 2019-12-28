function TargetTable (targets) {

	function E(n) {return document.getElementById(n);}
	
	var self = this;
	self.reDrawTargetTable = function () {};
	
	self.targets = targets;
	self.columns = [
		['Name', 100, 'name', 0],
		['RA', 90, 'raSexa', 0],
		['DEC', 90, 'decSexa', 0],
		['Prior', 70, 'pcode', 0],
		['Sel', 35, 'selected', 0],
		['In', 35, 'inMask', 0],		
		['Slit PA', 70, 'slitPA', 0],
		['Magn', 70, 'mag', 0],
		['Band', 50, 'band', 0],
		['Len1', 50, 'length1', 0],
		['Len2', 50, 'length2', 0],
		['SlitWidth', 70, 'slitWidth', 0]];
	
	self.showTable = function () {
		// columns: name, width, up/down:-1,0,1
	
		var i;
		var columns = self.columns;
		var names = targets.name;
		var raHours = targets.raSexa;
		var decDegs = targets.decSexa;
		var pcodes = targets.pcode;
		var selecteds = targets.selected;
		var inMask = targets.inMask;
		var slitPAs = targets.slitPA;
		var mags = targets.mag;
		var bands = targets.band;
		var len1s = targets.length1;
		var len2s = targets.length2;
		var slitWidths = targets.slitWidth;		
	
		buf = [];
		buf.push ("<table id='targetTable'>");
		buf.push("<thead><tr>");
		
		// Build the header row
		for (i in columns) {
			var col = columns[i];
			var label = col[0];
			var width = col[1];
			var name = col[2];
			var dir = col[3];
			var arrow = '';
			if (dir > 0) arrow = ' &#9650; ';
			if (dir < 0) arrow = ' &#9660; ';
			buf.push ("<th width='" + width + "px' id='sortIdx" + i + "'>" + label + arrow + "</td>");
		
		}
		buf.push("</tr></thead><tbody id='targetTableBody'>");
		
		// Table body content
		var idx;
		var sortedIdx = self.sortIndices;
		for (idx in names) {
			i = sortedIdx[idx];
			var tId = "target" + i;
			// 
			// Alternating color is done in CSS with tr:nth-child(even) and tr:nth-child(odd) 			
			//
			buf.push ("<tr id='" + tId + "'>");
			buf.push ("<td width='" + columns[0][1] + "'>" + names[i]);
			buf.push ("<td width='" + columns[1][1] + "'>" + raHours[i]);
			buf.push ("<td width='" + columns[2][1] + "'>" + decDegs[i]);
			buf.push ("<td width='" + columns[3][1] + "'>" + pcodes[i]);
			buf.push ("<td width='" + columns[4][1] + "'>" + selecteds[i]);
			buf.push ("<td width='" + columns[5][1] + "'>" + inMask[i]);
			buf.push ("<td width='" + columns[6][1] + "'>" + slitPAs[i]);
			buf.push ("<td width='" + columns[7][1] + "'>" + mags[i].toFixed(2));
			buf.push ("<td width='" + columns[8][1] + "'>" + bands[i]);
			buf.push ("<td width='" + columns[9][1] + "'>" + len1s[i].toFixed(1));
			buf.push ("<td width='" + columns[10][1] + "'>" + len2s[i].toFixed(1));
			buf.push ("<td width='" + columns[11][1] + "'>" + slitWidths[i]);
			buf.push ("</tr>");
		}
		buf.push ("</tbody></table>");
		
		// Returns table as HTML string
		return buf.join("");
	};	
	
	self.genSortFunction = function (idx) {
		// Returns the function with the sort index
		return function () {
			self.sortTable (idx);
		};	
	};
	
	self.setSortClickCB = function (fn) {
		// Setup the callback of the header row.
		var i;
		for (i in self.columns) {
			E('sortIdx' + i).onclick = self.genSortFunction (i);
		}
		// fn is a callback function to allow the caller 
		// to send the content of the table to an element that is unknown to this class.
		self.reDrawTargetTable = fn;
	};
	
	self.setOnClickCB = function (fn) {
		// Setup the function to call when a row in the target table is clicked on.
		var i;
		for (i in self.targets.orgIndex) {
			E('target' + i).onclick = fn;
		}
	};
	
	self.scrollTo = function (idx) {
		// Smooth scroll to the desired idx/reversed-idx.
		// See CSS file.
		if (idx < 0) return;
		var tBody = E('targetTableBody');
		if (tBody && self.targets.orgIndex) { 
			var nIdx = self.reverseIndices[idx];
			var scrollY = nIdx * tBody.scrollHeight / self.targets.orgIndex.length;
			tBody.scrollTop = scrollY;
		}
	};
	
	self.highLight = function (idx) {
		if (idx < 0) return;
		var elem = E('target' + idx);
		if (elem) elem.className = 'hiRow';
	};
	
	self.markSelected = function (idx) {
		if (idx < 0) return;
		var elem = E('target' + idx);
		if (elem) elem.className = 'selectedRow';
	};
	
	self.markNormal = function (idx) {
		if (idx < 0) return;
		// Make sure target/elem exists.
		var elem = E('target' + idx);
		//if (elem) elem.className = idx % 2 == 0 ? 'evenRow' : 'oddRow';
		if (elem) elem.className = '';
	};
	
	self.sortTable = function (idx) {
		function sortUp (a, b) {
			var elem1 = dataCol[a];
			var elem2 = dataCol[b];
			if (elem1 < elem2) return -1;
			if (elem1 > elem2) return 1;
			return 0;
		}
		function sortDown (a, b) {
			var elem1 = dataCol[a];
			var elem2 = dataCol[b];
			if (elem1 < elem2) return 1;
			if (elem1 > elem2) return -1;
			return 0;
		}
		var targets = self.targets;
		var i;
		var info = self.columns[Math.max(idx, 0)];
		var dataCol = targets[info[2]];
		var indices = new Array (dataCol.length);
		var upDown = info[3];
		
		// Remember original sort order
		for (i in dataCol) {
			indices[i] = i;
		}
		
		// Reset all sort flags
		for (i in self.columns) {
			self.columns[i][3] = 0;
		}
		
		// idx < 0 means original order, same as no sort
		if (idx >= 0) {
			// Check sort order up or down
			if (upDown >= 0) {
				indices.sort(sortUp);
				info[3] = -1;
			}
			else {
				indices.sort(sortDown);
				info[3] = 1;	
			}
		}
		
		// Setup reversed index table.
		for (i in indices) {
			self.reverseIndices[indices[i]] = i;
		}
		self.sortIndices = indices;
		
		// Call the caller supplied function.
		self.reDrawTargetTable();
	};
	
	self.sortIndices = new Array(self.targets.length);
	self.reverseIndices = new Array(self.targets.length);
	self.sortTable (-1);
	
	return self;
}