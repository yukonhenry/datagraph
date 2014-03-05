// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
// http://www.anujgakhar.com/2013/08/29/singletons-in-dojo/
define(["dojo/_base/declare", "dojo/_base/array", "dojo/_base/lang",
	"dojo/Stateful", "dojo/domReady!"],
	function(declare, arrayUtil, lang, Stateful){
		var Watch_class = declare([Stateful],{
			divstr_list:null,
			numweeks:0
		})
		var baseinfoSingleton = declare(null, {
			select_reg:null, select_dom:null, active_grid:null,
			dbname_list:null, active_grid_name:"", tbutton_reg:null,
			obj_list:null, watch_obj:null,
			constructor: function() {
				this.obj_list = new Array();
				this.watch_obj = new Watch_class();
				//this.watch_obj.set('divstr_list',[]);
			},
			register_obj: function(obj, idproperty) {
				this.obj_list.push({obj:obj, idproperty:idproperty});
			},
			watch_initialize: function() {
				this.watch_obj.watch('divstr_list',
					lang.hitch(this,function(name, oldValue, value) {
						var fieldinfo_obj = this.get_obj('field_id');
						if (fieldinfo_obj && fieldinfo_obj.editgrid && fieldinfo_obj.editgrid.schedInfoGrid) {
							console.log("calling fieldinfo set dialog w "+value);
							fieldinfo_obj.set_primaryuse_dialog_dropdown(value);
						}
					}));
				this.watch_obj.watch('numweeks',
					lang.hitch(this,function(name, oldValue, value) {
						var divinfo_obj = this.get_obj('div_id');
						if (divinfo_obj) {
							if (divinfo_obj.infogrid_store) {
								divinfo_obj.update_numweeks(value);
							} else {
								divinfo_obj.base_numweeks = value;
							}
						}
					}));
			},
			get_obj: function(idproperty) {
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
