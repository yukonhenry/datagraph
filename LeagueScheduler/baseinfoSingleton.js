// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
// http://www.anujgakhar.com/2013/08/29/singletons-in-dojo/
define(["dojo/_base/declare","dojo/domReady!"], function(declare, lang){
		var baseinfoSingleton = declare(null, {
			select_reg:null, select_dom:null, active_grid:null,
			dbname_list:null,
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
			},
			set_active_grid: function(active_grid) {
				this.active_grid = active_grid;
			},
			get_active_grid: function() {
				return this.active_grid;
			},
			set_dbname_list: function(dlist) {
				this.dbname_list = dlist;
			},
			get_dbname_list: function() {
				return this.dbname_list;
			},
			addto_dbname_list: function(elem) {
				this.dbname_list.push(elem);
			},
			// remove by value: http://stackoverflow.com/questions/3954438/remove-item-from-array-by-value
			removefrom_dbname_list: function(elem) {
				var index = this.dbname_list.indexOf(elem);
				if (index == -1)
					return false;
				else {
					this.dbname_list.splice(index, 1);
					return true;
				}
			}
		});
		if (!_instance) {
			var _instance = new baseinfoSingleton();
		}
		return _instance;
});
