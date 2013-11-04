// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/dom", "dojo/_base/declare","dojo/_base/lang",
       "dojo/_base/array", "dijit/registry", "dgrid/editor", "dojo/domReady!"],
	function(dom, declare, lang, arrayUtil, registry, editor){
		return declare(null, {
			columnsdef_obj : {
				gameday_id: "Game day#",
				start_time: "Time",
				match_id: "Match ID",
				venue: "Venue",
				home: editor({label:"Home Team", field:"home", autoSave:true},"text","dblclick"),
				away: editor({label:"Away Team", field:"away", autoSave:true},"text","dblclick"),
				comment: "Comment"
			}, server_interface:null, schedutil_obj:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			getServerDBSchedInfo: function(options_obj) {
				var item = options_obj.item;
				this.schedutil_obj.makeVisible(dom.byId("schedDBSelectDiv"));
				var select_reg = registry.byId("schedDBDivisionSelect");
				this.schedutil_obj.generateDivSelectDropDown(select_reg);
				options_obj.serverdata_key = 'game_list'
				select_reg.on("change", lang.hitch(this, function(evt) {
					var divisioncode = select_reg.get("value");
					this.server_interface.getServerData("get_scheddbcol/"+item,
						lang.hitch(this.schedutil_obj,
						           this.schedutil_obj.createEditGrid),
						{divisioncode:divisioncode}, options_obj);
				}));
			},
			convertServerDataFormat: function(server_data) {
				game_array = server_data.game_list;
				var game_grid_list = new Array();
				var listindex = 0;
				arrayUtil.forEach(game_array, function(item, index) {
					var gameday_id = item.GAMEDAY_ID;
					var gameday_data = item.GAMEDAY_DATA;
					var start_time = item.START_TIME;
					var game_grid_row = {};
					// fill in the game day number and start time
					game_grid_row[gameday_column_key_CONST] = schedUtil.getCalendarMap(gameday_id);
					game_grid_row[time_column_key_CONST] = schedUtil.tConvert(start_time);
					arrayUtil.forEach(gameday_data, function(item2, index2) {
						game_grid_row[item2.VENUE] = item2.HOME + 'v' + item2.AWAY;
					});
					game_grid_list[listindex] = game_grid_row;
					listindex++;

				});
			}
		});
});
