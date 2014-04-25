define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare",
	"dojo/_base/lang", "dojo/Stateful",
	"dojo/_base/array", "dojo/keys", "dojo/store/Memory", "dojo/store/Observable",
	"dijit/registry", "dijit/Tooltip",
	"dijit/form/ValidationTextBox","dijit/form/Select", "dijit/form/Button",
	"dijit/form/NumberSpinner", "dijit/form/DateTextBox",
	"dijit/layout/ContentPane", "dgrid/Grid",
	"dgrid/OnDemandGrid", "dgrid/Keyboard", "dgrid/Selection",
	"LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/widgetgen",
	"put-selector/put", "underscore-min", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, Stateful, arrayUtil, keys,
		Memory, Observable, registry, Tooltip, ValidationTextBox, Select, Button,
		NumberSpinner, DateTextBox, ContentPane, Grid,
		OnDemandGrid, Keyboard, Selection, EditGrid,
		baseinfoSingleton, WidgetGen, put) {
		var constant = {
			idproperty_str:'newsched_id',
			form_name:'newsched_form_id',
			scinput_div:'seasoncalendar_input',
			radio1_id:'scradio1_id',
			radio2_id:'scradio2_id',
			league_select_id:'scleague_select_id',
			fg_select_id:'fg_select_id',
			statustxt_id:'schedstatustxt_id',
			tabcontainer_id:'tabcontainer_id',
			newdivcpane_id:'newdivcpane_id',
			newdivcpane_txt_id:'newdivcpane_txt_id',
			newdivcpane_grid_id:'newdivcpane_grid_id',
			newdivcpane_schedheader_id:'newdivcpane_schedheader_id',
			newdivcpane_schedgrid_id:'newdivcpane_schedgrid_id',
			newfieldcpane_id:'newfieldcpane_id',
			newfieldcpane_txt_id:'newfieldcpane_txt_id',
			newfieldcpane_grid_id:'newfieldcpane_grid_id',
			newfieldcpane_schedheader_id:'newfieldcpane_schedheader_id',
			newfieldcpane_schedgrid_id:'newfieldcpane_schedgrid_id',
			newteamcpane_id:'newteamcpane_id',
			newteamcpane_txt_id:'newteamcpane_txt_id',
			newteamcpane_grid_id:'newteamcpane_grid_id',
			newteamcpane_schedheader_id:'newteamcpane_schedheader_id',
			newteamcpane_schedgrid_id:'newteamcpane_schedgrid_id',
			newteamcpane_select_id:'newteamcpane_select_id',
			newfaircpane_id:'newfaircpane_id',
			newfaircpane_txt_id:'newfaircpane_txt_id',
			newfaircpane_grid_id:'newfaircpane_grid_id',
			newfaircpane_schedheader_id:'newfaircpane_schedheader_id',
			newfaircpane_schedgrid_id:'newfaircpane_schedgrid_id',
			newfaircpane_select_id:'newfaircpane_select_id',
			defaultselect_db_type:'rrdb',
			db_type:'newscheddb'
		};
		var newschedwatch_class = declare([Stateful],{
			leagueselect_flag:false,
			fgselect_flag:false,
			league_fg_flag:false
		})
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			newsched_name:"", newsched_dom:"",
			schedutil_obj:null, storeutil_obj:null,
			info_obj:null, idproperty:constant.idproperty_str,
			server_path:"", server_key:"",
			seasondates_btn_reg:null,
			callback:null, text_node_str:"", tooltip:null,
			start_dtbox:null, end_dtbox:null, sl_spinner:null,
			seasonstart_handle:null, seasonend_handle:null,
			seasonlength_handle:null, league_select:null, fg_select:null,
			event_flag:false, uistackmgr:null, newschedwatch_obj:null,
			selectexists_flag:false,
			league_select_value:"", fg_select_value:"", widgetgen:null,
			current_db_type:constant.defaultselect_db_type,
			tabcontainer_reg:null,
			cpane_grid_id_mapobj:null, cpane_schedgrid_id:null,
			info_grid_mapobj:null, info_handle_mapobj:null, gridmethod_mapobj:null,
			sched_store_mapobj:null, sched_grid_mapobj:null,
			calendarmap_obj:null, common_calendardate_list:null,
			divselect_handle:null,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
				this.newschedwatch_obj = new newschedwatch_class();
				this.newschedwatch_obj.watch('leagueselect_flag',
					lang.hitch(this, function(name, oldValue, value) {
						this.newschedwatch_obj.set('league_fg_flag',
							this.newschedwatch_obj.get('fgselect_flag') && value);
					}));
				this.newschedwatch_obj.watch('fgselect_flag',
					lang.hitch(this, function(name, oldValue, value) {
						this.newschedwatch_obj.set('league_fg_flag',
							this.newschedwatch_obj.get('leagueselect_flag') && value);
					}));
				// create dictionaries/objects that map idproperty to idproperty-specific
				// id's or objects
				// w each dict mapping idproperty to either a schedule grid or the
				// corresponding .on handler
				this.cpane_grid_id_mapobj = {div_id:constant.newdivcpane_grid_id,
					field_id:constant.newfieldcpane_grid_id,
					team_id:constant.newteamcpane_grid_id,
					fair_id:constant.newfaircpane_grid_id}
				this.cpane_schedgrid_id_mapobj = {
					div_id:constant.newdivcpane_schedgrid_id,
					field_id:constant.newfieldcpane_schedgrid_id,
					team_id:constant.newteamcpane_schedgrid_id,
					fair_id:constant.newfaircpane_schedgrid_id}
				this.cpane_schedheader_id_mapobj = {
					div_id:constant.newdivcpane_schedheader_id,
					field_id:constant.newfieldcpane_schedheader_id,
					team_id:constant.newteamcpane_schedheader_id,
					fair_id:constant.newfaircpane_schedheader_id}
				this.info_grid_mapobj = {div_id:null, field_id:null, team_id:null,
					fair_id:null};
				this.info_handle_mapobj = {div_id:null, field_id:null,
					team_id:null, fair_id:null};
				this.gridmethod_mapobj = {
					div_id:lang.hitch(this, this.createdivsched_grid),
					field_id:lang.hitch(this, this.createfieldsched_grid),
					team_id:lang.hitch(this, this.createteamsched_grid),
					fair_id:lang.hitch(this, this.createfairsched_grid)};
				this.sched_store_mapobj = {div_id:null, field_id:null,
					team_id:null, fair_id:null};
				this.sched_grid_mapobj = {div_id:null, field_id:null, team_id:null,
					fair_id:null};
				this.calendarmap_obj = new Object();
			},
			initialize: function(arg_obj) {
				this.form_reg = registry.byId(constant.form_name);
				//this.dbname_reg = registry.byId("newsched_input_id");
				// put selector documentation
				// http://davidwalsh.name/put-selector
				// https://github.com/kriszyp/put-selector
				// first check to see if the domNode has already been created by
				// seeing the dom node can be retrieved
				var sched_input = dom.byId("newsched_input_id");
				if (!sched_input) {
					put(this.form_reg.domNode, "label.label_box[for=newsched_input_id]",
						'New Schedule Name:');
					sched_input = put(this.form_reg.domNode,
						"input#newsched_input_id[type=text][required=true]");
					this.dbname_reg = new ValidationTextBox({
						value:'PHMSA2014',
						regExp:'[\\w]+',
						promptMessage:'Enter New Schedule - only alphanumeric characters and _',
						invalidMessage:'only alphanumeric characters and _',
						missingMessage:'enter schedule name'
					}, sched_input);
				} else {
					// domnode already exists, get widget that should also be there
					// NOTE: registry.byNode() does not work -
					// sched_input is an HTML Input element
					// however, this.dbname_reg.domNode is an HTML Div Element
					// (not sure exactly why)
					// Anyway, is sched_input exists, then this.dbname_reg should exist
					// alternatively, use:
					//this.dbname_reg = registry.byId("newsched_input_id");
					// DON"T use below:
					//this.dbname_reg = registry.byNode(sched_input);
				}

				this.seasondates_btn_reg = registry.byId("seasondates_btn");
				this.showConfig();
			},
			set_obj: function(schedutil_obj, storeutil_obj) {
				this.schedutil_obj = schedutil_obj;
				this.storeutil_obj = storeutil_obj;
			},
			showConfig: function() {
				this.uistackmgr.switch_pstackcpane({idproperty:this.idproperty,
					p_stage:"preconfig", entry_pt:"init"});
				this.uistackmgr.switch_gstackcpane(this.idproperty, true);
				if (!this.tooltip) {
					var tooltipconfig = {connectId:['newsched_input_id'],
						label:"Enter Schedule Name and press ENTER",
						position:['below','after']};
					this.tooltip = new Tooltip(tooltipconfig);
				}
				if (this.keyup_handle)
					this.keyup_handle.remove();
				this.keyup_handle = this.dbname_reg.on("keyup", lang.hitch(this, this.processdivinfo_input));
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(event) {
				if (event.keyCode == keys.ENTER) {
					if (this.form_reg.validate()) {
						confirm('Input format is Valid, creating new Schedule DB');
						this.newsched_name = this.dbname_reg.get("value");
						if (!this.storeutil_obj.nodupdb_validate(this.newsched_name,
							this.idproperty)) {
							alert("Selected sched name already exists, choose another");
							return;
						}
						if (this.keyup_handle)
							this.keyup_handle.remove();
						if (!this.widgetgen) {
							this.create_widgets(constant.defaultselect_db_type);
						} else {
							// sometimes widgetgen might already exist as an
							// existing newsched may have been first selected from
							// the menu before a new newsched was selected. In this
							// case reset and reuse existing widgets
							// First reset watch objects
							this.reset_newschedwatch_obj();
							// reload widgets
							this.reload_widgets(constant.defaultselect_db_type);
						}
						this.uistackmgr.switch_pstackcpane({
							idproperty:this.idproperty, p_stage:"config",
							entry_pt:"init"});
					} else {
						alert('Input name is Invalid, please correct');
					}
				}
			},
			// callback function when dbtype radiobutton is changed
			radio1_callback: function(select_id, event) {
				if (event) {
					this.widgetgen.swap_league_select_db(select_id, 'rrdb');
					this.current_db_type = 'rrdb';
				}
			},
			radio2_callback: function(select_id, event) {
				if (event) {
					this.widgetgen.swap_league_select_db(select_id, 'tourndb');
					this.current_db_type = 'tourndb';
				}
			},
			removefrom_select: function(db_type, index) {
				// remove entries from the div or field group dropdown
				if (db_type == 'rrdb' || db_type == 'tourndb') {
					this.league_select.removeOption(index);
				} else if (db_type == 'fielddb') {
					this.fg_select.removeOption(index)
				}
			},
			addto_select: function(db_type, label, insertIndex) {
				var soption_obj = {label:label, value:insertIndex+1,
					selected:false};
				// need to take care of tourndb also below
				// we should be able to do a simple OR between rrdb and
				// tourndb as this.league_select should be pointing the current
				// db_type
				if (db_type == 'rrdb' || db_type == 'tourndb') {
					this.league_select.addOption(soption_obj);
				} else if (db_type == 'fielddb') {
					this.fg_select.addOption(soption_obj);
				}
			},
			is_serverdata_required: function(options_obj) {
				return (options_obj.item != this.newsched_name)?true:false;
			},
			is_newgrid_required: function() {
				return false;
			},
			getServerDBInfo: function(options_obj) {
				this.newsched_name = options_obj.item;
				this.server_interface.getServerData(
					'get_dbcol/'+constant.db_type+'/'+this.newsched_name,
					lang.hitch(this, this.create_schedconfig));
			},
			create_schedconfig: function(adata) {
				var param_obj = adata.param_obj;
				var divcol_name = param_obj.divcol_name;
				var divdb_type = param_obj.divdb_type;
				var fieldcol_name = param_obj.fieldcol_name;
				if (!this.widgetgen) {
					this.create_widgets(divdb_type, divcol_name,
						fieldcol_name);
				} else {
					// reset watch object fields
					this.reset_newschedwatch_obj();
					// reload widgets
					this.reload_widgets(divdb_type, divcol_name, fieldcol_name);
				}
				this.uistackmgr.switch_pstackcpane({
					idproperty:this.idproperty, p_stage:"config",
					entry_pt:"fromdb"});
				this.uistackmgr.switch_gstackcpane(this.idproperty, true);
			},
			create_widgets: function(divdb_type, divcol_name, fieldcol_name) {
				var divcol_name = (typeof divcol_name === "undefined" || divcol_name === null) ? "" : divcol_name;
				var fieldcol_name = (typeof fieldcol_name === "undefined" || fieldcol_name === null) ? "" : fieldcol_name;
				this.newsched_dom = dom.byId("newsched_text");
				this.newsched_dom.innerHTML = "Schedule Name: <b>"+this.newsched_name+"</b>";
				this.widgetgen = new WidgetGen({
					storeutil_obj:this.storeutil_obj,
					server_interface:this.server_interface
				});
				var scinput_dom = dom.byId(constant.scinput_div);
				this.widgetgen.create_dbtype_radiobtn(scinput_dom,
					constant.radio1_id, constant.radio2_id, divdb_type,
					this, this.radio1_callback, this.radio2_callback,
					constant.league_select_id);
				// create league info dropdowns
				var lsargs_obj = {
					topdiv_node:scinput_dom,
					select_id:constant.league_select_id,
					init_db_type:divdb_type,
					init_colname:divcol_name,
					onchange_callback:lang.hitch(this, function(evt) {
						this.newschedwatch_obj.set('leagueselect_flag',
							evt!="");
						this.league_select_value = evt;
					}),
					name_str:"league select",
					label_str:"Select League",
					put_trail_spacing:"span.empty_gap"
				}
				this.league_select = this.widgetgen.create_select(lsargs_obj);
				// create field group dropdown
				var fgargs_obj = {
					topdiv_node:scinput_dom,
					select_id:constant.fg_select_id,
					init_db_type:'fielddb',
					init_colname:fieldcol_name,
					onchange_callback:lang.hitch(this, function(evt) {
						this.newschedwatch_obj.set('fgselect_flag',
							evt!="");
						this.fg_select_value = evt;
					}),
					name_str:"fg_select",
					label_str:"Select Field Group",
					put_trail_spacing:"span.empty_gap"
				}
				this.fg_select = this.widgetgen.create_select(fgargs_obj);

				var btn_node = dom.byId("schedparambtn_id");
				if (!btn_node) {
					btn_node = put(scinput_dom,
						"button.dijitButton#schedparambtn_id[type=button]");
					var btn_tooltipconfig = {
						connectId:['schedparambtn_id'],
						label:"Ensure League and Field Group are Selected",
						position:['above','after']};
					var schedule_btn = new Button({
						label:"Generate",
						disabled:true,
						class:"success",
						onClick: lang.hitch(this, this.send_generate)
					}, btn_node);
					schedule_btn.startup();
					var btn_tooltip = new Tooltip(btn_tooltipconfig);
					btn_tooltip.startup();
					this.newschedwatch_obj.watch('league_fg_flag',
						function(name, oldValue, value) {
							if (value) {
								schedule_btn.set('disabled', false);
								btn_tooltip.set('label',
									'Press to Generate Schedule');
							}
						}
					)
					put(scinput_dom, "br, br");
				}
				var schedstatustxt_node = dom.byId(constant.statustxt_id);
				if (!schedstatustxt_node) {
					schedstatustxt_node = put(scinput_dom,
						"span#schedstatustxt_id",
						"Configure Schedule Parameters")
				}
				// set flag that is used by observable memory update in
				// storeutil
				this.selectexists_flag = true;
				// if initial option selection is other than the default blank
				// "", then call the onChange callback so that if necessary the
				// logic to enable the 'Generate' button is activated:
				// These calls need to be done at the end of create_widgets() after
				// all the this.newschedwatch_obj.watch() callback functions have
				// been defined
				if (divcol_name) {
					lsargs_obj.onchange_callback(divcol_name);
				}
				if (fieldcol_name) {
					fgargs_obj.onchange_callback(fieldcol_name);
				}
			},
			reload_widgets: function(divdb_type, divcol_name, fieldcol_name) {
				// reuse widgets that have already been created and reload new values
				var divcol_name = (typeof divcol_name === "undefined" || divcol_name === null) ? "" : divcol_name;
				var fieldcol_name = (typeof fieldcol_name === "undefined" || fieldcol_name === null) ? "" : fieldcol_name;
				this.newsched_dom.innerHTML = "Schedule Name: <b>"+this.newsched_name+"</b>";
				this.widgetgen.reload_dbytpe_radiobtn(constant.radio1_id, constant.radio2_id, divdb_type);
				var lsargs_obj = {
					select_reg:this.league_select,
					init_db_type:divdb_type,
					init_colname:divcol_name,
					label_str:"Select League",
				};
				this.widgetgen.reload_select(lsargs_obj);
				var fgargs_obj = {
					select_reg:this.fg_select,
					init_db_type:'fielddb',
					init_colname:fieldcol_name,
					label_str:"Select Field Group",
				}
				this.widgetgen.reload_select(fgargs_obj);
				var schedule_btn = registry.byId("schedparambtn_id");
				schedule_btn.set("disabled", true);
				var onchange_callback = null;
				if (divcol_name) {
					onchange_callback = this.league_select.get("onChange");
					onchange_callback(divcol_name);
				}
				if (fieldcol_name) {
					onchange_callback = this.fg_select.get("onChange");
					onchange_callback(fieldcol_name);
				}
			},
			send_generate: function() {
				var schedstatustxt_node = dom.byId(constant.statustxt_id);
				schedstatustxt_node.innerHTML = "Generating Schedule, Not Ready";
				schedstatustxt_node.style.color = 'red';
				var server_key_obj = {divcol_name:this.league_select_value,
					fieldcol_name:this.fg_select_value,
					db_type:this.current_db_type,
					schedcol_name:this.newsched_name};
				this.server_interface.getServerData("send_generate",
					lang.hitch(this, this.update_schedstatustxt), server_key_obj,
					{node:schedstatustxt_node});
				// add metadata to local store
				// third parameter 1 is the config_status, which is always complete
				// for the newsched_id idprop as send_generate will not be called
				// until newsched config is complete
				this.storeutil_obj.addtodb_store(this.newsched_name,
					this.idproperty, 1);
			},
			update_schedstatustxt: function(adata, options_obj) {
				var dbstatus = adata.dbstatus;
				var schedstatustxt_node = options_obj.node;
				this.schedutil_obj.updateDBstatus_node(dbstatus,
					schedstatustxt_node);
				// create new tab to hold table grid for newsched information
				this.tabcontainer_reg = registry.byId(constant.tabcontainer_id);
				var args_obj = {
					suffix_id:constant.newdivcpane_id,
					// define contents of div pane
					content_str:"<div id='"+constant.newdivcpane_txt_id+"'></div> <b>Click on Division row</b> to see division-specific schedule - scroll down. <div id='"+constant.newdivcpane_grid_id+"'></div><div id='"+constant.newdivcpane_schedheader_id+"'></div><div id='"+constant.newdivcpane_schedgrid_id+"'></div>",
					title_suffix:' by Div',
				}
				this.createnewsched_pane(args_obj);
				this.prepgrid_data('div_id', dbstatus);
				args_obj = {
					suffix_id:constant.newfieldcpane_id,
					// define contents of select-by-field pane
					content_str:"<div id='"+constant.newfieldcpane_txt_id+"'></div> <b>Click on Field row</b> to see field-specific schedule - scroll down. <div id='"+constant.newfieldcpane_grid_id+"'></div><div id='"+constant.newfieldcpane_schedheader_id+"'></div><div id='"+constant.newfieldcpane_schedgrid_id+"'></div>",
					title_suffix:' by Field',
				}
				this.createnewsched_pane(args_obj);
				this.prepgrid_data('field_id', dbstatus);
				// add by-team sched grid
				args_obj = {
					suffix_id:constant.newteamcpane_id,
					content_str:"<div id='"+constant.newteamcpane_txt_id+"'></div> <b>Select Division</b> and then select team ID from grid to see team-specific schedule - scroll down<br><label for='"+constant.newteamcpane_select_id+"'>Select Division</label><select id='"+constant.newteamcpane_select_id+"' data-dojo-type='dijit/form/Select' name='"+constant.newteamcpane_select_id+"'></select><div id='"+constant.newteamcpane_grid_id+"'></div><div id='"+constant.newteamcpane_schedheader_id+"'></div><div id='"+constant.newteamcpane_schedgrid_id+"'></div>",
					title_suffix:' by Team',
				}
				this.createnewsched_pane(args_obj);
				this.prepgrid_data('team_id', dbstatus)
				// add fairness metrics cpane
				args_obj = {
					suffix_id:constant.newfaircpane_id,
					content_str:"<div id='"+constant.newfaircpane_txt_id+"'></div> <b>Select Division</b> and then select team ID from grid to see team-specific Fairness Metrics - scroll down<br><label for='"+constant.newfaircpane_select_id+"'>Select Division</label><select id='"+constant.newfaircpane_select_id+"' data-dojo-type='dijit/form/Select' name='"+constant.newfaircpane_select_id+"'></select><div id='"+constant.newfaircpane_grid_id+"'></div><div id='"+constant.newfaircpane_schedheader_id+"'></div><div id='"+constant.newfaircpane_schedgrid_id+"'></div>",
					title_suffix:' by Fairness Metrics',
				}
				this.createnewsched_pane(args_obj);
				this.prepgrid_data('fair_id', dbstatus)
			},
			prepgrid_data: function(idproperty, dbstatus) {
				var statusnode_id = null;
				var select_value = null;
				var db_type = null;
				if (idproperty == 'div_id') {
					statusnode_id = constant.newdivcpane_txt_id;
					select_value = this.league_select_value;
					db_type = this.current_db_type;
					this.getgrid_data(idproperty, select_value, db_type);
				} else if (idproperty == 'field_id') {
					statusnode_id = constant.newfieldcpane_txt_id;
					select_value = this.fg_select_value;
					db_type = 'fielddb';
					this.getgrid_data(idproperty, select_value, db_type);
				} else if (idproperty == 'team_id') {
					statusnode_id = constant.newteamcpane_txt_id;
					// first get the div information selected by
					// league_select_value and current_db_type
					select_value = this.league_select_value;
					db_type = this.current_db_type;
					// check if the divselect_reg divsion select drop-down
					// for team id selection has been created; if it has not
					// create the dropdown.
					// first see if divinfo information is in current store
					var divinfo_obj = baseinfoSingleton.get_obj('div_id');
					if (divinfo_obj && divinfo_obj.infogrid_store &&
						divinfo_obj.activegrid_colname == select_value) {
						// if in store, get data and create dropdown
						var data_list = divinfo_obj.infogrid_store.query();
						this.createdivselect_dropdown(data_list);
					} else {
						// if not in store get from server
						this.server_interface.getServerData(
							'get_dbcol/'+db_type+'/'+select_value,
							lang.hitch(this, this.createdivselect_dropdown));
					}
				} else if (idproperty == 'fair_id') {

				}
				this.schedutil_obj.updateDBstatus_node(dbstatus,
					dom.byId(statusnode_id))
			},
			getgrid_data:function(idproperty, select_value, db_type) {
				// now we want to create and populate grids, starting with
				// divinfo/fieldinfo grid.  First check if local store has data
				// corresponding to current collection
				var info_obj = baseinfoSingleton.get_obj(idproperty);
				if (info_obj) {
					if (info_obj.infogrid_store &&
						info_obj.activegrid_colname == select_value) {
						var columnsdef_obj = info_obj.getfixedcolumnsdef_obj();
						/*
						var griddata_list = info_obj.infogrid_store.query().map(function(item) {
							var map_obj = {}
							// only extra data corresponding to keys specified in
							// columnsdef_obj.  This may be a subset of all the keys
							// available in the store.
							for (var key in columnsdef_obj) {
								map_obj[key] = item[key];
							}
							return map_obj;
						}) */
						var griddata_list = info_obj.infogrid_store.query();
						this.createinfo_grid(idproperty, columnsdef_obj, griddata_list);
					} else {
						// if info is not available in the store, get it from
						// the server.
						this.server_interface.getServerData(
							'get_dbcol/'+db_type+'/'+select_value,
							lang.hitch(this, this.pipegrid_data), null,
							{info_obj:info_obj, idproperty:idproperty});
					}
				} else {
					console.log("Error: No info_obj object");
				}
			},
			createdivselect_dropdown:function(data_list) {
				if (data_list.config_status == 1) {
					var info_list = data_list.info_list;
					// compare against div dropdown function in schedutil
					var option_list = [{label:"Select Division", value:"", selected:true, totalteams:0, div_age:"", div_gen:""}];
					arrayUtil.forEach(info_list, function(item, index) {
						var divstr = item.div_age + item.div_gen;
						// division code is 1-index based so increment by 1
						option_list.push({label:divstr, value:item.div_id,
							selected:false, totalteams:item.totalteams,
							div_age:item.div_age, div_gen:item.div_gen});
					});
					// set("options",) replaces options list if there was
					// a prior options list loaded onto the select widget
					// of course works for initial options list load also.
					var select_reg = registry.byId(constant.newteamcpane_select_id);
					select_reg.set("options", option_list);
					if (this.divselect_handle)
						this.divselect_handle.remove();
					this.divselect_handle = select_reg.set("onChange",
						lang.hitch(this, function(event) {
							// option_list is in the execution context of the
							// event handler (verify this is always true however)
							var match_option = arrayUtil.filter(option_list,
								function(item) {
									return item.value == event;
								})
							var match = match_option[0];
							var totalteams = match.totalteams;
							var query_obj = {div_age:match.div_age,
								div_gen:match.div_gen};
							var columnsdef_obj = {team_id:"Team ID"}
							var griddata_list = new Array();
							for (var i=1; i<totalteams+1; i++) {
								griddata_list.push({team_id:i})
							}
							this.createinfo_grid('team_id', columnsdef_obj,
								griddata_list, query_obj);
					}))
					select_reg.startup();
				} else {
					console.log("Warning: Div Configuration Not Complete");
				}

			},
			pipegrid_data: function(adata, options_obj) {
				var griddata_list = adata.info_list;
				var columnsdef_obj = options_obj.info_obj.getfixedcolumnsdef_obj();
				this.createinfo_grid(options_obj.idproperty, columnsdef_obj,
					griddata_list);
			},
			createinfo_grid: function(idproperty, columnsdef_obj, griddata_list, query_obj) {
				var query_obj = (typeof query_obj === "undefined" || query_obj === null) ? "" : query_obj;
				if (idproperty == 'field_id') {
					var simple_calendarmap_list = new Array();
					arrayUtil.forEach(griddata_list, function(item, index) {
						var start_date = new Date(item.start_date);
						var args_obj = {dayweek_list:item.dayweek_str.split(','),
							start_date:start_date,
							totalfielddays:item.totalfielddays};
						// get calendarmap list that maps fieldday_id to calendar
						// date, for each field
						var one_calendarmap_list = this.schedutil_obj.getcalendarmap_list(args_obj);
						//this.calendarmap_list.push({field_id:item.field_id,
						//	calendarmap_list:one_calendarmap_list})
						this.calendarmap_obj[item.field_id] = one_calendarmap_list;
						simple_calendarmap_list.push(one_calendarmap_list);
					}, this)
					//ref http://stackoverflow.com/questions/1316371/converting-a-javascript-array-to-a-function-arguments-list
					// for converting array to variable arguments for a function
					this.common_calendardate_list = _.intersection.apply(null,
						simple_calendarmap_list);
				}
				var info_grid = this.info_grid_mapobj[idproperty];
				if (!info_grid) {
					var cpane_grid_id = this.cpane_grid_id_mapobj[idproperty];
					var StaticGrid = declare([OnDemandGrid, Keyboard, Selection]);
					info_grid = new StaticGrid({
						columns:columnsdef_obj,
						selectionMode:"single"
					}, cpane_grid_id);
					this.info_grid_mapobj[idproperty] = info_grid;
				} else {
					// https://github.com/SitePen/dgrid/issues/170
					// call refresh() to clear array
					info_grid.refresh();
				}
				info_grid.renderArray(griddata_list);
				var info_handle = this.info_handle_mapobj[idproperty];
				if (info_handle)
					info_handle.remove();
				var callback_method = this.gridmethod_mapobj[idproperty]
				info_handle = info_grid.on("dgrid-select",
					lang.hitch(this, function(event) {
					var event_data = event.rows[0].data;
					var id = event_data[idproperty];
					this.setselect_text(event_data, idproperty);
					this.server_interface.getServerData('get_schedule/'+
						this.newsched_name+'/'+idproperty+'/'+id,
						callback_method,
						query_obj, {idproperty:idproperty, event_data:event_data})
					}));
				this.info_handle_mapobj[idproperty] = info_handle;
			},
			createdivsched_grid: function(adata, options_obj) {
				var idproperty = options_obj.idproperty;
				var fieldname_dict = adata.fieldname_dict;
				var game_list = adata.game_list;
				var columnsdef_obj = {
					date:'Game Day', time:'Game Time'
				}
				for (var key in fieldname_dict) {
					columnsdef_obj[key] = fieldname_dict[key]
				}
				var grid_list = new Array();
				arrayUtil.forEach(game_list, function(item, index) {
					var grid_row = new Object();
					// slot_id is the idProperty for the store also
					// Use slot_id as the idProp instead of game_id as a single
					// slot_id row can have multiple games.
					grid_row.slot_id = index+1;
					grid_row.date = item.game_date;
					grid_row.time = item.start_time;
					arrayUtil.forEach(item.gameday_data, function(item2) {
						grid_row[item2.venue] = item2.home+'v'+item2.away;
					})
					grid_list.push(grid_row);
				}, this)
				this.createsched_grid(idproperty, grid_list, columnsdef_obj,
					'slot_id');
			},
			createfieldsched_grid: function(adata, options_obj) {
				// create schedule grid defined by selected field_id
				var idproperty = options_obj.idproperty;
				var game_list = adata.game_list;
				var columnsdef_obj = {
    				game_date:'Game Date',
    				start_time:'Start Time',
    				div_age:'Age Group/Primary ID',
    				div_gen:'Gender/Secondary ID',
    				home:'Home Team#',
    				away:'Away Team#'
				}
				// var field_id = event_data.field_id; // selected field_id
				// get calendar map list for field_id
				// .filter creates single element list - get single elem/obj and
				// grab mapping list
				//var calendarmap_list = this.calendarmap_obj[field_id];
				arrayUtil.forEach(game_list, function(item, index) {
					item.game_id = index+1; //to be used as idprop for store
				})
				this.createsched_grid(idproperty, game_list, columnsdef_obj,
					'game_id');
			},
			createteamsched_grid: function(adata, options_obj) {
				var idproperty = options_obj.idproperty;
				var game_list = adata.game_list;
				var columnsdef_obj = {
   					game_date:'Game Date',
    				start_time:'Start Time',
    				venue:'Venue',
    				home:'Home Team#',
    				away:'Away Team#'
				}
				arrayUtil.forEach(game_list, function(item, index) {
					item.game_id = index+1; //to be used as idprop for store
				})
				this.createsched_grid(idproperty, game_list, columnsdef_obj,
					'game_id');
			},
			createsched_grid: function(idproperty, game_list, columnsdef_obj, store_idProperty) {
				// get store and grid for this idproperty
				var sched_store = this.sched_store_mapobj[idproperty];
				var sched_grid = this.sched_grid_mapobj[idproperty];
				if (sched_store) {
					// if store already exists, repopulate store with new data
					// and refresh grid
					sched_store.setData(game_list);
					sched_grid.refresh();
				} else {
					var cpane_schedgrid_id = this.cpane_schedgrid_id_mapobj[idproperty];
					sched_store = new Observable(new Memory({data:game_list, idProperty:store_idProperty}));
					var StaticGrid = declare([OnDemandGrid, Keyboard, Selection]);
					sched_grid = new StaticGrid({
						columns:columnsdef_obj,
						store:sched_store
					}, cpane_schedgrid_id);
					sched_grid.startup();
					this.sched_store_mapobj[idproperty] = sched_store;
					this.sched_grid_mapobj[idproperty] = sched_grid;
				}
				sched_grid.resize();
			},
			createnewsched_pane: function(args_obj) {
				var suffix_id = args_obj.suffix_id;
				var content_str = args_obj.content_str;
				var title_suffix = args_obj.title_suffix;
				var newcpane_id = this.newsched_name+suffix_id;
				var newcpane = registry.byId(newcpane_id);
				if (!newcpane) {
					var title_str = this.newsched_name + title_suffix;
					newcpane = new ContentPane({title:title_str,
						content:content_str, id:newcpane_id});
					this.tabcontainer_reg.addChild(newcpane);
				}
			},
			setselect_text: function(event_data, idproperty) {
				/* Utility function to set text between info grid and
				schedule grid.  Text determined by selected row of info grid
				and is idproperty-dependent. */
				var schedheader_id = this.cpane_schedheader_id_mapobj[idproperty];
				var text_str = "";
				if (idproperty == 'div_id') {
					text_str = event_data.div_age+event_data.div_gen + " selected";
				} else if (idproperty == 'field_id') {
					text_str = event_data.field_name + " selected";
				}
				dom.byId(schedheader_id).innerHTML = text_str;
			},
			reset_newschedwatch_obj: function() {
				this.newschedwatch_obj.set("leagueselect_flag", false);
				this.newschedwatch_obj.set("fgselect_flag", false);
				this.newschedwatch_obj.set("league_fg_flag", false);
			},
			cleanup: function() {
				if (this.seasonstart_handle)
					this.seasonstart_handle.remove();
				if (this.seasonend_handle)
					this.seasonend_handle.remove();
				if (this.seasonlength_handle)
					this.seasonlength_handle.remove();
				if (this.tooltip)
					this.tooltip.destroyRecursive();
				if (this.dbname_reg)
					this.dbname_reg.destroyRecursive();
				for (var idproperty in info_handle_mapobj) {
					var handle = info_handle_mapobj[idproperty];
					if (handle)
						handle.remove();
				}
				if (this.divselect_handle)
					this.divselect_handle.remove();
			}
		});
	})
