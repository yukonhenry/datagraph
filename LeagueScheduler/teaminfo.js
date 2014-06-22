define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dijit/form/TextBox", "dijit/form/DropDownButton",
	"dijit/form/Select", "dgrid/editor", "dijit/TooltipDialog",
	"dijit/form/CheckBox", "dijit/form/Button",
	"dijit/form/Form", "dijit/layout/StackContainer", "dijit/layout/ContentPane",
	"LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/idmgrSingleton", "LeagueScheduler/editgrid",
	"put-selector/put", "dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, TextBox,
		DropDownButton, Select, editor, TooltipDialog, CheckBox, Button,
		Form, StackContainer,
		ContentPane, baseinfo,
		baseinfoSingleton, idmgrSingleton, EditGrid, put){
		var constant = {
			idproperty_str:'team_id', db_type:'teamdb',
			dbname_str:'New Team List Name',
			vtextbox_str:'Enter Team List Name',
			ntextbox_str:'Enter Number of Teams',
			inputnum_str:'Number of Teams',
			text_node_str:'League/Division List Name',
			updatebtn_str:'Update Team Info',
			// entry_pt id's
			init:"init", fromdb:"fromdb",  fromdel:"fromdel",
		};
		return declare(baseinfo, {
			infogrid_store:null, idproperty:constant.idproperty_str,
			db_type:constant.db_type,
			//divstr_colname, divstr_db_type, widgetgen are all member var's
			// that have to do with the db_type radiobutton /
			// league select drop down
			divstr_colname:"", divstr_db_type:"rrdb", widgetgen:null,
			divfield_list:null,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
				this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
					id:this.idproperty, op_type:this.op_type});
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
					team_id: "ID",
					team_name: editor({label:"Team Name", autoSave:true,
						editorArgs:{
							trim:true, //propercase:true,
							style:"width:auto"
						}
					}, TextBox, "click"),
					af_field_str:{label:"Field Affinity",
						renderCell: lang.hitch(this, this.af_field_render)
					}
				};
				return columnsdef_obj;
				//return {};
			},
			getfixedcolumnsdef_obj: function() {
				// column definition for constraint satisfaction cpane display
				// after schedule is generated
				var columnsdef_obj = {
				}
				return columnsdef_obj;
			},
			modifyserver_data: function(data_list, divstr_obj) {
			},
			modify_toserver_data: function(raw_result) {
			},
			initialize: function(newgrid_flag, op_type) {
				var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : op_type;
				var param_cpane = registry.byId(this.idmgr_obj.numcpane_id);
				//var topdiv_node = put("div");
				this.initabovegrid_UI(param_cpane.containerNode);
				this.uistackmgr_type.switch_pstackcpane({idproperty:this.idproperty,
					p_stage: "preconfig", entry_pt:constant.init});
				// switch to blank cpane
				this.uistackmgr_type.switch_gstackcpane(this.idproperty, true);
				this.checkdelete_txtbtn();
			},
			getServerDBInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				if (!('op_type' in options_obj))
					options_obj.op_type = this.op_type;
				options_obj.idproperty = constant.idproperty_str;
				options_obj.server_path = "create_newdbcol/";
				options_obj.serverdata_key = 'info_list';
				options_obj.server_key = 'info_data';
				options_obj.cellselect_flag = false;
				options_obj.text_node_str = constant.text_node_str;
				options_obj.grid_id = this.idmgr_obj.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.getserver_path = 'get_dbcol/'
				options_obj.db_type = constant.db_type;
				this.inherited(arguments);
			},
			getInitialList: function(num, div_id) {
				var info_list = new Array();
				for (var i = 1; i < num+1; i++) {
					info_list.push({team_id:i, team_name:"", af_field_str:"",
					div_id:div_id, id:"div"+div_id+"team"+i});
				}
				return info_list;
			},
			get_gridhelp_list: function() {
				var gridhelp_list = [
					{id:'team_id', help_str:"Identifier, Non-Editable"},
					{id:'team_name', help_str:"Enter Team Name or Identifier"},
					{id:"af_field_str", help_str:"Select Field Preferences for Home Games, if any (default all fields assigned to division)"}
				]
				return gridhelp_list;
			},
			set_div_select: function(divstr_list) {
				var option_list = [{label:"Select Division", value:"",
						selected:true, totalteams:0}]
				if (divstr_list && divstr_list.length > 0) {
					arrayUtil.forEach(divstr_list, function(item) {
						var option_obj = {label:item.divstr, value:item.div_id,
							selected:false, totalteams:item.totalteams,
							divfield_list:item.divfield_list}
						// data value is read from the store and corresponds to
						// stored div_id value for that row
						option_list.push(option_obj);
					})
				}
				var divselect_id = this.op_prefix+"tm_divselect_id";
				var divselect_widget = registry.byId(divselect_id);
				if (!divselect_widget) {
					// place division select above grid (division select) should
					// always be visible when grid is present
					var topdiv_node = registry.byId(this.idmgr_obj.textbtncpane_id).containerNode;
					put(topdiv_node, "label.label_box[for=$]",
						divselect_id, "Select Division");
					var divselect_node = put(topdiv_node,
						"select[id=$][name=$]", divselect_id, divselect_id);
					var eventoptions_obj = {option_list:option_list.slice(1),
						topdiv_node:topdiv_node};
					var divselect_widget = new Select({
						//name:name_str,
						options:option_list,
						onChange: lang.hitch(this, this.set_team_select, eventoptions_obj)
					}, divselect_node);
				} else {
					// reset option list, with initial selection back to default
					divselect_widget.set("options", option_list);
				}
				divselect_widget.startup();
				this.uistackmgr_type.switch_pstackcpane({idproperty:this.idproperty,
					p_stage: "config", entry_pt:constant.init});
				//this.uistackmgr_type.switch_gstackcpane(this.idproperty, true);
			},
			set_team_select: function(options_obj, div_id_event) {
				var option_list = options_obj.option_list;
				var topdiv_node = options_obj.topdiv_node;
				var text_id = this.idmgr_obj.text_id;
				var span_node = dom.byId(text_id);
				if (!span_node) {
					put(topdiv_node, "span.empty_smallgap[id=$]", text_id);
				}
				var btn_id = this.idmgr_obj.btn_id;
				var btn_node = dom.byId(btn_id);
				if (!btn_node) {
					put(topdiv_node, "button[id=$]", this.idmgr_obj.btn_id);
				}
				var match_option = arrayUtil.filter(option_list,
					function(item) {
						return item.value == div_id_event;
					})[0]
				this.totalrows_num = match_option.totalteams;
				this.divfield_list = match_option.divfield_list;
				// name for the team list in teaminfo obj is restricted to be
				// a division id name
				this.activegrid_colname = this.divstr_colname;
				var info_list = this.getInitialList(this.totalrows_num,
					div_id_event);
				// query object for the store - use query to filter display to grid
				// in this example, show only the data where div_id matches -
				// div_id is determined by the division select
				var query_obj = {div_id:div_id_event}
				if (this.is_newgrid_required()) {
					var columnsdef_obj = this.getcolumnsdef_obj();
					this.editgrid = new EditGrid({
						griddata_list:info_list,
						colname:this.activegrid_colname,
						server_interface:this.server_interface,
						grid_id:this.idmgr_obj.grid_id,
						idproperty:this.idproperty,
						server_path:"create_newdbcol/",
						server_key:'info_data',
						cellselect_flag:false,
						info_obj:this,
						uistackmgr_type:this.uistackmgr_type,
						storeutil_obj:this.storeutil_obj,
						db_type:this.db_type
					})
					this.editgrid.recreateSchedInfoGrid(columnsdef_obj, query_obj);
					args_obj = {
						newgrid_flag:true
					}
				} else {
					this.editgrid.addreplace_store(this.activegrid_colname,
						info_list, query_obj);
					args_obj = {
						newgrid_flag:false
					}
				}
				args_obj.swapcpane_flag = true;
				args_obj.updatebtn_str = constant.updatebtn_str;
				args_obj.text_node_str = constant.text_node_str;
				args_obj.idproperty = this.idproperty;
				args_obj.colname = this.activegrid_colname;
				args_obj.entry_pt = constant.init;
				args_obj.op_type = this.op_type;
				this.reconfig_infobtn(args_obj);
			},
			af_field_render: function(object, data, node) {
				var team_id = object.team_id;
				// define parameters for the dialogtooltip that pops up in each
				// grid cell after ddown btn is clicked
				var content_str = "";
				var checkbox_list = new Array();
				if (this.divfield_list) {
					// create content_str for the checkboxes and labels that
					// will populate the tooltipdialog
					arrayUtil.forEach(this.divfield_list, function(field_id) {
						var idstr = this.op_prefix+"tmfield_checkbox"+team_id+
							field_id+"_id";
						content_str += '<input type="checkbox" data-dojo-type="dijit/form/CheckBox" style="color:green" id="'+
						idstr+
						'" value="'+field_id+'"><label for="'+idstr+'"> Field:<strong>'+field_id+'</strong></label><br>';
						checkbox_list.push(idstr);
					}, this)
				}
				var options_obj = {checkbox_list:checkbox_list, id:object.id}
				var button_id = this.op_prefix+"tmfield_btn"+team_id+"_id";
				// add button through adding declarative description into
				// content string instead of instantiating directly and adding
				// using addChild() - the latter does not work in a subsequent
				// loop when the checkbox content string has to be reassigned but
				// the button already exists.  Reassinging the content nullifies
				// the child button widget, but it is not possible to do another
				// addChild() with the button widget
				content_str += "<button data-dojo-type='dijit/form/Button' class ='info' type='submit' id='"+button_id+"'>Save</button>";
				/*
				var button_widget = registry.byId(button_id);
				if (!button_widget) {
					button_widget = new Button({
						label:"Save", class:"info", id:button_id, type:"submit",
						onClick: lang.hitch(this, this.af_dialogbtn_process,
							options_obj)
					})
				} */
				// define parameters for the tooltip dialog
				var tipdialog_prefix = this.op_prefix+"tmfield_tdialog";
				var tipdialog_id = tipdialog_prefix+team_id+"_id";
				var tipdialog_widget = registry.byId(tipdialog_id);
				if (!tipdialog_widget) {
					var tipdialog_widget = new TooltipDialog({
						id:tipdialog_id,
						content:content_str
					})
					//tipdialog_widget.addChild(button_widget);
				} else {
					tipdialog_widget.set("content", content_str);
					//tipdialog_widget.addChild(button_widget);
				}
				// define parameters for the ddown button embedded in grid cell
				var team_ddown_prefix = this.op_prefix+"tmfield_ddown";
				var team_ddown_id = team_ddown_prefix+team_id+"_id";
				var team_ddown_widget = registry.byId(team_ddown_id);
				if (!team_ddown_widget) {
					var ddown_node = put(node, "div");
					team_ddown_widget = new DropDownButton({
						label:"Field Affinity",
						class:"info",
						dropDown:tipdialog_widget
					}, ddown_node)
					//team_ddown_widget.startup();
				}
			},
			af_dialogbtn_process: function(options_obj, event) {
				//callback function for affinity field tooltipdialog button
				var checkbox_list = options_obj.checkbox_list;
				var id = options_obj.id;
				var value_str = "";
				// loop through each checkbox to see if there is a value
				arrayUtil.forEach(checkbox_list, function(checkbox_id) {
					var checkbox_widget = registry.byId(checkbox_id);
					if (checkbox_widget.get("checked")) {
						// create str to store (str of integer id elements)
						value_str += checkbox_widget.get("value")+',';
					}
				})
				// trim off last comma
				value_str = value_str.substring(0, value_str.length-1);
				if (this.editgrid) {
					var store_elem = this.editgrid.schedInfoStore.get(id);
					store_elem.af_field_str = value_str;
					this.editgrid.schedInfoStore.put(store_elem);
				}
				console.log("afprocess")
			},
			create_wizardcontrol: function(pcontainerdiv_node, gcontainerdiv_node) {
				// create cpane control for divinfo wizard pane under menubar
				this.pstackcontainer = new StackContainer({
					doLayout:false,
					style:"float:left; width:80%",
					id:this.idmgr_obj.pcontainer_id
				}, pcontainerdiv_node);
				// reset pane for initialization and after delete
				var reset_cpane = new ContentPane({
					id:this.idmgr_obj.resetcpane_id
				})
				this.pstackcontainer.addChild(reset_cpane)
				// add pref config (number) cpane
				// Note there is no number input form, but we will use the cpane
				// to host the dropdown select used in lieu of the input text box
				var team_cpane = new ContentPane({
					id:this.idmgr_obj.numcpane_id,
				})
				// Note form under the cpane like other infoobj's however
				/*
				var team_form = new Form({
					id:this.idmgr_obj.form_id
				})
				team_cpane.addChild(team_form); */
				this.pstackcontainer.addChild(team_cpane);
				// add txt + button cpane
				var txtbtn_cpane = new ContentPane({
					id:this.idmgr_obj.textbtncpane_id,
				})
				/*
				put(txtbtn_cpane.containerNode, "span[id=$]",
					this.idmgr_obj.text_id);
				put(txtbtn_cpane.containerNode, "button[id=$]",
					this.idmgr_obj.btn_id); */
				this.pstackcontainer.addChild(txtbtn_cpane)
				// create grid stack container and grid
				this.gstackcontainer = new StackContainer({
					doLayout:false,
					style:"clear:left",
					id:this.idmgr_obj.gcontainer_id
				}, gcontainerdiv_node);
				// add blank pane (for resetting)
				var blank_cpane = new ContentPane({
					id:this.idmgr_obj.blankcpane_id
				})
				this.gstackcontainer.addChild(blank_cpane);
				// add divinfo cpane and grid div
				var teamgrid_cpane = new ContentPane({
					id:this.idmgr_obj.gridcpane_id,
				})
				put(teamgrid_cpane.containerNode, "div[id=$]",
					this.idmgr_obj.grid_id);
				this.gstackcontainer.addChild(teamgrid_cpane);
			},
			checkdelete_txtbtn: function() {
				var text_id = this.idmgr_obj.text_id;
				var btn_id = this.idmgr_obj.btn_id;
				var btn_widget = registry.byId(btn_id);
				if (btn_widget) {
					btn_widget.destroyRecursive();
				}
				var text_node = dom.byId(text_id);
				if (text_node) {
					put(text_node, "!");
				}
				var btn_node = dom.byId(btn_id);
				if (btn_node) {
					put(btn_node, "!");
				}
			}
		});
});
