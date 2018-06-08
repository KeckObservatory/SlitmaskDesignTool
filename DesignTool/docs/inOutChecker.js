function InOutChecker(region) {
	//
	// Check is a point is inside region
	// Points is a list of (x,y, flag) 
	// Region is a list of points
	// flag will be set if inside, cleared if outside
	
	var self = this;
	
	function buildEdgeList(lines) {
		function addEdge (el, x1, y1, x2, y2) {
			if (y1 == y2) return;
			if (y1 > y2) {
				var t = x1;				
				x1 = x2;
				x2 = t;
				t = y1; 
				y1 = y2;
				y2 = t;				
			}			

			var m, b, x, y;
			m = (x2-x1) / (y2-y1);
			b = -m * y1 + x1 
			for (y = y1; y < y2; ++y) {
				x = y * m + b;
				if (!el[y])
					el[y] = [];
				el[y].push (x);
			}
		}
		var edgeList = [];
		var i;
		var x0, y0;
		var lastX, lastY;
		var x, y, code;
		var row;
		var ymin = 1E10, ymax = -99999;
		for (i in lines) {
			row = lines[i];
			//print ("line ", i, row);
			x = row[0];
			y = row[1];
			code = row[2];
			y = Math.floor(y);
			ymin = Math.min (ymin, y);
			ymax = Math.max (ymax, y);
			if (code == 0) {
				// start vertex
				lastX = x0 = x;
				lastY = y0 = y;
				continue;
			}
			if (code == 1) {
				// next vertex
				// edge = x,y -> lastX, lastY
				addEdge (edgeList, x, y, lastX, lastY);
				lastX = x;
				lastY = y;
				continue;
			}
			if (code == 2) {
				// end vertex, should be same as start vertex
				// edge = x,y -> x0, y0
				addEdge (edgeList, lastX, lastY, x0, y0);
			}
		}
		for (y = ymin; y < ymax; ++y) {
			if (edgeList[y])
				edgeList[y].sort(function(a, b) {return a-b;});
		}
		return edgeList;
	}		
	
	self.checkPoint = function (x, y) {
		var row = self.edgeList[Math.floor(y)];
		if (!row) return false;
		
		var i, len;
		len = row.length;
		len = len - (len % 2);
		i = 0;
		while (i < len) {
			if ((row[i] < x) && (x < row[i+1])) return true;
			i += 2;
		}
		return false;		
	};
	
	self.edgeList = buildEdgeList (region);
	
	return self;
}