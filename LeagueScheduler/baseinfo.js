define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/_base/array", "dojo/keys",
	"dijit/registry", "dijit/Tooltip", "dijit/form/Button",
	"dijit/form/RadioButton", "LeagueScheduler/widgetgen",
	"dijit/form/Form", "dijit/layout/StackContainer", "dijit/layout/ContentPane",
	"LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton",
	"LeagueScheduler/idmgrSingleton", "put-selector/put",
	"dojo/domReady!"],
	function(dbootstrap, dom, declare, lang, arrayUtil, keys,
		registry, Tooltip, Button, RadioButton, WidgetGen, Form, StackContainer,
		ContentPane, EditGrid,
		baseinfoSingleton, idmgrSingleton,
		put) {
		var constant = {
			// entry_pt id's
			init:"init", fromdb:"fromdb",  fromdel:"fromdel",
			serverstatus_key:"config_status"
		};
		return declare(null, {
			server_interface:null, editgrid:null, uistackmgr_type:null,
			storeutil_obj:null,
			keyup_handle:null, tooltip_list:null, totalrows_num:0,
			schedutil_obj:null, activegrid_colname:"",
			config_status:0, gridtooltip_list:null,
			btntxtid_list:null, op_type:"", op_prefix:"", idmgr_obj:null,
			infogrid_store:null,
			constructor: function(args) {
				lang.mixin(this, args);
				this.idmgr_obj = idmgrSingleton.get_idmgr_obj({
					id:this.idproperty, op_type:this.op_type});
				this.tooltip_list = new Array();
				// use to create op-type unique id strings local to this file
				this.op_prefix = this.op_type.substring(0,3);
			},
			showConfig: function(args_obj) {
				var tooltipconfig_list = args_obj.tooltipconfig_list;
				delete args_obj.tooltipconfig_list;  //save space before passing?
				var entrynum_reg = args_obj.entrynum_reg;
				// ref http://stackoverflow.com/questions/11743392/check-if-array-is-empty-or-exists
				// to check if array exists and is non-empty
				if (typeof tooltipconfig_list !== 'undefined' && this.tooltip_list.length == 0) {
					arrayUtil.forEach(tooltipconfig_list, function(item) {
						this.tooltip_list.push(new Tooltip(item));
					}, this);
				}
				this.uistackmgr_type.switch_pstackcpane({idproperty:this.idproperty,
					p_stage: "preconfig", entry_pt:constant.init});
				// switch to blank cpane
				this.uistackmgr_type.switch_gstackcpane(this.idproperty, true);
				if (this.keyup_handle)
					this.keyup_handle.remove();
				this.keyup_handle = entrynum_reg.on("keyup", lang.hitch(this, this.processdivinfo_input, args_obj));
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(args_obj, event) {
				if (event.keyCode == keys.ENTER) {
					var form_reg = args_obj.form_reg;
					var dbname_reg = args_obj.dbname_reg;
					var entrynum_reg = args_obj.entrynum_reg;
					var newgrid_flag = args_obj.newgrid_flag;
					var grid_id = args_obj.grid_id;
					var cellselect_flag = args_obj.cellselect_flag;
					var text_node_str = args_obj.text_node_str;
					var updatebtn_str = args_obj.updatebtn_str;
					var op_type = args_obj.op_type;
					if (form_reg.validate()) {
						confirm('Input format is Valid, creating new DB');
						this.activegrid_colname = dbname_reg.get("value")
						if (!this.storeutil_obj.nodupdb_validate(
							this.activegrid_colname, this.idproperty)) {
							alert("Selected sched name already exists, choose another");
							return;
						}
						//rownum, is the total # of divisions/fields/current config
						this.totalrows_num = entrynum_reg.get("value");
						var info_list = this.getInitialList(this.totalrows_num);
						if (this.keyup_handle)
							this.keyup_handle.remove();
						// if idproperty is field, create radio buttons for
						// db selection (for div select)
						baseinfoSingleton.set_watch_obj('divstr_list', [],
							this.op_type, this.idproperty)
						if (this.idproperty == 'field_id' ||
							this.idproperty == 'pref_id' ||
							this.idproperty == 'conflict_id') {
							// field_id-specific UI above grid
							this.initabovegrid_UI();
						} else if (this.idproperty == 'div_id') {
							this.create_calendar_input(op_type);
						} else if (this.idproperty == 'team_id') {
							console.log("CodeLogicError: baseinfo:processdivinfo_input: execution not expected for team_id");
						}
						var args_obj = null;
						if (newgrid_flag) {
							var columnsdef_obj = this.getcolumnsdef_obj();
							this.editgrid = new EditGrid({griddata_list:info_list,
								colname:this.activegrid_colname,
								server_interface:this.server_interface,
								grid_id:grid_id,
								//error_node:dom.byId("divisionInfoInputGridErrorNode"),
								idproperty:this.idproperty,
								cellselect_flag:cellselect_flag,
								info_obj:this,
								uistackmgr_type:this.uistackmgr_type,
								storeutil_obj:this.storeutil_obj,
								db_type:this.db_type});
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
						args_obj.updatebtn_str = updatebtn_str;
						args_obj.text_node_str = text_node_str;
						args_obj.idproperty = this.idproperty;
						args_obj.colname = this.activegrid_colname;
						args_obj.entry_pt = constant.init;
						args_obj.op_type = op_type;
						this.reconfig_infobtn(args_obj);
					} else {
						alert('Input name is Invalid, please correct');
					}
				}
			},
			// set and get divinfo  obj information that is attached to the current
			// info obj (fieldinfo or preferenceinfo)
			setdivstr_obj: function(colname, db_type) {
				this.divstr_colname = colname;
				this.divstr_db_type = db_type;
			},
			getdivstr_obj: function() {
				return {colname:this.divstr_colname, db_type:this.divstr_db_type};
			},
			initabovegrid_UI: function(topdiv_node) {
				if (typeof topdiv_node === "undefined" ||
					topdiv_node === null) {
					var infogrid_node = dom.byId(this.idmgr_obj.grid_id);
					var topdiv_node = put(infogrid_node, "-div");
				}
				this.create_dbselect_radiobtnselect(
					this.idmgr_obj.radiobtn1_id, this.idmgr_obj.radiobtn2_id,
					this.idmgr_obj.league_select_id, "", "", topdiv_node);
				return topdiv_node;
			},
			create_dbselect_radiobtnselect: function(radio1_id, radio2_id, select_id, init_db_type, init_colname, topdiv_node) {
				// passed in init_db_type and init_colname are typicall
				// for divinfo(divstr) db_type and colname even though it
				// is used for fieldinfo grid
				//For field grids, create radio button pair to select
				// schedule type - rr or tourn
				if (!this.widgetgen) {
					this.widgetgen = new WidgetGen({
						storeutil_obj:this.storeutil_obj,
						server_interface:this.server_interface
					});
				}
				this.widgetgen.create_dbtype_radiobtn(topdiv_node,
					radio1_id, radio2_id, init_db_type,
					this, this.radio1_callback, this.radio2_callback, select_id);
				//for callback function, additional parameters after the first two
				// are passed to the callback as extra parameters.
				var args_obj = {
					topdiv_node:topdiv_node, select_id:select_id,
					init_db_type:init_db_type,
					init_colname:init_colname,
					onchange_callback:lang.hitch(this.widgetgen, this.widgetgen.get_leagueparam_list, this),
					name_str:"league select",
					label_str:"Select League",
					put_trail_spacing:"br"}
				this.widgetgen.create_select(args_obj);
			},
			// callback function when dbtype radiobutton is changed
			radio1_callback: function(select_id, event) {
				if (event) {
					this.widgetgen.swap_league_select_db(select_id, 'rrdb');
					this.divstr_db_type = 'rrdb';
				}
			},
			radio2_callback: function(select_id, event) {
				if (event) {
					this.widgetgen.swap_league_select_db(select_id, 'tourndb');
					this.divstr_db_type = 'tourndb';
				}
			},
			getServerDBInfo: function(options_obj) {
				// note third parameter maps to query object, which in this case
				// there is none.  But we need to provide some argument as js does
				// not support named function arguments.  Also specifying "" as the
				// parameter instead of null might be a better choice as the query
				// object will be emitted in the jsonp request (though not consumed
				// at the server)
				var item = options_obj.item;
				var getserver_path = "get_dbcol/";
				// define key for object returned from server to get
				// status of configuration - config_status
				this.server_interface.getServerData(
					getserver_path+options_obj.db_type+'/'+item,
					lang.hitch(this, this.createEditGrid), null, options_obj);
			},
			createEditGrid: function(server_data, options_obj) {
				// don't create grid if a grid already exists and it points to the same schedule db col
				// if grid needs to be generated, make sure to clean up prior to recreating editGrid
				this.activegrid_colname = options_obj.item;
				var columnsdef_obj = this.getcolumnsdef_obj();
				var idproperty = this.idproperty;
				// if server data is fielddb information, then we need to do
				// some data conversion (convert to date obj) before passing onto grid
				// Note server_key is key for outgoing request
				// serverdata_key is for incoming data
				var data_list = server_data[options_obj.serverdata_key];
				// extract configuration status from server. integer value 0/1
				var config_status = server_data[constant.serverstatus_key];
				this.totalrows_num = data_list.length;
				if (options_obj.db_type == 'fielddb') {
					if (idproperty == 'field_id') {
						data_list = this.modifyserver_data(data_list,
							server_data.divstr_obj, columnsdef_obj);
					} else {
						alert('check db_type and idproperty consistency');
					}
				} else if (options_obj.db_type == 'prefdb') {
					if (idproperty == 'pref_id') {
						data_list = this.modifyserver_data(data_list,
							server_data.divstr_obj);
					} else {
						alert('check db_type and idproperty consistency');
					}
				}
				if (!this.server_interface) {
					console.log("no server interface");
					alert("no server interface, check if service running");
				}
				if (options_obj.newgrid_flag) {
					this.editgrid = new EditGrid({griddata_list:data_list,
						colname:this.activegrid_colname,
						server_interface:this.server_interface,
						grid_id:options_obj.grid_id,
						//error_node:dom.byId("divisionInfoInputGridErrorNode"),
						idproperty:idproperty,
						cellselect_flag:options_obj.cellselect_flag,
						info_obj:this,
						uistackmgr_type:this.uistackmgr_type,
						storeutil_obj:this.storeutil_obj,
						db_type:this.db_type});
					this.editgrid.recreateSchedInfoGrid(columnsdef_obj);
				} else {
					this.editgrid.replace_store(this.activegrid_colname, data_list);
				}
				var args_obj = {
					colname:this.activegrid_colname,
					text_node_str:options_obj.text_node_str,
					updatebtn_str:options_obj.updatebtn_str,
					idproperty:idproperty,
					swapcpane_flag:options_obj.swapcpane_flag,
					newgrid_flag:options_obj.newgrid_flag
				}
				args_obj.entry_pt = constant.fromdb;
				args_obj.op_type = options_obj.op_type;
				var gridstatus_node = this.reconfig_infobtn(args_obj);
				// add config status text next to update btn
				this.update_configdone(config_status, gridstatus_node);
			},
			// function to reassign infobtn_update with title string and callback
			// function.  Also update pstack/gstack_cpane.
			reconfig_infobtn: function(args_obj) {
				// parse args object
				this.activegrid_colname = args_obj.colname;
				var op_type = ('op_type' in args_obj)?args_obj.op_type:"advance";
				var text_node_str = args_obj.text_node_str;
				var updatebtn_str = args_obj.updatebtn_str;
				var idproperty = args_obj.idproperty;
				var swapcpane_flag = args_obj.swapcpane_flag;
				var newgrid_flag = args_obj.newgrid_flag;
				var entry_pt = args_obj.entry_pt;
				var text_id = this.idmgr_obj.text_id;
				var btn_id = this.idmgr_obj.btn_id;
				var text_node = dom.byId(text_id);
				var text_str = text_node_str + ": <b>"+this.activegrid_colname+"</b>";
				text_node.innerHTML = text_str;
				var updatebtn_widget = this.getInfoBtn_widget(updatebtn_str,
					idproperty, btn_id);
				// get status line node; also pass it to callback, callback in turn calls update_configdone
				var gridstatus_node = this.get_gridstatus_node(updatebtn_widget, op_type, idproperty);
				var btn_callback = lang.hitch(this.editgrid, this.editgrid.sendStoreInfoToServer, gridstatus_node);
				updatebtn_widget.set("onClick", btn_callback);
				this.update_configdone(-1, gridstatus_node); // reset
				if (swapcpane_flag) {
					this.uistackmgr_type.switch_pstackcpane({idproperty:idproperty,
						p_stage:"config", entry_pt:entry_pt,
						text_str:text_str, btn_callback: btn_callback,
						updatebtn_str:updatebtn_str});
					if (!newgrid_flag) {
						// also swap grid if we are not generating a new one
						// if we are generating a new grid, switchgstack is called
						// from within editgrid
						this.uistackmgr_type.switch_gstackcpane(idproperty, false,
							this.editgrid.schedInfoGrid);
					}
				}
				return gridstatus_node
			},
			reconfig_infobtn_fromuistack: function(args_obj) {
				// parse args object
				var op_type = ('op_type' in args_obj)?args_obj.op_type:"advance";
				var idproperty = args_obj.idproperty;
				var text_id = this.idmgr_obj.text_id;
				var btn_id = this.idmgr_obj.btn_id;
				var text_node = dom.byId(text_id);
				text_node.innerHTML = args_obj.text_str;
				var updatebtn_str = args_obj.updatebtn_str;
				var updatebtn_widget = this.getInfoBtn_widget(updatebtn_str,
					idproperty, btn_id);
				var btn_callback = args_obj.btn_callback;
				updatebtn_widget.set("onClick", btn_callback);
				var gridstatus_node = this.get_gridstatus_node(updatebtn_widget,
					op_type, idproperty);
				this.update_configdone(-1, gridstatus_node); // reset
			},
			getInfoBtn_widget: function(label_str, idproperty_str, infobtn_id) {
				var infobtn_widget = registry.byId(infobtn_id);
				if (infobtn_widget) {
					var info_type = infobtn_widget.get('info_type');
					if (info_type != idproperty_str) {
						infobtn_widget.set('label', label_str);
						infobtn_widget.set('info_type', idproperty_str);
					}
				} else {
					infobtn_widget = new Button({
						label:label_str,
						title:"Click to Save",
						type:"button",
						class:"primary",
						style:"margin-left:20px",
						info_type:idproperty_str
					}, infobtn_id);
					infobtn_widget.startup();
				}
				return infobtn_widget;
			},
			get_gridstatus_node: function(updatebtn_widget, op_type, idproperty) {
				var gridstatus_id = op_type+idproperty+'gridstatus_span';
				var gridstatus_node = dom.byId(gridstatus_id);
				if (!gridstatus_node) {
					gridstatus_node = put(updatebtn_widget.domNode,
						"+span.empty_smallgap_color[id=$]", gridstatus_id);
					//gridstatus_node.innerHTML = 'test span';
				}
				return gridstatus_node;
			},
			update_configdone: function(config_status, gridstatus_node) {
				if (config_status == 1) {
					gridstatus_node.style.color = 'green';
					gridstatus_node.innerHTML = "Config Complete";
				} else if (config_status == 0) {
					gridstatus_node.style.color = 'orange';
					gridstatus_node.innerHTML = "Config Not Complete";
				} else {
					// implement reset condition
					gridstatus_node.innerHTML = "";
				}
				// save as member var so that it can be accessed (i.e. send_delta)
				this.config_status = config_status;
			},
			is_serverdata_required: function(options_obj) {
				return (options_obj.item != this.activegrid_colname)?true:false;
			},
			is_newgrid_required: function() {
				if (!this.editgrid)
					return true;
				else
					return (this.editgrid.schedInfoGrid)?false:true;
			},
			checkconfig_status: function(raw_result){
				// do check to make sure all fields have been filled.
				// note construct of using arrayUtil.some works better than
				// query.filter() as loop will exit immediately if .some() returns
				// true.
				// config_status is an integer type as booleans cannot be directly
				// be transmitted to server (sent as 'true'/'false' string)
				// Baseline implementation - if need to customize, do so in
				// inherited child class
				var config_status = 0;
				if (arrayUtil.some(raw_result, function(item, index) {
					// ref http://stackoverflow.com/questions/8312459/iterate-through-object-properties
					// iterate through object's own properties too see if there
					// any unfilled fields.  If so alert and exit without sending
					// data to server
					var break_flag = false;
					for (var prop in item) {
						if (item[prop] === "") {
							//alert("Not all fields in grid filled out, but saving");
							break_flag = true;
							break;
						}
					}
					return break_flag;
				})) {
					// insert return statement here if plan is to prevent saving.
					console.log("Not all fields complete for "+this.idproperty+
						" but saving");
				} else {
					config_status = 1;
				}
				return config_status;
			},
			getuniquematch_obj: function(list, key, value) {
				var match_list = arrayUtil.filter(list,
					function(item) {
						return item[key] == value;
					});
				return match_list[0];
			},
			getmatch_list: function(list, key, value) {
				var match_list = arrayUtil.filter(list,
					function(item) {
						return item[key] == value;
					});
				return match_list;
			},
			enable_gridtooltips: function(grid) {
				var gridhelp_list = this.get_gridhelp_list();
				// ref http://stackoverflow.com/questions/11743392/check-if-array-is-empty-or-exists
				if (typeof gridhelp_list !== 'undefined' &&
					gridhelp_list.length > 0) {
					if (this.gridtooltip_list) {
						arrayUtil.forEach(this.gridtooltip_list, function(item) {
							item.destroyRecursive();
						})
					}
					this.gridtooltip_list = new Array();
					var tooltipconfig_list = new Array();
					arrayUtil.forEach(gridhelp_list, function(help_obj) {
						var tooltipconfig = {
							connectId:[grid.columns[help_obj.id].headerNode],
							label:help_obj.help_str,
							position:['above', 'before']}
						tooltipconfig_list.push(tooltipconfig);
						this.gridtooltip_list.push(new Tooltip(tooltipconfig));
					}, this)
				}
			},
			create_wizardcontrol: function(pcontainerdiv_node, gcontainerdiv_node) {
				// create cpane control for any info wizard pane under menubar -
				// define as baseinfo method as many info wizardcontrol has an
				// identical structure
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
				// add info config (number) cpane
				var info_cpane = new ContentPane({
					id:this.idmgr_obj.numcpane_id
				})
				var info_form = new Form({
					id:this.idmgr_obj.form_id
				})
				info_cpane.addChild(info_form);
				this.pstackcontainer.addChild(info_cpane);
				// add txt + button cpane
				var txtbtn_cpane = new ContentPane({
					id:this.idmgr_obj.textbtncpane_id,
				})
				put(txtbtn_cpane.containerNode, "span[id=$]",
					this.idmgr_obj.text_id);
				put(txtbtn_cpane.containerNode, "button[id=$]",
					this.idmgr_obj.btn_id);
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
				// add info cpane and grid div
				var infogrid_cpane = new ContentPane({
					id:this.idmgr_obj.gridcpane_id,
				})
				put(infogrid_cpane.containerNode, "div[id=$]",
					this.idmgr_obj.grid_id);
				this.gstackcontainer.addChild(infogrid_cpane);
			},
			cleanup:function() {
				arrayUtil.forEach(this.tooltip_list, function(item) {
					item.destroyRecursive();
				});
				if (this.keyup_handle)
					this.keyup_handle.remove();
			}
		})
	}
);
