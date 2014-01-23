define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/dom-style", "dojo/_base/array",
	"dojo/store/Observable", "dojo/store/Memory", "dijit/registry",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection",
	"dgrid/CellSelection", "dijit/form/Button", "dijit/form/ToggleButton",
	"LeagueScheduler/bracketinfo", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, domStyle,
	         arrayUtil, Observable, Memory,
		registry, OnDemandGrid, editor, Keyboard, Selection, CellSelection,
		Button, ToggleButton, BracketInfo, baseinfoSingleton) {
		var constant = {
			infobtn_id:"infoBtnNode_id"
		};
		return declare(null, {
			griddata_list:null, text_node:null, text_node_str:"",
			server_interface:null, colname:null,
			schedInfoStore:null, schedInfoGrid:null,
			grid_id:"",
			error_node:null, updatebtn_str:"",
			errorHandle:null, datachangeHandle:null,
			divisioncode:null, idproperty:null, bracketinfo:null,
			tbutton_reg:null, cellselect_flag:false, cellselect_handle:null,
			server_callback:null, server_path:"", server_key:"",
			info_obj:null, uistackmgr:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			makeVisible: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			},
			makeInvisible: function(dom_name) {
				domClass.replace(dom_name, "style_none", "style_inline");
			},
			recreateSchedInfoGrid: function(columnsdef_obj) {
				var text_str = this.text_node_str + ": <b>"+this.colname+"</b>";
				this.text_node.innerHTML = text_str;
				var updatebtn_widget = this.getInfoBtn_widget(
					this.updatebtn_str, this.idproperty);
				var btn_callback = lang.hitch(this, this.sendDivInfoToServer);
				this.uistackmgr.switch_pstackcpane(this.idproperty, "config", text_str, btn_callback);
				// for finding dom node from dijit registry:
				// http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
				// make store observable
				// ref https://github.com/SitePen/dgrid/wiki/OnDemandList-and-OnDemandGrid
				// Observable Memory + dgrid has issues - switching to Memory only
				//this.schedInfoStore = new Observable(new Memory({data:this.griddata_list, idProperty:this.idproperty}));
				this.schedInfoStore = new Memory({data:this.griddata_list, idProperty:this.idproperty});
				// this is mainly for fieldinfo object - allow the store to be accessed from fieldinfo object.
				// 'in' operator is generic and works through inherited objects
				// To use hasOwnProperty, initialize the.info_obj w new Object()
				if (this.info_obj && 'editgrid_obj' in this.info_obj) {
					this.info_obj.editgrid_obj = this;
				}
				if (this.cellselect_flag) {
					this.schedInfoGrid = new (declare([OnDemandGrid, Keyboard, CellSelection]))({
						store: this.schedInfoStore,
						columns : columnsdef_obj,
						selectionMode:"single"
					}, this.grid_id);
				} else {
					this.schedInfoGrid = new (declare([OnDemandGrid, Keyboard, Selection]))({
						store: this.schedInfoStore,
						columns : columnsdef_obj,
						selectionMode:"single"
					}, this.grid_id);
				}
				this.schedInfoGrid.startup();
				// switch to content pane that has grid
				this.uistackmgr.switch_gstackcpane(this.idproperty);
				//scontainer_reg.selectChild(this.cpane_id);
				// the resize on grid is required; another option is to
				// have a callback on scontainer_reg.on('show')
				this.schedInfoGrid.resize();
				// track which grid content panes have grids in them
				if (this.info_obj && 'editgrid' in this.info_obj) {
					this.info_obj.editgrid = this.schedInfoGrid;
				}
				this.errorHandle = this.schedInfoGrid.on("dgrid-error", function(event) {
					console.log("dgrid error fired");
					this.error_node.className = "message error";
					this.error_node.innerHTML = event.error.message;
				});
				this.datachangeHandle = this.schedInfoGrid.on("dgrid-datachange",
					lang.hitch(this, this.editschedInfoGrid));
				// do straight overrride on button onclick event handler
				// so that we don't have to worry about handler clean-up
				updatebtn_widget.set("onClick",
					lang.hitch(this, this.sendDivInfoToServer));
				/*
				this.submitHandle = this.updatebtn_widget.on("click",
					lang.hitch(this, this.sendDivInfoToServer));
				*/
				if (this.cellselect_flag) {
					this.manageCellSelect();
				}
				if (this.idproperty == 'div_id') {
					this.tbutton_reg = baseinfoSingleton.get_tbutton_reg();
					if (!this.tbutton_reg) {
						this.tbutton_reg = new ToggleButton({showLabel: true, checked: false,
							onChange: lang.hitch(this, function(val){
								if (val) {
									this.tbutton_reg.set('label','Disable Bracket Edit');
								} else {
									this.tbutton_reg.set('label', 'Enable Bracket Edit');
								}
								// based on change of toggle, turn on/off bracket edit
								this.manageBracketEdit(val);
							}),
							label: "Enable Bracket Edit", type:"button"}, "bracketenable_btn");
						this.tbutton_reg.startup();
						baseinfoSingleton.set_tbutton_reg(this.tbutton_reg);
					} else {
						// togglebutton widget already exists, merely show
						// ref http://stackoverflow.com/questions/18096763/how-can-i-hide-a-dijit-form-button
						//domClass.add(this.tbutton_reg.domNode, "dijitToggleButton info");
						domStyle.set(this.tbutton_reg.domNode, 'display', 'inline');
					}
				}
			},
			manageCellSelect: function() {
				if (this.cellselect_handle)
					this.cellselect_handle.remove();
				this.cellselect_handle = this.schedInfoGrid.on("dgrid-select", lang.hitch(this, this.cellSelectHandler));
			},
			manageBracketEdit: function(val) {
				// depending on toggle value enable/disable bracket editing
				if (this.rowSelectHandle){
					this.rowSelectHandle.remove();
				}
				if (val) {
					// if toggle switch is true
					this.rowSelectHandle = this.schedInfoGrid.on("dgrid-select",lang.hitch(this, this.rowSelectHandler));
				} else {
					if (this.bracketinfo) {
						this.bracketinfo.bracketinfotext_node.innerHTML = "";
						this.bracketinfo.cleanup();
						delete this.bracketinfo;
					}
				}
			},
			editschedInfoGrid: function(event) {
				var val = event.value;
        		console.log("gridval="+val+' replace='+event.oldValue+ ' cell row='+event.rowId +
        			'col='+event.cell.column.field);
        		var columntype = event.cell.column.field;
        		event.grid.columns[columntype].columntype = true;
			},
			rowSelectHandler: function(event) {
				var eventdata = event.rows[0].data
				var div_str = eventdata.div_age + eventdata.div_gen;
				var totalbrackets = eventdata.totalbrackets;
				if (this.bracketinfo) {
					this.bracketinfo.cleanup();
					delete this.bracketinfo;
				}
				this.bracketinfo = new BracketInfo({totalbrackets:totalbrackets,
					bracketinfo_name:"bracketInfoInputGrid",
					bracketinfotext_node:dom.byId("bracketInfoNodeText")});
				this.bracketinfo.createBracketInfoGrid(div_str);
			},
			cellSelectHandler: function(event) {
				if (this.info_obj) {
					var eventcell = event.cells[0];
					var row_id = eventcell.row.id;
					var column_name = eventcell.column.id;
					if (column_name == 'dates') {
						// pass collection name to edit_calendar handler as it will be
						// making independent requests to the server
						//this.info_obj.edit_calendar(parseInt(row_id), this.colname);
					}
				}
			},
			sendDivInfoToServer: function(event) {
				storedata_json = JSON.stringify(this.schedInfoStore.query());
				var server_callback = this.server_callback || this.server_interface.server_ack;
				var server_path = this.server_path || "create_newdbcol/";
				var server_key = this.server_key || 'divinfo_data';
				var server_key_obj = {};
				server_key_obj[server_key] = storedata_json;
				var options_obj = {item:this.colname};
				this.server_interface.getServerData(server_path+this.colname,
					server_callback, server_key_obj, options_obj);
				baseinfoSingleton.addto_dbname_list(this.colname);
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
			cleanup: function() {
				if (this.bracketinfo) {
					this.bracketinfo.cleanup();
					delete this.bracketinfo;
				}
				if (this.schedInfoGrid) {
					dom.byId(this.grid_id).innerHTML = "";
					delete this.schedInfoGrid;
					delete this.schedInfoStore;
					this.divisioncode = 0;
					this.text_node.innerHTML = "";
				}
				if (this.errorHandle) {
					this.error_node.innerHTML = "";
					//delete this.error_node;
					this.errorHandle.remove();
				}
				if (this.datachangeHandle)
					this.datachangeHandle.remove();
				if (this.rowSelectHandle)
					this.rowSelectHandle.remove();
				if (this.cellselect_handle)
					this.cellselect_handle.remove();
				if (this.tbutton_reg)
					domStyle.set(this.tbutton_reg.domNode, 'display', 'none');
			}
		});
	})
