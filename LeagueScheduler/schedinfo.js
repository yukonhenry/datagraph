// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/_base/declare","dojo/_base/lang","dgrid/editor", "dojo/domReady!"], function(declare, lang, editor){
		return declare(null, {
			columnsdef_obj : {
				gameday_id: "Game day#",
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
			}
		})
});
