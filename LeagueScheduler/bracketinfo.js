// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dbootstrap", "dojo/dom", "dojo/_base/declare","dojo/_base/lang","dojo/_base/array", "dojo/store/Memory","dijit/registry", "dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection","LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
	function(dbootstrap, dom, declare, lang, arrayUtil, Memory, registry, OnDemandGrid, editor, Keyboard, Selection, baseinfoSingleton){
		return declare(null, {
			columnsdef_obj : {
				bracket_id: "Bracket ID",
				team_list:editor({label:"Team List", field:"team_list", autoSave:true},"text","dblclick"),
			}, totalbrackets:0, server_interface:null, schedutil_obj:null,
			bracketinfo_name:"", bracketinfo_store:null, bracketinfo_grid:null,
			bracketinfotext_node:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			createBracketInfoGrid: function(div_str) {
				this.bracketinfotext_node.innerHTML="Enter Bracket Info for "+div_str;
				var bracketinfo_list = new Array();
				for (var i = 1; i < this.totalbrackets+1; i++) {
					bracketinfo_list.push({bracket_id:i,team_list:""});
				}
				this.bracketinfo_store = new Memory({data:bracketinfo_list,
					idProperty:"bracket_id"});
				this.bracketinfo_grid = new (declare([OnDemandGrid, Keyboard, Selection])) ({
					store: this.bracketinfo_store,
					columns: this.columnsdef_obj
				}, this.bracketinfo_name);
				this.bracketinfo_grid.startup();
			},
			cleanup: function() {
				if (this.bracketinfo_grid) {
					dom.byId(this.bracketinfo_name).innerHTML = "";
					delete this.bracketinfo_grid;
					delete this.bracketinfo_store;
				}
			},
			getServerDBSchedInfo: function(options_obj) {
				var item = options_obj.item;
				if (this.schedutil_obj.editGrid) {
					this.schedutil_obj.editGrid.cleanup();
					delete this.schedutil_obj.editGrid;
					this.select_reg_handle.remove();
				}
				if (!this.schedDBSelectDiv_dom) {
					this.schedDBSelectDiv_dom = dom.byId("schedDBSelectDiv");
					baseinfoSingleton.set_select_dom(this.schedDBSelectDiv_dom);
				}
				this.schedutil_obj.makeVisible(this.schedDBSelectDiv_dom);
				// we don't necessariy need to call get_dbcol again if select_reg already exists (we don't need to recreate the drop down)
				this.server_interface.getServerData("get_dbcol/"+item, lang.hitch(this, function(data) {
					this.divinfo_list = data.divinfo_list;
					if (!this.select_reg) {
						this.select_reg = registry.byId("schedDBDivisionSelect");
						baseinfoSingleton.set_select_reg(this.select_reg);
						this.schedutil_obj.generateDivSelectDropDown(this.select_reg, this.divinfo_list);
					}
					options_obj.serverdata_key = 'game_list';
					this.select_reg_handle = this.select_reg.on("change", lang.hitch(this, function(evt) {
						var divisioncode = this.select_reg.get("value");
						options_obj.divisioncode = divisioncode;
						options_obj.idproperty = 'match_id';
						options_obj.cellselect_flag = false;
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
				this.schedutil_obj.createEditGrid({game_list:game_grid_list}, options_obj);
				return game_grid_list;
			}
		});
});
