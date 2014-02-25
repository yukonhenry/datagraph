// ref http://dojotoolkit.org/reference-guide/1.9/dojo/_base/declare.html
define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang",
	"dijit/registry", "dgrid/editor", "LeagueScheduler/baseinfo",
	"LeagueScheduler/baseinfoSingleton",
	"dojo/domReady!"],
	function(declare, dom, lang, registry, editor, baseinfo,
		baseinfoSingleton){
		var constant = {
			infobtn_id:"infoBtnNode_id",
			text_id:"infoTextNode_id",
			idproperty_str:"tourndiv_id",
			updatebtn_str:"Update Tourn Div Info",
			grid_id:"tourndivinfogrid_id",
			text_node_str: 'Schedule Name',
		};
		return declare(baseinfo, {
			infogrid_store:null, idproperty:constant.idproperty_str,
			text_node:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.text_node = dom.byId(constant.text_id);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
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
			initialize: function(newgrid_flag) {
				var form_name = "newdivinfo_form_id";
				var form_reg = registry.byId(form_name);
				var input_reg = registry.byId("newdivinfo_input_id");
				var divnum_reg = registry.byId("divnum_input_id");
				var tooltipconfig_list = [{connectId:['divnum_input_id'],
					label:"Specify Number of Divisions and press ENTER",
					position:['below','after']},
					{connectId:['newdivinfo_input_id'],
					label:"Specify Schedule Name",
					position:['below','after']}];
				var args_obj = {
					dbname_reg:input_reg,
					form_reg:form_reg,
					entrynum_reg:divnum_reg,
					server_path:"create_tournnewdbcol/",
					server_key:"divinfo_data",
					text_node_str: constant.text_node_str,
					grid_id:constant.grid_id,
					updatebtn_str:constant.updatebtn_str,
					tooltipconfig_list:tooltipconfig_list,
					newgrid_flag:newgrid_flag,
					cellselect_flag:false
				}
				this.showConfig(args_obj);
			},
			getServerDBInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				options_obj.serverdata_key = 'divinfo_list';
				options_obj.idproperty = constant.idproperty_str;
				options_obj.server_key = 'divinfo_data';
				options_obj.server_path = "create_tournnewdbcol/";
				options_obj.cellselect_flag = false;
				options_obj.text_node_str = "Division List Name";
				options_obj.grid_id = constant.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.getserver_path = 'get_tourndbcol/'
				this.inherited(arguments);
				//this.server_interface.getServerData("get_dbcol/"+item,
				//lang.hitch(this, this.createEditGrid), null, options_obj);
			},
			getInitialList: function(divnum) {
				var divInfo_list = new Array();
				for (var i = 1; i < divnum+1; i++) {
					divInfo_list.push({div_id:i, div_age:"", div_gen:"",
					                  totalteams:1,
					                  totalbrackets:1,
					                  elimination_num:1,
					                  elimination_type:"",field_id_str:"",
					                  gameinterval:1, rr_gamedays:1});
				}
				return divInfo_list;
			},
			getDivstr_list: function() {
				if (this.infogrid_store) {
					var divstr_list = this.infogrid_store.query().map(function(item) {
						return item.div_age+item.div_gen;
					}).filter(function(divstr) {
						return divstr != "";
					});
					var dup_list = this.schedutil_obj.detect_arrayduplicate(divstr_list);
					if (dup_list.length > 0) {
						alert("duplicate div info entries (or blank)");
					}
					return divstr_list;
				} else {
					return [];
				}
			},
			/*
			createEditGrid: function(server_data, options_obj) {
				this.inherited(arguments);
			}, */
		});
});
