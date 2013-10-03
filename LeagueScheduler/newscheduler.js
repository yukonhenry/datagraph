define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang", 
	"dojo/dom-class", "dojo/keys", "dojo/domReady!"],
	function(dbootstrap, dom, declare, lang, domClass, keys) {
		return declare(null, {
			input_reg : null, form_reg: null, server_interface:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			makeVisible: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdbname_input: function(event) {
				if (event.keyCode == keys.ENTER) {
					if (this.form_reg.validate()) {
						confirm('Input Name is Valid, creating new Schedule DB');
						newdb_name = this.input_reg.get("value");
						console.log("newdb="+newdb_name);
						this.server_interface.getServerData("createnewdb", this.newdb_ack,
							{newdb_name:newdb_name});	
					} else {
						alert('Input name is Invalid, please correct');
					}
				} 
			},
			newdb_ack: function(adata) {
				console.log("data returned"+adata.test);
			}
		})
	})