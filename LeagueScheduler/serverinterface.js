define(["dojo/dom", "dojo/_base/declare", "dojo/_base/lang", "dojo/request/script", "dojo/domReady!"],
function(dom, declare, lang, script) {
	return declare(null, {
		hostURL : null,
		constructor: function(args) {
			lang.mixin(this, args);
		},
		getServerData: function(rest_path, then_function, query_obj, other_param) {
			// http://stackoverflow.com/questions/148901/is-there-a-better-way-to-do-optional-function-parameters-in-javascript
			query_obj = (typeof query_obj === "undefined") ? "" : query_obj;
			other_param = (typeof other_param === "undefined") ? "" : other_param;
			var data = null;
			wholeURL = this.hostURL + rest_path;
			console.log("getserver url="+wholeURL);
			script.get(wholeURL, {
				jsonp:"callback",
				query:query_obj
			}).then(function(data) {
				console.log("request to "+wholeURL+" returned");
				then_function(data, other_param);
			});
			return data;
		},
		server_ack: function(adata) {
				console.log("data returned"+adata.test);
		},
	})
})