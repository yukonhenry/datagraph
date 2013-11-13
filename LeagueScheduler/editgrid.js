define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/_base/array", "dojo/store/Memory", "dijit/registry",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection",
	"dijit/form/ToggleButton",
	"LeagueScheduler/bracketinfo", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, Memory,
		registry, OnDemandGrid, editor, Keyboard, Selection, ToggleButton, BracketInfo) {
		return declare(null, {
			griddata_list:null, text_node:null,
			server_interface:null, colname:null,
			schedInfoStore:null, schedInfoGrid:null, updatebtn_node:null,
			grid_name:null, error_node:null, submitbtn_reg:null,
			errorHandle:null, datachangeHandle:null, submitHandle:null,
			divisioncode:null, idproperty:null, bracketinfo:null,
			tbutton_reg:null, schedutil_obj:null,
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
					this.tbutton_reg = new ToggleButton({showLabel: true, checked: false,
						onChange: lang.hitch(this, function(val){
							if (val) {
								this.tbutton_reg.set('label','Disable Bracket Edit');
							}
							else {
								this.tbutton_reg.set('label', 'Enable Bracket Edit');
							}
							// based on change of toggle, turn on/off bracket edit
							this.manageBracketEdit(val);
						}),
						label: "Enable Bracket Edit"}, "bracketenable_btn");

				}
			},
			manageBracketEdit: function(val) {
				// depending on toggle value enable/disable bracket editing
				if (this.rowSelectHandle){
					this.rowSelectHandle.remove();
				}
				if (val) {
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
				//this.schedInfoStore.query().forEach(function(division) {
        		//});
				this.server_interface.getServerData("create_newdbcol/"+this.colname,
					this.server_interface.server_ack, {divinfo_data:storedata_json});
			},
			cleanup: function() {
				if (this.schedInfoGrid) {
					dom.byId(this.grid_name).innerHTML = "";
					delete this.schedInfoGrid;
					this.makeInvisible(this.updatebtn_node);
					delete this.schedInfoStore;
					this.divisioncode = 0;
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
			}
		});
	})
