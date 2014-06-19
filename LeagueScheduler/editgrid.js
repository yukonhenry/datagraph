define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/dom-style", "dojo/_base/array", "dojo/date",
	"dojo/store/Observable", "dojo/store/Memory", "dijit/registry",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection",
	"dgrid/CellSelection", "dijit/form/ToggleButton", "dijit/Tooltip",
	"LeagueScheduler/baseinfoSingleton", "dojo/domReady!"
	], function(dbootstrap, dom, on, declare, lang, domClass, domStyle,
	         arrayUtil, date, Observable, Memory,
		registry, OnDemandGrid, editor, Keyboard, Selection, CellSelection,
		ToggleButton, Tooltip, baseinfoSingleton) {
		return declare(null, {
			griddata_list:null,
			server_interface:null, colname:null,
			schedInfoStore:null, schedInfoGrid:null,
			grid_id:"",
			error_node:null,
			errorHandle:null, datachangeHandle:null, header_handle:null,
			idproperty:null,
			cellselect_flag:false, cellselect_handle:null, refresh_handle:null,
			server_path:"", server_key:"",
			info_obj:null, uistackmgr_type:null, storeutil_obj:null, db_type:null,
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
					this.idproperty == 'tourndiv_id' ) {
				//	|| this.idproperty == 'pref_id') {
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
				this.uistackmgr_type.switch_gstackcpane(this.idproperty, false,
					this.schedInfoGrid);
				//scontainer_reg.selectChild(this.cpane_id);
				// the resize on grid is required; another option is to
				// have a callback on scontainer_reg.on('show')
				// HOWEVER, comment out resize as we moved the resize function
				//into the switch_gstackcpane function
				// CORRECTION: resize needed for initial grid
				this.schedInfoGrid.resize();
				// enable help tool tips for each grid created
				this.info_obj.enable_gridtooltips(this.schedInfoGrid);
				if ('infogrid_store' in this.info_obj) {
					// set property that divinfo collection has been selected
					this.info_obj.infogrid_store = this.schedInfoStore;
				}
				// IMPORTANT: call to colname_obj.set needs to be later than
				// setting info_obj.infogrid_store above as colname_obj watch
				// function utilizes infogrid_store (for div_id idprop)
				this.errorHandle = this.schedInfoGrid.on("dgrid-error", function(event) {
					console.log("dgrid error fired, event=", event);
					//this.error_node.className = "message error";
					//this.error_node.innerHTML = event.error.message;
				});
				if (this.datachangeHandle)
					this.datachangeHandle.remove();
				//this.datachangeHandle = this.schedInfoGrid.on("dgrid-datachange",
				//	lang.hitch(this, this.editschedInfoGrid));
				this.datachangeHandle = this.schedInfoGrid.on("dgrid-datachange",
					lang.hitch(this, this.editschedInfoGrid));
				if (this.cellselect_flag) {
					this.manageCellSelect();
				}
				if (this.header_handle)
					this.header_handle.remove();
				this.header_handle = this.schedInfoGrid.on("dgrid-sort",
					lang.hitch(this, function(event) {
						if (this.idproperty == "field_id") {
							// deal with bug where renderCell gets fired
							// after grid is rendered and when header row
							// gets clicked on any column.
							this.info_obj.rendercell_flag = false;
						} else {
							// turn it back on
							this.info_obj.rendercell_flag = true;
						}
				}));
				/*
				if (this.refresh_handle)
					this.refresh_handle.remove();
				this.refresh_handle = this.schedInfoGrid.on(
					"dgrid-refresh-complete", lang.hitch(this, function(event) {
					if (this.idproperty == 'pref_id') {
						this.info_obj.create_gridselect(event.grid);
					}
				})); */
			},
			manageCellSelect: function() {
				if (this.cellselect_handle)
					this.cellselect_handle.remove();
				this.cellselect_handle = this.schedInfoGrid.on("dgrid-select", lang.hitch(this, this.cellSelectHandler));
			},
			editschedInfoGrid: function(event) {
				var val = event.value;
        		console.log("gridval="+val+' replace='+event.oldValue+ ' cell row='+event.rowId +
        			'col='+event.cell.column.field);
        		if (this.idproperty == 'div_id') {
        			if (event.cell.column.id == 'numgdaysperweek') {
        				// enable single shot writes to mingap and maxgap columns
        				event.grid.columns.mingap_days.change_flag = true;
        				event.grid.columns.maxgap_days.change_flag = true;
        			}
        		}
        		//var columntype = event.cell.column.field;
        		//event.grid.columns[columntype].columntype = true;
			},
			rowSelectHandler: function(event) {
				var eventdata = event.rows[0].data
				var div_str = eventdata.div_age + eventdata.div_gen;
				var totalbrackets = eventdata.totalbrackets;
			},
			cellSelectHandler: function(event) {
				if (this.info_obj) {
					var eventcell = event.cells[0];
					var row_id = eventcell.row.id;
					var column_name = eventcell.column.id;
					if (column_name == 'detaileddates') {
						// pass collection name to edit_calendar handler as it will be
						// making independent requests to the server
						//this.info_obj.edit_calendar(parseInt(row_id), this.colname);
					}
				}
			},
			sendStoreInfoToServer: function(gridstatus_node, event) {
				var raw_result = this.schedInfoStore.query();
				var config_status = this.info_obj.checkconfig_status(raw_result);
				this.info_obj.update_configdone(config_status, gridstatus_node);
				var storedata_json = null;
				var server_path = this.server_path;
				var server_key = this.server_key || "";
				var server_key_obj = {};
				if (this.idproperty == "field_id" || this.idproperty == "pref_id" ||
					this.idproperty == "team_id") {
					if (this.idproperty == "team_id") {
						// no need to modify result for team_id
						storedata_json = JSON.stringify(raw_result);
					} else {
						var newlist = null;
						// for field or pref id's modify grid data before sending to
						// server - also attach divstr information also
						newlist = this.info_obj.modify_toserver_data(raw_result);
						storedata_json = JSON.stringify(newlist);
					}
					divstr_obj = this.info_obj.getdivstr_obj();
					// get colname and db_type for the divinfo obj attached to the
					// current fieldinfo obj.
					server_key_obj.divstr_colname = divstr_obj.colname;
					server_key_obj.divstr_db_type = divstr_obj.db_type;
				} else {
					storedata_json = JSON.stringify(raw_result);
				}
				server_key_obj[server_key] = storedata_json;
				server_key_obj.config_status = config_status;
				//server_key_obj.db_type = this.db_type;
				//var options_obj = {item:this.colname};  // is this needed?
				this.server_interface.getServerData(
					server_path+this.db_type+'/'+this.colname,
					this.server_interface.server_ack, server_key_obj);
				// add to select db store (for dropdowns)
				this.storeutil_obj.addtodb_store(this.colname, this.idproperty, config_status);
			},
			replace_store: function(colname, griddata_list) {
				//reference http://www.sitepen.com/blog/2013/09/06/dojo-faq-how-can-i-add-filtering-controls-to-dgrid/
				// Note we should be setting filtering queries to the store, instead
				// of doing setData everytime new data comes in
				// setData does not work with observable stores - see comment in fieldinfo.js
				this.colname = colname;
				this.schedInfoStore.setData(griddata_list);
				this.schedInfoGrid.refresh();
				this.schedInfoGrid.resize();
				// we might not always need to switch the gstack, but do it
				// by default right now
				this.uistackmgr_type.switch_gstackcpane(this.idproperty, false, this.schedInfoGrid);
				if ('infogrid_store' in this.info_obj) {
					// set property that divinfo collection has been selected
					this.info_obj.infogrid_store = this.schedInfoStore;
				}
			},
			cleanup: function() {
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
				if (this.refresh_handle)
					this.refresh_handle.remove();
			}
		});
	})
