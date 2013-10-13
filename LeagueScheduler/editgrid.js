define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/_base/array", "dojo/keys", "dojo/store/Memory",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, keys, Memory,
		OnDemandGrid, editor, Keyboard, Selection) {
		return declare(null, {
			divinfo_list:null, text_node:null,
			server_interface:null, colname:null,
			divInfoStore:null, divInfoGrid:null, updatediv_node:null,
			divInfoGridName:null, error_node:null, submitbtn_reg:null,
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
			recreateDivInfoGrid: function() {
				this.text_node.innerHTML = "Schedule Name: <b>"+this.colname+"</b>";
				// for finding dom node from dijit registry:
				// http://dojotoolkit.org/reference-guide/1.9/dijit/info.html
				this.makeVisible(this.updatediv_node);
				this.divInfoStore = new Memory({data:this.divinfo_list, idProperty:"div_id"});
				this.divInfoGrid = new (declare([OnDemandGrid, Keyboard, Selection]))({
            		store: this.divInfoStore,
            		columns: {
                		div_id: "Div ID",
                		div_age: editor({label:"Age", field:"div_age", autoSave:true},"text","dblclick"),
                		div_gen: editor({label:"Gender", field:"div_gen", autoSave:true}, "text", "dblclick"),
                		totalteams: editor({label:"Total Teams", field:"totalteams", autoSave:true},
                			"text", "dblclick"),
                		totalbrackets: editor({label:"Total RR Brackets", field:"totalbrackets", autoSave:true},
                			"text", "dblclick"),
                		elimination_num: editor({label:"Elimination #", field:"elimination_num", autoSave:true},
                			"text", "dblclick"),
                		field_id_str: editor({label:"Fields", field:"field_id_str", autoSave:true},
                			"text", "dblclick"),
                		gameinterval: editor({label:"Inter-Game Interval (min)", field:"gameinterval", autoSave:true},
                			"text", "dblclick"),
                        rr_gamedays: editor({label:"Number RR Gamedays", field:"rr_gamedays", autoSave:true},
                            "text", "dblclick")
                	}
                }, this.divInfoGridName);
				this.divInfoGrid.startup();
				this.errorHandle = this.divInfoGrid.on("dgrid-error", function(event) {
					console.log("dgrid error fired");
					this.error_node.className = "message error";
					this.error_node.innerHTML = event.error.message;
				});
				this.datachangeHandle = this.divInfoGrid.on("dgrid-datachange",
					lang.hitch(this, this.editDivInfoGrid));
				this.submitHandle = this.submitbtn_reg.on("click",
					lang.hitch(this, this.sendDivInfoToServer));
			},
			editDivInfoGrid: function(event) {
				var val = event.value;
        		console.log("gridval="+val+' replace='+event.oldValue+ ' cell row='+event.rowId +
        			'col='+event.cell.column.field);
			},
			sendDivInfoToServer: function(event) {
				storedata_json = JSON.stringify(this.divInfoStore.query());
				//this.divInfoStore.query().forEach(function(division) {
        		//});
				this.server_interface.getServerData("create_newdbcol/"+this.colname,
					this.server_interface.server_ack, {divinfo_data:storedata_json});
			},
			cleanup: function(event) {
				if (this.divInfoGrid) {
					dom.byId(this.divInfoGridName).innerHTML = "";
					delete this.divInfoGrid;
					this.makeInVisible(this.updatediv_node);
					delete this.divInfoStore;
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
