define(["dojo/dom", "dojo/_base/declare", "dijit/form/ValidationTextBox", "dojo/domReady!"],
	function(dom, declare, ValidationTextBox) {
		return declare(null, {
			constructor: function(args) {
				lang.mixin(this.args);
			}
		})
	})