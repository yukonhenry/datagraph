define(["dojo/dom", "dojo/_base/declare", "dojo/dom-class", "dojo/domReady!"],
	function(dom, declare, domClass) {
		return declare(null, {
			constructor: function(args) {
				//lang.mixin(this.args);
			},
			createConfig: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			}
		})
	})