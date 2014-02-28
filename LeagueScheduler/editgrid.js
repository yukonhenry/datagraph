define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/dom-style", "dojo/_base/array", "dojo/date",
	"dojo/store/Observable", "dojo/store/Memory", "dijit/registry",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection",
	"dgrid/CellSelection", "dijit/form/ToggleButton",
	"LeagueScheduler/baseinfoSingleton", "dojo/domReady!"
	], function(dbootstrap, dom, on, declare, lang, domClass, domStyle,
	         arrayUtil, date, Observable, Memory,
		registry, OnDemandGrid, editor, Keyboard, Selection, CellSelection,
		ToggleButton, baseinfoSingleton) {
		return declare(null, {
			griddata_list:null,
			server_interface:null, colname:null,
			schedInfoStore:null, schedInfoGrid:null,
			grid_id:"",
			error_node:null,
			errorHandle:null, datachangeHandle:null, header_handle:null,
			idproperty:null,
			tbutton_reg:null, cellselect_flag:false, cellselect_handle:null,
			server_path:"", server_key:"",
			info_obj:null, uistackmgr:null, storeutil_obj:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			recreateSchedInfoGrid: function(columnsdef_obj) {
				// for finding dom node from dijit registry:
				// http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
				// make store observable
				// ref https://github.com/SitePen/dgrid/wiki/OnDemandList-and-OnDemandGrid
				// Observable Memory + dgrid has issues - switching to Memory only
				if (this.idproperty == 'div_id' ||
					this.idproperty == 'tourndiv_id') {
					this.schedInfoStore = new Observable(new Memory({data:this.griddata_list, idProperty:this.idproperty}));
				} else {
					this.schedInfoStore = new Memory({data:this.griddata_list, idProperty:this.idproperty});
				}
				// this is mainly for fieldinfo object - allow the store to be accessed from fieldinfo object.
				// 'in' operator is generic and works through inherited objects
				// To use hasOwnProperty, initialize the.info_obj w new Object()
				/*
				if (this.info_obj && 'editgrid_obj' in this.info_obj) {
					this.info_obj.editgrid_obj = this;
				} */
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
				// switch to content pane that has above generated grid
				this.uistackmgr.switch_gstackcpane(this.idproperty, false,
					this.schedInfoGrid);
				//scontainer_reg.selectChild(this.cpane_id);
				// the resize on grid is required; another option is to
				// have a callback on scontainer_reg.on('show')
				this.schedInfoGrid.resize();
				// track which grid content panes have grids in them
				// looks like editgrid_obj is servering same purpose
				//if (this.info_obj && 'editgrid' in this.info_obj) {
				//	this.info_obj.editgrid = this.schedInfoGrid;
				//}
				if ('infogrid_store' in this.info_obj) {
					// set property that divinfo collection has been selected
					this.info_obj.infogrid_store = this.schedInfoStore;
				}
				// IMPORTANT: call to colname_obj.set needs to be later than
				// setting info_obj.infogrid_store above as colname_obj watch
				// function utilizes infogrid_store (for div_id idprop)
				this.info_obj.colname_obj.set("colname", this.colname);
				this.errorHandle = this.schedInfoGrid.on("dgrid-error", function(event) {
					console.log("dgrid error fired");
					this.error_node.className = "message error";
					this.error_node.innerHTML = event.error.message;
				});
				if (this.datachangeHandle)
					this.datachangeHandle.remove();
				//this.datachangeHandle = this.schedInfoGrid.on("dgrid-datachange",
				//	lang.hitch(this, this.editschedInfoGrid));
				this.datachangeHandle = this.schedInfoGrid.on("dgrid-datachange",
					this.editschedInfoGrid);
				if (this.cellselect_flag) {
					this.manageCellSelect();
				}
				if (this.header_handle)
					this.header_handle.remove();
				this.header_handle = this.schedInfoGrid.on("dgrid-sort",
					lang.hitch(this, function(event) {
						if (event.grid.id == "fieldinfogrid_id") {
							// deal with bug where renderCell gets fired
							// after grid is rendered and when header row
							// gets clicked on any column.
							this.info_obj.rendercell_flag = false;
						}
					}));
				/*
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
				*/
			},
			manageCellSelect: function() {
				if (this.cellselect_handle)
					this.cellselect_handle.remove();
				this.cellselect_handle = this.schedInfoGrid.on("dgrid-select", lang.hitch(this, this.cellSelectHandler));
			},
			/*
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
			}, */
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
				/*
				if (this.bracketinfo) {
					this.bracketinfo.cleanup();
					delete this.bracketinfo;
				}
				this.bracketinfo = new BracketInfo({totalbrackets:totalbrackets,
					bracketinfo_name:"bracketInfoInputGrid",
					bracketinfotext_node:dom.byId("bracketInfoNodeText")});
				this.bracketinfo.createBracketInfoGrid(div_str);
				*/
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
				var raw_result = this.schedInfoStore.query();
				// do check to make sure all fields have been filled.
				// note construct of using arrayUtil.some works better than
				// query.filter() as loop will exit immediately if .some() returns
				// true.
				var configdone_flag = false;
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
					console.log("Not all fields complete, but saving");
				} else {
					configdone_flag = true;
				}
				this.info_obj.update_configdone(configdone_flag);
				var storedata_json = null;
				if (this.idproperty == "field_id") {
					var newlist = new Array();
					// for the field grid data convert Data objects to str
					// note we want to keep it as data objects inside of store to
					// maintain direct compatibility with Date and TimeTextBox's
					// and associated picker widgets.
					raw_result.map(function(item) {
						var newobj = lang.clone(item);
						newobj.start_date = newobj.start_date.toLocaleDateString();
						newobj.end_date = newobj.end_date.toLocaleDateString();
						newobj.start_time = newobj.start_time.toLocaleTimeString();
						newobj.end_time = newobj.end_time.toLocaleTimeString();
						return newobj;
					}).forEach(function(obj) {
						newlist.push(obj);
					});
					storedata_json = JSON.stringify(newlist);
				} else {
					storedata_json = JSON.stringify(raw_result);
				}
				var server_path = this.server_path || "create_newdbcol/";
				var server_key = this.server_key || "";
				var server_key_obj = {};
				server_key_obj[server_key] = storedata_json;
				server_key_obj.configdone_flag = configdone_flag;
				var options_obj = {item:this.colname};
				this.server_interface.getServerData(server_path+this.colname,
					this.server_interface.server_ack, server_key_obj, options_obj);
				this.storeutil_obj.addtodb_store(this.colname, this.idproperty);
			},
			replace_store: function(colname, griddata_list) {
				this.colname = colname;
				this.schedInfoStore.setData(griddata_list);
				this.schedInfoGrid.refresh();
				// we might not always need to switch the gstack, but do it
				// by default right now
				this.uistackmgr.switch_gstackcpane(this.idproperty, false, this.schedInfoGrid);
				if ('infogrid_store' in this.info_obj) {
					// set property that divinfo collection has been selected
					this.info_obj.infogrid_store = this.schedInfoStore;
				}
				this.info_obj.colname_obj.set("colname", colname);
			},
			cleanup: function() {
				/*
				if (this.bracketinfo) {
					this.bracketinfo.cleanup();
					delete this.bracketinfo;
				} */
				if (this.schedInfoGrid) {
					dom.byId(this.grid_id).innerHTML = "";
					delete this.schedInfoGrid;
					delete this.schedInfoStore;
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
