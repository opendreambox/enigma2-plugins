/*
 * This code is inspired by http://www.phpied.com/json-javascript-cookies/
 * and modified for use with prototype
 * It's a pretty straight forward way to store and load settings in a nice to use JSON-Object
 */

var userprefs = {
	data : {},

	load : function() {
		var the_cookie = document.cookie.split(';');

		var idx = 0;
		while(the_cookie[idx].trim().startsWith("TWISTED_SESSION") || the_cookie[idx].trim().startsWith("sid")) {
			idx += 1;
		}
		if (the_cookie[idx]) {
			this.data = JSON.parse(unescape(the_cookie[idx]));
		}
		return this.data;
	},

	save : function(expires, path) {
		var d = expires || new Date(2222, 01, 01);
		var p = path || '/';
		document.cookie = escape( JSON.stringify(this.data) ) + ';path=' + p
				+ ';expires=' + d.toUTCString();
	}
};

userprefs.load();