// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
// http://www.anujgakhar.com/2013/08/29/singletons-in-dojo/
define(["dojo/_base/declare", "dojo/_base/array", "dojo/_base/lang",
	"dojo/domReady!"],
	function(declare, arrayUtil, lang) {
		var suffix_obj = {form_id:"form_id", dbname_id:"dbname_id",
			inputnum_id:"inputnum_id",
			radiobtn1_id:"radio1_id", radiobtn2_id:"radio2_id",
			grid_id:"infogrid_id", league_select_id:"league_select_id",
			pcontainer_id:"pcontainer_id", gcontainer_id:"gcontainer_id",
			blankcpane_id:"blankcpane_id", resetcpane_id:"resetcpane_id",
			gridcpane_id:"gridcpane_id", textbtncpane_id:"textbtncpane_id",
			bcontainer_id:"bcontainer_id", text_id:"text_id",
			numcpane_id:"numcpane_id", btn_id:"btn_id",
			configstatus_id:"configstatus_id",
			addrowbtn_id:'addrowbtn_id', delrowbtn_id:'delrowbtn_id'}
		var op_type_list = ['advance', 'wizard', 'tutorial'];
		var id_list = ['div_id', 'tourndiv_id', 'field_id', 'newsched_id',
			'pref_id', 'team_id', 'conflict_id', 'xls_id']
		var sched_type_list = ['L','T']
		var idmgrSingleton = declare(null, {
			idmgr_list:null,
			constructor: function() {
				this.idmgr_list = new Array();
				arrayUtil.forEach(sched_type_list, function(sched_type) {
					arrayUtil.forEach(op_type_list, function(op_type) {
						// use the first three chars for the op_type as the prefix
						var op_prefix = op_type.substring(0,3)
						arrayUtil.forEach(id_list, function(id) {
							// concatenate with first three chars of idstr
							var id_prefix = id.substring(0,3);
							var idstr_obj = new Object();
							for (var key in suffix_obj) {
								if (op_type == "advance" && (key=="text_id" ||
									key=="btn_id" || key=="textbtncpane_id" ||
									key=="configstatus_id") &&
									(id != "newsched_id" && id != "team_id")) {
									// for advanced UI, and if idprop is not
									// newsched_id, there is only one
									// set of textbtncpane, text, configstatus, and
									// btn nodes across all of the idproperties
									idstr_obj[key] = sched_type+op_prefix+'_'+suffix_obj[key]
								} else {
									idstr_obj[key] = sched_type+op_prefix+
										id_prefix+'_'+suffix_obj[key]
								}
							}
							this.idmgr_list.push({op_type:op_type, id:id,
								sched_type:sched_type, idstr_obj:idstr_obj})
						}, this)
					}, this)
				}, this)
			},
			get_idmgr_obj: function(args_obj) {
				var id = args_obj.id;
				var op_type = args_obj.op_type;
				var sched_type = ('sched_type' in args_obj)?
					args_obj.sched_type:"L";
				var match_obj = arrayUtil.filter(this.idmgr_list,
				function(item) {
					return item.op_type == op_type && item.id == id &&
						item.sched_type == sched_type;
				})[0]
				return match_obj.idstr_obj;
			},
			get_idmgr_list: function(filterobj) {
				// return list of id's that match filterobj values for
				// respective keys
				var match_list = arrayUtil.filter(this.idmgr_list,
				function(item) {
					var matchflag = true;
					for (var key in filterobj) {
						if (item[key] != filterobj[key]) {
							// if key/values does not match, return
							// false for current item
							matchflag = false;
							break;
						}
					}
					return matchflag;
				})
				return match_list;
			}
		});
		if (!_instance) {
			var _instance = new idmgrSingleton();
		}
		return _instance;
});
