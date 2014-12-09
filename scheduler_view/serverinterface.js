define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/request/script", "dojo/domReady!"],
function(dom, declare, lang, script) {
	return declare(null, {
		hostURL : null,
		constructor: function(args) {
			lang.mixin(this, args);
		},
		getServerData: function(rest_path, then_function, query_obj, options_obj) {
			// http://stackoverflow.com/questions/148901/is-there-a-better-way-to-do-optional-function-parameters-in-javascript
			// also look at http://www.markhansen.co.nz/javascript-optional-parameters/
			var query_obj = (typeof query_obj === "undefined" || query_obj === null) ? "" : query_obj;
			var options_obj = options_obj || {};
			//other_param = (typeof other_param === "undefined") ? "" : other_param;
			var data = null;
			var wholeURL = this.hostURL + rest_path;
			console.log("getserver url="+wholeURL);
			var prom = script.get(wholeURL, {
				jsonp:"callback",
				query:query_obj
			}).then(function(data) {
				console.log("request to "+wholeURL+" returned");
				then_function(data, options_obj);
			}, function(err) {
				console.log("GetServer ERROR="+err);
			});
		},
		server_ack: function(adata) {
				console.log("data returned"+adata.test);
		},
	})
})
