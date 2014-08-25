define(["dojo/_base/declare", "dojo/dom", "dojo/_base/lang", "dojo/_base/array",
	"dijit/registry", "dijit/form/NumberTextBox", "dijit/form/ValidationTextBox",
	"dijit/form/DateTextBox", "dijit/form/TimeTextBox", "dijit/form/Select",
	"dgrid/editor",
	"dijit/form/Form", "dijit/layout/ContentPane",
	"LeagueScheduler/baseinfo", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/idmgrSingleton",
	"put-selector/put", "dojo/domReady!"],
	function(declare, dom, lang, arrayUtil, registry, NumberTextBox,
		ValidationTextBox, DateTextBox, TimeTextBox, Select, editor, Form,
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
		};
		return declare(baseinfo, {
			idproperty:constant.idproperty_str,
			db_type:constant.db_type, today:null, idmgr_obj:null,
			//divstr_colname, divstr_db_type, widgetgen are all member var's
			// that have to do with the db_type radiobutton /
			// league select drop down
			divstr_colname:"", divstr_db_type:"rrdb", widgetgen:null,
			divstr_list:null,
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
							style:"width:auto",
						}}, NumberTextBox),
					// for embedded select objects autoSave is disabled as the saves
					// will happen manually after select event is captured
					// autoSave does NOT work
					div_id: {label:"Division",
						renderCell: lang.hitch(this, this.div_select_render)
					},
					team_id: {label:"Team ID",
						renderCell: lang.hitch(this, this.team_select_render)
					},
					/*
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
						}}, Select), */
					game_date: editor({label:'Game Date', autoSave:true,
						editorArgs:{
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
				return columnsdef_obj;
			},
			modifyserver_data: function(data_list, divstr_obj) {
				// see comments for fieldinfo modifyserver_data - process divstr
				// data; separately process data_list (especially dates)
				this.divstr_colname = divstr_obj.colname;
				this.divstr_db_type = divstr_obj.db_type;
				var config_status = divstr_obj.config_status;
				var info_list = divstr_obj.info_list;
				/*
				info_list.sort(function(a,b) {
					return a.div_id-b.div_id
				}) */
				// create radio button pair to select
				// schedule type - rr or tourn
				var infogrid_node = dom.byId(this.idmgr_obj.grid_id);
				var topdiv_node = put(infogrid_node, "-div");
				if (this.divstr_colname && this.divstr_db_type) {
					this.create_dbselect_radiobtnselect(this.idmgr_obj.radiobtn1_id,
						this.idmgr_obj.radiobtn2_id,
						this.idmgr_obj.league_select_id,
						this.divstr_db_type, this.divstr_colname, topdiv_node);
				} else {
					this.initabovegrid_UI(topdiv_node);
				}
				if (config_status) {
					var divstr_list = arrayUtil.map(info_list,
					function(item) {
						// note divfield_list and fieldcol_name can be undefined
						// if field collection has not been specified, and divfield
						// list created
						return {'divstr':item.div_age + item.div_gen,
							'div_id':item.div_id, 'totalteams':item.totalteams,
							//'divfield_list':item.divfield_list,
							//'fieldcol_name':item.fieldcol_name
						};
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
					if ('satisfy' in item) {
						// don't need to send satisfy fields
						delete item.satisfy;
					}
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
				var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : op_type;
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
				if (!('op_type' in options_obj))
					options_obj.op_type = this.op_type;
				options_obj.cellselect_flag = false;
				options_obj.text_node_str = "Preference List Name";
				options_obj.grid_id = this.idmgr_obj.grid_id;
				options_obj.updatebtn_str = constant.updatebtn_str;
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
			set_griddiv_select: function(divstr_list) {
				// called from baseinfoSingleton watch obj callback for division
				// string list
				// baseinfoSingleton has already done a check for existence of
				// editgrid obj and grid itself
				// Config status check is completed before calling this method, i.e.
				// the divstr_list should make up all rows of the cb collection
				// Reference newschedulerbase/createdivselect_dropdown
				// set_griddiv_select is asynchronous call, so always overwrite
				// divstr_list
				this.divstr_list = divstr_list;
				var pref_grid = this.editgrid.schedInfoGrid;
				// First create the option_list that will feed the select
				// dropdown for each cell in the 'division' column of the pref
				// grid.
				// initialize option_list - option_list object should carry all
				// metadata required to process division information when a
				// a particular div is selected
				var option_list = [{label:"Select Division", value:"",
					selected:true, totalteams:0}];
				arrayUtil.forEach(divstr_list, function(item, index) {
					option_list.push({label:item.divstr, value:item.div_id,
						selected:false, totalteams:item.totalteams,
						//fieldcol_name:item.fieldcol_name,
						//divfield_list:item.divfield_list
					})
				})
				var div_select_prefix = this.op_prefix+"prefdiv_select";
				for (var row_id = 1; row_id < this.totalrows_num+1; row_id++) {
					var div_select_id = div_select_prefix+row_id+"_id";
					var div_select_widget = registry.byId(div_select_id);
					if (div_select_widget) {
						// the select widget should be there, but check for existence anyway
						var copy_list = lang.clone(option_list);
						//var select_widget = cell.element.widget;
						div_select_widget.set("options", copy_list);
						// We need to pass the id of the originating select widget
						// and also an option_list definition (can be the original
						// or copy - just needed to find the totalteams value for
						// the selected div_id)
						// don't need entire option_list, especially the first header row
						var options_obj = {
							pref_id:row_id, option_list:option_list.slice(1)
						}
						div_select_widget.set("onChange", lang.hitch(this,
							this.set_gridteam_select, options_obj));
						div_select_widget.startup();
					}
					//var cell = pref_grid.cell(row_id, 'div_id')
					// ref https://github.com/SitePen/dgrid/blob/v0.3.15/doc/components/core-components/Grid.md
					// need to make new make of option_list for each use in select
				}
			},
			set_gridteam_select: function(options_obj, divevent) {
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
				if (team_select_widget) {
					// for team select ddown widget create option list; note there
					// is no callback defined when a particular team is selected;
					// instead the value is read when the update btn is pressed.
					team_select_widget.set("options", option_list);
					/*
					team_select_widget.set("onChange", lang.hitch(this, function(event) {
						var pref_obj = this.editgrid.schedInfoStore.get(pref_id);
						pref_obj.team_id = event;
						this.editgrid.schedInfoStore.put(pref_obj);
					})) */
					team_select_widget.startup()
				}
			},
			div_select_render: function(object, data, node) {
				/* Called when grid is created */
				var pref_id = object.pref_id;
				var div_select_prefix = this.op_prefix+"prefdiv_select";
				var div_select_id = div_select_prefix+pref_id+"_id";
				var div_select_widget = registry.byId(div_select_id);
				if (!this.divstr_list) {
					this.divstr_list = baseinfoSingleton.get_watch_obj(
						'divstr_list', this.op_type, 'pref_id');
				}
				var option_list = new Array();
				var eventoptions_obj = null;
				if (this.divstr_list && this.divstr_list.length > 0) {
					option_list.push({label:"Select Division", value:"",
						selected:false, totalteams:0});
					// get reference to team_id cell for this row
					// as we will modify it here once we find out the div_id
					// that has been been selected
					//var team_cell = this.editgrid.schedInfoGrid.cell(
					//	object.pref_id, 'team_id');
					//var team_widget = team_cell.element.widget;
					arrayUtil.forEach(this.divstr_list, function(item) {
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
				//node.appendChild(div_id_select.domNode);
			},
			team_select_render: function(object, data, node) {
				var pref_id = object.pref_id; // equivalent to row
				var div_id = object.div_id;  // selected div_id for same row
				var team_select_prefix = this.op_prefix+"prefteam_select";
				var team_select_id = team_select_prefix+pref_id+"_id";
				var team_select_widget = registry.byId(team_select_id);
				var option_list = new Array();
				if (!this.divstr_list) {
					this.divstr_list = baseinfoSingleton.get_watch_obj(
						'divstr_list', this.op_type, 'pref_id');
				}
				if (this.divstr_list && this.divstr_list.length > 0) {
					var match_obj = arrayUtil.filter(this.divstr_list,
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
			},
		});
});
