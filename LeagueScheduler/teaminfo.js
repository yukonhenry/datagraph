define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dijit/form/TextBox", "dijit/form/ValidationTextBox",
	"dijit/form/Select", "dgrid/editor",
	"dijit/form/Form", "dijit/layout/StackContainer", "dijit/layout/ContentPane",
	"LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/idmgrSingleton", "LeagueScheduler/editgrid",
	"put-selector/put", "dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, TextBox,
		ValidationTextBox, Select, editor, Form, StackContainer,
		ContentPane, baseinfo,
		baseinfoSingleton, idmgrSingleton, EditGrid, put){
		var constant = {
			idproperty_str:'team_id', db_type:'teamdb',
			dbname_str:'New Team List Name',
			vtextbox_str:'Enter Team List Name',
			ntextbox_str:'Enter Number of Teams',
			inputnum_str:'Number of Teams',
			text_node_str:'Team List Name',
			updatebtn_str:'Update Team Info',
			// entry_pt id's
			init:"init", fromdb:"fromdb",  fromdel:"fromdel",
		};
		return declare(baseinfo, {
			infogrid_store:null, idproperty:constant.idproperty_str,
			db_type:constant.db_type, idmgr_obj:null,
			//divstr_colname, divstr_db_type, widgetgen are all member var's
			// that have to do with the db_type radiobutton /
			// league select drop down
			divstr_colname:"", divstr_db_type:"rrdb", widgetgen:null,
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
							trim:true, propercase:true, style:"width:auto"
						}
					}, TextBox),
					// affinity field checkbox creation
					af_field_str: {label:"Division",
						//renderCell: lang.hitch(this, this.af_field_render)
					},
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
				/*
				var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : op_type;
				var topdiv_node = put("div");
				this.initabovegrid_UI(topdiv_node);
				var param_cpane = registry.byId(this.idmgr_obj.numcpane_id);
				param_cpane.addChild(topdiv_node)
				this.create_team_select(topdiv_node); */
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
				options_obj.text_node_str = "Team List Name";
				options_obj.grid_id = this.idmgr_obj.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.getserver_path = 'get_dbcol/'
				options_obj.db_type = constant.db_type;
				this.inherited(arguments);
			},
			getInitialList: function(num) {
				var info_list = new Array();
				for (var i = 1; i < num+1; i++) {
					info_list.push({team_id:i, team_name:"", af_field_str:""});
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
							selected:false, totalteams:item.totalteams}
						// data value is read from the store and corresponds to
						// stored div_id value for that row
						option_list.push(option_obj);
					})
				}
				var top_cpane = registry.byId(this.idmgr_obj.numcpane_id);
				var top_containernode = top_cpane.containerNode;
				var divselect_id = this.op_prefix+"tm_divselect_id";
				var divselect_widget = registry.byId(divselect_id);
				if (!divselect_widget) {
					put(top_containernode, "label.label_box[for=$]",
						divselect_id, "Select Division");
					var divselect_node = put(top_containernode,
						"select[id=$][name=$]", divselect_id, divselect_id);
					var eventoptions_obj = {option_list:option_list,
						topdiv_node:top_containernode};
					var divselect_widget = new Select({
						//name:name_str,
						options:option_list,
						onChange: lang.hitch(this, this.set_team_select, eventoptions_obj)
					}, divselect_node);
					divselect_widget.startup();
				}
				this.uistackmgr_type.switch_pstackcpane({idproperty:this.idproperty,
					p_stage: "preconfig", entry_pt:constant.init});
				this.uistackmgr_type.switch_gstackcpane(this.idproperty, true);
			},
			set_team_select: function(options_obj, divevent) {
				var option_list = options_obj.option_list;
				var match_option = arrayUtil.filter(option_list,
					function(item) {
						return item.value == divevent;
					})[0]
				this.totalrows_num = match_option.totalteams;
				var info_list = this.getInitialList(this.totalrows_num);
				if (this.is_newgrid_required()) {
					var columnsdef_obj = this.getcolumnsdef_obj();
					this.editgrid = new EditGrid({
						griddata_list:info_list,
						colname:this.activegrid_colname,
						grid:this.idmgr_obj.grid_id,
						idproperty:this.idproperty,
						server_path:"create_newdbcol/",
						server_key:'info_data',
						cellselect_flag:false,
						info_obj:this,
						uistackmgr_type:this.uistackmgr_type,
						storeutil_obj:this.storeutil_obj,
						db_type:this.db_type
					})
					this.editgrid.recreateSchedInfoGrid(columnsdef_obj);
					args_obj = {
						newgrid_flag:true
					}
				} else {
					this.editgrid.replace_store(this.activegrid_colname, info_list);
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
				/*
				// set the select dropdown for the team id column in the pref grid
				var divoption_list = options_obj.option_list;
				var pref_id = options_obj.pref_id;
				// go ahead and save the div_id that was selected
				var pref_obj = this.editgrid.schedInfoStore.get(pref_id);
				pref_obj.div_id = divevent;
				this.editgrid.schedInfoStore.put(pref_obj);
				// find the totalteams match corresponding to the div_id event
				var match_option = arrayUtil.filter(divoption_list,
					function(item) {
						return item.value == divevent;
					})[0]
				var option_list = [{label:"Select Team", value:"",
					selected:true}];
				for (var team_id = 1; team_id < match_option.totalteams+1;
					team_id++) {
					option_list.push({label:team_id.toString(), value:team_id, selected:false})
				}
				// get cell - use id for the div_id selected widget to identify
				// the row number
				var team_select_prefix = this.op_prefix+"prefteam_select";
				var team_select_id = team_select_prefix+pref_id+"_id";
				var team_select_widget = registry.byId(team_select_id);
				//var cell = pref_grid.cell(pref_id, 'team_id')
				//var select_widget = cell.element.widget;
				if (team_select_widget) {
					team_select_widget.set("options", option_list);
					*/
					/*
					team_select_widget.set("onChange", lang.hitch(this, function(event) {
						var pref_obj = this.editgrid.schedInfoStore.get(pref_id);
						pref_obj.team_id = event;
						this.editgrid.schedInfoStore.put(pref_obj);
					})) */
/*
					team_select_widget.startup()
				} */
			},
			af_field_render: function(object, data, node) {
				/*
				var pref_id = object.pref_id;
				var div_select_prefix = this.op_prefix+"prefdiv_select";
				var div_select_id = div_select_prefix+pref_id+"_id";
				var div_select_widget = registry.byId(div_select_id);
				var divstr_list = baseinfoSingleton.get_watch_obj('divstr_list',
					this.op_type, 'pref_id');
				var option_list = new Array();
				var eventoptions_obj = null;
				if (divstr_list && divstr_list.length > 0) {
					option_list.push({label:"Select Division", value:"",
						selected:false, totalteams:0});
					// get reference to team_id cell for this row
					// as we will modify it here once we find out the div_id
					// that has been been selected
					//var team_cell = this.editgrid.schedInfoGrid.cell(
					//	object.pref_id, 'team_id');
					//var team_widget = team_cell.element.widget;
					arrayUtil.forEach(divstr_list, function(item) {
						var option_obj = {label:item.divstr, value:item.div_id,
							selected:false, totalteams:item.totalteams}
						// data value is read from the store and corresponds to
						// stored div_id value for that row
						if (item.div_id == data) {
							option_obj.selected = true;
						}
						option_list.push(option_obj);
					})
					// create options list to pass to the team select event handler
					eventoptions_obj = {pref_id:pref_id,
						option_list:option_list.slice(1)}
				} else {
					option_list.push({label:"Select League first", selected:true, value:""});
				}
				// create select node to place widget - use passed in node as reference
				if (!div_select_widget) {
					var select_node = put(node, "select");
					div_select_widget = new Select({
						options:option_list, style:"width:auto",
						id:div_select_id,
					}, select_node)
				} else {
					div_select_widget.set("options", option_list)
					node.appendChild(div_select_widget.domNode)
				}
				if (eventoptions_obj) {
					div_select_widget.set("onChange",
						lang.hitch(this, this.set_gridteam_select, eventoptions_obj))
				}
				div_select_widget.startup();
				//node.appendChild(div_id_select.domNode); */
			},
			team_select_render: function(object, data, node) {
				/*
				var pref_id = object.pref_id; // equivalent to row
				var div_id = object.div_id;  // selected div_id for same row
				var team_select_prefix = this.op_prefix+"prefteam_select";
				var team_select_id = team_select_prefix+pref_id+"_id";
				var team_select_widget = registry.byId(team_select_id);
				var option_list = new Array();
				var divstr_list = baseinfoSingleton.get_watch_obj('divstr_list',
					this.op_type, 'pref_id');
				if (divstr_list && divstr_list.length > 0) {
					var match_obj = arrayUtil.filter(divstr_list,
						function(item) {
						return item.div_id == div_id;
					})[0];
					for (var team_id = 1; team_id < match_obj.totalteams+1;
						team_id++) {
						var option_obj = {label:team_id.toString(),
							value:team_id, selected:false};
						if (team_id == data) {
							option_obj.selected = true;
						}
						option_list.push(option_obj);
					}
				} else {
					option_list.push({label:"Select Division first", selected:true, value:""});
				}
				// create select node to place widget - use passed in node as reference
				if (!team_select_widget) {
					var select_node = put(node, "select");
					team_select_widget = new Select({
						options:option_list, style:"width:auto",
						id:team_select_id,
						onChange: lang.hitch(this, function(event) {
							var pref_obj = this.editgrid.schedInfoStore.get(pref_id);
							pref_obj.team_id = event;
							this.editgrid.schedInfoStore.put(pref_obj);
						})
					}, select_node)
				} else {
					team_select_widget.set("options", option_list)
					node.appendChild(team_select_widget.domNode);
				}
				team_select_widget.startup();
				//node.appendChild(div_id_select.domNode);
				*/
			},
			/*
			create_team_select: function(topdiv_node) {
				var team_select_id = this.op_prefix+"teamselect_id";
				var select_node = dom.byId(team_select_id)
				if (!select_node) {
					put(topdiv_node, "label.label_box[for=$]",
					team_select_id, "Select Team ID:");
					select_node = put(topdiv_node, "select[id=$][name=$]", team_select_id, team_select_id);
					var team_select = new Select({
						name:team_select_id,
						onChange:function(event) {
							console.log("create_team_select="+event)
						}
					})
				}
			}, */
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
				put(txtbtn_cpane.containerNode, "span[id=$]",
					this.getbtntxtid_obj("wizard", this.idproperty).text_id);
				put(txtbtn_cpane.containerNode, "button[id=$]",
					this.getbtntxtid_obj("wizard", this.idproperty).btn_id);
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
		});
});
