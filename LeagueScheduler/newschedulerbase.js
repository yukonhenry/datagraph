define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare",
	"dojo/_base/lang", "dojo/Stateful",
	"dojo/_base/array", "dojo/keys", "dojo/store/Memory", "dojo/store/Observable",
	"dijit/registry", "dijit/Tooltip",
	"dijit/form/ValidationTextBox","dijit/form/Select", "dijit/form/Button",
	"dijit/form/DateTextBox", "dijit/form/Form",
	"dijit/layout/StackContainer","dijit/layout/ContentPane", "dgrid/Grid",
	"dgrid/OnDemandGrid", "dgrid/Keyboard", "dgrid/Selection",
	"LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/widgetgen", "LeagueScheduler/idmgrSingleton",
	"LeagueScheduler/generatexls", "LeagueScheduler/errormanager",
	"put-selector/put", "underscore-min", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, Stateful, arrayUtil, keys,
		Memory, Observable, registry, Tooltip, ValidationTextBox, Select, Button,
		DateTextBox, Form, StackContainer, ContentPane, Grid, OnDemandGrid,
		Keyboard, Selection, EditGrid, baseinfoSingleton, WidgetGen,
		idmgrSingleton, GenerateXLS, ErrorManager, put) {
		var constant = {
			idproperty_str:'newsched_id',
			tabcontainer_id:'tabcontainer_id',
			defaultselect_db_type:'rrdb',
			db_type:'newscheddb',
			slot_id:'slot_id',
			game_id:'game_id',
			team_id:'team_id',
			fair_id:'fair_id',
			pref_id:'pref_id',
			conflict_id:'conflict_id'
		};
		var idconstant = {
			radio1_id:'scradio1_id',
			radio2_id:'scradio2_id',
			fg_select_id:'fg_select_id',
			pref_select_id:'pref_select_id',
			conflict_select_id:'conflict_select_id',
			schedparambtn_id:'schedparambtn_id',
			schedstatustxt_id:'schedstatustxt_id',
			teamcpane_select_id:'teamcpane_select_id',
			faircpane_select_id:'faircpane_select_id',
		}
		var wizconstant = {
			nscpane_id:"wiznewschedcpane_id",
		};
		var newschedwatch_class = declare([Stateful],{
			leagueselect_flag:false,
			fgselect_flag:false,
			league_fg_flag:false
		})
		return declare(null, {
			server_interface:null,
			newsched_name:"", newsched_dom:"",
			schedutil_obj:null, storeutil_obj:null, op_type:"",
			info_obj:null, idproperty:constant.idproperty_str,
			seasondates_btn_reg:null, server_key_obj:null,
			callback:null, text_node_str:"", tooltip:null,
			start_dtbox:null, end_dtbox:null, sl_spinner:null,
			seasonstart_handle:null, seasonend_handle:null,
			seasonlength_handle:null, league_select:null, fg_select:null,
			pref_select:null, conflict_select:null,
			event_flag:false, uistackmgr_type:null, newschedwatch_obj:null,
			selectexists_flag:false,
			league_select_value:"", fg_select_value:"", widgetgen:null,
			current_db_type:constant.defaultselect_db_type,
			tabcontainer_reg:null,
			cpane_id_mapobj:null, cpane_txt_id_mapobj:null,
			cpane_grid_id_mapobj:null, cpane_schedgrid_id_mapobj:null,
			cpane_schedheader_id_mapobj:null,
			info_grid_mapobj:null, info_handle_mapobj:null, gridmethod_mapobj:null,
			sched_store_mapobj:null, sched_grid_mapobj:null,
			calendarmap_obj:null,
			teamdivselect_handle:null, fairdivselect_handle:null,
			idmgr_obj:null, op_type:"", opconstant_obj:null,
			pref_select_value:null, conflict_select_value:null, errormgr_obj:null,
			constructor: function(args) {
				lang.mixin(this, args);
				baseinfoSingleton.register_obj(this, constant.idproperty_str);
				this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
					id:this.idproperty, op_type:this.op_type});
				// watch object is specific to this object so we don't need to
				// expand watch functionality to accomodate op_type
				// also preference is only optional so it doesn't affect the league_fg_flag which enables the button
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
				var resultpane_id_list = ['div_id', 'field_id', 'team_id',
					'fair_id', 'pref_id', 'conflict_id', 'xls_id'];
				// reassign values for all the constant dom id's by adding an
				// op_type (first three chars) prefix
				var op_prefix = this.op_type.substring(0,3);
				// create dictionaries/objects that map idproperty to idproperty-specific
				// id's or objects
				// w each dict mapping idproperty to either a schedule grid or the
				// corresponding .on handler
				this.cpane_id_mapobj = new Object();
				this.cpane_txt_id_mapobj = new Object();
				this.cpane_grid_id_mapobj = new Object();
				this.cpane_schedgrid_id_mapobj = new Object();
				this.cpane_schedheader_id_mapobj = new Object();
				arrayUtil.forEach(resultpane_id_list, function(resultpane_id) {
					// first get the idstem which is the id minus the '_id'
					var idstem = resultpane_id.substring(0, resultpane_id.length-3);
					var prefix = op_prefix+"new"+idstem+"cpane_";
					this.cpane_id_mapobj[resultpane_id] = prefix + "id";
					this.cpane_txt_id_mapobj[resultpane_id] = prefix + "txt_id";
					this.cpane_grid_id_mapobj[resultpane_id] = prefix + "grid_id";
					this.cpane_schedgrid_id_mapobj[resultpane_id] = prefix +
						"schedgrid_id";
					this.cpane_schedheader_id_mapobj[resultpane_id] = prefix +
						"schedheader_id";
				}, this);

				this.opconstant_obj = new Object();
				for (var key in idconstant) {
					this.opconstant_obj[key] = op_prefix+idconstant[key]
				}
				this.info_grid_mapobj = {div_id:null, field_id:null, team_id:null,
					fair_id:null, pref_id:null, conflict_id:null};
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
				this.errormgr_obj = new ErrorManager();
			},
			initialize: function(op_type) {
				var op_type = (typeof op_type === "undefined" || op_type === null) ? "advance" : "wizard";
				form_reg = registry.byId(this.idmgr_obj.form_id);
				var form_node = form_reg.domNode;
				//this.dbname_reg = registry.byId("newsched_input_id");
				// put selector documentation
				// http://davidwalsh.name/put-selector
				// https://github.com/kriszyp/put-selector
				// first check to see if the domNode has already been created by
				// seeing the dom node can be retrieved
				var dbname_reg = registry.byId(this.idmgr_obj.dbname_id);
				if (!dbname_reg) {
					put(form_node,
						"label.label_box[for=$]", this.idmgr_obj.dbname_id,
						'New Schedule Name:');
					var dbname_node = put(form_node,
						"input[id=$][type=text][required=true]",
						this.idmgr_obj.dbname_id);
					dbname_reg = new ValidationTextBox({
						value:'',
						regExp:'\\D[\\w]+',
						promptMessage:'Enter New Schedule-start with letter or _, followed by alphanumeric or _',
						invalidMessage:'start with letter or _, followed by alphanumeric characters and _',
						missingMessage:'enter schedule name'
					}, dbname_node);
				} else {
					// domnode already exists, get widget that should also be there
					// NOTE: registry.byNode() does not work -
					// sched_input is an HTML Input element
					// however, this.dbname_reg.domNode is an HTML Div Element
					// (not sure exactly why)
					// Anyway, if sched_input exists, then this.dbname_reg should exist, so disregard below
					// alternatively, use:
					//this.dbname_reg = registry.byId("newsched_input_id");
					// DON"T use below:
					//this.dbname_reg = registry.byNode(sched_input);
				}
				//this.seasondates_btn_reg = registry.byId("seasondates_btn");
				args_obj = {
					dbname_reg:dbname_reg,
					form_reg:form_reg,
					op_type:op_type
				}
				this.showConfig(args_obj);
			},
			showConfig: function(args_obj) {
				var dbname_reg = args_obj.dbname_reg;
				this.uistackmgr_type.switch_pstackcpane({idproperty:this.idproperty,
					p_stage:"preconfig", entry_pt:"init"});
				this.uistackmgr_type.switch_gstackcpane(this.idproperty, true);
				if (!this.tooltip) {
					var tooltipconfig = {connectId:[this.idmgr_obj.dbname_id],
						label:"Enter New Schedule Name and press ENTER",
						position:['below','after']};
					this.tooltip = new Tooltip(tooltipconfig);
				}
				if (this.keyup_handle)
					this.keyup_handle.remove();
				this.keyup_handle = dbname_reg.on("keyup", lang.hitch(this, this.processdivinfo_input, args_obj));
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(args_obj, event) {
				if (event.keyCode == keys.ENTER) {
					var form_reg = args_obj.form_reg;
					var dbname_reg = args_obj.dbname_reg;
					var op_type = args_obj.op_type;
					if (form_reg.validate()) {
						confirm('Input format is Valid, creating new Schedule DB');
						this.newsched_name = dbname_reg.get("value");
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
						this.uistackmgr_type.switch_pstackcpane({
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
				} else if (db_type == 'prefdb') {
					this.pref_select.removeOption(index)
				} else if (db_type == 'conflictdb') {
					this.conflict_select.removeOption(index);
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
				} else if (db_type == 'prefdb') {
					this.pref_select.addOption(index)
				} else if (db_type == 'conflictdb') {
					this.conflict_select.addOption(index);
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
				// callback function when newsched config is retrieved from server
				var param_obj = adata.param_obj;
				var divcol_name = param_obj.divcol_name;
				var divdb_type = param_obj.divdb_type;
				var fieldcol_name = param_obj.fieldcol_name;
				var prefcol_name = param_obj.prefcol_name;
				var conflictcol_name = param_obj.conflictcol_name;
				if (!this.widgetgen) {
					this.create_widgets(divdb_type, divcol_name,
						fieldcol_name, prefcol_name, conflictcol_name);
				} else {
					// reset watch object fields
					this.reset_newschedwatch_obj();
					// reload widgets
					this.reload_widgets(divdb_type, divcol_name, fieldcol_name,
						prefcol_name, conflictcol_name);
				}
				this.uistackmgr_type.switch_pstackcpane({
					idproperty:this.idproperty, p_stage:"config",
					entry_pt:"fromdb"});
				this.uistackmgr_type.switch_gstackcpane(this.idproperty, true);
			},
			create_widgets: function(divdb_type, divcol_name, fieldcol_name, prefcol_name, conflictcol_name) {
				var radio1_id = this.opconstant_obj.radio1_id;
				var radio2_id = this.opconstant_obj.radio2_id;
				var fg_select_id = this.opconstant_obj.fg_select_id;
				var league_select_id = this.idmgr_obj.league_select_id;
				var schedparambtn_id = this.opconstant_obj.schedparambtn_id;
				var schedstatustxt_id = this.opconstant_obj.schedstatustxt_id;
				var pref_select_id = this.opconstant_obj.pref_select_id;
				var conflict_select_id = this.opconstant_obj.conflict_select_id;

				var divcol_name = (typeof divcol_name === "undefined" ||
					divcol_name === null) ? "" : divcol_name;
				var fieldcol_name = (typeof fieldcol_name === "undefined" ||
					fieldcol_name === null) ? "" : fieldcol_name;
				var prefcol_name = (typeof prefcol_name === "undefined" ||
					prefcol_name === null) ? "" : prefcol_name;
				var conflictcol_name = (typeof conflictcol_name === "undefined" ||
					conflictcol_name === null) ? "" : conflictcol_name;
				this.newsched_dom = dom.byId(this.idmgr_obj.text_id);
				this.newsched_dom.innerHTML = "Schedule Name: <b>"+this.newsched_name+"</b>";
				this.widgetgen = new WidgetGen({
					storeutil_obj:this.storeutil_obj,
					server_interface:this.server_interface
				});
				var scinput_dom = dom.byId(this.idmgr_obj.textbtncpane_id);
				this.widgetgen.create_dbtype_radiobtn(scinput_dom,
					radio1_id, radio2_id, divdb_type,
					this, this.radio1_callback, this.radio2_callback,
					league_select_id);
				// create league info dropdowns
				var lsargs_obj = {
					topdiv_node:scinput_dom,
					select_id:league_select_id,
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
					select_id:fg_select_id,
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
				put(scinput_dom, "br, br");
				// create preference list dropdown
				var prefargs_obj = {
					topdiv_node:scinput_dom,
					select_id:pref_select_id,
					init_db_type:'prefdb',
					init_colname:prefcol_name,
					onchange_callback:lang.hitch(this, function(evt) {
						this.pref_select_value = evt;
					}),
					name_str:"pref_select",
					label_str:"Select Preference List",
					put_trail_spacing:"span.empty_gap"
				}
				this.pref_select = this.widgetgen.create_select(prefargs_obj);
				put(scinput_dom, "br, br");
				// create conflict list dropdown
				var conflictargs_obj = {
					topdiv_node:scinput_dom,
					select_id:conflict_select_id,
					init_db_type:'conflictdb',
					init_colname:conflictcol_name,
					onchange_callback:lang.hitch(this, function(evt) {
						this.conflict_select_value = evt;
					}),
					name_str:"conflict_select",
					label_str:"Select Conflict List",
					put_trail_spacing:"span.empty_gap"
				}
				this.conflict_select = this.widgetgen.create_select(conflictargs_obj);
				var btn_node = dom.byId(schedparambtn_id);
				if (!btn_node) {
					btn_node = put(scinput_dom,
						"button.dijitButton[id=$][type=button]", schedparambtn_id);
					var btn_tooltipconfig = {
						connectId:[schedparambtn_id],
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
				var schedstatustxt_node = dom.byId(schedstatustxt_id);
				if (!schedstatustxt_node) {
					schedstatustxt_node = put(scinput_dom,
						"span[id=$]", schedstatustxt_id,
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
				if (prefcol_name) {
					prefargs_obj.onchange_callback(prefcol_name);
				}
				if (conflictcol_name) {
					conflictargs_obj.onchange_callback(conflictcol_name);
				}
			},
			reload_widgets: function(divdb_type, divcol_name, fieldcol_name, prefcol_name, conflictcol_name) {
				// reuse widgets that have already been created and reload new values
				var radio1_id = this.opconstant_obj.radio1_id;
				var radio2_id = this.opconstant_obj.radio2_id;
				var schedparambtn_id = this.opconstant_obj.schedparambtn_id;

				var divcol_name = (typeof divcol_name === "undefined" || divcol_name === null) ? "" : divcol_name;
				var fieldcol_name = (typeof fieldcol_name === "undefined" || fieldcol_name === null) ? "" : fieldcol_name;
				var prefcol_name = (typeof prefcol_name === "undefined" || prefcol_name === null) ? "" : prefcol_name;
				var conflictcol_name = (typeof conflictcol_name === "undefined" ||
					conflictcol_name === null) ? "" : conflictcol_name;
				this.newsched_dom.innerHTML = "Schedule Name: <b>"+this.newsched_name+"</b>";
				this.widgetgen.reload_dbytpe_radiobtn(radio1_id, radio2_id, divdb_type);
				// div league select
				var lsargs_obj = {
					select_reg:this.league_select,
					init_db_type:divdb_type,
					init_colname:divcol_name,
					label_str:"Select League",
				};
				this.widgetgen.reload_select(lsargs_obj);
				// field group select
				var fgargs_obj = {
					select_reg:this.fg_select,
					init_db_type:'fielddb',
					init_colname:fieldcol_name,
					label_str:"Select Field Group",
				}
				this.widgetgen.reload_select(fgargs_obj);
				// pref list select
				var prefargs_obj = {
					select_reg:this.pref_select,
					init_db_type:'prefdb',
					init_colname:prefcol_name,
					label_str:"Select Preference List",
				}
				this.widgetgen.reload_select(prefargs_obj);
				// conflict list select
				var conflictargs_obj = {
					select_reg:this.conflict_select,
					init_db_type:'conflictdb',
					init_colname:conflictcol_name,
					label_str:"Select Conflict List",
				}
				this.widgetgen.reload_select(conflictargs_obj);
				var schedule_btn = registry.byId(schedparambtn_id);
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
				if (prefcol_name) {
					onchange_callback = this.pref_select.get("onChange");
					onchange_callback(prefcol_name);
				}
				if (conflictcol_name) {
					onchange_callback = this.conflict_select.get("onChange");
					onchange_callback(conflictcol_name);
				}
			},
			send_generate: function() {
				var schedstatustxt_id = this.opconstant_obj.schedstatustxt_id;
				var schedstatustxt_node = dom.byId(schedstatustxt_id);
				schedstatustxt_node.innerHTML = "Generating Schedule, Not Ready";
				schedstatustxt_node.style.color = 'red';
				// save server_key_obj to a member variable, as this will 'lock' the
				// values and used as data for the newly generate schedule cpanes.
				this.server_key_obj = {divcol_name:this.league_select_value,
					fieldcol_name:this.fg_select_value,
					prefcol_name:this.pref_select_value,
					conflictcol_name:this.conflict_select_value,
					db_type:this.current_db_type,
					schedcol_name:this.newsched_name};
				this.server_interface.getServerData("send_generate",
					lang.hitch(this, this.update_schedstatustxt), this.server_key_obj,
					{node:schedstatustxt_node});
				// add metadata to local store
				// third parameter 1 is the config_status, which is always complete
				// for the newsched_id idprop as send_generate will not be called
				// until newsched config is complete
				this.storeutil_obj.addtodb_store(this.newsched_name,
					this.idproperty, 1);
			},
			update_schedstatustxt: function(adata, options_obj) {
				if ('error_code' in adata) {
					this.errormgr_obj.emit_error(adata.error_code);
					return false;
				}
				var dbstatus = adata.dbstatus;
				var schedstatustxt_node = options_obj.node;
				this.schedutil_obj.updateDBstatus_node(dbstatus,
					schedstatustxt_node);
				// create new tab to hold table grid for newsched information
				this.tabcontainer_reg = registry.byId(constant.tabcontainer_id);
				var cpane_id = this.cpane_id_mapobj.div_id;
				var cpane_txt_id = this.cpane_txt_id_mapobj.div_id;
				var cpane_grid_id = this.cpane_grid_id_mapobj.div_id;
				var cpane_schedgrid_id = this.cpane_schedgrid_id_mapobj.div_id;
				var cpane_schedheader_id = this.cpane_schedheader_id_mapobj.div_id;
				var args_obj = {
					suffix_id:cpane_id,
					// define contents of div pane
					content_str:"<div id='"+cpane_txt_id+"'></div> <b>Click on Division row</b> to see division-specific schedule - scroll down. <div id='"+cpane_grid_id+"'></div><div id='"+cpane_schedheader_id+"'></div><div id='"+cpane_schedgrid_id+"'></div>",
					title_suffix:' by Div',
				}
				this.createnewsched_pane(args_obj);
				this.prepgrid_data('div_id', dbstatus);
				//--- results field pane
				cpane_id = this.cpane_id_mapobj.field_id;
				cpane_txt_id = this.cpane_txt_id_mapobj.field_id;
				cpane_grid_id = this.cpane_grid_id_mapobj.field_id;
				cpane_schedgrid_id = this.cpane_schedgrid_id_mapobj.field_id;
				cpane_schedheader_id = this.cpane_schedheader_id_mapobj.field_id;
				args_obj = {
					suffix_id:cpane_id,
					// define contents of select-by-field pane
					content_str:"<div id='"+cpane_txt_id+"'></div> <b>Click on Field row</b> to see field-specific schedule - scroll down. <div id='"+cpane_grid_id+"'></div><div id='"+cpane_schedheader_id+"'></div><div id='"+cpane_schedgrid_id+"'></div>",
					title_suffix:' by Field',
				}
				this.createnewsched_pane(args_obj);
				this.prepgrid_data('field_id', dbstatus);
				// add by-team sched grid
				cpane_id = this.cpane_id_mapobj.team_id;
				cpane_txt_id = this.cpane_txt_id_mapobj.team_id;
				cpane_grid_id = this.cpane_grid_id_mapobj.team_id;
				cpane_schedgrid_id = this.cpane_schedgrid_id_mapobj.team_id;
				cpane_schedheader_id = this.cpane_schedheader_id_mapobj.team_id;
				var cpane_select_id = this.opconstant_obj.teamcpane_select_id;
				args_obj = {
					suffix_id:cpane_id,
					content_str:"<div id='"+cpane_txt_id+"'></div> <b>Select Division</b> and then select team ID by <b>clicking grid row</b> to see team-specific schedule - scroll down<br><label for='"+cpane_select_id+"'>Select Division</label><select id='"+cpane_select_id+"' data-dojo-type='dijit/form/Select' name='"+cpane_select_id+"'></select><div id='"+cpane_grid_id+"'></div><div id='"+cpane_schedheader_id+"'></div><div id='"+cpane_schedgrid_id+"'></div>",
					title_suffix:' by Team',
				}
				this.createnewsched_pane(args_obj);
				this.prepgrid_data(constant.team_id, dbstatus)
				// add fairness metrics cpane
				cpane_id = this.cpane_id_mapobj.fair_id;
				cpane_txt_id = this.cpane_txt_id_mapobj.fair_id;
				cpane_grid_id = this.cpane_grid_id_mapobj.fair_id;
				cpane_schedgrid_id = this.cpane_schedgrid_id_mapobj.fair_id;
				cpane_schedheader_id = this.cpane_schedheader_id_mapobj.fair_id;
				cpane_select_id = this.opconstant_obj.faircpane_select_id;
				args_obj = {
					suffix_id:cpane_id,
					content_str:"<div id='"+cpane_txt_id+"'></div> <b>Select Division</b> and then select team ID by <b>clicking grid row</b> to see team-specific Fairness Metrics - scroll down<br><label for='"+cpane_select_id+"'>Select Division</label><select id='"+cpane_select_id+"' data-dojo-type='dijit/form/Select' name='"+cpane_select_id+"'></select><div id='"+cpane_grid_id+"'></div><div id='"+cpane_schedheader_id+"'></div><div id='"+cpane_schedgrid_id+"'></div>",
					title_suffix:' by Fairness Metrics',
				}
				this.createnewsched_pane(args_obj);
				this.prepgrid_data(constant.fair_id, dbstatus)
				// add cpane to display constraint satisfaction only if preferences
				// were specified
				if (this.pref_select_value) {
					cpane_id = this.cpane_id_mapobj.pref_id;
					cpane_txt_id = this.cpane_txt_id_mapobj.pref_id;
					cpane_grid_id = this.cpane_grid_id_mapobj.pref_id;
					cpane_schedheader_id = this.cpane_schedheader_id_mapobj.pref_id;
					args_obj = {
						suffix_id:cpane_id,
						content_str:"<div id='"+cpane_txt_id+"'></div><div id='"+cpane_schedheader_id+"'></div><div id='"+cpane_grid_id+"'></div><br>",
						title_suffix:' by Preference',
					}
					this.createnewsched_pane(args_obj);
					this.prepgrid_data(constant.pref_id, dbstatus);
				}
				// add cpane to display conflict avoidance only if team conflicts
				// were specified
				if (this.conflict_select_value) {
					cpane_id = this.cpane_id_mapobj.conflict_id;
					cpane_txt_id = this.cpane_txt_id_mapobj.conflict_id;
					cpane_grid_id = this.cpane_grid_id_mapobj.conflict_id;
					cpane_schedheader_id = this.cpane_schedheader_id_mapobj.conflict_id;
					args_obj = {
						suffix_id:cpane_id,
						content_str:"<div id='"+cpane_txt_id+"'></div><div id='"+cpane_schedheader_id+"'></div><div id='"+cpane_grid_id+"'></div><br>",
						title_suffix:' by Conflict',
					}
					this.createnewsched_pane(args_obj);
					this.prepgrid_data(constant.conflict_id, dbstatus);
				}
				// add cpane for xls hardcopy links
				cpane_id = this.cpane_id_mapobj.xls_id;
				//cpane_txt_id = this.cpane_txt_id_mapobj.xls_id;
				args_obj = {
					suffix_id:cpane_id,
					content_str:"",
					title_suffix:' hardcopy .xls'
				}
				var xls_cpane = this.createnewsched_pane(args_obj);
				var xls_obj = new GenerateXLS({op_type:this.op_type,
					server_interface:this.server_interface,
					schedcol_name:this.newsched_name});
				xls_obj.generate_xlscpane_widgets(xls_cpane);
			},
			prepgrid_data: function(idproperty, dbstatus) {
				var statusnode_id = null;
				var select_value = null;
				var db_type = null;
				if (idproperty == 'div_id') {
					statusnode_id = this.cpane_txt_id_mapobj.div_id;
					select_value = this.server_key_obj.divcol_name;
					db_type = this.server_key_obj.db_type;
					this.getgrid_data(idproperty, select_value, db_type);
				} else if (idproperty == 'field_id') {
					statusnode_id = this.cpane_txt_id_mapobj.field_id;
					select_value = this.server_key_obj.fieldcol_name;
					db_type = 'fielddb';
					this.getgrid_data(idproperty, select_value, db_type);
				} else if (idproperty == constant.team_id) {
					statusnode_id = this.cpane_txt_id_mapobj.team_id;
					this.getdivselect_dropdown(idproperty,
						this.opconstant_obj.teamcpane_select_id);
				} else if (idproperty == constant.fair_id) {
					statusnode_id = this.cpane_txt_id_mapobj.fair_id;
					this.getdivselect_dropdown(idproperty,
						this.opconstant_obj.faircpane_select_id);
				} else if (idproperty == constant.pref_id) {
					statusnode_id = this.cpane_txt_id_mapobj.pref_id;
					select_value = this.server_key_obj.prefcol_name;
					db_type = 'prefdb';
					this.getgrid_data(idproperty, select_value, db_type);
				} else if (idproperty == constant.conflict_id) {
					statusnode_id = this.cpane_txt_id_mapobj.conflict_id;
					select_value = this.server_key_obj.conflictcol_name;
					db_type = 'conflictdb';
					this.getgrid_data(idproperty, select_value, db_type);
				}
				this.schedutil_obj.updateDBstatus_node(dbstatus,
					dom.byId(statusnode_id))
			},
			getgrid_data:function(idproperty, select_value, db_type) {
				// now we want to create and populate grids, starting with
				// divinfo/fieldinfo grid.  First check if local store has data
				// corresponding to current collection
				var info_obj = baseinfoSingleton.get_obj(idproperty, this.op_type);
				if (info_obj) {
					// for pref_id or conflict_id always get from server as we want
					// to get the constraint/conflict satisfaction status from
					// the generated schedule
					if (idproperty != constant.pref_id &&
						idproperty != constant.conflict_id &&
						info_obj.infogrid_store &&
						info_obj.activegrid_colname == select_value) {
						var columnsdef_obj = info_obj.getfixedcolumnsdef_obj();
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
			pipegrid_data: function(adata, options_obj) {
				var griddata_list = adata.info_list;
				var columnsdef_obj = options_obj.info_obj.getfixedcolumnsdef_obj();
				this.createinfo_grid(options_obj.idproperty, columnsdef_obj,
					griddata_list);
			},
			getdivselect_dropdown: function(idproperty, select_id) {
				// first get the div information selected by
				// league_select_value and current_db_type
				// cross-reference widgetgen/get_leagueparam_list
				var select_value = this.league_select_value;
				var db_type = this.current_db_type;
				// check if the divselect_reg divsion select drop-down
				// for team id selection has been created; if it has not
				// create the dropdown.
				// first see if divinfo information is in current store
				var divinfo_obj = baseinfoSingleton.get_obj('div_id', this.op_type);
				if (divinfo_obj && divinfo_obj.infogrid_store &&
					divinfo_obj.activegrid_colname == select_value) {
					// if in store, get data and create dropdown
					var data_obj = new Object();
					data_obj.info_list = divinfo_obj.infogrid_store.query();
					// need to create config status property for data_list
					// before passing to createdivselect_dropdown as function
					// depends on config_status being true to create dropdown
					data_obj.config_status = divinfo_obj.config_status;
					this.createdivselect_dropdown(data_obj, {idproperty:idproperty,
						select_id:select_id});
				} else {
					// if not in store get from server
					this.server_interface.getServerData(
						'get_dbcol/'+db_type+'/'+select_value,
						lang.hitch(this, this.createdivselect_dropdown), null,
						{idproperty:idproperty, select_id:select_id});
				}
			},
			createdivselect_dropdown:function(data_obj, options_obj) {
				var idproperty = options_obj.idproperty;
				var select_id = options_obj.select_id;
				if (data_obj.config_status == 1) {
					var info_list = data_obj.info_list;
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
					var select_reg = registry.byId(select_id);
					select_reg.set("options", option_list);
					select_reg.startup();

					if (idproperty == constant.team_id) {
						if (this.teamdivselect_handle)
							this.teamdivselect_handle.remove();
						this.teamdivselect_handle = select_reg.on("change",
							lang.hitch(this, this.createteaminfo_grid,
								option_list, idproperty));
					} else if (idproperty == constant.fair_id) {
						if (this.fairdivselect_handle)
							this.fairdivselect_handle.remove();
						this.fairdivselect_handle = select_reg.on("change",
							lang.hitch(this, this.createfairinfo_grid,
								option_list, idproperty));
					}
					//select_reg.startup();
				} else {
					console.log("Warning: Div Configuration Not Complete");
				}
			},
			createteaminfo_grid: function(option_list, idproperty, event) {
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
				// Note team_id below in columnsdef does not reflect
				// idproperty - we are merely creating a grid of team id's whether idproperty is constant.team_id or constant.fair_id
				var columnsdef_obj = {team_id:"Team ID"}
				var griddata_list = new Array();
				for (var i=1; i<totalteams+1; i++) {
					griddata_list.push({team_id:i})
				}
				this.createinfo_grid(idproperty, columnsdef_obj,
					griddata_list, query_obj);
			},
			createfairinfo_grid: function(option_list, idproperty, event) {
				var match_option = arrayUtil.filter(option_list,
					function(item) {
						return item.value == event;
					})
				var match = match_option[0];
				var query_obj = {div_age:match.div_age,
					div_gen:match.div_gen};
				this.setselect_text(match, idproperty);
				var callback_method = this.gridmethod_mapobj[idproperty]
				// send request to server = note event is the div_id here
				this.server_interface.getServerData('get_schedule/'+
					this.newsched_name+'/'+idproperty+'/'+event,
					callback_method,
					query_obj, {idproperty:idproperty}
				);
			},
			createinfo_grid: function(idproperty, columnsdef_obj, griddata_list, query_obj) {
				var query_obj = (typeof query_obj === "undefined" || query_obj === null) ? "" : query_obj;
				/*
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
				} */
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
				if (idproperty != 'pref_id' && idproperty != 'conflict_id') {
					// set up infogrid selection handles and setup callbacks that
					// will create secondary grids
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
				} else {
					// preference id grid is a standalong-grid and it's rows
					// are not selectable
					// set secondary text for pref_id
					if (idproperty == 'pref_id') {
						this.setselect_text({prefcol_name:this.server_key_obj.prefcol_name}, 'pref_id');
						// change convert satisfy status to text
						arrayUtil.forEach(griddata_list, function(item) {
							if (item.satisfy) {
								item.satisfy = 'Yes';
							} else {
								item.satisfy = 'No';
							}
						})
					} else if (idproperty == 'conflict_id') {
						this.setselect_text({conflictcol_name:this.server_key_obj.conflictcol_name}, 'conflict_id');
					}

				}
				info_grid.renderArray(griddata_list);
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
					constant.slot_id);
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
					constant.game_id);
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
					constant.game_id);
			},
			createfairsched_grid: function(adata, options_obj) {
				var idproperty = options_obj.idproperty;
				var metrics_list = adata.metrics_list;
				var divfield_list = adata.divfield_list;
				var columnsdef_obj = {
					team_id:"Team ID",
					games_total:"Total# Games",
					homegames_ratio:"Home Ratio",
					earliest_count:"# Earliest Games",
					latest_count:"# Latest Games",
				}
				// see schedmaster.py get_schedule() for definition of divfield_list
				// also see fieldinfo.js modify_toserver() where divfield is created
				// locally
				// Extract column header field names
				arrayUtil.forEach(divfield_list, function(item) {
					columnsdef_obj[item.field_id] = "# Games "+item.field_name;
				})
				// flatten field_count_list
				arrayUtil.forEach(metrics_list, function(item) {
					arrayUtil.forEach(item.field_count_list, function(item2) {
						item[item2.field_id] = item2.field_count;
					})
				})
				//
				this.createsched_grid(idproperty, metrics_list, columnsdef_obj,
					constant.team_id);
			},
			createsched_grid: function(idproperty, game_list, columnsdef_obj, store_idproperty) {
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
					sched_store = new Observable(new Memory({data:game_list, idProperty:store_idproperty}));
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
				return newcpane
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
				} else if (idproperty == constant.team_id) {
					text_str = "Team ID#"+event_data.team_id + " selected";
				} else if (idproperty == 'pref_id') {
					text_str = "Preference List ID: "+event_data.prefcol_name;
				} else if (idproperty == 'conflict_id') {
					text_str = "Conflict List ID: "+event_data.conflictcol_name;
				}
				dom.byId(schedheader_id).innerHTML = text_str;
			},
			reset_newschedwatch_obj: function() {
				this.newschedwatch_obj.set("leagueselect_flag", false);
				this.newschedwatch_obj.set("fgselect_flag", false);
				this.newschedwatch_obj.set("league_fg_flag", false);
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
				// add sched config  cpane
				var newsched_cpane = new ContentPane({
					id:wizconstant.nscpane_id,
				})
				var newsched_form = new Form({
					id:this.idmgr_obj.form_id
				})
				newsched_cpane.addChild(newsched_form);
				this.pstackcontainer.addChild(newsched_cpane);
				// add txt + button cpane
				var txtbtn_cpane = new ContentPane({
					id:this.idmgr_obj.textbtncpane_id,
				})
				put(txtbtn_cpane.containerNode, "span[id=$]",
					this.idmgr_obj.text_id);
				put(txtbtn_cpane.containerNode, "br");
				//put(txtbtn_cpane.containerNode, "button[id=$]",
				//	this.idmgr_obj.btn_id);
				this.pstackcontainer.addChild(txtbtn_cpane)
				// create grid stack container and grid
				this.gstackcontainer = new StackContainer({
					doLayout:false,
					style:"clear:left",
					id:this.idmgr_obj.gcontainer_id
				}, gcontainerdiv_node);
				// add blank pane (for resetting); no grid for new sched
				var blank_cpane = new ContentPane({
					id:this.idmgr_obj.blankcpane_id
				})
				this.gstackcontainer.addChild(blank_cpane);
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
				if (this.teamdivselect_handle)
					this.teamdivselect_handle.remove();
				if (this.fairdivselect_handle)
					this.fairdivselect_handle.remove();
			}
		});
	})
