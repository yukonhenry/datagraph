// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/dom", "dojo/_base/declare","dojo/_base/lang",
	"dojo/_base/array", "dijit/registry", "dgrid/editor",
	"LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
	"dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry, editor,
		baseinfo, baseinfoSingleton){
		return declare(baseinfo, {
			info_list:null,
			select_reg:null, select_reg_handle:null,
			idproperty:"sched_id", colname:"",
			constructor: function(args) {
				lang.mixin(this, args);
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
					gameday: "Game day",
					start_time: "Time",
					match_id: "Match ID",
					venue: "Venue",
					home: editor({label:"Home Team", field:"home", autoSave:true},"text","dblclick"),
					away: editor({label:"Away Team", field:"away", autoSave:true},"text","dblclick"),
					comment: "Comment"
				};
				return columnsdef_obj;
			},
			getServerDBInfo: function(options_obj) {
				var item = options_obj.item;
				this.colname = item;
				if (this.select_reg_handle)
					this.select_reg_handle.remove();
				// we don't necessariy need to call get_dbcol again if select_reg already exists (we don't need to recreate the drop down)
				// TODO: 'rrdb' is a simple hack right now - revisit
				this.server_interface.getServerData('get_dbcol/rrdb/'+item, lang.hitch(this, function(data) {
					this.info_list = data.info_list;
					if (!this.select_reg) {
						this.select_reg = registry.byId("schedDBDivisionSelect");
						//this.schedutil_obj.generateDivSelectDropDown(this.select_reg, this.info_list);
					}
					this.uistackmgr.switch_pstackcpane({idproperty:this.idproperty,
						p_stage:"preconfig", entry_pt:"fromdb"});
					this.uistackmgr.switch_gstackcpane(this.idproperty, true);
					options_obj.serverdata_key = 'game_list';
					this.select_reg_handle = this.select_reg.on("change", lang.hitch(this, function(evt) {
						var divisioncode = this.select_reg.get("value");
						options_obj.divisioncode = divisioncode;
						options_obj.cellselect_flag = false;
						options_obj.text_node_str = 'Schedule Name';
						options_obj.grid_id = 'schedinfogrid_id';
						options_obj.storeutil_obj = this.storeutil_obj;
						// recalculate need for a new grid here
						// as code flow does not go through uistackmanager
						options_obj.newgrid_flag = this.is_newgrid_required();
						this.server_interface.getServerData("get_scheddbcol/"+item,
							lang.hitch(this, this.convertServerDataFormat),
							{divisioncode:divisioncode}, options_obj);
					}));
				}));

			},
			convertServerDataFormat: function(server_data, options_obj) {
				var game_array = server_data.game_list;
				var game_grid_list = new Array();
				arrayUtil.forEach(game_array, lang.hitch(this, function(item, index) {
					var gameday = this.schedutil_obj.getTournCalendarMap(item.GAMEDAY_ID);
					var gameday_data = item.GAMEDAY_DATA;
					var start_time = this.schedutil_obj.tConvert(item.START_TIME);
					// fill in the game day number and start time
					var game_grid_row_list = arrayUtil.map(gameday_data, function(item2, index2) {
						return {
							gameday : gameday,
							start_time : start_time,
							match_id : item2.MATCH_ID,
							venue : item2.VENUE,
							home: item2.HOME,
							away: item2.AWAY,
							comment: item2.COMMENT
						};
					});
					game_grid_list = game_grid_list.concat(game_grid_row_list);
				}));
				this.createEditGrid({game_list:game_grid_list}, options_obj);
				return game_grid_list;
			},
			// overrides base class as sched_id does not have update btn
			// (but maybe it should)
			reconfig_infobtn: function(args_obj) {
				var colname = args_obj.colname;
				var idproperty = args_obj.idproperty;
				var swapcpane_flag = args_obj.swapcpane_flag;
				var newgrid_flag = args_obj.newgrid_flag;
				var entry_pt = args_obj.entry_pt;
				if (swapcpane_flag) {
					this.uistackmgr.switch_pstackcpane({idproperty:idproperty,
						p_stage:"config", entry_pt:entry_pty});
					if (!newgrid_flag) {
						// also swap grid if we are not generating a new one
						this.uistackmgr.switch_gstackcpane(idproperty, false, this.editgrid.schedInfoGrid);
					}
				}
			},
		});
});
