// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
// http://www.anujgakhar.com/2013/08/29/singletons-in-dojo/
define(["dojo/_base/declare","dojo/domReady!"], function(declare, lang){
		var baseinfoSingleton = declare(null, {
			select_reg:null, select_dom:null,
			set_select_reg: function(select_reg) {
				this.select_reg = select_reg;
			},
			get_select_reg: function() {
				return this.select_reg;
			},
			set_select_dom: function(select_dom) {
				this.select_dom = select_dom;
			},
			get_select_dom: function() {
				return this.select_dom;
			}
		});
		if (!_instance) {
			var _instance = new baseinfoSingleton();
		}
		return _instance;
});
