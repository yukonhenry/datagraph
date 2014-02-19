// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
// http://www.anujgakhar.com/2013/08/29/singletons-in-dojo/
define(["dojo/_base/declare", "dojo/_base/array", "dojo/_base/lang",
	"dojo/Stateful", "dojo/domReady!"],
	function(declare, arrayUtil, lang, Stateful){
		var watch_class = declare([Stateful],{
			divstr_list:null
		})
		var baseinfoSingleton = declare(null, {
			select_reg:null, select_dom:null, active_grid:null,
			dbname_list:null, active_grid_name:"", tbutton_reg:null,
			obj_list:null, watch_obj:null,
			constructor: function() {
				this.obj_list = new Array();
				this.watch_obj = new watch_class();
				//this.watch_obj.set('divstr_list',[]);
			},
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
			set_tbutton_reg: function(tbutton_reg) {
				this.tbutton_reg = tbutton_reg;
			},
			get_tbutton_reg: function() {
				return this.tbutton_reg;
			},
			register_obj: function(obj, idproperty) {
				this.obj_list.push({obj:obj, idproperty:idproperty});
			},
			watch_initialize: function() {
				this.watch_obj.watch('divstr_list',
					lang.hitch(this,function(name, oldValue, value) {
						var fieldinfo_obj = this.get_info_obj('field_id');
						if (fieldinfo_obj && fieldinfo_obj.editgrid && fieldinfo_obj.editgrid.schedInfoGrid) {
							console.log("calling fieldinfo set dialog w "+value);
							fieldinfo_obj.set_primaryuse_dialog_dropdown(value);
						}
					}));
			},
			get_info_obj: function(idproperty) {
				var match_list = arrayUtil.filter(this.obj_list,
				function(item, index) {
					return item.idproperty == idproperty;
				})
				if (match_list.length == 1) {
					match_obj = match_list[0].obj;
					return match_obj;
				} else if (match_list.length > 1) {
					console.log("Error code 3 - multiple instances of idproperty "+idproperty);
				} else if (match_list.length < 1) {
					console.log("Error code 4 - idproperty "+idproperty+" obj not registered");
				}
				return null;
			}
		});
		if (!_instance) {
			var _instance = new baseinfoSingleton();
			_instance.watch_initialize();
		}
		return _instance;
});
