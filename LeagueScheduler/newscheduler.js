define(["dbootstrap", "dojo/dom", "dojo/on", "dojo/_base/declare", "dojo/_base/lang", 
	"dojo/dom-class", "dojo/_base/array", "dojo/store/Memory",
	"dgrid/OnDemandGrid", "dgrid/editor", "dgrid/Keyboard", "dgrid/Selection", "dojo/domReady!"],
	function(dbootstrap, dom, on, declare, lang, domClass, arrayUtil, Memory,
		OnDemandGrid, editor, Keyboard, Selection) {
		return declare(null, {
			dbname_reg : null, form_reg: null, server_interface:null,
			divnum_reg: null, divInfoStore:null, divInfoGrid:null,
			divInfoGridName:null,
			constructor: function(args) {
				lang.mixin(this, args);
			},
			makeVisible: function(dom_name) {
				domClass.replace(dom_name, "style_inline", "style_none");
			},
			// ref http://dojotoolkit.org/documentation/tutorials/1.9/key_events/
			processdbname_input: function(event) {
				if (this.form_reg.validate()) {
					confirm('Input Name is Valid, creating new Schedule DB');
					newdb_name = this.dbname_reg.get("value");
					divnum = this.divnum_reg.get("value");
					console.log("newdb="+newdb_name+" divnum="+divnum);
					this.createDivInfoGrid(divnum);
					on(this.divInfoGrid, "dgrid-datachange",
						lang.hitch(this, this.editDivInfoGrid));
					this.server_interface.getServerData("createnewdb", this.newdb_ack,
						{newdb_name:newdb_name});
				} else {
						alert('Input name is Invalid, please correct');
				}
			},
			newdb_ack: function(adata) {
				console.log("data returned"+adata.test);
			},
			createDivInfoGrid: function(divnum) {
				if (this.divInfoGrid) {
					dom.byId(this.divInfoGridName).innerHTML = "";
					delete this.divInfoGrid;
				}
				divInfo_list = new Array();
				for (var i = 1; i < divnum+1; i++) {
					divInfo_list.push({div_id:i, div_age:"", div_gen:"",
						totalteams:1, totalbrackets:1});
				}
				this.divInfoStore = new Memory({data:divInfo_list, idProperty:"div_id"});
				this.divInfoGrid = new (declare([OnDemandGrid, Keyboard, Selection]))({
            		store: this.divInfoStore,
            		columns: {
                		div_id: "Div ID",
                		div_age: editor({label:"Age", field:"div_age"},"text","dblclick"),
                		div_gen: editor({label:"Gen", field:"div_gen"}, "text", "dblclick"),
                		totalteams: editor({label:"Total Teams", field:"totalteams"}, "text", "dblclick"),
                		totalbrackets: editor({label:"Total Brackets", field:"totalbrackets"}, "text", "dblclick")
                	}
                }, this.divInfoGridName);
				this.divInfoGrid.startup();
			},
			editDivInfoGrid: function(event) {
				var val = event.value;
        		console.log("gridval="+val+' replace='+event.oldValue+ ' cell row='+event.rowId +
        			'col='+event.cell.column.field);				
			}

		});
	})