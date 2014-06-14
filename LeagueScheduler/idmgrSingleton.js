// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
// http://www.anujgakhar.com/2013/08/29/singletons-in-dojo/
define(["dojo/_base/declare", "dojo/_base/array", "dojo/_base/lang",
	"dojo/Stateful", "dojo/domReady!"],
	function(declare, arrayUtil, lang) {
		var suffix_obj = {form_id:"form_id", dbname_id:"dbname_id",
			inputnum_id:"inputnum_id",
			radiobtn1_id:"radio1_id", radiobtn2_id:"radio2_id",
			grid_id:"infogrid_id", league_select_id:"league_select_id",
			pcontainer_id:"pcontainer_id", gcontainer_id:"gcontainer_id",
			blankcpane_id:"blankcpane_id", resetcpane_id:"resetcpane_id",
			gridcpane_id:"gridcpane_id", textbtncpane_id:"textbtncpane_id",
			bcontainer_id:"bcontainer_id", text_id:"text_id", numcpane_id:"numcpane_id"}
		var op_type_list = ['advance', 'wizard'];
		var id_list = ['div_id', 'tourndiv_id', 'field_id', 'newsched_id',
			'pref_id', 'team_id']
		var idmgrSingleton = declare(null, {
			idmgr_list:null,
			constructor: function() {
				this.idmgr_list = new Array();
				arrayUtil.forEach(op_type_list, function(op_type) {
					// use the first three chars for the op_type as the prefix
					var op_prefix = op_type.substring(0,3)
					arrayUtil.forEach(id_list, function(id) {
						// concatenate with first three chars of idstr
						var id_prefix = id.substring(0,3);
						var idstr_obj = new Object();
						for (var key in suffix_obj) {
							idstr_obj[key] = op_prefix+id_prefix+'_'+suffix_obj[key];
						}
						this.idmgr_list.push({op_type:op_type, id:id,
							idstr_obj:idstr_obj})
					}, this)
				}, this)
			},
			get_idmgr_obj: function(args_obj) {
				var id = args_obj.id;
				var op_type = args_obj.op_type;
				var match_obj = arrayUtil.filter(this.idmgr_list,
				function(item) {
					return item.op_type == op_type && item.id == id;
				})[0]
				return match_obj.idstr_obj;
			},
			get_idmgr_list: function(key, value) {
				var match_list = arrayUtil.filter(this.idmgr_list,
				function(item) {
					return item[key] == value;
				})
				return match_list;
			}
		});
		if (!_instance) {
			var _instance = new idmgrSingleton();
		}
		return _instance;
});
