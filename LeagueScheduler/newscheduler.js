define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/_base/array", "dojo/keys",
	"dijit/registry", "dijit/Tooltip",
	"LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, arrayUtil, keys,
		registry, Tooltip, EditGrid,
		baseinfoSingleton) {
		var constant = {
			infobtn_id:"infoBtnNode_id"
		};
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			entrynum_reg: null, error_node:null, text_node:null,
			newcol_name:"", editgrid:null,
			info_obj:null, idproperty:"", server_path:"", server_key:"",
			cellselect_flag:false,
			text_node_str:"",
			updatebtn_str:"", storeutil_obj:null,
			grid_id:"", uistackmgr:null, tooltip_list:null,
			constructor: function(args) {
				lang.mixin(this, args)
				this.tooltip_list = new Array();
			},
			cleanup: function() {
				// cleanup here is cleaning up what is left over from other
				// forms and grids
				if (active_grid) {
					active_grid.cleanup();
					//baseinfoSingleton.reset_active_grid();
				}
				arrayUtil.forEach(this.tooltip_list, function(item) {
					item.destroyRecursive();
				});
			}

		});
	})
