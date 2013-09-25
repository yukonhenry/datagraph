define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang", 
	"dojo/dom-class", "dojo/keys", "dojo/domReady!"],
	function(dbootstrap, dom, declare, lang, domClass, keys) {
		return declare(null, {
			newsched_reg : null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			createConfig: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdbname_input: function(event) {
				if (event.keyCode == keys.ENTER) {
					newdb_name = this.newsched_reg.get("value");
					console.log("newdb="+newdb_name);	
				} 
			}
		})
	})