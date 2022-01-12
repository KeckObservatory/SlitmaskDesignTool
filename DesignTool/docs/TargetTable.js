function TargetTable(targets) {

	function E(n) {
		return document.getElementById(n);
	}

	var self = this;
	self.reDrawTargetTable = function () { };
	self.selectedIdx = -1;

	self.targets = targets;
	self.columns = [
		['#', 60, 'orgIndex', 0],
		['Name', 160, 'objectId', 0],
		['RA', 80, 'raSexa', 0],
		['DEC', 80, 'decSexa', 0],
		
		['Magn', 60, 'mag', 0],
		['Band', 50, 'pBand', 0],	
		['Prior', 60, 'pcode', 0],		
		['Sel', 35, 'selected', 0],
		['Slit PA', 60, 'slitLPA', 0],
		['Len1', 50, 'length1', 0],
		['Len2', 50, 'length2', 0],
		['SlitWidth', 60, 'slitWidth', 0],
		['In', 35, 'inMask', 0],
	];

	self.showTable = function () {
		// columns: name, width, up/down:-1,0,1

		let i;
		let columns = self.columns;
		let sum = 0;
		let bufHeader = [];
		let buf = []

		// Build the header row
		for (i in columns) {
			let col = columns[i];
			let label = col[0];
			let width = col[1];
			let dir = col[3];
			let arrow = '';
			if (dir > 0) arrow = ' &#9650; ';
			if (dir < 0) arrow = ' &#9660; ';
			bufHeader.push("<th width='" + width + "px' id='sortIdx" + i + "'>" + label + arrow + "</td>");
			sum += width;
		}
		self.tableWidth = sum;
		//sum += 25;

		//buf.push("<table id='targetTable' style='width:"+ sum + "px'>");
		buf.push("<table id='targetTable'>");
		buf.push("<thead><tr>");
		buf.push(bufHeader.join(''));
		buf.push("</tr></thead>");
		buf.push("<tbody id='targetTableBody'>");

		//buf.push("<tr>");
		//buf.push (bufHeader.join(''));

		if (targets) {
			let orgIndex = targets.orgIndex;
			let names = targets.objectId;
			let raHours = targets.raSexa;
			let decDegs = targets.decSexa;
			let pcodes = targets.pcode;
			let selecteds = targets.selected;
			let inMask = targets.inMask;
			let slitPAs = targets.slitLPA;
			let mags = targets.mag;
			let bands = targets.pBand;
			let len1s = targets.length1;
			let len2s = targets.length2;
			let slitWidths = targets.slitWidth;

			// Table body content
			let idx;
			let i;
			let sortedIdx = self.sortIndices;
			for (idx in names) {
				i = sortedIdx[idx];
				let k = 0;
				let tId = "target" + i;
				// 
				// Alternating color is done in CSS with tr:nth-child(even) and tr:nth-child(odd) 			
				//
				buf.push("<tr id='" + tId + "'>");
				buf.push("<td width='" + columns[k][1] + "px'>" + (orgIndex[i] + 1));
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + names[i]);
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + raHours[i]);
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + decDegs[i]);
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + mags[i].toFixed(2));
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + bands[i]);
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + pcodes[i]);
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + selecteds[i]);
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + slitPAs[i]);
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + len1s[i].toFixed(2));
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + len2s[i].toFixed(2));
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + slitWidths[i].toFixed(2));
				k += 1;
				buf.push("<td width='" + columns[k][1] + "px'>" + inMask[i]);
				buf.push("</tr>");
			}
		}
		buf.push("</tbody></table>");

		// Returns table as HTML string
		return buf.join("");
	};

	self.genSortFunction = function (idx) {
		// Returns the function with the sort index
		return function () {
			self.sortTable(idx);
		};
	};

	self.setSortClickCB = function (fn) {
		// Setup the callback of the header row.
		let i;
		for (i in self.columns) {
			E('sortIdx' + i).onclick = self.genSortFunction(i);
		}
		// fn is a callback function to allow the caller 
		// to send the content of the table to an element that is unknown to this class.
		self.reDrawTargetTable = fn;
	};

	self.setOnClickCB = function (fn) {
		// Setup the function to call when a row in the target table is clicked on.
		let i;
		for (i in self.targets.orgIndex) {
			E('target' + i).onclick = fn;
		}
	};

	self.scrollTo = function (idx) {
		// Smooth scroll to the desired idx/reversed-idx.
		// See CSS file.
		if (idx < 0) return;
		let tBody = E('targetTableBody');
		if (tBody && self.targets.orgIndex) {
			let nRows = self.targets.orgIndex.length;
			let pixelPerRow = tBody.scrollHeight / nRows;
			let visibleRows = tBody.clientHeight / pixelPerRow; // no margin, scrollbar
			let nIdx = self.reverseIndices[idx];
			let scrollY = nIdx * pixelPerRow;

			// Where are we now?
			let topRow = tBody.scrollTop / pixelPerRow;

			if (nIdx < visibleRows) {
				// In first page
				scrollY = 0;
			} else {
				nIdx -= 5;
				nIdx = Math.max(0, nIdx);
				scrollY = nIdx * pixelPerRow;
			}

			tBody.scrollTop = scrollY;
		}
	};

	self.highLight = function (idx) {
		if (idx < 0) return;
		let elem = E('target' + idx);
		if (elem) elem.className = 'hiRow';
	};

	self.markSelected = function (idx) {
		self.selectedIdx = idx;
		if (idx < 0) return;
		let elem = E('target' + idx);
		if (elem) elem.className = 'selectedRow';
	};

	self.markNormal = function (idx) {
		if (idx < 0) return;
		// Make sure target/elem exists.
		let elem = E('target' + idx);
		//if (elem) elem.className = idx % 2 == 0 ? 'evenRow' : 'oddRow';
		if (elem) elem.className = '';
	};

	self.sortTable = function (idx) {
		function sortUp(a, b) {
			let elem1 = dataCol[a];
			let elem2 = dataCol[b];
			if (elem1 < elem2) return -1;
			if (elem1 > elem2) return 1;
			return 0;
		}

		function sortDown(a, b) {
			let elem1 = dataCol[a];
			let elem2 = dataCol[b];
			if (elem1 < elem2) return 1;
			if (elem1 > elem2) return -1;
			return 0;
		}

		if (!self.targets) return;

		let targets = self.targets;
		let i;
		let info = self.columns[Math.max(idx, 0)];
		let dataCol = targets[info[2]];
		let indices = new Array(dataCol.length);
		let upDown = info[3];

		// Remember original sort order
		for (i = 0; i < dataCol.length; ++i) {
			indices[i] = i;
		}

		// Reset all sort flags
		for (i = 0; i < self.columns.length; ++i) {
			self.columns[i][3] = 0;
		}

		// idx < 0 means original order, same as no sort
		if (idx >= 0) {
			// Check sort order up or down
			if (upDown >= 0) {
				indices.sort(sortUp);
				info[3] = -1;
			} else {
				indices.sort(sortDown);
				info[3] = 1;
			}
		}

		// Setup reversed index table.
		for (i = 0; i < indices.length; ++i) {
			self.reverseIndices[indices[i]] = i;
		}
		self.sortIndices = indices;

		// Call the caller supplied function.
		self.reDrawTargetTable();
	};

	self.sortIndices = new Array(self.targets.length);
	self.reverseIndices = new Array(self.targets.length);
	self.sortTable(-1);

	return self;
}