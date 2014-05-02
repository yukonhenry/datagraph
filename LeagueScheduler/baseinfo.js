define(["dbootstrap", "dojo/dom", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/_base/array", "dojo/keys", "dojo/Stateful",
	"dijit/registry", "dijit/Tooltip", "dijit/form/Button",
	"dijit/form/RadioButton",
	"LeagueScheduler/editgrid", "LeagueScheduler/baseinfoSingleton",
	"put-selector/put",
	"dojo/domReady!"],
	function(dbootstrap, dom, declare, lang, arrayUtil, keys, Stateful,
		registry, Tooltip, Button, RadioButton, EditGrid, baseinfoSingleton,
		put) {
		var constant = {
			infobtn_id:"infoBtnNode_id",
			text_id:"infoTextNode_id",
			// entry_pt id's
			init:"init", fromdb:"fromdb",  fromdel:"fromdel",
		};
		return declare(null, {
			server_interface:null, editgrid:null, uistackmgr:null,
			storeutil_obj:null, text_node:null,
			keyup_handle:null, tooltip_list:null, rownum:0,
			button_div:null, schedutil_obj:null, activegrid_colname:"",
			constructor: function(args) {
				lang.mixin(this, args);
				this.text_node = dom.byId(constant.text_id);
				this.tooltip_list = new Array();
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
					if (form_reg.validate()) {
						confirm('Input format is Valid, creating new DB');
						this.activegrid_colname = dbname_reg.get("value")
						if (!this.storeutil_obj.nodupdb_validate(
							this.activegrid_colname, this.idproperty)) {
							alert("Selected sched name already exists, choose another");
							return;
						}
						//rownum, is the total # of divisions/fields/current config
						this.rownum = entrynum_reg.get("value");
						var info_list = this.getInitialList(this.rownum);
						if (this.keyup_handle)
							this.keyup_handle.remove();
						// if idproperty is field, create radio buttons for
						// db selection (for div select)
						if (this.idproperty == 'field_id') {
							// field_id-specific UI above grid
							this.initabovegrid_UI();
						} else if (this.idproperty == 'div_id') {
							this.create_calendar_input();
						}
						if (newgrid_flag) {
							var columnsdef_obj = this.getcolumnsdef_obj();
							this.editgrid = new EditGrid({griddata_list:info_list,
								colname:this.activegrid_colname,
								server_interface:this.server_interface,
								grid_id:grid_id,
								error_node:dom.byId("divisionInfoInputGridErrorNode"),
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
						this.reconfig_infobtn(args_obj);
					} else {
						alert('Input name is Invalid, please correct');
					}
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
				//options_obj.storeutil_obj = this.storeutil_obj;
				// define key for object returned from server to get
				// status of configuration - config_status
				options_obj.serverstatus_key = 'config_status'
				/*
				var query_obj = null;
				if ('db_type' in options_obj) {
					query_obj = {db_type:options_obj.db_type};
				} */
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
				this.rownum = data_list.length;
				if (options_obj.db_type == 'fielddb') {
					if (idproperty == 'field_id') {
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
						error_node:dom.byId("divisionInfoInputGridErrorNode"),
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
				this.reconfig_infobtn(args_obj);
				// add config status text next to update btn
				this.update_configdone(config_status);
			},
			// function to reassign infobtn_update with title string and callback
			// function.  Also update pstack/gstack_cpane.
			reconfig_infobtn: function(args_obj) {
				// parse args object
				this.activegrid_colname = args_obj.colname;
				var text_node_str = args_obj.text_node_str;
				var updatebtn_str = args_obj.updatebtn_str;
				var idproperty = args_obj.idproperty;
				var swapcpane_flag = args_obj.swapcpane_flag;
				var newgrid_flag = args_obj.newgrid_flag;
				var entry_pt = args_obj.entry_pt;

				var text_str = text_node_str + ": <b>"+this.activegrid_colname+"</b>";
				this.text_node.innerHTML = text_str;
				var updatebtn_widget = this.getInfoBtn_widget(updatebtn_str,
					idproperty);
				var btn_callback = lang.hitch(this.editgrid, this.editgrid.sendStoreInfoToServer);
				updatebtn_widget.set("onClick", btn_callback);
				var gridstatus_node = this.get_gridstatus_node(updatebtn_widget);
				this.update_configdone(-1); // reset
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
			},
			reconfig_infobtn_fromuistack: function(args_obj) {
				// parse args object
				this.text_node.innerHTML = args_obj.text_str;
				var updatebtn_str = args_obj.updatebtn_str;
				var updatebtn_widget = this.getInfoBtn_widget(updatebtn_str,
					args_obj.idproperty);
				var btn_callback = args_obj.btn_callback;
				updatebtn_widget.set("onClick", btn_callback);
				var gridstatus_node = this.get_gridstatus_node(updatebtn_widget);
				this.update_configdone(-1); // reset
				// https://github.com/kriszyp/put-selector
				// button is enclosed in a div
				// outer div has class that has the float:right property
				/*
				var generate_button = null;
				if (!this.button_div) {
					this.button_div = put(updatebtn_widget.domNode,
						"+div.generate_button button");
					generate_button = new Button({
						label:"Generate", type:"button", class:"success"},
						this.button_div);
					generate_button.startup();
				} else {
					generate_button = registry.byId(this.button_div);
				} */
			},
			getInfoBtn_widget: function(label_str, idproperty_str) {
				var infobtn_widget = registry.byId(constant.infobtn_id);
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
						info_type:idproperty_str
					}, constant.infobtn_id);
					infobtn_widget.startup();
				}
				return infobtn_widget;
			},
			get_gridstatus_node: function(updatebtn_widget) {
				var gridstatus_node = dom.byId('gridstatus_span');
				if (!gridstatus_node) {
					gridstatus_node = put(updatebtn_widget.domNode,
						"+span.empty_smallgap_color#gridstatus_span");
					//gridstatus_node.innerHTML = 'test span';
				}
				return gridstatus_node;
			},
			update_configdone: function(config_status) {
				var gridstatus_node = dom.byId('gridstatus_span');
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
			set_obj: function(schedutil_obj, storeutil_obj) {
				this.schedutil_obj = schedutil_obj;
				this.storeutil_obj = storeutil_obj;
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
