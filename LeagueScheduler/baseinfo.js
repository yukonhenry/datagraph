define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/_base/array", "dojo/keys", "dojo/Stateful",
	"dijit/registry", "dijit/Tooltip", "dijit/form/Button",
	"dijit/form/RadioButton", "LeagueScheduler/widgetgen",
	"LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton",
	"put-selector/put",
	"dojo/domReady!"],
	function(dbootstrap, dom, declare, lang, arrayUtil, keys, Stateful,
		registry, Tooltip, Button, RadioButton, WidgetGen, EditGrid, baseinfoSingleton,
		put) {
		var constant = {
			infobtn_id:"infobtn_id",
			text_id:"infotxt_id",
			// entry_pt id's
			init:"init", fromdb:"fromdb",  fromdel:"fromdel",
		};
		return declare(null, {
			server_interface:null, editgrid:null, uistackmgr:null,
			storeutil_obj:null,
			keyup_handle:null, tooltip_list:null, totalrows_num:0,
			schedutil_obj:null, activegrid_colname:"",
			config_status:0,
			btntxtid_list:null, op_type:"",
			constructor: function(args) {
				lang.mixin(this, args);
				this.tooltip_list = new Array();
				this.btntxtid_list = new Array();
				this.btntxtid_list.push({op_type:"advance", btn_id:"infobtn_id",
					text_id:"infotxt_id"});
				this.btntxtid_list.push({op_type:"wizard", id:"div_id",
					btn_id:"wizdivinfobtn_id", text_id:"wizdivinfotxt_id"})
				// tourndiv maps to the same id's as div
				this.btntxtid_list.push({op_type:"wizard", id:"tourndiv_id",
					btn_id:"wizdivinfobtn_id", text_id:"wizdivinfotxt_id"})
				this.btntxtid_list.push({op_type:"wizard", id:"field_id",
					btn_id:"wizfieldinfobtn_id", text_id:"wizfieldinfotxt_id"})
				this.btntxtid_list.push({op_type:"wizard", id:"pref_id",
					btn_id:"wizprefinfobtn_id", text_id:"wizprefinfotxt_id"})
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
				this.uistackmgr.switch_pstackcpane({idproperty:this.idproperty,
					p_stage: "preconfig", entry_pt:constant.init});
				// switch to blank cpane
				this.uistackmgr.switch_gstackcpane(this.idproperty, true);
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
					var server_path = args_obj.server_path;
					var server_key = args_obj.server_key;
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
						if (this.idproperty == 'field_id' ||
							this.idproperty == 'pref_id') {
							// field_id-specific UI above grid
							this.initabovegrid_UI();
						} else if (this.idproperty == 'div_id') {
							this.create_calendar_input(op_type);
						}
						if (newgrid_flag) {
							var columnsdef_obj = this.getcolumnsdef_obj();
							this.editgrid = new EditGrid({griddata_list:info_list,
								colname:this.activegrid_colname,
								server_interface:this.server_interface,
								grid_id:grid_id,
								//error_node:dom.byId("divisionInfoInputGridErrorNode"),
								idproperty:this.idproperty,
								server_path:server_path,
								server_key:server_key,
								cellselect_flag:cellselect_flag,
								info_obj:this,
								uistackmgr:this.uistackmgr,
								storeutil_obj:this.storeutil_obj,
								db_type:this.db_type});
							this.editgrid.recreateSchedInfoGrid(columnsdef_obj);
							var args_obj = {
								colname:this.activegrid_colname,
								text_node_str:text_node_str,
								updatebtn_str:updatebtn_str,
								idproperty:this.idproperty,
								swapcpane_flag:true,
								newgrid_flag:true
							}
						} else {
							this.editgrid.replace_store(this.activegrid_colname, info_list);
							var args_obj = {
								colname:this.activegrid_colname,
								text_node_str:text_node_str,
								updatebtn_str:updatebtn_str,
								idproperty:this.idproperty,
								swapcpane_flag:true,
								newgrid_flag:false
							}
						}
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
			initabovegrid_UI: function() {
				this.create_dbselect_radiobtnselect(
					this.idmgr_obj.radiobtn1_id, this.idmgr_obj.radiobtn2_id,
					this.idmgr_obj.league_select_id);
			},
			create_dbselect_radiobtnselect: function(radio1_id, radio2_id, select_id, init_db_type, init_colname) {
				// passed in init_db_type and init_colname are typicall
				// for divinfo(divstr) db_type and colname even though it
				// is used for fieldinfo grid
				var init_db_type = init_db_type || "";
				var init_colname = init_colname || "";
				//For field grids, create radio button pair to select
				// schedule type - rr or tourn
				var infogrid_node = dom.byId(this.idmgr_obj.grid_id);
				var topdiv_node = put(infogrid_node, "-div");
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
					onchange_callback:lang.hitch(this.widgetgen, this.widgetgen.getname_list, this),
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
				// define key for object returned from server to get
				// status of configuration - config_status
				options_obj.serverstatus_key = 'config_status'
				this.server_interface.getServerData(
					options_obj.getserver_path+options_obj.db_type+'/'+item,
					lang.hitch(this, this.createEditGrid), null, options_obj);
			},
			createEditGrid: function(server_data, options_obj) {
				// don't create grid if a grid already exists and it points to the same schedule db col
				// if grid needs to be generated, make sure to clean up prior to recreating editGrid
				this.activegrid_colname = options_obj.item;
				var columnsdef_obj = options_obj.columnsdef_obj;
				var idproperty = options_obj.idproperty;
				// if server data is fielddb information, then we need to do
				// some data conversion (convert to date obj) before passing onto grid
				// Note server_key is key for outgoing request
				// serverdata_key is for incoming data
				var data_list = server_data[options_obj.serverdata_key];
				// extract configuration status from server. integer value 0/1
				var config_status = server_data[options_obj.serverstatus_key];
				/*
				var serverdb_type = server_data.db_type;
				if (serverdb_type != this.db_type) {
					// db_type retruned from server should match up with this obj's
					// db_type; if not, reanalyze
					console.log("createEditGrid: warning: check db_type/serverdb_type logic");
				} */
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
						server_path:options_obj.server_path,
						server_key:options_obj.server_key,
						cellselect_flag:options_obj.cellselect_flag,
						info_obj:this,
						uistackmgr:this.uistackmgr,
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
				var btntxtid_obj = this.getbtntxtid_obj(op_type, idproperty);
				var text_id = btntxtid_obj.text_id;
				var btn_id = btntxtid_obj.btn_id;
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
					this.uistackmgr.switch_pstackcpane({idproperty:idproperty,
						p_stage:"config", entry_pt:entry_pt,
						text_str:text_str, btn_callback: btn_callback,
						updatebtn_str:updatebtn_str});
					if (!newgrid_flag) {
						// also swap grid if we are not generating a new one
						// if we are generating a new grid, switchgstack is called
						// from within editgrid
						this.uistackmgr.switch_gstackcpane(idproperty, false,
							this.editgrid.schedInfoGrid);
					}
				}
				return gridstatus_node
			},
			reconfig_infobtn_fromuistack: function(args_obj) {
				// parse args object
				var op_type = ('op_type' in args_obj)?args_obj.op_type:"advance";
				var idproperty = args_obj.idproperty;
				var btntxtid_obj = this.getbtntxtid_obj(op_type, idproperty);
				var text_id = btntxtid_obj.text_id;
				var btn_id = btntxtid_obj.btn_id;
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
			getbtntxtid_obj: function (op_type, idproperty) {
				var text_id = null;
				var btn_id = null;
				var idmatch_list = this.getmatch_list(this.btntxtid_list,
					'op_type', op_type)
				if (op_type == "advance") {
					text_id = idmatch_list[0].text_id;
					btn_id = idmatch_list[0].btn_id;
				} else  {
					var idmatch_obj = this.getuniquematch_obj(idmatch_list, 'id',
						idproperty);
					text_id = idmatch_obj.text_id;
					btn_id = idmatch_obj.btn_id;
				}
				return {text_id:text_id, btn_id:btn_id}
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
