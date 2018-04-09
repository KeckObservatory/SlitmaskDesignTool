function AjaxClass() {
	/*-*
	 * forexmaple() {
	 * 		 function callback (jsVar) { 
	 * 			jsVar contains the returned value 
	 * 		} 
	 * 		var ajax = new AjaxClass(); 
	 * 		var url = "abc/xyz"; 
	 * 		var parms = {a: 1, b: 2}; 
	 * 		ajax.sendRequest (url, parms, callback); 
	 * }
	 * 
	 */
	var self = this;

	function array2Query(arr) {
		var buf = new Array();
		for (idx in arr) {
			buf.push(idx + "=" + arr[idx]);
		}
		return buf.join("&");
	}

	function toValue(xt) {
		if (!xt)
			return false;
		var txt = xt.responseText;
		if (!txt)
			return false;
		return eval('(' + txt + ')');
	}

	self.initialize = function() {
		var xt = false;

		if (typeof XMLHttpRequest != 'undefined') {
			xt = new XMLHttpRequest();
		} else {
			try {
				xt = new ActiveXObject("Msxml2.XMLHTTP");
			} catch (e1) {
				try {
					xt = new ActiveXObject("Microsoft.XMLHTTP");
				} catch (e2) {
					xt = false;
				}
			}
		}
		self.maxTime = 60000;
		self.xmlHttp = xt;
	};

	self.setMaxTime = function(mtime) {
		self.maxTime = mtime;
	};

	self.sendRequest = function(script, params, callback) {
		var xt = self.xmlHttp;
		if (!xt)
			return;

		var d = new Date();
		params["rnd"] = d.getTime();
		var query = script + "?" + array2Query(params);
		xt.onreadystatechange = function() {
			if (xt.readyState == 4)
				callback(toValue(xt));
		};
		xt.open("GET", query, true); // true for asyncrhonuous
		xt.timeout = self.maxTime;
		xt.setRequestHeader("Content-Type", "text/xml");
		xt.send("");
	};

	self.postRequest = function(script, params, callback) {
		var xt = self.xmlHttp;
		if (!xt)
			return;

		var d = new Date();
		params["rnd"] = d.getTime();
		var content = array2Query(params);
		xt.onreadystatechange = function() {
			if (xt.readyState == 4)
				callback(toValue(xt));
		};
		xt.open("POST", script, true); // true for asyncrhonuous
		xt.timeout = self.maxTime;
		xt
				.setRequestHeader("Content-Type",
						"application/x-www-form-urlencoded");
		xt.setRequestHeader("Content-length", content.length);
		xt.setRequestHeader("Connection", "close");
		xt.send(content);
	};

	self.end = function() {
		try {
			self.xmlHttp.abort();
		} catch (e) {
		}
		;
	};

	self.initialize();
} // AjaxClass

function noop() {
}

function ajaxCall(url, parms, callback) {
	var ajax = new AjaxClass();
	ajax.sendRequest(url, parms, callback);
}

function ajaxPost(url, parms, callback) {
	var ajax = new AjaxClass();
	ajax.postRequest(url, parms, callback);
}
