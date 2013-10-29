define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang",
	"dojo/dom-class", "dojo/_base/array", "dojo/keys", "dojo/store/Memory",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection", "LeagueScheduler/divinfo", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, keys, Memory,
		OnDemandGrid, editor, Keyboard, Selection, divinfo) {
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			divnum_reg: null, divInfoStore:null, divInfoGrid:null,
			divInfoGridName:null, error_node:null, newcol_name: null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			makeVisible: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdivinfo_input: function(event) {
				if (event.keyCode == keys.ENTER) {
					if (this.form_reg.validate()) {
						confirm('Input Name is Valid, creating new Schedule DB');
						this.newcol_name = this.dbname_reg.get("value");
						divnum = this.divnum_reg.get("value");
						console.log("newdb="+this.newcol_name+" divnum="+divnum);
						this.createDivInfoGrid(divnum);
						on(this.divInfoGrid, "dgrid-datachange",
							lang.hitch(this, this.editDivInfoGrid));
					} else {
						alert('Input name is Invalid, please correct');
					}
				}
			},
			createDivInfoGrid: function(divnum) {
				if (this.divInfoGrid) {
					dom.byId(this.divInfoGridName).innerHTML = "";
					delete this.divInfoGrid;
				}
				divInfo_list = new Array();
				for (var i = 1; i < divnum+1; i++) {
					divInfo_list.push({div_id:i, div_age:"", div_gen:"",
						totalteams:1, totalbrackets:1, elimination_num:1,
						elimination_type:"",
						field_id_str:"", gameinterval:1, rr_gamedays:1});
				}
				this.divInfoStore = new Memory({data:divInfo_list, idProperty:"div_id"});
				divinfo_grid = new divinfo;
				columnsdef_obj = divinfo_grid.columnsdef_obj;
				this.divInfoGrid = new (declare([OnDemandGrid, Keyboard, Selection]))({
            		store: this.divInfoStore,
            		columns: columnsdef_obj
                }, this.divInfoGridName);
				this.divInfoGrid.startup();
				this.divInfoGrid.on("dgrid-error", function(event) {
					this.error_node.className = "message error";
					this.error_node.innerHTML = event.error.message;
				});
			},
			editDivInfoGrid: function(event) {
				var val = event.value;
        		console.log("gridval="+val+' replace='+event.oldValue+ ' cell row='+event.rowId +
        			'col='+event.cell.column.field);
			},
			sendDivInfoToServer: function(event) {
				if (this.form_reg.validate()) {
					storedata_json = JSON.stringify(this.divInfoStore.query());
					//this.divInfoStore.query().forEach(function(division) {
        			//});
					this.server_interface.getServerData("create_newdbcol/"+this.newcol_name,
						this.server_interface.server_ack, {divinfo_data:storedata_json});
				}
			}
		});
	})
