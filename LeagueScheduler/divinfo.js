// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/_base/declare","dojo/_base/lang","dgrid/editor", "dojo/domReady!"], function(declare, lang, editor){
		return declare(null, {
			columnsdef_obj : {
				div_id: "Div ID",
				div_age: editor({label:"Age", field:"div_age", autoSave:true},"text","dblclick"),
				div_gen: editor({label:"Gender", field:"div_gen", autoSave:true}, "text", "dblclick"),
				totalteams: editor({label:"Total Teams", field:"totalteams", autoSave:true}, "text", "dblclick"),
				totalbrackets: editor({label:"Total RR Brackets", field:"totalbrackets", autoSave:true}, "text", "dblclick"),
				elimination_num: editor({label:"Elimination #", field:"elimination_num", autoSave:true}, "text", "dblclick"),
				elimination_type: editor({label:"Elimination Type", field:"elimination_type", autoSave:true}, "text", "dblclick"),
				field_id_str: editor({label:"Fields", field:"field_id_str", autoSave:true}, "text", "dblclick"),
				gameinterval: editor({label:"Inter-Game Interval (min)", field:"gameinterval", autoSave:true}, "text", "dblclick"),
				rr_gamedays: editor({label:"Number RR Gamedays", field:"rr_gamedays", autoSave:true}, "text", "dblclick")
			}, server_interface:null, schedutil_obj:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			getServerDBDivInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				var item = options_obj.item;
				this.server_interface.getServerData("get_dbcol/"+item,
					lang.hitch(this.schedutil_obj, this.schedutil_obj.createEditGrid), null, options_obj);
			}
		});
});
