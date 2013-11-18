define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/dom-style", "dojo/_base/array", "dojo/store/Memory", "dijit/registry",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection",
	"dijit/form/ToggleButton",
	"LeagueScheduler/bracketinfo", "LeagueScheduler/baseinfoSingleton", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, domStyle,
	         arrayUtil, Memory,
		registry, OnDemandGrid, editor, Keyboard, Selection, ToggleButton, BracketInfo, baseinfoSingleton) {
		return declare(null, {
			griddata_list:null, text_node:null,
			server_interface:null, colname:null,
			schedInfoStore:null, schedInfoGrid:null, updatebtn_node:null,
			grid_name:null, error_node:null, submitbtn_reg:null,
			errorHandle:null, datachangeHandle:null, submitHandle:null,
			divisioncode:null, idproperty:null, bracketinfo:null,
			tbutton_reg:null,
			server_callback:null, server_path:"", server_key:"",
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
				this.text_node.innerHTML = "Schedule Name: <b>"+this.colname+"</b>";
				// for finding dom node from dijit registry:
				// http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
				this.makeVisible(this.updatebtn_node);
				this.schedInfoStore = new Memory({data:this.griddata_list, idProperty:this.idproperty});
				this.schedInfoGrid = new (declare([OnDemandGrid, Keyboard, Selection]))({
					store: this.schedInfoStore,
					columns : columnsdef_obj
				}, this.grid_name);
				this.schedInfoGrid.startup();
				this.errorHandle = this.schedInfoGrid.on("dgrid-error", function(event) {
					console.log("dgrid error fired");
					this.error_node.className = "message error";
					this.error_node.innerHTML = event.error.message;
				});
				this.datachangeHandle = this.schedInfoGrid.on("dgrid-datachange",
					lang.hitch(this, this.editschedInfoGrid));
				this.submitHandle = this.submitbtn_reg.on("click",
					lang.hitch(this, this.sendDivInfoToServer));
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
			cleanup: function() {
				if (this.bracketinfo) {
					this.bracketinfo.cleanup();
					delete this.bracketinfo;
				}
				if (this.schedInfoGrid) {
					dom.byId(this.grid_name).innerHTML = "";
					delete this.schedInfoGrid;
					this.makeInvisible(this.updatebtn_node);
					delete this.schedInfoStore;
					this.divisioncode = 0;
					this.text_node.innerHTML = "";
				}
				if (this.errorHandle) {
					this.error_node.innerHTML = "";
					delete this.error_node;
					this.errorHandle.remove();
				}
				if (this.datachangeHandle)
					this.datachangeHandle.remove();
				if (this.submitHandle)
					this.submitHandle.remove();
				if (this.rowSelectHandle)
					this.rowSelectHandle.remove();
				if (this.tbutton_reg)
					domStyle.set(this.tbutton_reg.domNode, 'display', 'none');
			}
		});
	})
