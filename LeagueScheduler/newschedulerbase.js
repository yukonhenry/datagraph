define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare",
	"dojo/_base/lang", "dojo/Stateful",
	"dojo/_base/array", "dojo/keys", "dojo/store/Memory", "dojo/store/Observable",
	"dijit/registry", "dijit/Tooltip",
	"dijit/form/ValidationTextBox","dijit/form/Select", "dijit/form/Button",
	"dijit/form/NumberSpinner", "dijit/form/DateTextBox",
	"dijit/layout/ContentPane", "dgrid/Grid",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection",
	"LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/widgetgen",
	"put-selector/put", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, Stateful, arrayUtil, keys,
		Memory, Observable, registry, Tooltip, ValidationTextBox, Select, Button,
		NumberSpinner, DateTextBox, ContentPane, Grid,
		OnDemandGrid, editor, Keyboard, Selection, EditGrid,
		baseinfoSingleton, WidgetGen, put) {
		var constant = {
			idproperty_str:'newsched_id',
			form_name:'newsched_form_id',
			scinput_div:'seasoncalendar_input',
			radio1_id:'scradio1_id',
			radio2_id:'scradio2_id',
			league_select_id:'scleague_select_id',
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
			default_db_type:'rrdb',
			get_dbcol:'get_dbcol/'
		};
		var newschedwatch_class = declare([Stateful],{
			leagueselect_flag:false,
			league_fg_flag:false
		})
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			newsched_dom:"", schedutil_obj:null, storeutil_obj:null,
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
			current_db_type:constant.default_db_type,
			tabcontainer_reg:null,
			cpane_grid_id_mapobj:null, cpane_schedgrid_id:null,
			info_grid_mapobj:null, info_handle_mapobj:null, gridmethod_mapobj:null,
			sched_store_mapobj:null, sched_grid_mapobj:null,
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
					field_id:constant.newfieldcpane_grid_id}
				this.cpane_schedgrid_id_mapobj = {
					div_id:constant.newdivcpane_schedgrid_id,
					field_id:constant.newfieldcpane_schedgrid_id}
				this.cpane_schedheader_id_mapobj = {
					div_id:constant.newdivcpane_schedheader_id,
					field_id:constant.newfieldcpane_schedheader_id}
				this.info_grid_mapobj = {div_id:null, field_id:null};
				this.info_handle_mapobj = {div_id:null, field_id:null};
				this.gridmethod_mapobj = {
					div_id:lang.hitch(this, this.createsched_grid),
					field_id:lang.hitch(this, this.createfieldsched_grid)};
				this.sched_store_mapobj = {div_id:null, field_id:null};
				this.sched_grid_mapobj = {div_id:null, field_id:null};
			},
			initialize: function(arg_obj) {
				this.form_reg = registry.byId(constant.form_name);
				//this.dbname_reg = registry.byId("newsched_input_id");
				// put selector documentation
				// http://davidwalsh.name/put-selector
				// https://github.com/kriszyp/put-selector
				// first check to see if the domNode has already been created by
				// seeing the dom node can be retrieved
				var sched_input = dom.byId("newched_input_id");
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
					this.dbname_reg = registry.byNode(sched_input);
				}

				this.seasondates_btn_reg = registry.byId("seasondates_btn");
				this.newsched_dom = dom.byId("newsched_text");
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
				var tooltipconfig = {connectId:['newsched_input_id'],
					label:"Enter Schedule Name and press ENTER",
					position:['below','after']};
				this.tooltip = new Tooltip(tooltipconfig);
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
						// disable schedule name form
						//this.schedutil_obj.makeInvisible(this.form_dom);
						if (this.keyup_handle)
							this.keyup_handle.remove();
						this.newsched_dom.innerHTML = "Schedule Name: "+this.newsched_name;
						var today = new Date();
						var scinput_dom = dom.byId(constant.scinput_div);
						// get or create handle to widgetgen obj
						if (!this.widgetgen) {
							this.widgetgen = new WidgetGen({
								storeutil_obj:this.storeutil_obj,
								server_interface:this.server_interface
							});
						}
						this.widgetgen.create_dbtype_radiobtn(scinput_dom,
							constant.radio1_id, constant.radio2_id,
							constant.default_db_type, this,
							this.radio1_callback, this.radio2_callback,
							constant.league_select_id);
						// create league info dropdowns
						var select_node = dom.byId(constant.league_select_id);
						if (!select_node) {
							// get parent dom and generate dropdown selects
							put(scinput_dom,
								"label.label_box[for=$]", constant.league_select_id,
								"Select League");
							select_node = put(scinput_dom,
								"select[id=$][name=league_select]",
								constant.league_select_id);
							this.league_select = new Select({
								name:'league_select',
								onChange: lang.hitch(this, function(evt) {
									this.newschedwatch_obj.set('leagueselect_flag',evt!="");
									this.league_select_value = evt;
								})
							}, select_node);
							args_obj = {db_type:'rrdb', label_str:'Select League',
								config_status:true};
							var option_list = this.storeutil_obj.getLabelDropDown_list(args_obj);
							this.league_select.addOption(option_list);
							this.league_select.startup();
							if (option_list.length < 2) {
								var ls_tooltipconfig = {
									connectId:[constant.league_select_id],
									label:"If Empty Specify League Spec's First",
									position:['above','after']};
								var ls_tooltip = new Tooltip(ls_tooltipconfig);
							}
							put(scinput_dom, "br, br");  // add space
						} else {
							this.league_select = registry.byNode(select_node);
						}
						// create field group dropdown
						var fg_select_node = dom.byId("fg_select_id");
						if (!fg_select_node) {
							put(scinput_dom,
								"label.label_box[for=fg_select_id]",
								"Select Field Group");
							fg_select_node = put(scinput_dom,
								"select#fg_select_id[name=fg_select]");
							this.fg_select = new Select({
								name:'fg_select',
								onChange: lang.hitch(this, function(evt) {
									this.newschedwatch_obj.set('fgselect_flag',
										evt!="");
									this.fg_select_value = evt;
								})
							}, fg_select_node);
							args_obj = {db_type:'fielddb',
								label_str:'Select Field Group', config_status:true};
							var option_list = this.storeutil_obj.getLabelDropDown_list(args_obj);
							this.fg_select.addOption(option_list);
							this.fg_select.startup();
							if (option_list.length < 2) {
								var fg_tooltipconfig = {
									connectId:['fg_select_id'],
									label:"If Empty Specify Field Groups First",
									position:['above','after']};
								var fg_tooltip = new Tooltip(fg_tooltipconfig);
							}
							put(scinput_dom, "span.empty_gap");
						} else {
							this.fg_select = registry.byNode(fg_select_node);
						}
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
						// storeutl
						this.selectexists_flag = true;
						// need to add btn callbacks here
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
				// follow up on cases where data needs to be queried from server.
				return false;
			},
			is_newgrid_required: function() {
				return false;
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
			},
			update_schedstatustxt: function(adata, options_obj) {
				dbstatus = adata.dbstatus;
				var schedstatustxt_node = options_obj.node;
				this.schedutil_obj.updateDBstatus_node(dbstatus,
					schedstatustxt_node);
				// create new tab to hold table grid for newsched information
				this.tabcontainer_reg = registry.byId(constant.tabcontainer_id);
				var args_obj = {
					suffix_id:constant.newdivcpane_id,
					// define contents of div pane
					content_str:"<div id='"+constant.newdivcpane_txt_id+"'></div> <b>Click on Division row</b> to see division-specific schedule - scroll down. <div id='"+constant.newdivcpane_grid_id+"'></div><div id='"+constant.newdivcpane_schedheader_id+"'></div><div id='"+constant.newdivcpane_schedgrid_id+"'></div>",
					title_suffix:' by Div'
				}
				this.createnewsched_pane(args_obj);
				this.getgrid_data('div_id');
				args_obj = {
					suffix_id:constant.newfieldcpane_id,
					// define contents of select-by-field pane
					content_str:"<div id='"+constant.newfieldcpane_txt_id+"'></div> <b>Click on Field row</b> to see field-specific schedule - scroll down. <div id='"+constant.newfieldcpane_grid_id+"'></div><div id='"+constant.newfieldcpane_schedheader_id+"'></div><div id='"+constant.newfieldcpane_schedgrid_id+"'></div>",
					title_suffix:' by Field'
				}
				this.createnewsched_pane(args_obj);
				this.getgrid_data('field_id');
			},
			getgrid_data: function(idproperty) {
				var statusnode_id = null;
				var select_value = null;
				var db_type = null;
				if (idproperty == 'div_id') {
					statusnode_id = constant.newdivcpane_txt_id;
					select_value = this.league_select_value;
					db_type = this.current_db_type;
				} else if (idproperty == 'field_id') {
					statusnode_id = constant.newfieldcpane_txt_id;
					select_value = this.fg_select_value;
					db_type = 'fielddb';
				}
				this.schedutil_obj.updateDBstatus_node(dbstatus,
					dom.byId(statusnode_id))
				// now we want to create and populate grids, starting with
				// divinfo grid.  First check if local store has data
				// corresponding to current collection
				var info_obj = baseinfoSingleton.get_obj(idproperty);
				if (info_obj && info_obj.infogrid_store &&
					info_obj.activegrid_colname == select_value) {
					var columnsdef_obj = info_obj.getfixedcolumnsdef_obj();
					var griddata_list = info_obj.infogrid_store.query().map(function(item) {
						var map_obj = {}
						// only extra data corresponding to keys specified in
						// columnsdef_obj.  This may be a subset of all the keys
						// available in the store.
						for (var key in columnsdef_obj) {
							map_obj[key] = item[key];
						}
						return map_obj;
					})
					this.createinfo_grid(idproperty, columnsdef_obj, griddata_list);
				} else {
					// if info is not available in the store, get it from
					// the server.
					this.server_interface.getServerData(
						"get_dbcol/"+select_value,
						lang.hitch(this, this.pipegrid_data),
						{db_type:db_type},
						{info_obj:info_obj, idproperty:idproperty});
				}
			},
			pipegrid_data: function(adata, options_obj) {
				var griddata_list = adata.info_list;
				var columnsdef_obj = options_obj.info_obj.getfixedcolumnsdef_obj();
				this.createinfo_grid(options_obj.idproperty, columnsdef_obj,
					griddata_list);
			},
			createinfo_grid: function(idproperty, columnsdef_obj, griddata_list) {
				var info_grid = this.info_grid_mapobj[idproperty];
				if (!info_grid) {
					var cpane_grid_id = this.cpane_grid_id_mapobj[idproperty];
					var StaticGrid = declare([Grid, Keyboard, Selection]);
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
						null, {idproperty:idproperty});
				}))
				this.info_handle_mapobj[idproperty] = info_handle;
			},
			createsched_grid: function(adata, options_obj) {
				var idproperty = options_obj.idproperty;
				var fieldname_dict = adata.fieldname_dict;
				var game_list = adata.game_list;
				var fieldinfo_obj = baseinfoSingleton.get_obj('field_id');
				var fielddaymapdate_obj = fieldinfo_obj.fielddaymapdate_obj;
				var columnsdef_obj = {
					date:'Game Day', time:'Game Time'
				}
				for (var key in fieldname_dict) {
					columnsdef_obj[key] = fieldname_dict[key]
				}
				var grid_list = new Array();
				arrayUtil.forEach(game_list, function(item, index) {
					var grid_row = new Object();
					grid_row.game_id = index+1;
					grid_row.date = fielddaymapdate_obj[item.fieldday_id];
					grid_row.time = item.start_time;
					arrayUtil.forEach(item.gameday_data, function(item2) {
						grid_row[item2.venue] = item2.home+'v'+item2.away;
					})
					grid_list.push(grid_row);
				})
				var sched_store = this.sched_store_mapobj[idproperty];
				var sched_grid = this.sched_grid_mapobj[idproperty];
				if (sched_store) {
					// if store already exists, repopulate store with new data
					// and refresh grid
					sched_store.setData(grid_list);
					sched_grid.refresh();
				} else {
					var cpane_schedgrid_id = this.cpane_schedgrid_id_mapobj[idproperty];
					sched_store = new Observable(new Memory({data:grid_list, idProperty:'game_id'}));
					var StaticGrid = declare([OnDemandGrid, Keyboard, Selection]);
					sched_grid = new StaticGrid({
						columns:columnsdef_obj,
						store:sched_store
					}, cpane_schedgrid_id);
					sched_grid.startup();
					sched_grid.resize();
					this.sched_store_mapobj[idproperty] = sched_store;
					this.sched_grid_mapobj[idproperty] = sched_grid;
				}
			},
			createfieldsched_grid: function(adata, options_obj) {
				// create schedule grid defined by selected field_id
				var idproperty = options_obj.idproperty;
				var game_list = adata.game_list;
				var fieldinfo_obj = baseinfoSingleton.get_obj('field_id');
				var fielddaymapdate_obj = fieldinfo_obj.fielddaymapdate_obj;
				var columnsdef_obj = {
    				fieldday_id:'Game Date',
    				start_time:'Start Time',
    				div_age:'Age Group/Primary ID',
    				div_gen:'Gender/Secondary ID',
    				home:'Home Team#',
    				away:'Away Team#'
				}
				arrayUtil.forEach(game_list, function(item, index) {
					item.game_id = index+1; //to be used as idprop for store
					item.fieldday_id = fielddaymapdate_obj[item.fieldday_id];
				})
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
					sched_store = new Observable(new Memory({data:game_list, idProperty:'game_id'}));
					var StaticGrid = declare([OnDemandGrid, Keyboard, Selection]);
					sched_grid = new StaticGrid({
						columns:columnsdef_obj,
						store:sched_store
					}, cpane_schedgrid_id);
					sched_grid.startup();
					sched_grid.resize();
					this.sched_store_mapobj[idproperty] = sched_store;
					this.sched_grid_mapobj[idproperty] = sched_grid;
				}
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
			}
		});
	})
