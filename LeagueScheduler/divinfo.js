// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dbootstrap", "dojo/_base/declare", "dojo/dom", "dojo/_base/lang",
	"dijit/registry", "dgrid/editor",
	"LeagueScheduler/baseinfoSingleton", "LeagueScheduler/newscheduler",
	"dijit/form/Button",
	"dojo/domReady!"],
	function(dbootstrap, declare, dom, lang, registry, editor, baseinfoSingleton,
		newscheduler, Button){
		var constant = {
			infobtn_id:"infoBtnNode_id",
			text_id:"infoTextNode_id",
			idproperty_str:"div_id",
			updatebtn_str:"Update Div Info",
			grid_id:"divinfogrid_id",
			text_node_str: 'Schedule Name',
		};
		return declare(null, {
			server_interface:null, schedutil_obj:null, storeutil_obj:null,
			colname:"", infogrid_store:null, idproperty:constant.idproperty_str,
			text_node:null, uistackmgr:null, updatebtn_str:constant.updatebtn_str,
			editgrid_obj:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.text_node = dom.byId(constant.text_id);
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
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
				};
				return columnsdef_obj;
			},
			set_obj: function(schedutil_obj, storeutil_obj) {
				this.schedutil_obj = schedutil_obj;
				this.storeutil_obj = storeutil_obj;
			},
			initialize: function(evt) {
				var form_name = "newdivinfo_form_id";
				var form_reg = registry.byId(form_name);
				var input_reg = registry.byId("newdivinfo_input_id");
				var divnum_reg = registry.byId("divnum_input_id");

				var newScheduler = new newscheduler({dbname_reg:input_reg,
					form_reg:form_reg,
					entrynum_reg:divnum_reg,
					server_interface:this.server_interface,
					schedutil_obj:this.schedutil_obj,
					info_obj: this, idproperty:constant.idproperty_str,
					server_path:"create_newdbcol/",
					text_node_str: constant.text_node_str,
					grid_id:constant.grid_id,
					text_node:this.text_node,
					updatebtn_str:constant.updatebtn_str,
					uistackmgr:this.uistackmgr,
					storeutil_obj:this.storeutil_obj
				});
				var tooltipconfig_list = [{connectId:['divnum_input_id'],
					label:"Specify Number of Divisions and press ENTER",
					position:['below','after']},
					{connectId:['newdivinfo_input_id'],
					label:"Specify Schedule Name",
					position:['below','after']}];
				newScheduler.showConfig(tooltipconfig_list);
			},
			getServerDBInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				var item = options_obj.item;
				this.colname = item;
				options_obj.serverdata_key = 'divinfo_list';
				options_obj.idproperty = constant.idproperty_str;
				options_obj.server_key = 'divinfo_data';
				options_obj.server_path = "create_newdbcol/";
				options_obj.cellselect_flag = false;
				options_obj.text_node_str = "Division List Name";
				options_obj.grid_id = constant.grid_id;
				options_obj.text_node = this.text_node;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.uistackmgr = this.uistackmgr;
				options_obj.storeutil_obj = this.storeutil_obj;
				this.server_interface.getServerData("get_dbcol/"+item,
					lang.hitch(this.schedutil_obj, this.schedutil_obj.createEditGrid), null, options_obj);
			},
			getInitialList: function(divnum) {
				var divInfo_list = new Array();
				for (var i = 1; i < divnum+1; i++) {
					divInfo_list.push({div_id:i, div_age:"", div_gen:"",
					                  totalteams:1, totalbrackets:1,
					                  elimination_num:1,
					                  elimination_type:"",field_id_str:"",
					                  gameinterval:1, rr_gamedays:1});
				}
				return divInfo_list;
			},
			getDivstr_list: function() {
				var divstr_list = this.infogrid_store.query().map(function(item) {
					return item.div_age+item.div_gen;
				});
				return divstr_list;
			},
			is_serverdata_required: function(options_obj) {
				return (options_obj.item != this.colname)?true:false;
			},
			is_newgrid_required: function() {
				if (!this.editgrid_obj)
					return true;
				else
					return (this.editgrid_obj.schedInfoGrid)?false:true;
			}
		});
});
