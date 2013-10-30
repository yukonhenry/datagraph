define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/_base/array", "dojo/keys", "dojo/store/Memory",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection",
	"LeagueScheduler/divinfo", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, keys, Memory,
		OnDemandGrid, editor, Keyboard, Selection, divinfo) {
		return declare(null, {
			griddata_list:null, text_node:null,
			server_interface:null, colname:null,
			schedInfoStore:null, schedInfoGrid:null, updatebtn_node:null,
			grid_name:null, error_node:null, submitbtn_reg:null,
			errorHandle:null, datachangeHandle:null, submitHandle:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			makeVisible: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			},
			makeInvisible: function(dom_name) {
				domClass.replace(dom_name, "style_none", "style_inline");
			},
			recreateSchedInfoGrid: function() {
				this.text_node.innerHTML = "Schedule Name: <b>"+this.colname+"</b>";
				// for finding dom node from dijit registry:
				// http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
				this.makeVisible(this.updatebtn_node);
				this.schedInfoStore = new Memory({data:this.griddata_list, idProperty:"div_id"});
				divinfo_grid = new divinfo;
				columnsdef_obj = divinfo_grid.columnsdef_obj;
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
			},
			editschedInfoGrid: function(event) {
				var val = event.value;
        		console.log("gridval="+val+' replace='+event.oldValue+ ' cell row='+event.rowId +
        			'col='+event.cell.column.field);
			},
			sendDivInfoToServer: function(event) {
				storedata_json = JSON.stringify(this.schedInfoStore.query());
				//this.schedInfoStore.query().forEach(function(division) {
        		//});
				this.server_interface.getServerData("create_newdbcol/"+this.colname,
					this.server_interface.server_ack, {divinfo_data:storedata_json});
			},
			cleanup: function(event) {
				if (this.schedInfoGrid) {
					dom.byId(this.grid_name).innerHTML = "";
					delete this.schedInfoGrid;
					this.makeInVisible(this.updatebtn_node);
					delete this.schedInfoStore;
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
			}
		});
	})
