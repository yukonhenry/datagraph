define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dijit/form/NumberTextBox", "dijit/form/ValidationTextBox",
	"dijit/form/DateTextBox", "dijit/form/TimeTextBox", "dijit/form/Select",
	"dgrid/editor",
	"dijit/form/Form", "dijit/layout/StackContainer", "dijit/layout/ContentPane",
	"LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/idmgrSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, NumberTextBox,
		ValidationTextBox, DateTextBox, TimeTextBox, Select, editor, Form, StackContainer,
		ContentPane, baseinfo,
		baseinfoSingleton, idmgrSingleton, put){
		var constant = {
			idproperty_str:'pref_id', db_type:'prefdb',
			dbname_str:'New Preference List Name',
			vtextbox_str:'Enter Preference List Name',
			ntextbox_str:'Enter Number of Preferences',
			inputnum_str:'Number of Preferences',
			text_node_str:'Preference List Name',
			updatebtn_str:'Update Preference Info',
			text_node_str: 'Preference List Name',
		};
		var wizconstant = {
			npcpane_id:"wiznumprefcpane_id",
		};
		return declare(baseinfo, {
			infogrid_store:null, idproperty:constant.idproperty_str,
			db_type:constant.db_type, today:null, idmgr_obj:null,
			//divstr_colname, divstr_db_type, widgetgen are all member var's
			// that have to do with the db_type radiobutton /
			// league select drop down
			divstr_colname:"", divstr_db_type:"rrdb", widgetgen:null,
			rendercell_flag:true,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
				this.today = new Date();
				this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
					id:this.idproperty, op_type:this.op_type});
			},
			getcolumnsdef_obj: function() {
				var columnsdef_obj = {
					pref_id: "ID",
					priority: editor({label:"Priority", autoSave:true,
						editorArgs:{
							constraints:{min:1, max:500},
							promptMessage:'Enter Priority Number (lower is higher priority)',
							invalidMessage:'Must be Non-zero integer',
							missingMessage:'Enter Priority',
							value:'1',
							//style:'width:6em',
							style:"width:auto",
						}}, NumberTextBox),
					// for embedded select objects autoSave is disabled as the saves
					// will happen manually after select event is captured
					// autoSave does NOT work
					/*
					div_id: {label:"Division",
						renderCell: lang.hitch(this, this.div_id_select_render)
					}, */
					div_id: editor({label:"Divison", autoSave:false,
						editorArgs:{
							style:"width:auto",
							name:"division_select",
							options:[{label:"Select League first", selected:true, value:""}],
						}}, Select),
					team_id: editor({label:"Team Id", autoSave:false,
						editorArgs:{
							//style:"width:auto",
							name:"team_select",
							options:[{label:"Select Div first", selected:true, value:""}]
						}}, Select),
					game_date: editor({label:'Game Date', autoSave:true,
						editorArgs:{
							//style:'width:120px'
							style:"width:auto",
						}
					}, DateTextBox),
					start_after: editor({label:'Start After', autoSave:true,
						editorArgs:{
							style:"width:auto",
						}
					}, TimeTextBox),
					end_before: editor({label:'End Before', autoSave:true,
						editorArgs:{
							style:"width:auto",
						}
					}, TimeTextBox),
				};
				return columnsdef_obj;
			},
			getfixedcolumnsdef_obj: function() {
				// column definition for constraint satisfaction cpane display
				// after schedule is generated
				var columnsdef_obj = {
					pref_id:"Preference ID",
					priority:"Priority",
					div_id:"Division",
					team_id:"Team ID",
					game_date:"Game Date",
					start_after:"Start After",
					end_before:"End Before",
					satisfy:"Met"
				}
			},
			modifyserver_data: function(data_list, divstr_obj) {
				// see comments for fieldinfo modifyserver_data - process divstr
				// data; separately process data_list (especially dates)
				this.divstr_colname = divstr_obj.colname;
				this.divstr_db_type = divstr_obj.db_type;
				var config_status = divstr_obj.config_status;
				var info_list = divstr_obj.info_list;
				// create radio button pair to select
				// schedule type - rr or tourn
				if (this.divstr_colname && this.divstr_db_type) {
					this.create_dbselect_radiobtnselect(this.idmgr_obj.radiobtn1_id,
						this.idmgr_obj.radiobtn2_id,
						this.idmgr_obj.league_select_id,
						this.divstr_db_type, this.divstr_colname);
				} else {
					this.initabovegrid_UI();
				}
				if (config_status) {
					var divstr_list = arrayUtil.map(info_list,
					function(item) {
						return {'divstr':item.div_age + item.div_gen,
							'div_id':item.div_id, 'totalteams':item.totalteams};
					})
					baseinfoSingleton.set_watch_obj('divstr_list', divstr_list,
						this.op_type, 'pref_id');
				}
				arrayUtil.forEach(data_list, function(item, index) {
					// save date str to pass into start and end time calc
					// (though it can be a dummy date)
					var game_date_str = item.game_date;
					var start_after_str = item.start_after;
					var end_before_str = item.end_before;
					item.game_date = new Date(game_date_str);
					item.start_after = new Date(game_date_str+' '+start_after_str);
					item.end_before = new Date(game_date_str+' '+end_before_str);
				});
				return data_list;
			},
			modify_toserver_data: function(raw_result) {
				// modify store data before sending data to server
				var newlist = new Array();
				// similar to field data, for the pref grid data convert Data objects to str
				// note we want to keep it as data objects inside of store to
				// maintain direct compatibility with Date and TimeTextBox's
				// and associated picker widgets.
				raw_result.map(function(item) {
					var newobj = lang.clone(item);
					newobj.game_date = newobj.game_date.toLocaleDateString();
					newobj.start_after = newobj.start_after.toLocaleTimeString();
					newobj.end_before = newobj.end_before.toLocaleTimeString();
					return newobj;
				}).forEach(function(obj) {
					newlist.push(obj);
				});
				return newlist;
			},
			initialize: function(newgrid_flag, op_type) {
				var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : "wizard";
				var form_reg = registry.byId(this.idmgr_obj.form_id);
				var form_node = form_reg.domNode;
				var dbname_reg = registry.byId(this.idmgr_obj.dbname_id);
				var inputnum_reg = null;
				if (!dbname_reg) {
					put(form_node, "label.label_box[for=$]",
						this.idmgr_obj.dbname_id, constant.dbname_str);
					var dbname_node = put(form_node,
						"input[id=$][type=text][required=true]",
						this.idmgr_obj.dbname_id)
					dbname_reg = new ValidationTextBox({
						value:'',
						regExp:'\\D[\\w]+',
						style:'width:12em',
						promptMessage:constant.vtextbox_str + '-start with letter or _, followed by alphanumeric or _',
						invalidMessage:'start with letter or _, followed by alphanumeric characters and _',
						missingMessage:constant.vtextbox_str
					}, dbname_node);
					put(form_node, "span.empty_smallgap");
					put(form_node, "label.label_box[for=$]",
						this.idmgr_obj.inputnum_id, constant.inputnum_str);
					var inputnum_node = put(form_node,
						"input[id=$][type=text][required=true]",
						this.idmgr_obj.inputnum_id);
					inputnum_reg = new NumberTextBox({
						value:'1',
						style:'width:5em',
						constraints:{min:1, max:500},
						promptMessage:constant.ntextbox_str,
						invalidMessage:'Must be Non-zero integer',
						missingMessage:constant.ntextbox_str+' (positive integer)'
					}, inputnum_node);
				} else {
					inputnum_reg = registry.byId(this.idmgr_obj.inputnum_id);
				}
				var tooltipconfig_list = [{connectId:[this.idmgr_obj.inputnum_id],
					label:"Specify Initial Number of Preferences and press ENTER",
					position:['below','after']},
					{connectId:[this.idmgr_obj.dbname_id],
					label:"Specify Preference List Name",
					position:['below','after']}];
				var args_obj = {
					dbname_reg:dbname_reg,
					form_reg:form_reg,
					entrynum_reg:inputnum_reg,
					server_path:"create_newdbcol/",
					server_key:'info_data',
					text_node_str: constant.text_node_str,
					grid_id:this.idmgr_obj.grid_id,
					updatebtn_str:constant.updatebtn_str,
					tooltipconfig_list:tooltipconfig_list,
					newgrid_flag:newgrid_flag,
					cellselect_flag:true,
					op_type:op_type
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
				options_obj.serverdata_key = 'info_list';
				options_obj.idproperty = constant.idproperty_str;
				options_obj.server_key = 'info_data';
				options_obj.server_path = "create_newdbcol/";
				options_obj.cellselect_flag = false;
				options_obj.text_node_str = "Preference List Name";
				options_obj.grid_id = this.idmgr_obj.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
				options_obj.getserver_path = 'get_dbcol/'
				options_obj.db_type = constant.db_type;
				this.inherited(arguments);
			},
			getInitialList: function(num) {
				var info_list = new Array();
				for (var i = 1; i < num+1; i++) {
					info_list.push({pref_id:i, div_id:"", team_id:"",
						priority:i, game_date:this.today,
						start_after:new Date(2014,0,1,8,0,0),
						end_before:new Date(2014,0,1,17,0,0)});
				}
				return info_list;
			},
			get_gridhelp_list: function() {
				var gridhelp_list = [
					{id:'pref_id', help_str:"Identifier, Non-Editable"},
					{id:'priority', help_str:"Priority of the preference - assign positive integer, lower value is higher priority"},
					{id:'div_id', help_str:"Select Division identifier after division list has been selected"},
					{id:'team_id', help_str:"Select Team ID after division has been selected"},
					{id:'game_date', help_str:"Select Date where preference applies"},
					{id:'start_after', help_str:"Choose preference start time - game should start after this time"},
					{id:'end_before', help_str:"Choose preference end time - game should end before this time - Note 'end_before' can be before 'start_after' times (which case there is a blocked out time range sandwiched between two available time ranges"}]
				return gridhelp_list;
			},
			set_gridselect: function(divstr_list) {
				// called from baseinfoSingleton watch obj callback for division
				// string list
				// baseinfoSingleton has already done a check for existence of
				// editgrid obj and grid itself
				// Config status check is completed before calling this method, i.e.
				// the divstr_list should make up all rows of the cb collection
				// Reference newschedulerbase/createdivselect_dropdown
				var pref_grid = this.editgrid.schedInfoGrid;
				// First create the option_list that will feed the select
				// dropdown for each cell in the 'division' column of the pref
				// grid.
				// initialize option_list
				var option_list = [{label:"Select Division", value:"",
					selected:true, totalteams:0}];
				arrayUtil.forEach(divstr_list, function(item, index) {
					option_list.push({label:item.divstr, value:item.div_id,
						selected:false, totalteams:item.totalteams})
				})
				for (var row_id = 1; row_id < this.totalrows_num+1; row_id++) {
					var cell = pref_grid.cell(row_id, 'div_id')
					// ref https://github.com/SitePen/dgrid/blob/v0.3.15/doc/components/core-components/Grid.md
					// need to make new make of option_list for each use in select
					var copy_list = lang.clone(option_list);
					var select_widget = cell.element.widget;
					select_widget.set("options", copy_list);
					// We need to pass the id of the originating select widget
					// and also an option_list definition (can be the original
					// or copy - just needed to find the totalteams value for
					// the selected div_id)
					var options_obj = {
						pref_id:row_id, option_list:copy_list
					}
					select_widget.set("onChange", lang.hitch(this,
						this.set_gridteamselect, options_obj));
					select_widget.startup();
				}
			},
			set_gridteamselect: function(options_obj, divevent) {
				// set the select dropdown for the team id column in the pref grid
				var divoption_list = options_obj.option_list;
				var pref_id = options_obj.pref_id;
				var pref_grid = this.editgrid.schedInfoGrid;
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
				var cell = pref_grid.cell(pref_id, 'team_id')
				var select_widget = cell.element.widget;
				select_widget.set("options", option_list);
				select_widget.set("onChange", lang.hitch(this, function(event) {
					var pref_obj = this.editgrid.schedInfoStore.get(pref_id);
					pref_obj.div_id = divevent;
					pref_obj.team_id = event;
					this.editgrid.schedInfoStore.put(pref_obj);
				}))
				select_widget.startup();
			},
			create_gridselect: function(grid) {
				var divstr_list = baseinfoSingleton.get_watch_obj(
					'divstr_list', this.op_type, 'pref_id');
				if (divstr_list && divstr_list.length > 0) {
					this.set_gridselect(divstr_list);
				}
			},
			div_id_select_render: function(object, data, node) {
				if (this.rendercell_flag) {
					var divstr_list = baseinfoSingleton.get_watch_obj('divstr_list',
						this.op_type, 'pref_id');
					var option_list = new Array();
					if (divstr_list && divstr_list.length > 0) {
						option_list.push({label:"Select Division", value:"",
							selected:false, totalteams:0});
						arrayUtil.forEach(divstr_list, function(item) {
							var option_obj = {label:item.divstr, value:item.div_id,
								selected:false, totalteams:item.totalteams}
							if (item.div_id == data) {
								option_obj.selected = true;
							}
							option_list.push(option_obj);
						})
					} else {
						option_list.push({label:"Select League first", selected:true, value:""});
					}
					var select_node = put(node, "select");
					var div_id_select = new Select({
						options:option_list, style:"width:auto"}, select_node)
					div_id_select.startup();
					//node.appendChild(div_id_select.domNode);
				}
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
				var pref_cpane = new ContentPane({
					id:wizconstant.npcpane_id,
				})
				var pref_form = new Form({
					id:this.idmgr_obj.form_id
				})
				pref_cpane.addChild(pref_form);
				this.pstackcontainer.addChild(pref_cpane);
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
				var prefgrid_cpane = new ContentPane({
					id:this.idmgr_obj.gridcpane_id,
				})
				put(prefgrid_cpane.containerNode, "div[id=$]",
					this.idmgr_obj.grid_id);
				this.gstackcontainer.addChild(prefgrid_cpane);
			},
		});
});
