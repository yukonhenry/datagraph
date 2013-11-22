// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
// http://www.anujgakhar.com/2013/08/29/singletons-in-dojo/
define(["dojo/_base/declare","dojo/domReady!"], function(declare, lang){
		var baseinfoSingleton = declare(null, {
			select_reg:null, select_dom:null, active_grid:null,
			dbname_list:null, active_grid_name:"", tbutton_reg:null,
			visible_form_name:"",
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
			reset_active_grid: function() {
				delete this.active_grid;
				//this.active_grid = null;
				this.active_grid_name = "";
			},
			set_active_grid_name: function(active_grid_name) {
				this.active_grid_name = active_grid_name;
			},
			get_active_grid_name: function() {
				return this.active_grid_name;
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
			},
			set_tbutton_reg: function(tbutton_reg) {
				this.tbutton_reg = tbutton_reg;
			},
			get_tbutton_reg: function() {
				return this.tbutton_reg;
			},
			set_visible_form_name: function(form_name) {
				this.visible_form_name = form_name;
			},
			reset_visible_form_name: function(form_name) {
				this.visible_form_name = "";
			},
			get_visible_form_name: function() {
				return this.visible_form_name;
			}
		});
		if (!_instance) {
			var _instance = new baseinfoSingleton();
		}
		return _instance;
});
