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
			obj_list:null, watch_obj:null,
			constructor: function() {
				this.obj_list = new Array();
				this.watch_list = new Array();
				arrayUtil.forEach(['advance', 'wizard'], function(item) {
					// create separate watch object for each op_type
					var watch_obj = new Watch_class();
					this.watch_list.push({watch_obj:watch_obj, op_type:item})
				}, this)
			},
			register_obj: function(obj, idproperty) {
				this.obj_list.push({obj:obj, idproperty:idproperty, op_type:obj.op_type});
			},
			watch_initialize: function() {
				// cycle through watch_list, and then set watches for each watch_obj
				// instance
				arrayUtil.forEach(this.watch_list, function(item) {
					item.watch_obj.watch('divstr_list',
						lang.hitch(this,function(name, oldValue, value) {
							var fieldinfo_obj = this.get_obj('field_id', item.op_type);
							if (fieldinfo_obj && fieldinfo_obj.editgrid && fieldinfo_obj.editgrid.schedInfoGrid) {
								fieldinfo_obj.set_primaryuse_dialog_dropdown(value);
							}
						})
					);
					item.watch_obj.watch('numweeks',
						lang.hitch(this,function(name, oldValue, value) {
							var divinfo_obj = this.get_obj('div_id', item.op_type);
							if (divinfo_obj) {
								if (divinfo_obj.infogrid_store) {
									divinfo_obj.update_numweeks(value);
								} else {
									divinfo_obj.base_numweeks = value;
								}
							}
						})
					);
				}, this);
			},
			set_watch_obj: function(watch_field, value, op_type) {
				var match_obj = arrayUtil.filter(this.watch_list, function(item) {
					return item.op_type == op_type;
				})[0]
				match_obj.watch_obj.set(watch_field, value);
			},
			get_watch_obj: function(watch_field, op_type) {
				var watch_obj = arrayUtil.filter(this.watch_list, function(item) {
					return item.op_type == op_type;
				})[0];
				return watch_obj[watch_field];
			},
			get_obj: function(idproperty, op_type) {
				var match_list = arrayUtil.filter(this.obj_list,
				function(item, index) {
					return item.idproperty == idproperty && item.op_type == op_type;
				})
				if (match_list.length == 1) {
					match_obj = match_list[0].obj;
					return match_obj;
				} else if (match_list.length > 1) {
					console.log("Error code 3 - multiple instances of idproperty and op_type "+idproperty);
				} else if (match_list.length < 1) {
					console.log("Error code 4 - idproperty and op_type "+idproperty+" obj not registered");
				}
				return null;
			},
			get_obj_list: function(idproperty) {
				var match_list = arrayUtil.filter(this.obj_list,
				function(item, index) {
					return item.idproperty == idproperty;
				})
				return match_list;
			}
		});
		if (!_instance) {
			var _instance = new baseinfoSingleton();
			_instance.watch_initialize();
		}
		return _instance;
});
