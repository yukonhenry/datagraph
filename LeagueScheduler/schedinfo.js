// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/dom", "dojo/_base/declare","dojo/_base/lang","dijit/registry", "dgrid/editor", "dojo/domReady!"],
	function(dom, declare, lang, registry, editor){
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
				select_reg.on("change", lang.hitch(this, function(evt) {
					var divisioncode = select_reg.get("value");
					this.server_interface.getServerData("get_scheddbcol/"+item,
						lang.hitch(this.schedutil_obj,
						           this.schedutil_obj.createEditGrid),
						{divisioncode:divisioncode}, options_obj);
				}));
			}
		});
});
