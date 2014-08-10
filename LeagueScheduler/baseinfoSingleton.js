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
			obj_list:null, watch_obj:null, xlsdownload_path:"", userid_name:"",
			constructor: function() {
				this.obj_list = new Array();
				this.watch_list = new Array();
				arrayUtil.forEach(['advance', 'wizard'], function(item) {
					arrayUtil.forEach(['field_id', 'pref_id', 'div_id', 'team_id',
						'conflict_id'], function(id) {
						// create separate watch object for each op_type and id
						// separate watch obj necessary as different info_obj's
						// may have different divstr_list's depending on the
						// current state of configuration
						var watch_obj = new Watch_class();
						watch_obj.set('divstr_list', new Array());
						this.watch_list.push({watch_obj:watch_obj, op_type:item,
							idproperty:id})
					}, this)
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
							// Execute when watch gets activated for any change to
							// divstr_list; team_id, field_id, pref_id, conflict_id
							// are relevant to the watch
							var info_obj = this.get_obj(item.idproperty,
								item.op_type);
							if (info_obj) {
								if (item.idproperty == 'team_id') {
									info_obj.set_div_select(value);
								} else if (info_obj.editgrid &&
									info_obj.editgrid.schedInfoGrid &&
									value.length > 0) {
									if (item.idproperty == 'field_id') {
										info_obj.set_primaryuse_dialog_dropdown(value);
									} else if (item.idproperty == 'pref_id' ||
										item.idproperty == 'conflict_id') {
										info_obj.set_griddiv_select(value);
									}
								}
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
			set_watch_obj: function(watch_field, value, op_type, idproperty) {
				var match_obj = arrayUtil.filter(this.watch_list, function(item) {
					return item.op_type == op_type && item.idproperty == idproperty;
				})[0]
				match_obj.watch_obj.set(watch_field, value);
			},
			get_watch_obj: function(watch_field, op_type, idproperty) {
				var match_obj = arrayUtil.filter(this.watch_list, function(item) {
					return item.op_type == op_type && item.idproperty == idproperty;
				})[0];
				return match_obj.watch_obj.get(watch_field);
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
			},
			set_hostserver: function(hostserver) {
				if (hostserver == "webfaction") {
					this.xlsdownload_path = "http://www.yukontr.com/download/xls/";
				} else {
					this.xlsdownload_path = "http://localhost/doc/xls/";
				}
			},
			get_xlsdownload_path: function() {
				return this.xlsdownload_path;
			},
			set_userid_name: function(userid_name) {
				this.userid_name = userid_name;
			},
			get_userid_name: function() {
				return this.userid_name;
			}
		});
		if (!_instance) {
			var _instance = new baseinfoSingleton();
			_instance.watch_initialize();
		}
		return _instance;
});
